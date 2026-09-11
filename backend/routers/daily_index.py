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
    return {"data": []}
