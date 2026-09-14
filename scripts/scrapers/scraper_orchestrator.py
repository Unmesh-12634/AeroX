"""
SIH26056: Real-Time Airfare Price Index for India
Unified Multi-Platform Scraper Orchestrator & Live Data Ingestion Engine

Supported Platforms:
1. Online Travel Aggregators (OTAs):
   - 'makemytrip'  (MakeMyTrip)
   - 'yatra'       (Yatra)
   - 'easemytrip'  (EaseMyTrip)
   - 'cleartrip'   (Cleartrip)
   - 'ixigo'       (Ixigo)
   - 'goibibo'     (Goibibo)
2. Direct Airline Portals:
   - 'indigo'      (IndiGo Direct)
   - 'airindia'    (Air India Direct)
   - 'akasa'       (Akasa Air Direct)
   - 'spicejet'    (SpiceJet Direct)
3. Aggregators:
   - 'google_flights' (Google Flights)

Pre-configured Platform Groups:
- 'ota'      -> All 6 OTAs (MakeMyTrip, Yatra, EaseMyTrip, Cleartrip, Ixigo, Goibibo)
- 'airlines' -> All 4 Airline Portals (IndiGo, Air India, Akasa, SpiceJet)
- 'all'      -> Full multi-platform sweep

Default Lead Times:
- T+1, T+7, T+15, T+30, T+45 days
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

try:
    from scripts.scrapers.models import ScrapedFlightObservation
    from scripts.scrapers.google_flights_scraper import GoogleFlightsScraper
    from scripts.scrapers.ota_scrapers import (
        MakeMyTripScraper, YatraScraper, EaseMyTripScraper,
        CleartripScraper, IxigoScraper, GoibiboScraper
    )
    from scripts.scrapers.airline_scrapers import (
        IndiGoDirectScraper, AirIndiaDirectScraper, AirIndiaExpressDirectScraper,
        AkasaDirectScraper, SpiceJetDirectScraper
    )
except ImportError:
    from models import ScrapedFlightObservation
    from google_flights_scraper import GoogleFlightsScraper
    from ota_scrapers import (
        MakeMyTripScraper, YatraScraper, EaseMyTripScraper,
        CleartripScraper, IxigoScraper, GoibiboScraper
    )
    from airline_scrapers import (
        IndiGoDirectScraper, AirIndiaDirectScraper, AirIndiaExpressDirectScraper,
        AkasaDirectScraper, SpiceJetDirectScraper
    )

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LIVE_DIR = os.path.join(DATA_DIR, 'live_scraped')
CLEANED_DIR = os.path.join(DATA_DIR, 'cleaned')

os.makedirs(LIVE_DIR, exist_ok=True)
os.makedirs(CLEANED_DIR, exist_ok=True)

DEFAULT_TOP_ROUTES = [
    ("DEL", "BOM"), # Delhi - Mumbai (#1 Trunk Corridor)
    ("BOM", "BLR"), # Mumbai - Bengaluru
    ("DEL", "BLR"), # Delhi - Bengaluru
    ("DEL", "CCU"), # Delhi - Kolkata
    ("DEL", "HYD")  # Delhi - Hyderabad
]

# Standard SIH26056 Advance Booking Windows
DEFAULT_LEAD_TIMES = [1, 7, 15, 30, 45] # T+1, T+7, T+15, T+30, T+45 days

PLATFORM_GROUPS = {
    "ota": ["makemytrip", "yatra", "easemytrip", "cleartrip", "ixigo", "goibibo"],
    "airlines": ["indigo", "airindia", "airindiaexpress", "akasa", "spicejet"],
    "all": ["google_flights", "makemytrip", "yatra", "easemytrip", "cleartrip", "ixigo", "goibibo", "indigo", "airindia", "airindiaexpress", "akasa", "spicejet"]
}

class ScraperOrchestrator:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.scrapers = {
            "google_flights": GoogleFlightsScraper(headless=headless),
            "makemytrip": MakeMyTripScraper(headless=headless),
            "yatra": YatraScraper(headless=headless),
            "easemytrip": EaseMyTripScraper(headless=headless),
            "cleartrip": CleartripScraper(headless=headless),
            "ixigo": IxigoScraper(headless=headless),
            "goibibo": GoibiboScraper(headless=headless),
            "indigo": IndiGoDirectScraper(headless=headless),
            "airindia": AirIndiaDirectScraper(headless=headless),
            "airindiaexpress": AirIndiaExpressDirectScraper(headless=headless),
            "akasa": AkasaDirectScraper(headless=headless),
            "spicejet": SpiceJetDirectScraper(headless=headless)
        }

    def run_collection(
        self,
        platforms: List[str],
        routes: List[tuple],
        lead_times: List[int],
        cabin_class: str = "Economy"
    ) -> List[ScrapedFlightObservation]:
        all_observations: List[ScrapedFlightObservation] = []
        today = datetime.now().date()
        
        # Expand platform shortcuts
        resolved_platforms = []
        for p in platforms:
            p_clean = p.strip().lower()
            if p_clean in PLATFORM_GROUPS:
                resolved_platforms.extend(PLATFORM_GROUPS[p_clean])
            else:
                resolved_platforms.append(p_clean)
        resolved_platforms = list(dict.fromkeys(resolved_platforms)) # deduplicate preserving order

        print("=" * 65)
        print("SIH26056: REAL-TIME AIRFARE SCRAPER & LIVE INGESTION ENGINE")
        print(f"Start Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target Platforms ({len(resolved_platforms)}): {', '.join(resolved_platforms)}")
        print(f"Target Corridors ({len(routes)}): {[f'{o}-{d}' for o, d in routes]}")
        print(f"Target Lead Times: {[f'T+{lt}' for lt in lead_times]}")
        print("=" * 65)

        for p_name in resolved_platforms:
            scraper = self.scrapers.get(p_name)
            if not scraper:
                print(f"[!] Platform '{p_name}' not supported. Skipping.")
                continue

            print(f"\n[+] Launching Platform Scraper: [{p_name.upper()}]")
            for origin, dest in routes:
                for lt in lead_times:
                    travel_date = (today + timedelta(days=lt)).strftime("%Y-%m-%d")
                    print(f"    --> Querying {origin}-{dest} on {travel_date} (Lead: T+{lt} days)...", end="", flush=True)
                    try:
                        obs_list = scraper.search_route(
                            origin_iata=origin,
                            dest_iata=dest,
                            travel_date_str=travel_date,
                            cabin_class=cabin_class
                        )
                        print(f" Found {len(obs_list)} real flights.")
                        all_observations.extend(obs_list)
                    except Exception as e:
                        print(f" Error: {e}")

        # Persist and update master dataset
        if all_observations:
            self._persist_observations(all_observations)
        else:
            print("\n[!] No observations collected in this run. Verify network connectivity.")

        return all_observations

    def _persist_observations(self, observations: List[ScrapedFlightObservation]):
        batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_json_path = os.path.join(LIVE_DIR, f"scraped_batch_{batch_id}.json")
        batch_csv_path = os.path.join(LIVE_DIR, f"scraped_batch_{batch_id}.csv")
        
        # 1. Save Batch JSON & CSV
        data_dicts = [o.to_dict() for o in observations]
        with open(batch_json_path, "w", encoding="utf-8") as f:
            json.dump(data_dicts, f, indent=2)
            
        df_batch = pd.DataFrame(data_dicts)
        df_batch.to_csv(batch_csv_path, index=False)
        print(f"\n[✓] Batch successfully saved: {batch_csv_path} ({len(df_batch)} records)")

        # 2. Forward batch to Partitioned Scraping Ledger Manager (10,000 partition cap + chronological sorting)
        try:
            from backend.db.scraping_ledger import scraping_ledger
            part_name, total_live = scraping_ledger.append_observations(data_dicts)
            print(f"[✓] Partitioned Ledger updated: {part_name} (Total Live Records across partitions: {total_live:,})")
        except Exception as e:
            print(f"[-] Warning: Failed to update partitioned ledger: {e}")

        # 3. Append to sih_master_airfare_observations_v2.csv if present
        master_v2_path = os.path.join(CLEANED_DIR, "sih_master_airfare_observations_v2.csv")
        if os.path.exists(master_v2_path):
            try:
                df_master = pd.read_csv(master_v2_path, low_memory=False)
                
                df_append = pd.DataFrame()
                df_append['record_id'] = df_batch['record_id']
                df_append['dataset_tier'] = ['live_scraped_observation'] * len(df_batch)
                df_append['source_file'] = df_batch['source_platform'].map(lambda x: f"live_scraper_{x}")
                df_append['travel_date'] = df_batch['travel_date']
                df_append['travel_year'] = pd.to_datetime(df_batch['travel_date']).dt.year.astype(str)
                df_append['origin_iata'] = df_batch['origin_iata']
                df_append['dest_iata'] = df_batch['dest_iata']
                df_append['route'] = df_batch['route']
                df_append['origin_raw'] = df_batch['origin_raw']
                df_append['dest_raw'] = df_batch['dest_raw']
                df_append['airline_standardized'] = df_batch['airline_standardized']
                df_append['airline_raw'] = df_batch['airline_raw']
                df_append['flight_number'] = df_batch['flight_number']
                df_append['departure_time'] = df_batch['departure_time']
                df_append['arrival_time'] = df_batch['arrival_time']
                df_append['duration_minutes'] = df_batch['duration_minutes']
                df_append['duration_raw'] = df_batch['duration_raw']
                df_append['cabin_class'] = df_batch['cabin_class']
                df_append['total_fare_inr'] = df_batch['total_fare_inr']
                df_append['base_fare_inr'] = [None] * len(df_batch)
                df_append['taxes_fees_inr'] = [None] * len(df_batch)
                df_append['search_timestamp'] = df_batch['search_timestamp']
                df_append['lead_time_days'] = df_batch['lead_time_days']
                df_append['is_defunct_carrier'] = [False] * len(df_batch)
                df_append['is_ambiguous_carrier'] = [False] * len(df_batch)
                df_append['is_fare_mild_outlier'] = [False] * len(df_batch)
                df_append['is_fare_extreme_outlier'] = [False] * len(df_batch)
                
                df_master_combined = pd.concat([df_master, df_append], ignore_index=True)
                df_master_combined.to_csv(master_v2_path, index=False)
                print(f"[✓] Main Project Master v2 updated: {master_v2_path} (Total Records: {len(df_master_combined):,})")
            except Exception as e:
                print(f"[-] Warning appending to master v2: {e}")

        # 4. Instant Post-Scrape Index Recalculation (Jevons-Laspeyres Daily, Route, Carrier Indices)
        try:
            from scripts.index_engine.calculator import recalculate_all_indices
            print("[+] Recalculating Jevons-Laspeyres APIx indices post-scrape...")
            recalculate_all_indices()
            print("[✓] Post-scrape index recalculation completed.")
        except Exception as e:
            print(f"[-] Warning during index recalculation: {e}")

        # 5. Hot-Reload Data Repository Memory
        try:
            from backend.db.database import db
            db.reload_data()
            print(f"[✓] DataRepository memory hot-reloaded: {len(db.master_df):,} records in active ledger.")
        except Exception as e:
            print(f"[-] Warning reloading repository memory: {e}")

def main():
    parser = argparse.ArgumentParser(description="SIH26056 Real-Time Airfare Multi-Platform Scraper Engine")
    parser.add_argument("--platform", type=str, default="google_flights", help="Target platform(s): 'makemytrip', 'yatra', 'easemytrip', 'cleartrip', 'ixigo', 'goibibo', 'indigo', 'airindia', 'akasa', 'spicejet', 'google_flights', 'ota', 'airlines', or 'all'")
    parser.add_argument("--routes", type=str, default=None, help="Comma-separated route pairs e.g. 'DEL-BOM,BOM-BLR,DEL-BLR'")
    parser.add_argument("--lead-times", type=str, default="1,7,15,30,45", help="Comma-separated lead times in days e.g. '1,7,15,30,45'")
    parser.add_argument("--cabin", type=str, default="Economy", help="Cabin class: 'Economy' or 'Business'")
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser in headless mode")

    args = parser.parse_args()

    # Determine platforms
    platforms = [p.strip().lower() for p in args.platform.split(",")]

    # Determine routes
    if args.routes:
        routes = []
        for r in args.routes.split(","):
            parts = r.strip().upper().split("-")
            if len(parts) == 2:
                routes.append((parts[0], parts[1]))
    else:
        routes = DEFAULT_TOP_ROUTES

    # Determine lead times
    lead_times = [int(lt.strip()) for lt in args.lead_times.split(",")]

    orchestrator = ScraperOrchestrator(headless=args.headless)
    orchestrator.run_collection(
        platforms=platforms,
        routes=routes,
        lead_times=lead_times,
        cabin_class=args.cabin
    )

if __name__ == "__main__":
    main()
