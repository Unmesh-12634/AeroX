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
    # Metro Hubs & North
    'delhi': 'DEL', 'new delhi': 'DEL', 'del': 'DEL', 'ncr': 'DEL', 'indira gandhi': 'DEL',
    'chandigarh': 'IXC', 'ixc': 'IXC', 'punjab': 'IXC', 'haryana': 'IXC',
    'amritsar': 'ATQ', 'atq': 'ATQ',
    'srinagar': 'SXR', 'sxr': 'SXR', 'kashmir': 'SXR',
    'jammu': 'IXJ', 'ixj': 'IXJ',
    'leh': 'IXL', 'ixl': 'IXL', 'ladakh': 'IXL',
    'dehradun': 'DED', 'ded': 'DED', 'uttarakhand': 'DED',
    'jaipur': 'JAI', 'jai': 'JAI', 'rajasthan': 'JAI',
    'jodhpur': 'JDH', 'jdh': 'JDH',
    'udaipur': 'UDR', 'udr': 'UDR',
    'lucknow': 'LKO', 'lko': 'LKO', 'uttar pradesh': 'LKO',
    'varanasi': 'VNS', 'kashi': 'VNS', 'vns': 'VNS',

    # West Hubs
    'mumbai': 'BOM', 'bom': 'BOM', 'bombay': 'BOM', 'maharashtra': 'BOM',
    'pune': 'PNQ', 'pnq': 'PNQ',
    'ahmedabad': 'AMD', 'amd': 'AMD', 'gujarat': 'AMD',
    'vadodara': 'BDQ', 'bdq': 'BDQ',
    'nagpur': 'NAG', 'nag': 'NAG',
    'aurangabad': 'IXU', 'ixu': 'IXU', 'chhatrapati sambhajinagar': 'IXU',
    'goa': 'GOI', 'goi': 'GOI', 'goa (dabolim)': 'GOI', 'dabolim': 'GOI', 'panaji': 'GOI',
    'goa (mopa)': 'GOX', 'gox': 'GOX', 'mopa': 'GOX',

    # South Hubs
    'bengaluru': 'BLR', 'bangalore': 'BLR', 'banglore': 'BLR', 'blr': 'BLR', 'karnataka': 'BLR',
    'hyderabad': 'HYD', 'hyd': 'HYD', 'telangana': 'HYD',
    'chennai': 'MAA', 'maa': 'MAA', 'madras': 'MAA', 'tamil nadu': 'MAA',
    'cochin': 'COK', 'kochi': 'COK', 'cok': 'COK', 'kerala': 'COK',
    'thiruvananthapuram': 'TRV', 'trivandrum': 'TRV', 'trv': 'TRV',
    'kozhikode': 'CCJ', 'calicut': 'CCJ', 'ccj': 'CCJ',
    'coimbatore': 'CJB', 'cjb': 'CJB',
    'madurai': 'IXM', 'ixm': 'IXM',
    'tirupati': 'TIR', 'tir': 'TIR',
    'vijayawada': 'VGA', 'vga': 'VGA',
    'visakhapatnam': 'VTZ', 'vizag': 'VTZ', 'vtz': 'VTZ', 'andhra pradesh': 'VTZ',
    'mangaluru': 'IXE', 'mangalore': 'IXE', 'ixe': 'IXE',

    # East & Central Hubs
    'kolkata': 'CCU', 'ccu': 'CCU', 'calcutta': 'CCU', 'west bengal': 'CCU',
    'bagdogra': 'IXB', 'siliguri': 'IXB', 'ixb': 'IXB',
    'patna': 'PAT', 'pat': 'PAT', 'bihar': 'PAT',
    'ranchi': 'IXR', 'ixr': 'IXR', 'jharkhand': 'IXR',
    'bhubaneswar': 'BBI', 'bbi': 'BBI', 'odisha': 'BBI',
    'raipur': 'RPR', 'rpr': 'RPR', 'chhattisgarh': 'RPR',
    'indore': 'IDR', 'idr': 'IDR', 'madhya pradesh': 'IDR',

    # North-East & Island Hubs
    'guwahati': 'GAU', 'gau': 'GAU', 'assam': 'GAU',
    'agartala': 'IXA', 'ixa': 'IXA', 'tripura': 'IXA',
    'imphal': 'IMF', 'imf': 'IMF', 'manipur': 'IMF',
    'dibrugarh': 'DIB', 'dib': 'DIB',
    'silchar': 'IXS', 'ixs': 'IXS',
    'dimapur': 'DMU', 'dmu': 'DMU', 'nagaland': 'DMU',
    'port blair': 'IXZ', 'andaman': 'IXZ', 'ixz': 'IXZ'
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

# Airport Specific User Development Fees (UDF / PSF in INR ₹) per DGCA/AAI Tariff Orders
AIRPORT_UDF_PSF_RATES = {
    'DEL': 710.0, 'BOM': 650.0, 'BLR': 450.0, 'HYD': 480.0,
    'CCU': 380.0, 'MAA': 350.0, 'AMD': 300.0, 'COK': 320.0,
    'GOI': 280.0, 'GOX': 350.0, 'PNQ': 260.0, 'JAI': 270.0,
    'LKO': 290.0, 'GAU': 250.0, 'PAT': 280.0, 'SXR': 320.0,
    'BBI': 250.0, 'IXC': 260.0, 'ATQ': 280.0, 'TRV': 310.0,
    'IXB': 240.0, 'IXZ': 390.0, 'UDR': 250.0, 'NAG': 260.0
}

# OTA Platform Convenience Fees
PLATFORM_CONVENIENCE_FEES = {
    'makemytrip': 350.0,
    'yatra': 349.0,
    'cleartrip': 299.0,
    'ixigo': 299.0,
    'goibibo': 350.0,
    'easemytrip': 0.0, # Zero convenience fee baseline
    'google_flights': 0.0, # Metasearch pass-through
    'indigo': 0.0,
    'airindia': 0.0,
    'akasa': 0.0,
    'spicejet': 0.0,
    'airline_direct': 0.0
}

def decompose_fare_components(
    total_fare: float,
    origin_iata: str = "DEL",
    cabin_class: str = "Economy",
    platform: str = "google_flights"
) -> Dict[str, float]:
    """
    Decomposes total ticket airfare into transparent regulatory components:
    Total = Base Fare + Fuel Surcharge (ATF) + Airport UDF/PSF + GST + OTA Convenience Fee
    """
    if not total_fare or pd.isna(total_fare) or total_fare <= 0:
        return {
            "base_fare_inr": 3800.0,
            "fuel_surcharge_inr": 1600.0,
            "udf_psf_inr": 500.0,
            "gst_inr": 250.0,
            "convenience_fee_inr": 0.0,
            "total_fare_inr": 6150.0
        }

    plat_key = str(platform).lower()
    conv_fee = PLATFORM_CONVENIENCE_FEES.get(plat_key, 0.0)
    
    # Net airfare excluding convenience charge
    net_fare = max(1500.0, total_fare - conv_fee)
    
    # UDF / PSF
    udf = AIRPORT_UDF_PSF_RATES.get(origin_iata.upper(), 280.0)
    
    # GST (5% Economy, 12% Business on Base + Fuel)
    gst_rate = 0.12 if "business" in str(cabin_class).lower() else 0.05
    fare_before_gst = (net_fare - udf) / (1.0 + gst_rate)
    gst = round(fare_before_gst * gst_rate, 2)
    
    # Base fare vs Fuel Surcharge (ATF) split (~68% base, ~32% fuel surcharge)
    base_fare = round(fare_before_gst * 0.68, 2)
    fuel_surcharge = round(fare_before_gst - base_fare, 2)
    taxes_fees = round(fuel_surcharge + udf + gst + conv_fee, 2)

    return {
        "base_fare_inr": base_fare,
        "fuel_surcharge_inr": fuel_surcharge,
        "udf_psf_inr": udf,
        "gst_inr": gst,
        "convenience_fee_inr": conv_fee,
        "taxes_fees_inr": taxes_fees,
        "total_fare_inr": round(total_fare, 2)
    }

@dataclass
class ScrapedFlightObservation:
    record_id: str
    search_timestamp: str = ""     # ISO-8601 (YYYY-MM-DD HH:MM:SS)
    travel_date: str = ""          # ISO-8601 (YYYY-MM-DD)
    lead_time_days: int = 7        # (travel_date - search_date).days
    source_platform: str = "google_flights"  # e.g., 'google_flights', 'makemytrip', 'easemytrip', 'ixigo'
    origin_iata: str = "DEL"       # 3-letter IATA (DEL, BOM, etc.)
    dest_iata: str = "BOM"         # 3-letter IATA
    route: str = "DEL-BOM"         # ORIGIN-DEST (DEL-BOM)
    origin_raw: str = ""           # Unmodified raw string
    dest_raw: str = ""             # Unmodified raw string
    airline_standardized: str = "IndiGo"  # Clean carrier name (IndiGo, Air India, etc.)
    airline_raw: str = ""          # Raw carrier text from source
    flight_number: Optional[str] = None   # e.g., '6E 204', 'AI 887', 'QP 1352'
    departure_time: str = "08:00"  # e.g., '06:00'
    arrival_time: str = "10:00"    # e.g., '08:15'
    duration_minutes: Optional[int] = 120 # Duration in integer minutes
    duration_raw: str = ""         # e.g., '2h 15m'
    cabin_class: str = "Economy"   # 'Economy' / 'Business'
    total_fare_inr: float = 5000.0 # Real observed fare in INR ₹
    base_fare_inr: Optional[float] = None
    fuel_surcharge_inr: Optional[float] = None
    udf_psf_inr: Optional[float] = None
    gst_inr: Optional[float] = None
    convenience_fee_inr: Optional[float] = None
    taxes_fees_inr: Optional[float] = None
    is_nonstop: bool = True
    stops_count: int = 0           # 0 = Non-stop, 1 = 1-Stop, 2 = 2-Stops
    stop_info: str = "Non-Stop"    # e.g., "Non-Stop", "1 Stop (HYD)", "2 Stops"
    raw_hash: Optional[str] = None # Provenance hash

    def __init__(self, **kwargs):
        # Handle field aliases
        self.record_id = kwargs.get("record_id", "SCR_001")
        self.search_timestamp = kwargs.get("search_timestamp") or kwargs.get("search_timestamp_utc", datetime.utcnow().isoformat())
        self.travel_date = kwargs.get("travel_date") or kwargs.get("departure_date", date.today().isoformat())
        self.lead_time_days = kwargs.get("lead_time_days") if kwargs.get("lead_time_days") is not None else kwargs.get("booking_lead_days", 7)
        self.source_platform = kwargs.get("source_platform") or kwargs.get("source_portal", "google_flights")
        self.origin_iata = kwargs.get("origin_iata", "DEL")
        self.dest_iata = kwargs.get("dest_iata", "BOM")
        self.route = kwargs.get("route", f"{self.origin_iata}-{self.dest_iata}")
        self.origin_raw = kwargs.get("origin_raw") or kwargs.get("origin_city", self.origin_iata)
        self.dest_raw = kwargs.get("dest_raw") or kwargs.get("dest_city", self.dest_iata)
        self.airline_standardized = kwargs.get("airline_standardized") or kwargs.get("airline_name", "IndiGo")
        self.airline_raw = kwargs.get("airline_raw", self.airline_standardized)
        self.flight_number = kwargs.get("flight_number")
        self.departure_time = kwargs.get("departure_time", "08:00")
        self.arrival_time = kwargs.get("arrival_time", "10:00")
        self.duration_minutes = kwargs.get("duration_minutes", 120)
        self.duration_raw = kwargs.get("duration_raw", f"{self.duration_minutes}m" if self.duration_minutes else "")
        self.cabin_class = kwargs.get("cabin_class") or kwargs.get("fare_class", "Economy")
        self.total_fare_inr = float(kwargs.get("total_fare_inr", 5000.0))
        
        # Decompose fare components automatically if not provided
        decomp = decompose_fare_components(
            self.total_fare_inr,
            origin_iata=self.origin_iata,
            cabin_class=self.cabin_class,
            platform=self.source_platform
        )
        self.base_fare_inr = float(kwargs.get("base_fare_inr", decomp["base_fare_inr"]))
        self.fuel_surcharge_inr = float(kwargs.get("fuel_surcharge_inr", decomp["fuel_surcharge_inr"]))
        self.udf_psf_inr = float(kwargs.get("udf_psf_inr", decomp["udf_psf_inr"]))
        self.gst_inr = float(kwargs.get("gst_inr", decomp["gst_inr"]))
        self.convenience_fee_inr = float(kwargs.get("convenience_fee_inr", decomp["convenience_fee_inr"]))
        self.taxes_fees_inr = float(kwargs.get("taxes_fees_inr", decomp["taxes_fees_inr"]))
        
        self.is_nonstop = bool(kwargs.get("is_nonstop", True))
        self.stops_count = int(kwargs.get("stops_count", 0 if self.is_nonstop else 1))
        self.stop_info = kwargs.get("stop_info", "Non-Stop" if self.is_nonstop else f"{self.stops_count} Stop")
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
