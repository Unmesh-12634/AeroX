import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.index_engine.weights import get_basket_routes

client = TestClient(app)

def test_dgca_basket_realtime_data():
    """Verify DGCA basket returns genuine real-time extracted data across all 15 corridors."""
    response = client.get("/api/v1/scrape/basket?cabin_class=Economy&platform=ALL")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["basket_size"] == 15
    assert len(data["routes"]) == 15

    # Aggregate breakdown must exist and have realistic non-zero values
    agg = data["aggregate_breakdown"]
    assert agg["mean_base_fare_inr"] > 1000
    assert agg["mean_fuel_surcharge_inr"] > 500
    assert agg["mean_udf_psf_inr"] > 200
    assert agg["mean_gst_inr"] > 100
    assert 40.0 <= agg["base_fare_pct"] <= 75.0
    assert 15.0 <= agg["fuel_surcharge_pct"] <= 40.0

    basket_def = get_basket_routes()
    expected_corridors = set(basket_def.keys())
    returned_corridors = {r["route"] for r in data["routes"]}
    assert expected_corridors == returned_corridors

    for r in data["routes"]:
        # Must be real-time extracted
        assert r["data_mode"] == "REAL_TIME_SCRAPED"
        assert "Real-Time Scraped" in r["quality_label"] or "Live" in r["quality_label"]
        assert r["current_fare_inr"] >= 2000.0

        # Authentic flight details
        assert r["carrier"] in ["IndiGo", "Air India", "Akasa Air", "SpiceJet", "Air India Express"]
        assert r["flight_number"] != ""
        assert "direct" not in r["flight_number"].lower()
        assert r["departure_time"] != ""
        assert "\u202f" not in r["departure_time"]
        assert r["duration"] != ""

        # Unbundled fare reconciliation: Base + Fuel + UDF + GST + Conv == Total Fare
        ub = r["unbundled_fare"]
        sum_components = (
            ub["base_fare_inr"] +
            ub["fuel_surcharge_inr"] +
            ub["udf_psf_inr"] +
            ub["gst_inr"] +
            ub["convenience_fee_inr"]
        )
        assert abs(sum_components - r["current_fare_inr"]) < 2.0, f"Fare mismatch on {r['route']}: sum={sum_components} vs total={r['current_fare_inr']}"

        # Working booking URLs
        assert r["booking_url"].startswith("http")
        assert r["airline_url"].startswith("http")

def test_dgca_basket_business_class():
    """Verify Business class returns scaled business fares with Air India / premium carrier."""
    response = client.get("/api/v1/scrape/basket?cabin_class=Business")
    assert response.status_code == 200
    data = response.json()
    assert data["cabin_class"] == "Business"
    assert data["basket_size"] == 15

    for r in data["routes"]:
        assert r["current_fare_inr"] > 10000.0  # Domestic business fares are higher
        assert r["data_mode"] == "REAL_TIME_SCRAPED"
        assert r["unbundled_fare"]["gst_pct"] >= 8.0 or r["unbundled_fare"]["gst_inr"] > 500  # 12% GST
