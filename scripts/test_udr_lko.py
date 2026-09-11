import urllib.request
import json

if __name__ == "__main__":
    try:
        req = urllib.request.Request(
            'http://127.0.0.1:8000/api/v1/scrape/search',
            data=json.dumps({'origin': 'UDR', 'dest': 'LKO', 'lead_time': 'ALL', 'airline': 'ALL', 'platform': 'ALL', 'cabin_class': 'Economy'}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        res = urllib.request.urlopen(req, timeout=5)
        data = json.loads(res.read().decode('utf-8'))

        print("Route:", data.get("route"))
        print("Mean Fare (INR):", data.get("mean_fare_inr"))
        print("Min Fare (INR):", data.get("min_fare_inr"))
        print("Max Fare (INR):", data.get("max_fare_inr"))
        print("Route Jevons Index:", data.get("route_apix_index"))
        print("Sample Flights:")
        for f in data.get("flights", [])[:4]:
            print(f"  - {f.get('flight_number')} ({f.get('airline')}) | {f.get('departure_time')} -> {f.get('arrival_time')} | Fare: INR {f.get('total_fare_inr')}")
    except Exception as e:
        print(f"Could not connect to server: {e}")

