import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

payload = {
    "origin": "DEL",
    "dest": "BOM",
    "departure_date": "2026-09-17",
    "cabin_class": "economy"
}

print("=" * 60)
print("TESTING POST /api/v1/scraper/run (LIVE PLAYWRIGHT INVOCATION)")
print("=" * 60)
print("Payload:", json.dumps(payload))
start = time.time()
response = client.post("/api/v1/scraper/run", json=payload)
elapsed = time.time() - start

print(f"\nResponse Status Code: {response.status_code}")
print(f"Elapsed Time: {elapsed:.2f}s")

if response.status_code == 200:
    data = response.json()
    print(f"Status: {data.get('status')}")
    print(f"Data Source: {data.get('source')}")
    print(f"Route: {data.get('origin')} -> {data.get('destination')}")
    print(f"Departure Date: {data.get('departure_date')} (Lead Time: {data.get('lead_time_days')} days)")
    print(f"Total Fresh Flights Found: {data.get('total_flights_found')}")
    print(f"Scrape Timestamp UTC: {data.get('scrape_timestamp_utc')}")
    print(f"Scrape Timestamp IST: {data.get('scrape_timestamp_ist')}")
    print(f"Reported Execution Time: {data.get('execution_time_seconds')}s")
    
    print("\n--- Spot-Check Sample Flights ---")
    flights = data.get("flights", [])
    for idx, f in enumerate(flights[:8], start=1):
        airline = f.get("airline")
        fnum = f.get("flight_number")
        dep = f.get("departure_time")
        arr = f.get("arrival_time")
        price = f.get("price")
        stops = f.get("stops")
        dur = f.get("duration")
        print(f"[{idx}] {airline} ({fnum}) | Dep: {dep} -> Arr: {arr} | ₹{price:,} | Stops: {stops} | Dur: {dur}")
    
    with open("live_api_response_del_bom.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("\nSuccessfully written full JSON response to live_api_response_del_bom.json")
else:
    print("Error:", response.text)
