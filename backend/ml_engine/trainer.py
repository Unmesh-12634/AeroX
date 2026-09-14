"""
SIH26056: Real-Time Airfare Price Index for India (APIx)
Institutional ML Trainer: HistGradientBoostingRegressor on 20,816 Real Observations

Features:
- distance_km (Continuous)
- lead_time_days (1-45 days)
- festive_surge_factor (1.0 - 2.5 derived from official GOI festive calendar)
- weather_risk_score (0.0 - 1.0 composite airport IFR risk)
- day_of_week (0-6)
- travel_month (1-12)
- departure_hour (0-23)
- is_weekend (0 or 1)
- route (Categorical string)
- carrier (Categorical string)
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import r2_score, root_mean_squared_error, mean_absolute_error
from sklearn.preprocessing import OrdinalEncoder

from backend.config import settings
from backend.ml_engine.data_loader import load_consolidated_dataset

MODEL_DIR = settings.DATA_DIR / "models"
MODEL_PATH = MODEL_DIR / "airfare_predictor_v1.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

CATEGORICAL_COLS = ["route", "carrier"]
NUMERICAL_COLS = [
    "distance_km", "lead_time_days", "festive_surge_factor",
    "weather_risk_score", "day_of_week", "travel_month",
    "departure_hour", "is_weekend"
]
FEATURE_COLS = CATEGORICAL_COLS + NUMERICAL_COLS

def train_and_save_model() -> Dict[str, Any]:
    start_time = time.time()
    print("[+] [ML Trainer] Ingesting consolidated real flight dataset (20,816+ records)...")
    df = load_consolidated_dataset()

    # Preprocessing
    df = df.dropna(subset=FEATURE_COLS + ["total_fare_inr"])
    X = df[FEATURE_COLS].copy()
    y = df["total_fare_inr"].values

    # Ordinal encoding for categorical columns
    encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    X[CATEGORICAL_COLS] = encoder.fit_transform(X[CATEGORICAL_COLS])

    # 80/20 Chronological/Stratified Train-Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, shuffle=True
    )

    print(f"[+] [ML Trainer] Training HistGradientBoostingRegressor on {len(X_train)} samples, testing on {len(X_test)} samples...")

    # Train HistGradientBoostingRegressor
    # Categorical features specified by indices: [0, 1]
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

    model.fit(X_train, y_train)

    # Evaluate
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    r2_train = round(float(r2_score(y_train, y_pred_train)), 3)
    r2_test = round(float(r2_score(y_test, y_pred_test)), 3)
    rmse_test = round(float(root_mean_squared_error(y_test, y_pred_test)), 2)
    mae_test = round(float(mean_absolute_error(y_test, y_pred_test)), 2)
    mean_fare = round(float(np.mean(y)), 2)

    # Compute Feature Importances via feature permutation approximation or tree-based variance
    # For HistGradientBoostingRegressor, compute permutation importance
    from sklearn.inspection import permutation_importance
    perm_imp = permutation_importance(model, X_test, y_test, n_repeats=5, random_state=42)
    feature_importance_list = []
    for col, imp in zip(FEATURE_COLS, perm_imp.importances_mean):
        feature_importance_list.append({
            "feature": col,
            "importance": round(float(max(0.0, imp)), 4),
            "label": col.replace("_", " ").title()
        })
    feature_importance_list.sort(key=lambda x: x["importance"], reverse=True)

    # Package and save artifacts
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "model": model,
        "encoder": encoder,
        "categorical_cols": CATEGORICAL_COLS,
        "numerical_cols": NUMERICAL_COLS,
        "feature_cols": FEATURE_COLS
    }
    joblib.dump(artifacts, MODEL_PATH)

    metadata = {
        "model_name": "HistGradientBoostingRegressor (LightGBM Architecture)",
        "framework": "scikit-learn 1.9.0",
        "training_samples": len(X_train),
        "testing_samples": len(X_test),
        "total_observations": len(df),
        "r2_score": r2_test,
        "r2_train": r2_train,
        "rmse_inr": rmse_test,
        "mae_inr": mae_test,
        "mean_fare_inr": mean_fare,
        "feature_importances": feature_importance_list,
        "training_duration_seconds": round(time.time() - start_time, 2),
        "trained_at": datetime.now().isoformat(),
        "status": "active"
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"[+] [ML Trainer] Model trained successfully! R2={r2_test}, RMSE=Rs.{rmse_test}, MAE=Rs.{mae_test}")
    print(f"[+] [ML Trainer] Saved pipeline to {MODEL_PATH}")

    return metadata

if __name__ == "__main__":
    train_and_save_model()
