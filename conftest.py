"""
SIH26056: Real-Time Airfare Price Index for India
Pytest configuration and shared test fixtures.
"""

import sys
from pathlib import Path
import pytest
import pandas as pd

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

@pytest.fixture
def sample_valid_observation_dict():
    """Fixture providing a valid flight observation dictionary."""
    return {
        "record_id": "SCR_TEST_001",
        "search_timestamp_utc": "2026-09-09T06:00:00Z",
        "departure_date": "2026-09-16",
        "booking_lead_days": 7,
        "lead_time_bucket": "4-7d",
        "origin_iata": "DEL",
        "origin_city": "New Delhi",
        "dest_iata": "BOM",
        "dest_city": "Mumbai",
        "route": "DEL-BOM",
        "airline_name": "IndiGo",
        "airline_standardized": "IndiGo",
        "carrier_iata": "6E",
        "flight_number": "6E-205",
        "departure_time": "08:15",
        "arrival_time": "10:30",
        "duration_minutes": 135,
        "is_nonstop": True,
        "fare_class": "Economy",
        "base_fare_inr": 4800.0,
        "taxes_fees_inr": 1040.0,
        "total_fare_inr": 5840.0,
        "source_portal": "MakeMyTrip",
        "source_type": "OTA",
        "is_outlier": False,
        "is_psd_route": True
    }

@pytest.fixture
def sample_observations_df():
    """Fixture providing a multi-route sample DataFrame for testing calculations."""
    data = [
        {
            "record_id": "REC001",
            "observation_date": "2026-08-01",
            "search_timestamp_utc": "2026-08-01T06:00:00Z",
            "departure_date": "2026-08-08",
            "booking_lead_days": 7,
            "lead_time_bucket": "4-7d",
            "origin_iata": "DEL",
            "dest_iata": "BOM",
            "route": "DEL-BOM",
            "airline_standardized": "IndiGo",
            "carrier_iata": "6E",
            "flight_number": "6E-205",
            "departure_time": "08:15",
            "duration_minutes": 135,
            "is_nonstop": True,
            "fare_class": "Economy",
            "base_fare_inr": 4500.0,
            "taxes_fees_inr": 900.0,
            "total_fare_inr": 5400.0,
            "source_portal": "MakeMyTrip",
            "source_type": "OTA",
            "is_outlier": False,
            "is_psd_route": True
        },
        {
            "record_id": "REC002",
            "observation_date": "2026-08-01",
            "search_timestamp_utc": "2026-08-01T06:00:00Z",
            "departure_date": "2026-08-08",
            "booking_lead_days": 7,
            "lead_time_bucket": "4-7d",
            "origin_iata": "DEL",
            "dest_iata": "BOM",
            "route": "DEL-BOM",
            "airline_standardized": "Air India",
            "carrier_iata": "AI",
            "flight_number": "AI-805",
            "departure_time": "10:00",
            "duration_minutes": 130,
            "is_nonstop": True,
            "fare_class": "Economy",
            "base_fare_inr": 4900.0,
            "taxes_fees_inr": 980.0,
            "total_fare_inr": 5880.0,
            "source_portal": "Google Flights",
            "source_type": "METASEARCH",
            "is_outlier": False,
            "is_psd_route": True
        },
        {
            "record_id": "REC003",
            "observation_date": "2026-08-01",
            "search_timestamp_utc": "2026-08-01T06:00:00Z",
            "departure_date": "2026-08-08",
            "booking_lead_days": 7,
            "lead_time_bucket": "4-7d",
            "origin_iata": "BLR",
            "dest_iata": "DEL",
            "route": "BLR-DEL",
            "airline_standardized": "IndiGo",
            "carrier_iata": "6E",
            "flight_number": "6E-501",
            "departure_time": "06:30",
            "duration_minutes": 165,
            "is_nonstop": True,
            "fare_class": "Economy",
            "base_fare_inr": 5500.0,
            "taxes_fees_inr": 1100.0,
            "total_fare_inr": 6600.0,
            "source_portal": "EaseMyTrip",
            "source_type": "OTA",
            "is_outlier": False,
            "is_psd_route": True
        }
    ]
    return pd.DataFrame(data)
