"""
SIH26056: Real-Time Airfare Price Index for India
Data Normalization & Standardization Module
"""

import re
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

CITY_SYNONYMS = {
    'delhi': 'DEL', 'new delhi': 'DEL', 'ncr': 'DEL', 'indira gandhi': 'DEL',
    'mumbai': 'BOM', 'bombay': 'BOM', 'chhatrapati shivaji': 'BOM',
    'bengaluru': 'BLR', 'bangalore': 'BLR', 'kempegowda': 'BLR',
    'hyderabad': 'HYD', 'rajiv gandhi': 'HYD', 'secunderabad': 'HYD',
    'kolkata': 'CCU', 'calcutta': 'CCU', 'netaji subhash': 'CCU',
    'chennai': 'MAA', 'madras': 'MAA', 'meenambakkam': 'MAA',
    'ahmedabad': 'AMD', 'gujarat': 'AMD', 'sardar vallabhbhai': 'AMD',
    'kochi': 'COK', 'cochin': 'COK', 'nedumbassery': 'COK',
    'goa': 'GOI', 'dabolim': 'GOI', 'goa dabolim': 'GOI', 'goa (dabolim)': 'GOI', 'mopa': 'GOX', 'goa mopa': 'GOX', 'goa (mopa)': 'GOX', 'panaji': 'GOI',
    'pune': 'PNQ', 'lohegaon': 'PNQ',
    'jaipur': 'JAI', 'sanganer': 'JAI', 'rajasthan': 'JAI',
    'lucknow': 'LKO', 'amausi': 'LKO', 'chaudhary charan singh': 'LKO',
    'guwahati': 'GAU', 'borjhar': 'GAU', 'assam': 'GAU',
    'patna': 'PAT', 'bihar': 'PAT',
    'bhubaneswar': 'BBI', 'odisha': 'BBI',
    'srinagar': 'SXR', 'kashmir': 'SXR',
    'chandigarh': 'IXC', 'punjab': 'IXC',
    'amritsar': 'ATQ', 'rajasansi': 'ATQ',
    'indore': 'IDR', 'madhya pradesh': 'IDR',
    'visakhapatnam': 'VTZ', 'vizag': 'VTZ',
    'ranchi': 'IXR', 'jharkhand': 'IXR',
    'raipur': 'RPR', 'chhattisgarh': 'RPR',
    'dehradun': 'DED', 'jolly grant': 'DED',
    'varanasi': 'VNS', 'babatpur': 'VNS', 'kashi': 'VNS',
    'thiruvananthapuram': 'TRV', 'trivandrum': 'TRV',
    'bagdogra': 'IXB', 'siliguri': 'IXB',
    'port blair': 'IXZ', 'andaman': 'IXZ',
    'udaipur': 'UDR', 'dabok': 'UDR',
    'nagpur': 'NAG', 'sonegaon': 'NAG'
}

AIRLINE_STANDARDIZATION_MAP = {
    'indigo': 'IndiGo',
    '6e': 'IndiGo',
    'air india': 'Air India',
    'ai': 'Air India',
    'airindia': 'Air India',
    'akasa': 'Akasa Air',
    'akasa air': 'Akasa Air',
    'qp': 'Akasa Air',
    'spicejet': 'SpiceJet',
    'sg': 'SpiceJet',
    'air india express': 'Air India Express',
    'airindia express': 'Air India Express',
    'aix': 'Air India Express',
    'ix': 'Air India Express',
    'aix connect': 'Air India Express',
    'airasia': 'Air India Express',
    'airasia india': 'Air India Express',
    'vistara': 'Vistara',
    'uk': 'Vistara',
    'tata sia': 'Vistara',
    'star air': 'Star Air',
    'fly91': 'Fly91',
    'alliance air': 'Alliance Air'
}

DEFUNCT_CARRIERS = {
    'jet airways', 'jetairways', '9w', 'kingfisher', 'kingfisher airlines',
    'goair', 'go air', 'go first', 'g8', 'paramount', 'air costa', 'air carnival'
}

def resolve_iata(city_or_code: str) -> Optional[str]:
    if not city_or_code:
        return None
    cleaned = str(city_or_code).strip().lower()
    if len(cleaned) == 3 and cleaned.upper() in [
        'DEL', 'BOM', 'BLR', 'HYD', 'CCU', 'MAA', 'AMD', 'COK', 'GOI', 'GOX',
        'PNQ', 'JAI', 'LKO', 'GAU', 'PAT', 'BBI', 'SXR', 'IXC', 'ATQ', 'IDR',
        'VTZ', 'IXR', 'RPR', 'DED', 'VNS', 'TRV', 'IXB', 'IXZ', 'UDR', 'NAG'
    ]:
        return cleaned.upper()
    return CITY_SYNONYMS.get(cleaned, None)

def standardize_airline(airline_raw: str) -> Tuple[str, bool, bool]:
    if not airline_raw or pd.isna(airline_raw):
        return "Unknown Carrier", False, True
    raw_lower = str(airline_raw).strip().lower()
    
    is_defunct = any(d in raw_lower for d in DEFUNCT_CARRIERS)
    
    for key, std_name in AIRLINE_STANDARDIZATION_MAP.items():
        if key in raw_lower:
            return std_name, is_defunct, False
            
    return str(airline_raw).title(), is_defunct, False

def normalize_fare_components(total_fare: float, base_fare: Optional[float] = None, taxes_fees: Optional[float] = None) -> Tuple[float, float, float]:
    total = float(total_fare)
    if base_fare is not None and not pd.isna(base_fare) and base_fare > 0:
        base = float(base_fare)
    else:
        # Standard domestic tax ratio (~15-18% taxes + airport development fees)
        base = round(total * 0.84, 2)
        
    if taxes_fees is not None and not pd.isna(taxes_fees) and taxes_fees > 0:
        taxes = float(taxes_fees)
    else:
        taxes = round(total - base, 2)
        
    return total, base, taxes

class Normalizer:
    """Class wrapper for data normalization operations."""
    
    @staticmethod
    def normalize_iata(city_or_code: str) -> str:
        res = resolve_iata(city_or_code)
        if res:
            return res
        clean = str(city_or_code).strip()
        return clean.upper() if len(clean) == 3 else clean

    @staticmethod
    def normalize_airline(airline_raw: str) -> str:
        std, _, _ = standardize_airline(airline_raw)
        return std

    @staticmethod
    def decompose_fare(total_fare: float, distance_km: float = 1000.0) -> Tuple[float, float]:
        total, base, taxes = normalize_fare_components(total_fare)
        return base, taxes

    @staticmethod
    def categorize_lead_time(lead_days: int) -> str:
        if lead_days <= 1:
            return "T+1"
        elif lead_days <= 3:
            return "T+3"
        elif lead_days <= 7:
            return "T+7"
        elif lead_days <= 14:
            return "T+14"
        elif lead_days <= 30:
            return "T+30"
        return "T+45+"

