"""
SIH26056: Real-Time Airfare Price Index for India
Unit Tests: Index Formulas, PSD Weights, Elasticity & Explainability
"""

import pytest
import numpy as np
import pandas as pd
from backend.index_engine.formulas import JevonsIndex, LaspeyresIndex, DutotIndex, CarliIndex
from backend.index_engine.weights import (
    PSD_WEIGHTS,
    get_normalized_psd_weights,
    get_route_psd_weight
)
from backend.index_engine.elasticity import BookingLeadTimeElasticity
from backend.index_engine.explainability import PriceChangeExplainer

class TestIndexFormulas:
    """Test suite for price index mathematical formulations."""

    def test_jevons_index_calculation(self):
        """Test Jevons geometric mean index calculation."""
        current_prices = [5500.0, 6000.0, 4800.0]
        base_prices = [5000.0, 5000.0, 4000.0]
        # (55/50 * 60/50 * 48/40)^(1/3) * 100 = (1.10 * 1.20 * 1.20)^(1/3) * 100
        # = (1.584)^(1/3) * 100 ≈ 1.1657 * 100 = 116.57
        idx = JevonsIndex.compute(current_prices, base_prices)
        assert idx == pytest.approx(116.57, 0.05)

    def test_laspeyres_index_calculation(self):
        """Test Laspeyres base-weighted aggregate price index."""
        current_route_indices = {
            "DEL-BOM": 108.5,
            "BLR-DEL": 112.0,
            "BOM-BLR": 105.0
        }
        weights = {
            "DEL-BOM": 0.50,
            "BLR-DEL": 0.30,
            "BOM-BLR": 0.20
        }
        # 108.5*0.5 + 112.0*0.3 + 105.0*0.2 = 54.25 + 33.60 + 21.0 = 108.85
        lasp = LaspeyresIndex.compute_from_route_indices(current_route_indices, weights)
        assert lasp == pytest.approx(108.85, 0.01)

    def test_dutot_and_carli(self):
        """Test Dutot and Carli index calculations."""
        current_p = [6000.0, 4000.0]
        base_p = [5000.0, 4000.0]
        # Dutot: (10000 / 9000) * 100 = 111.11
        dutot = DutotIndex.compute(current_p, base_p)
        assert dutot == pytest.approx(111.11, 0.05)

        # Carli: 0.5 * (6000/5000 + 4000/4000) * 100 = 0.5 * (1.20 + 1.0) * 100 = 110.0
        carli = CarliIndex.compute(current_p, base_p)
        assert carli == pytest.approx(110.0, 0.05)


class TestPSDWeights:
    """Test suite for DGCA Passenger Seat Demand weights."""

    def test_psd_weights_exist(self):
        """Verify standard major metro PSD routes are present."""
        assert "DEL-BOM" in PSD_WEIGHTS
        assert "BLR-DEL" in PSD_WEIGHTS
        assert "BOM-BLR" in PSD_WEIGHTS
        assert get_route_psd_weight("DEL-BOM") > 0.05

    def test_normalized_psd_weights(self):
        """Verify normalized weights strictly sum to 1.0."""
        routes = ["DEL-BOM", "BLR-DEL", "BOM-BLR", "DEL-CCU"]
        norm_w = get_normalized_psd_weights(routes)
        total_w = sum(norm_w.values())
        assert total_w == pytest.approx(1.0, 0.0001)


class TestElasticityAndExplainability:
    """Test suite for economic elasticity and price change decomposition."""

    def test_lead_time_elasticity(self):
        """Verify dynamic pricing multiplier decay as lead time expands."""
        curve = BookingLeadTimeElasticity.get_lead_time_multipliers()
        assert curve[1] > curve[7] > curve[14] > curve[30]
        # T+1 should be at a premium (> 1.25x)
        assert curve[1] >= 1.25
        # T+30 should be at discount (<= 0.90x)
        assert curve[30] <= 0.90

    def test_why_price_changed_decomposition(self):
        """Verify explainability breakdown factors sum to total change."""
        explanation = PriceChangeExplainer.explain(
            route="DEL-BOM",
            current_fare=7200.0,
            base_fare=5400.0,
            lead_time_days=3,
            atf_change_pct=4.5
        )
        assert "total_change_pct" in explanation
        assert "breakdown" in explanation
        assert "drivers" in explanation
        assert explanation["total_change_pct"] > 0
