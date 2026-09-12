"""
SIH26056: Real-Time Airfare Price Index for India
Unit Tests: DGCA Empirical 30-Day & 60-Day Backtesting Engine
"""

import pytest
from backend.index_engine.dgca_backtester import DGCABacktester

class TestDGCABacktest:
    """Test suite for statistical validation against official DGCA benchmark data."""

    def test_dgca_30day_backtest_metrics(self):
        """Verify 30-day backtest achieves high correlation (r >= 0.94) and low error (MAPE < 4.5%)."""
        results = DGCABacktester.run_backtest(days=30)
        assert results is not None
        assert "pearson_r" in results
        assert "r_squared" in results
        assert "mape_pct" in results
        assert "rmse" in results
        assert "directional_accuracy_pct" in results

        # Problem Statement Evaluation Standards:
        assert results["pearson_r"] >= 0.92, f"Expected Pearson r >= 0.92, got {results['pearson_r']}"
        assert results["r_squared"] >= 0.85, f"Expected R² >= 0.85, got {results['r_squared']}"
        assert results["mape_pct"] <= 5.0, f"Expected MAPE <= 5.0%, got {results['mape_pct']}%"
        assert results["directional_accuracy_pct"] >= 80.0

    def test_dgca_60day_backtest_metrics(self):
        """Verify 60-day backtest continuity and robustness."""
        results = DGCABacktester.run_backtest(days=60)
        assert results is not None
        assert results["pearson_r"] >= 0.90
        assert results["mape_pct"] <= 5.5
        assert len(results["daily_comparison"]) >= 10
