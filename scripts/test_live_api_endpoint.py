import requests
import json
import time

payload = {
    "origin": "DEL",
    "dest": "BOM",
    "departure_date": "2026-09-17",
    "cabin_class": "economy"
}

print("Checking server health...")
for _ in range(5):
    try:
        r = requests.get("http://127.0.0.1:8000/docs", timeout=2)
        if r.status_code == 200:
            print("Server is ready.")
            break
    except Exception:
        time.sleep(1)

print("\nSending live request to POST http://127.0.0.1:8000/api/v1/scraper/run...")
start = time.time()
r = requests.post("http://127.0.0.1:8000/api/v1/scraper/run", json=payload, timeout=40)
elapsed = time.time() - start

print(f"Status Code: {r.status_code}")
print(f"HTTP Roundtrip Time: {elapsed:.2f}s")

if r.status_code == 200:
    data = r.json()
    print("Response Status:", data.get("status"))
    print("Source:", data.get("source"))
    print(f"Route: {data.get('origin')} -> {data.get('destination')}")
    print("Departure Date:", data.get("departure_date"))
    print("Total Flights Found:", data.get("total_flights_found"))
    print("Execution Time:", data.get("execution_time_seconds"), "seconds")
    print("Scrape Timestamp (UTC):", data.get("scrape_timestamp_utc"))
    print("Scrape Timestamp (IST):", data.get("scrape_timestamp_ist"))
    print("\nSample Live Flights:")
    for idx, f in enumerate(data.get("flights", [])[:6], start=1):
        print(f"  {idx}. {f.get('airline')} ({f.get('flight_number')}): {f.get('departure_time')} -> {f.get('arrival_time')} | Price: ₹{f.get('price')} | Stops: {f.get('stops')} | Duration: {f.get('duration')}")
    
    with open("live_api_response_del_bom.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("\nSaved full JSON to live_api_response_del_bom.json")
else:
    print("Error text:", r.text)
