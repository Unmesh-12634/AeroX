import urllib.request
import json

req_data = json.dumps({
    'origin': 'DEL',
    'dest': 'BOM',
    'platform': 'ALL',
    'travel_date': '2026-09-18'
}).encode('utf-8')

req = urllib.request.Request(
    'http://localhost:8000/api/v1/scrape/search',
    data=req_data,
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req, timeout=30) as res:
        data = json.loads(res.read().decode('utf-8'))
        flights = data.get('flights', [])
        print(f"Status: {res.status}")
        print(f"Total flights count: {len(flights)}")
        platforms = sorted(list(set(f['source_platform'] for f in flights)))
        print(f"Platforms represented: {platforms}")
        for i, f in enumerate(flights[:8]):
            print(f"  [{i+1}] {f['airline']} ({f['flight_number']}) | INR {f['total_fare_inr']} | {f['source_platform']} | {f['departure_time']} - {f['arrival_time']}")
            print(f"      Booking: {f['booking_url']}")
            print(f"      Official: {f['airline_url']}")
except Exception as e:
    print(f"Error: {e}")
