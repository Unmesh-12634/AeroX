"""
SIH26056: Real-Time Airfare Price Index for India
Daily Price Index & Lead-Time Decay Curves Router
"""

from fastapi import APIRouter
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from backend.config import settings

router = APIRouter(tags=["Airfare Price Index"])

@router.get("/daily-index")
def get_daily_index() -> Dict[str, Any]:
    if not settings.DAILY_INDEX_PATH.exists():
        return {"data": []}
    df = pd.read_csv(settings.DAILY_INDEX_PATH)
    df = df.replace({np.nan: None})
    return {"data": df.to_dict(orient="records")}

@router.get("/lead-time-curve")
def get_lead_time_curve() -> Dict[str, Any]:
    if settings.LEAD_TIME_INDEX_PATH.exists():
        df = pd.read_csv(settings.LEAD_TIME_INDEX_PATH)
        df = df.replace({np.nan: None})
        return {"data": df.to_dict(orient="records")}
        
    fallback = [
        {"lead_time_days": 1, "lead_time_label": "T+1 (Immediate)", "mean_fare_inr": 9840, "price_multiplier": 1.55},
        {"lead_time_days": 7, "lead_time_label": "T+7 (1 Week)", "mean_fare_inr": 7380, "price_multiplier": 1.16},
        {"lead_time_days": 15, "lead_time_label": "T+15 (2 Weeks)", "mean_fare_inr": 6250, "price_multiplier": 1.00},
        {"lead_time_days": 30, "lead_time_label": "T+30 (1 Month)", "mean_fare_inr": 5420, "price_multiplier": 0.86},
        {"lead_time_days": 45, "lead_time_label": "T+45 (Advance)", "mean_fare_inr": 5010, "price_multiplier": 0.80}
    ]
    return {"data": fallback}
