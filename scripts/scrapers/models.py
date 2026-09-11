"""
SIH26056: Real-Time Airfare Price Index for India
Scraper Data Models & Normalization Helpers
"""

import re
from datetime import datetime, date
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import numpy as np
import pandas as pd

OFFICIAL_IATA_MAP = {
    'delhi': 'DEL', 'new delhi': 'DEL', 'del': 'DEL',
    'mumbai': 'BOM', 'bom': 'BOM',
    'bangalore': 'BLR', 'bengaluru': 'BLR', 'banglore': 'BLR', 'blr': 'BLR',
    'kolkata': 'CCU', 'ccu': 'CCU',
    'hyderabad': 'HYD', 'hyd': 'HYD',
    'chennai': 'MAA', 'maa': 'MAA',
    'cochin': 'COK', 'kochi': 'COK', 'cok': 'COK',
    'goa': 'GOI', 'goi': 'GOI', 'goa (dabolim)': 'GOI', 'goa (mopa)': 'GOX',
    'ahmedabad': 'AMD', 'amd': 'AMD',
    'pune': 'PNQ', 'pnq': 'PNQ',
    'jaipur': 'JAI', 'jai': 'JAI',
    'guwahati': 'GAU', 'gau': 'GAU',
    'srinagar': 'SXR', 'sxr': 'SXR'
}

AIRLINE_STANDARDIZATION = {
    'indigo': 'IndiGo',
    '6e': 'IndiGo',
    'air india': 'Air India',
    'ai': 'Air India',
    'vistara': 'Vistara',
    'uk': 'Vistara',
    'spicejet': 'SpiceJet',
    'sg': 'SpiceJet',
    'akasa air': 'Akasa Air',
    'akasa': 'Akasa Air',
    'qp': 'Akasa Air',
    'airasia': 'AirAsia India',
    'airasia india': 'AirAsia India',
    'aix connect': 'AirAsia India',
    'i5': 'AirAsia India',
    'air india express': 'Air India Express',
    'ix': 'Air India Express'
}

@dataclass
class ScrapedFlightObservation:
    record_id: str
    search_timestamp: str = ""     # ISO-8601 (YYYY-MM-DD HH:MM:SS)
    travel_date: str = ""          # ISO-8601 (YYYY-MM-DD)
    lead_time_days: int = 7        # (travel_date - search_date).days
    source_platform: str = "MakeMyTrip"  # e.g., 'google_flights', 'makemytrip', 'easemytrip', 'ixigo'
    origin_iata: str = "DEL"       # 3-letter IATA (DEL, BOM, etc.)
    dest_iata: str = "BOM"         # 3-letter IATA
    route: str = "DEL-BOM"         # ORIGIN-DEST (DEL-BOM)
    origin_raw: str = ""           # Unmodified raw string
    dest_raw: str = ""             # Unmodified raw string
    airline_standardized: str = "IndiGo"  # Clean carrier name (IndiGo, Air India, etc.)
    airline_raw: str = ""          # Raw carrier text from source
    flight_number: Optional[str] = None   # e.g., '6E 2131', 'AI 887', 'QP 1352'
    departure_time: str = "08:00"  # e.g., '06:00'
    arrival_time: str = "10:00"    # e.g., '08:15'
    duration_minutes: Optional[int] = 120 # Duration in integer minutes
    duration_raw: str = ""         # e.g., '2h 15m'
    cabin_class: str = "Economy"   # 'Economy' / 'Business'
    total_fare_inr: float = 5000.0 # Real observed fare in INR ₹
    base_fare_inr: Optional[float] = None
    taxes_fees_inr: Optional[float] = None
    is_nonstop: bool = True
    stops: Optional[str] = None
    raw_hash: Optional[str] = None # Provenance hash

    def __init__(self, **kwargs):
        # Handle field aliases
        self.record_id = kwargs.get("record_id", "SCR_001")
        self.search_timestamp = kwargs.get("search_timestamp") or kwargs.get("search_timestamp_utc", datetime.utcnow().isoformat())
        self.travel_date = kwargs.get("travel_date") or kwargs.get("departure_date", date.today().isoformat())
        self.lead_time_days = kwargs.get("lead_time_days") if kwargs.get("lead_time_days") is not None else kwargs.get("booking_lead_days", 7)
        self.source_platform = kwargs.get("source_platform") or kwargs.get("source_portal", "MakeMyTrip")
        self.origin_iata = kwargs.get("origin_iata", "DEL")
        self.dest_iata = kwargs.get("dest_iata", "BOM")
        self.route = kwargs.get("route", f"{self.origin_iata}-{self.dest_iata}")
        self.origin_raw = kwargs.get("origin_raw") or kwargs.get("origin_city", self.origin_iata)
        self.dest_raw = kwargs.get("dest_raw") or kwargs.get("dest_city", self.dest_iata)
        self.airline_standardized = kwargs.get("airline_standardized") or kwargs.get("airline_name", "IndiGo")
        self.airline_raw = kwargs.get("airline_raw", self.airline_standardized)
        self.flight_number = kwargs.get("flight_number")
        self.departure_time = kwargs.get("departure_time")
        self.arrival_time = kwargs.get("arrival_time")
        self.duration_minutes = kwargs.get("duration_minutes", 120)
        self.duration_raw = kwargs.get("duration_raw", f"{self.duration_minutes}m" if self.duration_minutes else "")
        self.cabin_class = kwargs.get("cabin_class") or kwargs.get("fare_class", "Economy")
        self.total_fare_inr = float(kwargs.get("total_fare_inr", 0.0))
        self.base_fare_inr = float(kwargs["base_fare_inr"]) if kwargs.get("base_fare_inr") is not None else None
        self.taxes_fees_inr = float(kwargs["taxes_fees_inr"]) if kwargs.get("taxes_fees_inr") is not None else None
        self.is_nonstop = bool(kwargs.get("is_nonstop", True))
        self.stops = kwargs.get("stops")
        self.raw_hash = kwargs.get("raw_hash")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def normalize_iata(val: str) -> str:
    clean = str(val).strip().lower()
    return OFFICIAL_IATA_MAP.get(clean, clean.upper())

def normalize_airline(val: str) -> str:
    clean = str(val).strip().lower()
    return AIRLINE_STANDARDIZATION.get(clean, str(val).strip().title())

def parse_price(val: Any) -> float:
    if pd.isna(val):
        return np.nan
    s = str(val).replace(',', '').replace('₹', '').replace('Rs.', '').replace('Rs', '').replace('INR', '').strip()
    try:
        return float(s)
    except ValueError:
        return np.nan

def parse_duration_to_mins(val: str) -> Optional[int]:
    if not val:
        return None
    s = str(val).strip().lower()
    h_match = re.search(r'(\d+)\s*(?:h|hr|hrs)', s)
    m_match = re.search(r'(\d+)\s*(?:m|min|mins)', s)
    hours = int(h_match.group(1)) if h_match else 0
    mins = int(m_match.group(1)) if m_match else 0
    if hours == 0 and mins == 0:
        if ':' in s:
            parts = s.split(':')
            try:
                return int(parts[0]) * 60 + int(parts[1])
            except:
                return None
        return None
    return hours * 60 + mins
