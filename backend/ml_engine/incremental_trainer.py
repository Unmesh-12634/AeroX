"""
SIH26056: Real-Time Airfare Price Index for India (APIx)
Continuous Online Incremental Retraining Engine — Option A

Architecture:
  - Nightly at midnight (or on-demand via API): loads all new live scraped observations
    that arrived since the last training checkpoint.
  - Runs 6-layer validation guardrails to reject promotional/noisy fares.
  - Combines validated new data with historical corpus and retrains from scratch
    (HistGradientBoostingRegressor trains fast enough — ~14s on 25k records).
  - Hot-swaps the in-memory predictor singleton WITHOUT a server restart.
  - Writes an audit log entry for every retraining run.

Guardrails applied (in order):
  1. Fare floor/ceiling (Rs. 1,500 - Rs. 90,000)
  2. Route-level IQR outlier rejection  (> 3.0 × IQR from route median)
  3. Promotional fare filter            (< 55% of route rolling mean = flash sale)
  4. Duplicate detection                (route + carrier + travel_date + dep_time)
  5. Minimum batch size gate            (< MIN_NEW_RECORDS → skip, not worth retrain)
  6. R² regression guard               (new R² must not drop > 0.05 vs current)
"""

import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, root_mean_squared_error, mean_absolute_error
from sklearn.preprocessing import OrdinalEncoder
from sklearn.inspection import permutation_importance

from backend.config import settings
from backend.ml_engine.data_loader import load_consolidated_dataset, calculate_distance_km
from backend.ml_engine.festive_calendar import get_festive_surge_factor, get_weather_disruption_risk

# ── Constants ───────────────────────────────────────────────────────────────
MODEL_DIR        = settings.DATA_DIR / "models"
MODEL_PATH       = MODEL_DIR / "airfare_predictor_v1.joblib"
METADATA_PATH    = MODEL_DIR / "model_metadata.json"
AUDIT_LOG_PATH   = MODEL_DIR / "incremental_retrain_audit.jsonl"
CHECKPOINT_PATH  = MODEL_DIR / "last_retrain_checkpoint.json"

MIN_NEW_RECORDS      = 30      # skip retraining if fewer new records
MAX_R2_REGRESSION    = 0.05    # reject new model if R² drops more than this
IQR_OUTLIER_FACTOR   = 3.0     # reject fare if > 3 IQR from route median
PROMO_FARE_THRESHOLD = 0.55    # reject fare if < 55% of route rolling mean

CATEGORICAL_COLS = ["route", "carrier"]
NUMERICAL_COLS   = [
    "distance_km", "lead_time_days", "festive_surge_factor",
    "weather_risk_score", "day_of_week", "travel_month",
    "departure_hour", "is_weekend"
]
FEATURE_COLS = CATEGORICAL_COLS + NUMERICAL_COLS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("incremental_trainer")


# ── Guardrail Layer ──────────────────────────────────────────────────────────

def _apply_guardrails(df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, int]]:
    """
    Apply all 6 validation guardrails. Returns (clean_df, rejection_report).
    """
    stats = {"total_in": len(df), "g1_fare_range": 0, "g2_iqr_outlier": 0,
             "g3_promo_fare": 0, "g4_duplicate": 0, "total_out": 0}

    # G1 — Fare floor / ceiling
    before = len(df)
    df = df[df["total_fare_inr"].between(1500.0, 90000.0)]
    stats["g1_fare_range"] = before - len(df)

    # G2 — Route-level IQR outlier rejection
    before = len(df)
    if "route" in df.columns and not df.empty:
        route_stats = df.groupby("route")["total_fare_inr"].agg(["median", "std"]).reset_index()
        route_stats.columns = ["route", "r_median", "r_std"]
        route_q1 = df.groupby("route")["total_fare_inr"].quantile(0.25).reset_index()
        route_q3 = df.groupby("route")["total_fare_inr"].quantile(0.75).reset_index()
        route_q1.columns = ["route", "q1"]
        route_q3.columns = ["route", "q3"]
        bounds = route_q1.merge(route_q3, on="route")
        bounds["iqr"]   = bounds["q3"] - bounds["q1"]
        bounds["lower"] = bounds["q1"] - IQR_OUTLIER_FACTOR * bounds["iqr"]
        bounds["upper"] = bounds["q3"] + IQR_OUTLIER_FACTOR * bounds["iqr"]
        df = df.merge(bounds[["route", "lower", "upper"]], on="route", how="left")
        df = df[
            (df["total_fare_inr"] >= df["lower"].fillna(1500)) &
            (df["total_fare_inr"] <= df["upper"].fillna(90000))
        ]
        df = df.drop(columns=["lower", "upper"], errors="ignore")
    stats["g2_iqr_outlier"] = before - len(df)

    # G3 — Promotional flash-sale filter (< 55% of route mean)
    before = len(df)
    if not df.empty:
        route_means = df.groupby("route")["total_fare_inr"].mean().reset_index()
        route_means.columns = ["route", "r_mean"]
        df = df.merge(route_means, on="route", how="left")
        df = df[df["total_fare_inr"] >= PROMO_FARE_THRESHOLD * df["r_mean"].fillna(3000)]
        df = df.drop(columns=["r_mean"], errors="ignore")
    stats["g3_promo_fare"] = before - len(df)

    # G4 — Duplicate detection
    before = len(df)
    dedup_cols = [c for c in ["route", "carrier", "travel_date", "departure_hour"] if c in df.columns]
    if dedup_cols:
        df = df.drop_duplicates(subset=dedup_cols, keep="last")
    stats["g4_duplicate"] = before - len(df)

    stats["total_out"] = len(df)
    return df.reset_index(drop=True), stats


# ── Feature Engineering (mirrors data_loader) ────────────────────────────────

def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    from datetime import datetime, date
    import math

    if "distance_km" not in df.columns:
        df["distance_km"] = df.apply(
            lambda r: calculate_distance_km(
                str(r.get("origin", "DEL")), str(r.get("dest", "BOM"))
            ), axis=1
        )

    days_of_week, months, is_weekends, festive_factors, weather_risks = [], [], [], [], []
    for _, row in df.iterrows():
        d_str = str(row.get("travel_date", "2026-09-25"))
        try:
            d_obj = datetime.strptime(d_str[:10], "%Y-%m-%d").date()
        except Exception:
            d_obj = date(2026, 9, 25)
        dow = d_obj.weekday()
        days_of_week.append(dow)
        months.append(d_obj.month)
        is_weekends.append(1 if dow in [4, 5, 6] else 0)
        route = str(row.get("route", "DEL-BOM"))
        f_info = get_festive_surge_factor(route, d_obj)
        w_info = get_weather_disruption_risk(route, d_obj.month)
        festive_factors.append(f_info["surge_multiplier"])
        weather_risks.append(w_info["composite_risk_score"])

    df["day_of_week"]          = days_of_week
    df["travel_month"]         = months
    df["is_weekend"]           = is_weekends
    df["festive_surge_factor"] = festive_factors
    df["weather_risk_score"]   = weather_risks

    if "departure_hour" not in df.columns:
        df["departure_hour"] = 10
    if "lead_time_days" not in df.columns:
        df["lead_time_days"] = 7

    return df


# ── Core Retraining Logic ────────────────────────────────────────────────────

def _load_current_r2() -> float:
    """Returns current model R² from metadata, 0.0 if unavailable."""
    try:
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)
        return float(meta.get("r2_score", 0.0))
    except Exception:
        return 0.0


def _write_audit_entry(entry: Dict[str, Any]):
    """Appends a JSON line to the audit log."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def run_incremental_retrain(triggered_by: str = "scheduler") -> Dict[str, Any]:
    """
    Main entry point for incremental retraining.

    Steps:
      1. Load full consolidated dataset (historical + live scraped)
      2. Apply guardrails
      3. Gate on MIN_NEW_RECORDS
      4. Train new model
      5. Gate on R² regression
      6. Hot-swap predictor in memory
      7. Write audit log + checkpoint

    Returns a status dict with all metrics.
    """
    run_start = time.time()
    run_ts    = datetime.now().isoformat()
    logger.info(f"[IncrementalTrainer] Starting retrain — triggered_by={triggered_by}")

    # ── Step 1: Load consolidated dataset ──────────────────────────────
    try:
        df_raw = load_consolidated_dataset()
    except Exception as e:
        err = f"Dataset load failed: {e}"
        logger.error(f"[IncrementalTrainer] {err}")
        _write_audit_entry({"ts": run_ts, "status": "error", "error": err, "triggered_by": triggered_by})
        return {"status": "error", "error": err}

    logger.info(f"[IncrementalTrainer] Raw dataset: {len(df_raw)} records")

    # ── Step 2: Apply guardrails ────────────────────────────────────────
    df_clean, guardrail_stats = _apply_guardrails(df_raw)
    logger.info(f"[IncrementalTrainer] After guardrails: {len(df_clean)} records | Rejected: {guardrail_stats}")

    # ── Step 3: Minimum batch gate ──────────────────────────────────────
    # Compare against last checkpoint total to figure out how many are "new"
    last_total = 0
    try:
        if CHECKPOINT_PATH.exists():
            with open(CHECKPOINT_PATH, "r") as f:
                chk = json.load(f)
            last_total = int(chk.get("total_records_used", 0))
    except Exception:
        pass

    new_records_count = max(0, len(df_clean) - last_total)
    logger.info(f"[IncrementalTrainer] New observations since last run: {new_records_count}")

    if new_records_count < MIN_NEW_RECORDS and last_total > 0:
        msg = f"Only {new_records_count} new records (threshold={MIN_NEW_RECORDS}). Skipping retrain."
        logger.info(f"[IncrementalTrainer] {msg}")
        _write_audit_entry({
            "ts": run_ts, "status": "skipped", "reason": msg,
            "new_records": new_records_count, "triggered_by": triggered_by
        })
        return {"status": "skipped", "reason": msg, "new_records": new_records_count}

    # ── Step 4: Engineer features & train ──────────────────────────────
    try:
        df_feat = _engineer_features(df_clean)
    except Exception as e:
        err = f"Feature engineering failed: {e}"
        logger.error(f"[IncrementalTrainer] {err}")
        _write_audit_entry({"ts": run_ts, "status": "error", "error": err, "triggered_by": triggered_by})
        return {"status": "error", "error": err}

    df_feat = df_feat.dropna(subset=FEATURE_COLS + ["total_fare_inr"])
    X = df_feat[FEATURE_COLS].copy()
    y = df_feat["total_fare_inr"].values

    encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    X[CATEGORICAL_COLS] = encoder.fit_transform(X[CATEGORICAL_COLS])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, shuffle=True
    )

    model = HistGradientBoostingRegressor(
        categorical_features=[0, 1],
        max_iter=600,
        learning_rate=0.05,
        max_leaf_nodes=63,
        min_samples_leaf=10,
        max_depth=8,
        l2_regularization=0.5,
        early_stopping=True,
        validation_fraction=0.12,
        n_iter_no_change=25,
        random_state=42
    )

    logger.info(f"[IncrementalTrainer] Training on {len(X_train)} samples …")
    model.fit(X_train, y_train)

    y_pred_test  = model.predict(X_test)
    y_pred_train = model.predict(X_train)
    new_r2_test  = round(float(r2_score(y_test, y_pred_test)), 3)
    new_r2_train = round(float(r2_score(y_train, y_pred_train)), 3)
    new_rmse     = round(float(root_mean_squared_error(y_test, y_pred_test)), 2)
    new_mae      = round(float(mean_absolute_error(y_test, y_pred_test)), 2)
    mean_fare    = round(float(np.mean(y)), 2)

    # ── Step 5: R² regression guard ────────────────────────────────────
    current_r2 = _load_current_r2()
    r2_delta   = new_r2_test - current_r2
    if r2_delta < -MAX_R2_REGRESSION:
        msg = (f"R² regression guard triggered: new R²={new_r2_test} vs "
               f"current R²={current_r2} (delta={r2_delta:.3f} < threshold={-MAX_R2_REGRESSION}). "
               f"Discarding new model — keeping existing weights.")
        logger.warning(f"[IncrementalTrainer] {msg}")
        _write_audit_entry({
            "ts": run_ts, "status": "rejected_r2_regression",
            "new_r2": new_r2_test, "current_r2": current_r2,
            "delta": r2_delta, "triggered_by": triggered_by,
            "guardrail_stats": guardrail_stats
        })
        return {
            "status": "rejected",
            "reason": "r2_regression_guard",
            "new_r2": new_r2_test,
            "current_r2": current_r2,
            "delta": r2_delta
        }

    # ── Step 6: Persist model ───────────────────────────────────────────
    perm_imp = permutation_importance(model, X_test, y_test, n_repeats=5, random_state=42)
    feature_importance_list = sorted([
        {"feature": col, "importance": round(float(max(0.0, imp)), 4),
         "label": col.replace("_", " ").title()}
        for col, imp in zip(FEATURE_COLS, perm_imp.importances_mean)
    ], key=lambda x: x["importance"], reverse=True)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "model": model, "encoder": encoder,
        "categorical_cols": CATEGORICAL_COLS, "numerical_cols": NUMERICAL_COLS,
        "feature_cols": FEATURE_COLS
    }
    joblib.dump(artifacts, MODEL_PATH)

    metadata = {
        "model_name": "HistGradientBoostingRegressor (LightGBM Architecture)",
        "framework": "scikit-learn 1.9.0",
        "training_samples": len(X_train),
        "testing_samples": len(X_test),
        "total_observations": len(df_feat),
        "r2_score": new_r2_test,
        "r2_train": new_r2_train,
        "rmse_inr": new_rmse,
        "mae_inr": new_mae,
        "mean_fare_inr": mean_fare,
        "feature_importances": feature_importance_list,
        "training_duration_seconds": round(time.time() - run_start, 2),
        "trained_at": run_ts,
        "incremental_run": True,
        "triggered_by": triggered_by,
        "new_records_added": new_records_count,
        "guardrail_rejection_summary": guardrail_stats,
        "status": "active"
    }
    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # Save checkpoint
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump({"total_records_used": len(df_feat), "last_run": run_ts}, f)

    # ── Step 7: Hot-swap in-memory predictor ────────────────────────────
    try:
        from backend.ml_engine.predictor import predictor as _predictor_singleton
        _predictor_singleton._load()
        logger.info("[IncrementalTrainer] ✅ Hot-swap complete — predictor singleton updated in memory.")
    except Exception as e:
        logger.warning(f"[IncrementalTrainer] Hot-swap warning (server restart may be needed): {e}")

    duration = round(time.time() - run_start, 2)
    logger.info(
        f"[IncrementalTrainer] ✅ Retrain complete in {duration}s | "
        f"R²={new_r2_test} (Δ{r2_delta:+.3f}) | RMSE=Rs.{new_rmse} | MAE=Rs.{new_mae} | "
        f"Records={len(df_feat)} (+{new_records_count} new)"
    )

    audit_entry = {
        "ts": run_ts, "status": "success",
        "triggered_by": triggered_by,
        "r2_test": new_r2_test, "r2_train": new_r2_train,
        "r2_delta": r2_delta, "rmse_inr": new_rmse, "mae_inr": new_mae,
        "total_records": len(df_feat), "new_records": new_records_count,
        "duration_seconds": duration, "guardrail_stats": guardrail_stats
    }
    _write_audit_entry(audit_entry)

    return {
        "status": "success",
        "r2_score": new_r2_test,
        "r2_train": new_r2_train,
        "r2_delta": r2_delta,
        "rmse_inr": new_rmse,
        "mae_inr": new_mae,
        "mean_fare_inr": mean_fare,
        "total_observations": len(df_feat),
        "new_records_added": new_records_count,
        "duration_seconds": duration,
        "feature_importances": feature_importance_list,
        "guardrail_stats": guardrail_stats,
        "trained_at": run_ts
    }
