import sys
import os
import time
from datetime import datetime, timedelta
import pprint

# Set path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from scripts.scrapers.google_flights_scraper import GoogleFlightsScraper

def main():
    today = datetime.now().date()
    target_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    
    print(f"=== LIVE SCRAPE TEST (Google Flights) ===")
    print(f"Current Date: {today}")
    print(f"Target Departure Date (T+7): {target_date}")
    print(f"Route: DEL -> BOM")
    print(f"Mode: Visible Browser (headless=False)\n")
    
    start_time = time.time()
    
    # Initialize scraper with headless=False
    scraper = GoogleFlightsScraper(headless=False)
    
    # Execute scrape
    results = scraper.search_route(
        origin_iata="DEL",
        dest_iata="BOM",
        travel_date_str=target_date,
        cabin_class="Economy"
    )
    
    elapsed = time.time() - start_time
    
    print(f"\n=== SCRAPING COMPLETED ===")
    print(f"Time Taken: {elapsed:.2f} seconds")
    print(f"Total Flights Returned: {len(results)}\n")
    
    print("=== FULL RAW RESULTS LIST ===")
    for i, obs in enumerate(results, start=1):
        print(f"\n--- [Flight #{i}] ---")
        pprint.pprint(obs.__dict__)

if __name__ == "__main__":
    main()
