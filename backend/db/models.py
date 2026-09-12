"""
SIH26056: Real-Time Airfare Price Index for India
Data Models & Pydantic Schemas Module
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class FlightObservation(BaseModel):
    record_id: str
    dataset_tier: str = "pan_india_calibrated_ledger"
    source_file: str = "portal_google_flights"
    travel_date: str
    travel_year: Optional[str] = "2026"
    origin_iata: str
    dest_iata: str
    route: str
    origin_raw: Optional[str] = None
    dest_raw: Optional[str] = None
    airline_standardized: str
    airline_raw: Optional[str] = None
    flight_number: Optional[str] = "6E 204"
    departure_time: Optional[str] = "10:00"
    arrival_time: Optional[str] = "12:15"
    duration_minutes: Optional[float] = 135.0
    duration_raw: Optional[str] = "2h 15m"
    cabin_class: str = "Economy"
    total_fare_inr: float
    base_fare_inr: Optional[float] = None
    taxes_fees_inr: Optional[float] = None
    convenience_fee_inr: Optional[float] = 0.0
    search_timestamp: Optional[str] = None
    lead_time_days: Optional[float] = 7.0
    is_defunct_carrier: Optional[bool] = False
    is_ambiguous_carrier: Optional[bool] = False
    is_fare_mild_outlier: Optional[bool] = False
    is_fare_extreme_outlier: Optional[bool] = False
    is_nonstop: Optional[bool] = True
    stops_count: Optional[int] = 0
    stop_info: Optional[str] = "Non-Stop"

class ScrapeRequest(BaseModel):
    platforms: List[str] = ["google_flights"]
    routes: List[str] = ["DEL-BOM"]
    lead_times: List[int] = [1, 7, 15, 30]
    cabin_class: str = "Economy"

class LiveSearchRequest(BaseModel):
    origin: str = "DEL"
    dest: str = "BOM"
    lead_time: str = "ALL"
    airline: str = "ALL"
    platform: str = "ALL"
    stops_filter: Optional[str] = "ALL"  # "ALL", "NONSTOP", "1_STOP", "2_PLUS_STOPS"
    cabin_class: str = "Economy"
    travel_date: Optional[str] = None
    force_scrape: Optional[bool] = False

class PolicySimRequest(BaseModel):
    fuel_surcharge_delta_pct: float = 0.0     # e.g., +15.0%
    route_cap_inr: Optional[float] = None     # e.g., max ₹8000 on economy
    demand_surge_factor: float = 1.0          # e.g., 1.25x for festival season
    target_routes: List[str] = []

class ReplayStartRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    speed_seconds_per_day: float = 1.5
    routes: List[str] = ["DEL-BOM", "BLR-DEL", "HYD-BBI", "DEL-JAI"]

class AirportMetadata(BaseModel):
    iata: str
    city: str
    state: str
    name: str
    lat: float
    lon: float
    is_hub: bool = False
    tier: str = "Metro"

class CarrierMetadata(BaseModel):
    airline: str
    code: str
    color: str
    class_name: str
    mean_fare_inr: float
    median_fare_inr: float
    min_fare_inr: float
    max_fare_inr: float
    observations_count: int
    market_share_pct: float
    delta_pct: float
    volatility: str
    volatility_class: str
    routes_served: str

class AnomalyRecord(BaseModel):
    id: str
    time: str
    route: str
    airline: str
    current_fare: float
    expected_fare: float
    deviation_pct: float
    severity: str
    z_score: float
    root_cause: str
