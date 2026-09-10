"""
SIH26056: Real-Time Airfare Price Index for India
DGCA Backtesting & Verification Router
"""

from fastapi import APIRouter, Query
from typing import Dict, Any
from backend.index_engine.dgca_backtester import run_dgca_backtest

router = APIRouter(tags=["DGCA Backtest Verification"])

@router.get("/backtest/dgca")
def get_dgca_backtest(days: int = Query(30, ge=7, le=90)) -> Dict[str, Any]:
    return run_dgca_backtest(window_days=days)
