"""
SIH26056: Real-Time Airfare Price Index for India
Unit Tests: Data Cleaner, Normalizer & Quality Assurance Engine
"""

import pytest
import pandas as pd
import numpy as np
from backend.cleaner.normalizer import Normalizer
from backend.cleaner.quality_checker import QualityChecker

class TestNormalizer:
    """Test suite for data normalization logic."""

    def test_normalize_iata_airports(self):
        """Verify city name to standard 3-letter IATA mapping."""
        assert Normalizer.normalize_iata("New Delhi") == "DEL"
        assert Normalizer.normalize_iata("BOM") == "BOM"
        assert Normalizer.normalize_iata("Bengaluru") == "BLR"
        assert Normalizer.normalize_iata("Goa Dabolim") == "GOI"
        assert Normalizer.normalize_iata("Port Blair") == "IXZ"
        assert Normalizer.normalize_iata("Srinagar") == "SXR"

    def test_normalize_airline(self):
        """Verify airline standard branding."""
        assert Normalizer.normalize_airline("6E") == "IndiGo"
        assert Normalizer.normalize_airline("Indigo") == "IndiGo"
        assert Normalizer.normalize_airline("Air India") == "Air India"
        assert Normalizer.normalize_airline("AI") == "Air India"
        assert Normalizer.normalize_airline("Vistara") == "Vistara"
        assert Normalizer.normalize_airline("Akasa") == "Akasa Air"

    def test_decompose_fare(self):
        """Verify fare breakdown when only total is given."""
        # Standard domestic route DEL-BOM (distance ~1150km)
        base, taxes = Normalizer.decompose_fare(5500.0, 1150)
        assert base > 0
        assert taxes > 0
        assert base + taxes == pytest.approx(5500.0, 0.01)

    def test_lead_time_bucket(self):
        """Verify lead time bucketing categories."""
        assert Normalizer.categorize_lead_time(1) == "T+1"
        assert Normalizer.categorize_lead_time(3) == "T+3"
        assert Normalizer.categorize_lead_time(7) == "T+7"
        assert Normalizer.categorize_lead_time(14) == "T+14"
        assert Normalizer.categorize_lead_time(30) == "T+30"


class TestQualityChecker:
    """Test suite for statistical IQR outlier detection and quality scoring."""

    def test_iqr_outlier_detection(self):
        """Test IQR outlier marking for abnormal spikes or drops."""
        fares = [5000, 5200, 4900, 5100, 5300, 5050, 4950, 5150, 5250, 4850, 50000, 100]
        df = pd.DataFrame({
            "route": ["DEL-BOM"] * len(fares),
            "lead_time_days": [7] * len(fares),
            "total_fare_inr": fares
        })

        flagged_df = QualityChecker.detect_outliers_iqr(df, group_cols=["route", "lead_time_days"])
        assert "is_outlier" in flagged_df.columns
        # 50,000 should be marked as outlier
        assert flagged_df.loc[df["total_fare_inr"] == 50000, "is_outlier"].values[0] is True or flagged_df.loc[df["total_fare_inr"] == 50000, "is_outlier"].values[0] == 1

    def test_deduplication(self):
        """Test exact duplicate flight record pruning."""
        df = pd.DataFrame([
            {
                "search_timestamp": "2026-09-09 08:00:00",
                "travel_date": "2026-09-16",
                "route": "DEL-BOM",
                "flight_number": "6E-205",
                "departure_time": "08:15",
                "total_fare_inr": 5840.0,
                "source_platform": "MakeMyTrip"
            },
            {
                "search_timestamp": "2026-09-09 08:00:00",
                "travel_date": "2026-09-16",
                "route": "DEL-BOM",
                "flight_number": "6E-205",
                "departure_time": "08:15",
                "total_fare_inr": 5840.0,
                "source_platform": "MakeMyTrip"
            }
        ])

        deduped = QualityChecker.deduplicate_observations(df)
        assert len(deduped) == 1

    def test_quality_audit_summary(self):
        """Test comprehensive dataset audit computation."""
        df = pd.DataFrame([
            {"route": "DEL-BOM", "total_fare_inr": 5400.0, "is_outlier": False, "is_psd_route": True},
            {"route": "BLR-DEL", "total_fare_inr": 6200.0, "is_outlier": False, "is_psd_route": True},
            {"route": "BOM-GOI", "total_fare_inr": 3800.0, "is_outlier": False, "is_psd_route": False}
        ])
        audit = QualityChecker.calculate_quality_score(df)
        assert audit["total_records"] == 3
        assert audit["valid_records"] == 3
        assert audit["quality_score_pct"] >= 95.0
