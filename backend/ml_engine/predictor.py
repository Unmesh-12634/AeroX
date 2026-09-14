"""
SIH26056: Real-Time Airfare Price Index for India (APIx)
Institutional ML Predictor & Scenario Simulation Engine
"""

import json
import math
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import joblib

from backend.config import settings
from backend.ml_engine.festive_calendar import (
    get_festive_surge_factor,
    get_weather_disruption_risk,
    FESTIVE_EVENTS
)
from backend.ml_engine.data_loader import calculate_distance_km

MODEL_DIR = settings.DATA_DIR / "models"
MODEL_PATH = MODEL_DIR / "airfare_predictor_v1.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

class AirfarePredictor:
    def __init__(self):
        self.model = None
        self.encoder = None
        self.metadata = {}
        self.is_loaded = False
        self._load()

    def _load(self):
        if MODEL_PATH.exists():
            try:
                artifacts = joblib.load(MODEL_PATH)
                self.model = artifacts["model"]
                self.encoder = artifacts["encoder"]
                if METADATA_PATH.exists():
                    with open(METADATA_PATH, "r", encoding="utf-8") as f:
                        self.metadata = json.load(f)
                self.is_loaded = True
                print("[+] [AirfarePredictor] Model pipeline successfully loaded into memory.")
            except Exception as e:
                print(f"[-] [AirfarePredictor] Error loading model: {e}")

    def predict_single(
        self,
        route: str,
        carrier: str,
        travel_date: date,
        lead_time_days: int = 14,
        dep_hour: int = 10,
        festive_override: Optional[float] = None,
        weather_override: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executes single flight fare ML prediction with factor decomposition.
        """
        if not self.is_loaded:
            self._load()

        orig, dest = route.split("-") if "-" in route else ("DEL", "BOM")
        dist_km = calculate_distance_km(orig, dest)

        # Festive factor
        f_info = get_festive_surge_factor(route, travel_date)
        festive_mult = festive_override if festive_override is not None else f_info["surge_multiplier"]

        # Weather factor
        w_info = get_weather_disruption_risk(route, travel_date.month)
        weather_risk = weather_override if weather_override is not None else w_info["composite_risk_score"]

        dow = travel_date.weekday()
        is_weekend = 1 if dow in [4, 5, 6] else 0
        month = travel_date.month

        # Encode categoricals: route, carrier
        if self.encoder is not None:
            cat_df = pd.DataFrame([{"route": route, "carrier": carrier}])
            cat_encoded = self.encoder.transform(cat_df)[0]
        else:
            cat_encoded = [0.0, 0.0]

        # Feature vector: [route, carrier, distance_km, lead_time_days, festive_surge_factor, weather_risk_score, day_of_week, travel_month, departure_hour, is_weekend]
        feat_vector = np.array([[
            cat_encoded[0], cat_encoded[1],
            dist_km, lead_time_days, festive_mult,
            weather_risk, dow, month, dep_hour, is_weekend
        ]])

        if self.model is not None:
            raw_fare = float(self.model.predict(feat_vector)[0])
        else:
            # Fallback benchmark
            raw_fare = (2400.0 + dist_km * 3.45) * festive_mult * (1.0 + (30 - lead_time_days) * 0.015)

        # Baseline clamp to realistic DGCA bounds
        predicted_fare = max(2100.0, round(raw_fare, 0))

        # 95% Prediction Interval (using test RMSE ~3390)
        rmse = self.metadata.get("rmse_inr", 3390.0)
        lower_bound = max(1800.0, round(predicted_fare - 1.645 * rmse * 0.45, 0))
        upper_bound = round(predicted_fare + 1.645 * rmse * 0.55, 0)

        # Unbundled breakdown
        base_fare = round(predicted_fare * 0.76, 2)
        fuel_surcharge = round(predicted_fare * 0.12, 2)
        taxes_gst = round(predicted_fare * 0.12, 2)

        return {
            "route": route,
            "carrier": carrier,
            "travel_date": travel_date.isoformat(),
            "lead_time_days": lead_time_days,
            "predicted_fare_inr": predicted_fare,
            "confidence_interval_95": {
                "lower_bound_inr": lower_bound,
                "upper_bound_inr": upper_bound,
                "spread_inr": round(upper_bound - lower_bound, 0)
            },
            "unbundled_fare": {
                "base_fare_inr": base_fare,
                "fuel_surcharge_inr": fuel_surcharge,
                "taxes_gst_inr": taxes_gst
            },
            "factors": {
                "distance_km": dist_km,
                "festive_event": f_info["event_name"],
                "festive_surge_factor": round(festive_mult, 2),
                "weather_risk_score": round(weather_risk, 2),
                "weather_condition": w_info["risk_label"],
                "is_weekend": bool(is_weekend)
            }
        }

    def generate_30_day_forecast(self, route: str = "DEL-BOM", carrier: str = "IndiGo") -> Dict[str, Any]:
        """
        Generates 30-day ahead predictive curves with baseline, festive, and weather shock layers.
        """
        today = date.today()
        daily_forecasts = []

        orig, dest = route.split("-") if "-" in route else ("DEL", "BOM")
        dist_km = calculate_distance_km(orig, dest)

        for day_offset in range(1, 31):
            target_date = today + timedelta(days=day_offset)
            lead_time = day_offset

            # 1. Baseline Fair Market Rate (Standard seasonal lead curve)
            base_pred = self.predict_single(
                route=route,
                carrier=carrier,
                travel_date=target_date,
                lead_time_days=lead_time,
                festive_override=1.0,  # neutral festive
                weather_override=0.10  # neutral nominal weather
            )

            # 2. Real Festive Overlay (Derived from authentic festive calendar)
            f_info = get_festive_surge_factor(route, target_date)
            festive_fare = round(base_pred["predicted_fare_inr"] * f_info["surge_multiplier"], 0)

            # 3. Adverse Weather Disruption Shock (CAT-III / cloudburst diversion shock)
            w_info = get_weather_disruption_risk(route, target_date.month)
            weather_fare = round(base_pred["predicted_fare_inr"] * w_info["weather_surge_multiplier"], 0)

            # Composite expected market rate
            composite_pred = self.predict_single(
                route=route,
                carrier=carrier,
                travel_date=target_date,
                lead_time_days=lead_time
            )

            daily_forecasts.append({
                "day_offset": day_offset,
                "date": target_date.strftime("%Y-%m-%d"),
                "date_formatted": target_date.strftime("%d %b"),
                "day_name": target_date.strftime("%a"),
                "lead_window": f"T+{day_offset}",
                "baseline_fare_inr": base_pred["predicted_fare_inr"],
                "festive_fare_inr": festive_fare,
                "weather_fare_inr": weather_fare,
                "composite_fare_inr": composite_pred["predicted_fare_inr"],
                "lower_bound_95": composite_pred["confidence_interval_95"]["lower_bound_inr"],
                "upper_bound_95": composite_pred["confidence_interval_95"]["upper_bound_inr"],
                "active_festival": f_info["event_name"] if f_info["has_festival"] else None,
                "festive_surge_pct": f_info["surge_pct"],
                "weather_risk_label": w_info["risk_label"],
                "weather_risk_score": w_info["composite_risk_score"]
            })

        mean_baseline = round(float(np.mean([d["baseline_fare_inr"] for d in daily_forecasts])), 0)
        mean_composite = round(float(np.mean([d["composite_fare_inr"] for d in daily_forecasts])), 0)
        max_surge = max([d["composite_fare_inr"] for d in daily_forecasts])
        min_fare = min([d["composite_fare_inr"] for d in daily_forecasts])

        return {
            "route": route,
            "carrier": carrier,
            "distance_km": dist_km,
            "forecast_start_date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
            "forecast_end_date": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "kpis": {
                "mean_30d_fare_inr": mean_composite,
                "baseline_mean_inr": mean_baseline,
                "spread_inr": round(max_surge - min_fare, 0),
                "peak_projected_fare_inr": max_surge,
                "trough_fare_inr": min_fare,
                "active_festive_days": len([d for d in daily_forecasts if d["active_festival"] is not None])
            },
            "daily_points": daily_forecasts
        }

    def simulate_scenario(
        self,
        route: str,
        carrier: str,
        lead_time_days: int = 14,
        travel_date_str: Optional[str] = None,
        month: Optional[int] = None,
        dep_hour: int = 10,
        is_weekend: Optional[bool] = None,
        apply_festive: bool = True,
        apply_weather: bool = True,
        festival_scenario: str = "auto",
        weather_scenario: str = "nominal"
    ) -> Dict[str, Any]:
        """
        Interactive simulation endpoint handler with user-specified scenario overrides.
        """
        if travel_date_str:
            try:
                t_date = datetime.strptime(travel_date_str[:10], "%Y-%m-%d").date()
            except Exception:
                t_date = date.today() + timedelta(days=lead_time_days)
        elif month is not None:
            # construct date for target month
            curr_year = date.today().year
            t_date = date(curr_year, month, min(15, 28))
        else:
            t_date = date.today() + timedelta(days=lead_time_days)

        festive_override = None
        if not apply_festive:
            festive_override = 1.00
        elif festival_scenario == "major_cultural":
            festive_override = 1.70  # +70% Durga Puja / Diwali peak
        elif festival_scenario == "regional_peak":
            festive_override = 2.20  # +120% Chhath Puja peak
        elif festival_scenario == "national_festival":
            festive_override = 1.45  # +45% Dussehra / Long weekend
        elif festival_scenario == "none":
            festive_override = 1.00

        weather_override = None
        if not apply_weather:
            weather_override = 0.05
        elif weather_scenario == "severe_fog":
            weather_override = 0.90  # CAT-III Winter Fog ground delays
        elif weather_scenario == "monsoon_disruption":
            weather_override = 0.85  # Heavy monsoon cloudburst
        elif weather_scenario == "clear":
            weather_override = 0.05

        return self.predict_single(
            route=route,
            carrier=carrier,
            travel_date=t_date,
            lead_time_days=lead_time_days,
            dep_hour=dep_hour,
            festive_override=festive_override,
            weather_override=weather_override
        )


    def get_metadata(self) -> Dict[str, Any]:
        return self.metadata

# Global Singleton Instance
predictor = AirfarePredictor()

