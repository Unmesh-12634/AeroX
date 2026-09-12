import sys
import os
from urllib.parse import urlparse

sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

def run_tests():
    print("=" * 60)
    print("RUNNING END-TO-END PIPELINE & REDIRECT VERIFICATION")
    print("=" * 60)

    # 1. Search DEL-BOM
    res = client.post("/api/v1/scrape/search", json={
        "origin": "DEL",
        "dest": "BOM",
        "platform": "ALL",
        "travel_date": "2026-09-18"
    })
    assert res.status_code == 200, f"Search failed: {res.status_code}"
    data = res.json()
    flights = data.get("flights", [])
    print(f"[OK] DEL-BOM search returned {len(flights)} real scraped flights")
    print(f"     Source Mode: {data.get('data_source_mode')}")
    print(f"     Platforms: {sorted(list(set(f['source_platform'] for f in flights)))}")
    print(f"     Airlines: {sorted(list(set(f['airline'] for f in flights)))}")

    # 2. Check unbundling & cleaning
    sample = flights[0]
    print(f"\n[Sample Flight 1]: {sample['airline']} {sample['flight_number']} | Platform: {sample['source_platform']}")
    print(f"     Timings: {sample['departure_time']} -> {sample['arrival_time']} ({sample['duration']})")
    print(f"     Fare: INR {sample['total_fare_inr']} (Base: INR {sample['base_fare_inr']}, Fuel: INR {sample['fuel_surcharge_inr']}, UDF/PSF: INR {sample['udf_psf_inr']}, GST: INR {sample['gst_inr']}, Convenience: INR {sample['convenience_fee_inr']})")
    print(f"     Booking URL: {sample['booking_url'][:80]}...")
    print(f"     Airline URL: {sample['airline_url'][:80]}...")
    print(f"     Redirect URL: {sample['redirect_url']}")

    assert sample['total_fare_inr'] == round(sample['base_fare_inr'] + sample['taxes_fees_inr'], 2)
    assert "\u202f" not in sample['departure_time']
    assert "\xa0" not in sample['departure_time']
    assert sample['flight_number'].lower() != "nan"

    # 3. Test Redirect Endpoint for MakeMyTrip
    red_res = client.get("/api/v1/scrape/redirect?platform=makemytrip&origin=DEL&dest=BOM&date=2026-09-18&airline=IndiGo&flight=6E%20414&target_type=booking", follow_redirects=False)
    assert red_res.status_code == 307
    loc = red_res.headers.get("location")
    print(f"\n[OK] MakeMyTrip 307 Redirect Location: {loc}")
    booking_host = (urlparse(loc).hostname or "").lower()
    assert booking_host == "www.makemytrip.com" or booking_host.endswith(".makemytrip.com")

    # 4. Test Redirect Endpoint for Air India Official
    red_ai = client.get("/api/v1/scrape/redirect?platform=google_flights&origin=DEL&dest=BOM&date=2026-09-18&airline=Air%20India&flight=AI%20804&target_type=airline", follow_redirects=False)
    assert red_ai.status_code == 307
    loc_ai = red_ai.headers.get("location")
    print(f"[OK] Air India Official 307 Redirect Location: {loc_ai}")
    airline_host = (urlparse(loc_ai).hostname or "").lower()
    assert airline_host == "www.airindia.com" or airline_host.endswith(".airindia.com")

    # 5. Search DEL-BLR
    res_blr = client.post("/api/v1/scrape/search", json={
        "origin": "DEL",
        "dest": "BLR",
        "platform": "ALL",
        "travel_date": "2026-09-20"
    })
    assert res_blr.status_code == 200
    data_blr = res_blr.json()
    print(f"\n[OK] DEL-BLR search returned {len(data_blr.get('flights', []))} real scraped flights")

    print("\nALL VERIFICATION CHECKS PASSED WITH ZERO ERRORS!")

if __name__ == "__main__":
    run_tests()
