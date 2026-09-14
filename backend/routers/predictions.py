"""
AeroX Live - Machine Learning Predictions & Scenario Simulator Router
Provides 30-day forecast curves, festival surges, weather disruption indices, and real-time inference.
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from backend.ml_engine.predictor import predictor
from backend.ml_engine.festive_calendar import FESTIVE_EVENTS, WEATHER_PROFILES, get_weather_disruption_risk

router = APIRouter(prefix="/predictions", tags=["ML Predictions & Simulation"])


class ScenarioSimulationRequest(BaseModel):
    route: str = Field(..., example="DEL-BOM", description="Origin-Destination corridor")
    carrier: str = Field(..., example="IndiGo", description="Airline carrier")
    lead_days: int = Field(14, ge=1, le=45, description="Days before departure")
    month: int = Field(10, ge=1, le=12, description="Departure month (1-12)")
    dep_hour: int = Field(10, ge=0, le=23, description="Departure hour (0-23)")
    is_weekend: bool = Field(False, description="Is flight on a weekend")
    apply_festive: bool = Field(True, description="Apply seasonal festive elasticity")
    apply_weather: bool = Field(True, description="Apply meteorological risk factor")


@router.get("/30-day-forecast")
async def get_30_day_forecast(
    route: str = Query("DEL-BOM", description="Flight corridor (e.g. DEL-BOM, BOM-BLR, DEL-CCU)"),
    carrier: str = Query("IndiGo", description="Airline carrier")
):
    """
    Returns 30-day daily fare forecast curve combining baseline lead-time decay/surge,
    authentic festive calendar surge points, and weather disruption risk.
    """
    try:
        forecast_result = predictor.generate_30_day_forecast(route=route, carrier=carrier)
        return {
            "status": "success",
            **forecast_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")



@router.post("/simulate")
async def simulate_flight_scenario(req: ScenarioSimulationRequest):
    """
    Simulates real-time pricing prediction under customized scenario parameters.
    """
    try:
        result = predictor.simulate_scenario(
            route=req.route,
            carrier=req.carrier,
            lead_time_days=req.lead_days,
            month=req.month,
            dep_hour=req.dep_hour,
            is_weekend=req.is_weekend,
            apply_festive=req.apply_festive,
            apply_weather=req.apply_weather
        )

        return {
            "status": "success",
            "scenario": req.dict(),
            "prediction": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


@router.get("/festivals")
async def get_festival_calendar():
    """
    Returns authentic Indian 2026 festive travel calendar with affected routes and surge multipliers.
    """
    return {
        "status": "success",
        "total_festivals": len(FESTIVE_EVENTS),
        "festivals": FESTIVE_EVENTS
    }


@router.get("/weather-risk")
async def get_weather_risk_index(
    airport: Optional[str] = Query(None, description="IATA code (e.g., DEL, BOM, CCU, SXR)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Month 1-12")
):
    """
    Returns empirical weather disruption risk index by airport and season.
    """
    if airport:
        code = airport.upper()
        if code not in WEATHER_PROFILES:
            raise HTTPException(status_code=404, detail=f"Weather profile for {code} not found")
        monthly_data = WEATHER_PROFILES[code]
        if month:
            risk = monthly_data.get(month, 0.15)
            return {"airport": code, "month": month, "risk_score": risk}
        return {"airport": code, "monthly_risk_scores": monthly_data}

    return {
        "status": "success",
        "airports": WEATHER_PROFILES
    }


@router.get("/model-metrics")
async def get_model_metrics():
    """
    Returns ML Model training metadata, evaluation benchmarks (R², RMSE, MAE),
    genuine record counts, and feature permutation importance.
    """
    metadata = predictor.get_metadata()
    return {
        "status": "success",
        "model_engine": "HistGradientBoostingRegressor",
        "framework": "scikit-learn 1.9.0",
        "metadata": metadata
    }
