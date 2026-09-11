"""
SIH26056: Real-Time Airfare Price Index for India
API Integration Tests: FastAPI Endpoints Verification
"""

import pytest
from starlette.testclient import TestClient
from backend.app import app

client = TestClient(app)

class TestAPIEndpoints:
    """Comprehensive test suite for all 16 API endpoints."""

    def test_overview_endpoint(self):
        """Test GET /api/v1/overview returns core KPIs."""
        response = client.get("/api/v1/overview")
        assert response.status_code == 200
        data = response.json()
        assert "latest_apix_index" in data
        assert "total_audited_observations" in data
        assert "system_status" in data
        assert data["system_status"] == "OPERATIONAL"

    def test_airports_endpoint(self):
        """Test GET /api/v1/airports returns full Indian airports catalog."""
        response = client.get("/api/v1/airports")
        assert response.status_code == 200
        data = response.json()
        assert "airports" in data
        assert len(data["airports"]) >= 30
        del_apt = next((a for a in data["airports"] if a["iata"] == "DEL"), None)
        assert del_apt is not None
        assert "Delhi" in del_apt["city"]


    def test_daily_index_endpoint(self):
        """Test GET /api/v1/daily-index returns time-series index data."""
        response = client.get("/api/v1/daily-index")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0
        first = data["data"][0]
        assert "travel_date" in first
        assert "apix_jevons_laspeyres" in first

    def test_lead_time_curve_endpoint(self):
        """Test GET /api/v1/lead-time-curve."""
        response = client.get("/api/v1/lead-time-curve")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0

    def test_routes_endpoint(self):
        """Test GET /api/v1/routes returns route breakdown."""
        response = client.get("/api/v1/routes")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0

    def test_route_detail_endpoint(self):
        """Test GET /api/v1/routes/DEL-BOM returns specific route insights."""
        response = client.get("/api/v1/routes/DEL-BOM")
        assert response.status_code == 200
        data = response.json()
        assert "route" in data
        assert data["route"]["origin_iata"] in ["DEL", "BOM"]

    def test_airlines_endpoint(self):
        """Test GET /api/v1/airlines returns dynamically aggregated airline stats."""
        response = client.get("/api/v1/airlines")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0
        indigo = next((a for a in data["data"] if a.get("airline") == "IndiGo"), None)
        assert indigo is not None

    def test_observations_endpoint(self):
        """Test GET /api/v1/observations supports filtering and pagination."""
        response = client.get("/api/v1/observations?limit=10&route=DEL-BOM")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "observations" in data
        assert len(data["observations"]) <= 10

    def test_anomalies_endpoint(self):
        """Test GET /api/v1/anomalies returns detected price spikes/drops."""
        response = client.get("/api/v1/anomalies")
        assert response.status_code == 200
        data = response.json()
        assert "anomalies" in data
        assert len(data["anomalies"]) > 0

    def test_why_price_changed_endpoint(self):
        """Test GET /api/v1/why-price-changed explainability breakdown."""
        response = client.get("/api/v1/why-price-changed?route=DEL-BOM&lead_time_days=3")
        assert response.status_code == 200
        data = response.json()
        assert "components" in data
        assert "summary" in data

    def test_elasticity_endpoint(self):
        """Test GET /api/v1/elasticity returns booking lead curve."""
        response = client.get("/api/v1/elasticity")
        assert response.status_code == 200
        data = response.json()
        assert "lead_time_decay_curve" in data
        assert "elasticity_coefficient" in data

    def test_market_intelligence_endpoint(self):
        """Test GET /api/v1/market-intelligence."""
        response = client.get("/api/v1/market-intelligence")
        assert response.status_code == 200
        data = response.json()
        assert "overall_market_pulse" in data or "hhi_index" in data

    def test_data_quality_endpoint(self):
        """Test GET /api/v1/data-quality returns audit scoring."""
        response = client.get("/api/v1/data-quality")
        assert response.status_code == 200
        data = response.json()
        assert "overall_quality_score" in data
        assert data["overall_quality_score"] >= 90.0

    def test_dgca_backtest_endpoint(self):
        """Test GET /api/v1/backtest/dgca returns backtest validation."""
        response = client.get("/api/v1/backtest/dgca?days=30")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        metrics = data["metrics"]
        assert "pearson_r" in metrics
        assert "r_squared" in metrics
        assert "mape_pct" in metrics

    def test_replay_status_endpoint(self):
        """Test GET /api/v1/replay/status."""
        response = client.get("/api/v1/replay/status")
        assert response.status_code == 200
        data = response.json()
        assert "is_running" in data

    def test_simulate_policy_endpoint(self):
        """Test POST /api/v1/simulate-policy returns simulated impact."""
        response = client.post("/api/v1/simulate-policy", json={
            "policy_type": "atf_tax_reduction",
            "fuel_surcharge_delta_pct": -10.0,
            "demand_surge_factor": 1.05
        })
        assert response.status_code == 200
        data = response.json()
        assert "simulated_apix" in data
        assert "impact_summary" in data

    def test_live_search_and_scrape_endpoint(self):
        """Test POST /api/v1/scrape/search returns live multi-portal flight fares and Jevons index."""
        response = client.post("/api/v1/scrape/search", json={
            "origin": "DEL",
            "dest": "BOM",
            "lead_time": "1",
            "airline": "ALL",
            "platform": "ALL",
            "stops_filter": "ALL",
            "cabin_class": "Economy"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["route"] == "DEL-BOM"
        assert "route_apix_index" in data
        assert "mean_fare_inr" in data
        assert "flights" in data
        assert len(data["flights"]) > 0
        first_flight = data["flights"][0]
        assert "airline" in first_flight
        assert "total_fare_inr" in first_flight
        assert "source_platform" in first_flight
        assert "is_nonstop" in first_flight
        assert "stops_count" in first_flight
        assert "stop_info" in first_flight

    def test_live_search_stoppage_filtering(self):
        """Test POST /api/v1/scrape/search with NONSTOP and 1_STOP filters."""
        # Nonstop filter
        res_ns = client.post("/api/v1/scrape/search", json={
            "origin": "DEL",
            "dest": "BOM",
            "stops_filter": "NONSTOP"
        })
        assert res_ns.status_code == 200
        data_ns = res_ns.json()
        assert data_ns["stops_filter"] == "NONSTOP"
        assert all(f["is_nonstop"] is True or f["stops_count"] == 0 for f in data_ns["flights"])

        # 1-Stop filter
        res_1s = client.post("/api/v1/scrape/search", json={
            "origin": "DEL",
            "dest": "BOM",
            "stops_filter": "1_STOP"
        })
        assert res_1s.status_code == 200
        data_1s = res_1s.json()
        assert data_1s["stops_filter"] == "1_STOP"
        assert all(f["stops_count"] == 1 for f in data_1s["flights"])

    def test_scraper_status_endpoint(self):
        """Test GET /api/v1/scrape/status returns scraper engine health."""
        response = client.get("/api/v1/scrape/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert "supported_platforms" in data
        assert "makemytrip" in data["supported_platforms"]
        assert "easemytrip" in data["supported_platforms"]
