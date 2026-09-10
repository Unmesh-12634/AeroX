"""
SIH26056: Real-Time Airfare Price Index for India
Unit Tests: Scraper Data Models, Normalization, and Parsers
"""

import pytest
import numpy as np
from scripts.scrapers.models import (
    ScrapedFlightObservation,
    normalize_iata,
    normalize_airline,
    parse_price,
    parse_duration_to_mins
)

class TestScraperModelsAndHelpers:
    """Test suite for data models and normalization routines."""

    def test_observation_model_instantiation(self, sample_valid_observation_dict):
        """Test ScrapedFlightObservation instantiates and serializes accurately."""
        obs = ScrapedFlightObservation(**sample_valid_observation_dict)
        assert obs.record_id == "SCR_TEST_001"
        assert obs.origin_iata == "DEL"
        assert obs.dest_iata == "BOM"
        assert obs.route == "DEL-BOM"
        assert obs.airline_standardized == "IndiGo"
        assert obs.total_fare_inr == 5840.0
        assert obs.is_nonstop is True

        d = obs.to_dict()
        assert isinstance(d, dict)
        assert d["record_id"] == "SCR_TEST_001"
        assert d["total_fare_inr"] == 5840.0

    @pytest.mark.parametrize("input_city,expected_iata", [
        ("delhi", "DEL"),
        ("New Delhi", "DEL"),
        ("DEL", "DEL"),
        ("mumbai", "BOM"),
        ("BOM", "BOM"),
        ("bangalore", "BLR"),
        ("bengaluru", "BLR"),
        ("kolkata", "CCU"),
        ("hyderabad", "HYD"),
        ("chennai", "MAA"),
        ("cochin", "COK"),
        ("kochi", "COK"),
        ("goa", "GOI"),
        ("goa (dabolim)", "GOI"),
        ("goa (mopa)", "GOX"),
        ("ahmedabad", "AMD"),
        ("jaipur", "JAI"),
        ("srinagar", "SXR")
    ])
    def test_normalize_iata(self, input_city, expected_iata):
        """Test IATA code normalization for common airport and city variants."""
        assert normalize_iata(input_city) == expected_iata

    @pytest.mark.parametrize("raw_carrier,expected_standardized", [
        ("indigo", "IndiGo"),
        ("6E", "IndiGo"),
        ("air india", "Air India"),
        ("AI", "Air India"),
        ("vistara", "Vistara"),
        ("UK", "Vistara"),
        ("spicejet", "SpiceJet"),
        ("SG", "SpiceJet"),
        ("akasa air", "Akasa Air"),
        ("QP", "Akasa Air"),
        ("air india express", "Air India Express"),
        ("IX", "Air India Express"),
        ("airasia india", "AirAsia India")
    ])
    def test_normalize_airline(self, raw_carrier, expected_standardized):
        """Test airline standard name resolution across 2-letter IATA codes and strings."""
        assert normalize_airline(raw_carrier) == expected_standardized

    @pytest.mark.parametrize("raw_price_str,expected_val", [
        ("5840", 5840.0),
        ("5,840", 5840.0),
        ("₹6,314.00", 6314.0),
        ("Rs. 7250", 7250.0),
        ("Rs 4500", 4500.0),
        ("INR 9,120", 9120.0),
        (5500, 5500.0),
        (4820.5, 4820.5)
    ])
    def test_parse_price_valid(self, raw_price_str, expected_val):
        """Test numeric price parser strips currencies, commas, and handles decimals."""
        assert parse_price(raw_price_str) == pytest.approx(expected_val, 0.01)

    def test_parse_price_invalid(self):
        """Test price parser handles missing or corrupted strings safely with NaN."""
        assert np.isnan(parse_price("Sold Out"))
        assert np.isnan(parse_price(""))
        assert np.isnan(parse_price(None))

    @pytest.mark.parametrize("duration_str,expected_mins", [
        ("2h 15m", 135),
        ("1 hr 45 min", 105),
        ("02 hrs 30 mins", 150),
        ("55m", 55),
        ("3h", 180),
        ("1h 0m", 60)
    ])
    def test_parse_duration_to_mins(self, duration_str, expected_mins):
        """Test flight duration string conversion into total integer minutes."""
        assert parse_duration_to_mins(duration_str) == expected_mins

    def test_parse_duration_empty(self):
        """Test duration parser returns None on empty or None input."""
        assert parse_duration_to_mins("") is None
        assert parse_duration_to_mins(None) is None
