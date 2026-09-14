"""
SIH26056: Real-Time Airfare Price Index for India (APIx)
Incremental Retraining API Router

Endpoints:
  POST /api/v1/training/retrain          — Trigger immediate on-demand retrain
  GET  /api/v1/training/status           — Current model metrics + training health
  GET  /api/v1/training/audit-log        — Last N nightly retrain audit entries
  GET  /api/v1/training/guardrail-config — Live view of all 6 guardrail thresholds
"""

import json
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from backend.config import settings
from backend.ml_engine.incremental_trainer import (
    run_incremental_retrain,
    AUDIT_LOG_PATH,
    CHECKPOINT_PATH,
    MIN_NEW_RECORDS,
    MAX_R2_REGRESSION,
    IQR_OUTLIER_FACTOR,
    PROMO_FARE_THRESHOLD,
    MODEL_PATH,
    METADATA_PATH,
)

router = APIRouter(prefix="/training", tags=["Incremental ML Retraining"])

# In-memory lock to prevent concurrent retrains
_retrain_lock = threading.Lock()
_retrain_status: Dict[str, Any] = {"running": False, "last_result": None}


def _background_retrain(triggered_by: str):
    """Background thread wrapper with lock guard."""
    global _retrain_status
    if not _retrain_lock.acquire(blocking=False):
        return  # already running — silently skip
    try:
        _retrain_status["running"] = True
        result = run_incremental_retrain(triggered_by=triggered_by)
        _retrain_status["last_result"] = result
    finally:
        _retrain_status["running"] = False
        _retrain_lock.release()


@router.post("/retrain")
async def trigger_retrain(
    background_tasks: BackgroundTasks,
    triggered_by: str = Query("api_manual", description="Identifier of who triggered the retrain"),
    async_mode: bool = Query(True, description="If true, runs in background and returns immediately")
):
    """
    Trigger an immediate incremental retrain of the airfare ML model.

    The engine will:
    - Load all consolidated data (historical + live scraped)
    - Apply 6-layer validation guardrails
    - Train HistGradientBoostingRegressor with optimized hyperparameters
    - Hot-swap the in-memory predictor if new model passes the R² guard
    - Write an audit log entry

    Use async_mode=false to wait for the result synchronously (slower, ~15-20s).
    """
    if _retrain_status["running"]:
        raise HTTPException(
            status_code=409,
            detail="A retrain is already running. Check /training/status for progress."
        )

    if async_mode:
        background_tasks.add_task(_background_retrain, triggered_by)
        return {
            "status": "accepted",
            "message": "Incremental retrain launched in background. Poll /training/status for completion.",
            "triggered_by": triggered_by,
            "async_mode": True
        }
    else:
        # Synchronous — wait for result
        result = run_incremental_retrain(triggered_by=triggered_by)
        _retrain_status["last_result"] = result
        return {
            "status": "completed",
            "result": result,
            "triggered_by": triggered_by
        }


@router.get("/status")
async def get_training_status():
    """
    Returns comprehensive ML model health:
    - Current R², RMSE, MAE from model_metadata.json
    - Whether a retrain is currently running
    - Last retrain result
    - Total records used, new records since last checkpoint
    - Training engine active status
    """
    metadata: Dict[str, Any] = {}
    if METADATA_PATH.exists():
        try:
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception:
            pass

    checkpoint: Dict[str, Any] = {}
    if CHECKPOINT_PATH.exists():
        try:
            with open(CHECKPOINT_PATH, "r") as f:
                checkpoint = json.load(f)
        except Exception:
            pass

    model_exists = MODEL_PATH.exists()
    model_size_kb = round(MODEL_PATH.stat().st_size / 1024, 1) if model_exists else 0

    return {
        "status": "success",
        "engine": {
            "model_active": model_exists,
            "model_size_kb": model_size_kb,
            "retrain_running": _retrain_status["running"],
            "last_result_summary": {
                k: v for k, v in (_retrain_status.get("last_result") or {}).items()
                if k not in ["feature_importances", "guardrail_stats"]
            }
        },
        "model_metrics": {
            "r2_test": metadata.get("r2_score"),
            "r2_train": metadata.get("r2_train"),
            "rmse_inr": metadata.get("rmse_inr"),
            "mae_inr": metadata.get("mae_inr"),
            "mean_fare_inr": metadata.get("mean_fare_inr"),
            "total_observations": metadata.get("total_observations"),
            "training_samples": metadata.get("training_samples"),
            "testing_samples": metadata.get("testing_samples"),
            "trained_at": metadata.get("trained_at"),
            "triggered_by": metadata.get("triggered_by", "initial_train"),
            "new_records_last_run": metadata.get("new_records_added", "N/A"),
            "training_duration_seconds": metadata.get("training_duration_seconds"),
        },
        "checkpoint": {
            "last_retrain": checkpoint.get("last_run"),
            "total_records_at_last_run": checkpoint.get("total_records_used"),
        },
        "feature_importances": metadata.get("feature_importances", []),
        "guardrail_rejection_summary": metadata.get("guardrail_rejection_summary", {})
    }


@router.get("/audit-log")
async def get_audit_log(
    last_n: int = Query(20, ge=1, le=100, description="Number of recent entries to return")
):
    """
    Returns the last N nightly/on-demand retrain audit log entries.
    Each entry shows: timestamp, status, R² delta, RMSE, new records, guardrail rejection counts.
    """
    if not AUDIT_LOG_PATH.exists():
        return {"status": "success", "entries": [], "message": "No retrain audit log found yet."}

    try:
        entries: List[Dict[str, Any]] = []
        with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        pass

        recent = list(reversed(entries[-last_n:]))
        return {
            "status": "success",
            "total_runs": len(entries),
            "returned": len(recent),
            "entries": recent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read audit log: {e}")


@router.get("/guardrail-config")
async def get_guardrail_config():
    """
    Returns all active validation guardrail thresholds used during retraining.
    """
    return {
        "status": "success",
        "guardrails": {
            "g1_fare_range": {
                "description": "Hard floor/ceiling for domestic Indian airfare",
                "floor_inr": 1500,
                "ceiling_inr": 90000,
                "action": "reject"
            },
            "g2_iqr_outlier": {
                "description": "Route-level IQR outlier rejection",
                "iqr_factor": IQR_OUTLIER_FACTOR,
                "formula": "reject if fare < Q1 - 3×IQR or fare > Q3 + 3×IQR per route",
                "action": "reject"
            },
            "g3_promotional_fare": {
                "description": "Promotional / flash-sale filter — prevents flash-sale fares from skewing weights",
                "threshold_pct": round(PROMO_FARE_THRESHOLD * 100, 0),
                "formula": f"reject if fare < {PROMO_FARE_THRESHOLD} × route_rolling_mean",
                "action": "reject"
            },
            "g4_duplicate": {
                "description": "Duplicate detection on (route, carrier, travel_date, departure_hour)",
                "dedup_keys": ["route", "carrier", "travel_date", "departure_hour"],
                "action": "keep_last"
            },
            "g5_minimum_batch": {
                "description": "Minimum new observations gate before retraining",
                "min_new_records": MIN_NEW_RECORDS,
                "action": "skip_retrain_if_below"
            },
            "g6_r2_regression_guard": {
                "description": "Rejects new model if R² drops too far vs current production model",
                "max_allowed_drop": MAX_R2_REGRESSION,
                "formula": f"reject if new_r2 < current_r2 - {MAX_R2_REGRESSION}",
                "action": "discard_new_model_keep_current"
            }
        }
    }
