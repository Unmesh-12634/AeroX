import time
import concurrent.futures
from datetime import datetime, timedelta
from scripts.scrapers.google_flights_scraper import GoogleFlightsScraper
from scripts.scrapers.models import decompose_fare_components

ROUTES = [
    ("DEL", "BOM"), ("DEL", "BLR"), ("BOM", "BLR"),
    ("DEL", "CCU"), ("DEL", "HYD"), ("DEL", "MAA"),
    ("BLR", "HYD"), ("BOM", "GOI"), ("DEL", "PNQ"),
    ("DEL", "LKO"), ("BOM", "LKO"), ("DEL", "UDR"),
    ("BOM", "UDR"), ("DEL", "SXR"), ("DEL", "GAU")
]

target_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

def scrape_one(route):
    orig, dest = route
    t0 = time.time()
    try:
        scraper = GoogleFlightsScraper(headless=True)
        flights = scraper.search_route(orig, dest, target_date, cabin_class="Economy")
        elapsed = round(time.time() - t0, 2)
        print(f"[{orig}-{dest}] Scraped {len(flights)} flights in {elapsed}s")
        return (f"{orig}-{dest}", flights)
    except Exception as e:
        print(f"[{orig}-{dest}] Error: {e}")
        return (f"{orig}-{dest}", [])

if __name__ == "__main__":
    t_start = time.time()
    print(f"Starting parallel scrape for 15 DGCA corridors for date {target_date}...")
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(scrape_one, r): r for r in ROUTES}
        for fut in concurrent.futures.as_completed(futures):
            rk, fl = fut.result()
            results[rk] = fl

    print(f"\nCompleted in {round(time.time() - t_start, 2)}s.")
    print("Summary of scraped flights per corridor:")
    for rk in [f"{o}-{d}" for o, d in ROUTES]:
        fl = results.get(rk, [])
        if fl:
            best = min(fl, key=lambda x: x.total_fare_inr if x.total_fare_inr and x.total_fare_inr > 1000 else 999999)
            print(f"  {rk}: {len(fl)} flights. Lowest: {best.airline_standardized} {best.flight_number} at {best.departure_time} -> Rs {best.total_fare_inr}")
        else:
            print(f"  {rk}: 0 flights")
