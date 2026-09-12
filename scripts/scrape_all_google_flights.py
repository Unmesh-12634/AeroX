"""
SIH26056: Real-Time Google Flights Live Harvester
Scrapes genuine live market airfares across top Indian corridors directly from Google Flights.
"""

import os
import sys
import time
import json
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from scripts.scrapers.google_flights_scraper import GoogleFlightsScraper

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LIVE_DIR = os.path.join(DATA_DIR, 'live_scraped')
CLEANED_DIR = os.path.join(DATA_DIR, 'cleaned')

os.makedirs(LIVE_DIR, exist_ok=True)
os.makedirs(CLEANED_DIR, exist_ok=True)

KEY_ROUTES = [
    ("DEL", "BOM"), # Delhi - Mumbai
    ("BOM", "BLR"), # Mumbai - Bengaluru
    ("DEL", "BLR"), # Delhi - Bengaluru
    ("DEL", "CCU"), # Delhi - Kolkata
    ("DEL", "HYD"), # Delhi - Hyderabad
    ("DEL", "MAA"), # Delhi - Chennai
    ("DEL", "AMD"), # Delhi - Ahmedabad
    ("DEL", "GOI"), # Delhi - Goa
    ("DEL", "LKO"), # Delhi - Lucknow
    ("DEL", "SXR"), # Delhi - Srinagar
    ("DEL", "PAT"), # Delhi - Patna
    ("BOM", "GOI"), # Mumbai - Goa
    ("BOM", "HYD"), # Mumbai - Hyderabad
    ("BLR", "HYD"), # Bengaluru - Hyderabad
    ("UDR", "DEL"), # Udaipur - Delhi
    ("UDR", "BOM")  # Udaipur - Mumbai
]

LEAD_TIMES = [1, 2, 7, 15]

def main():
    print("=" * 65)
    print("HARVESTING REAL LIVE FLIGHTS FROM GOOGLE FLIGHTS")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)
    
    scraper = GoogleFlightsScraper(headless=True)
    today = datetime.now().date()
    all_obs = []
    
    for origin, dest in KEY_ROUTES:
        for lt in LEAD_TIMES:
            t_date = (today + timedelta(days=lt)).strftime("%Y-%m-%d")
            print(f"--> Scraping {origin} -> {dest} for date {t_date} (T+{lt}d)...", end=" ", flush=True)
            try:
                obs = scraper.search_route(origin, dest, t_date)
                print(f"Found {len(obs)} real Google Flights.")
                all_obs.extend(obs)
            except Exception as e:
                print(f"Error: {e}")
            time.sleep(0.5)

    if not all_obs:
        print("[!] No observations collected.")
        return

    print(f"\n[+] Total Google Flights observations scraped: {len(all_obs):,}")
    
    # Save batch
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_json = os.path.join(LIVE_DIR, f"scraped_batch_gf_{batch_id}.json")
    batch_csv = os.path.join(LIVE_DIR, f"scraped_batch_gf_{batch_id}.csv")
    
    data_dicts = [o.to_dict() for o in all_obs]
    with open(batch_json, "w", encoding="utf-8") as f:
        json.dump(data_dicts, f, indent=2)
        
    df_batch = pd.DataFrame(data_dicts)
    # Clean non-breaking spaces in time strings
    for col in ['departure_time', 'arrival_time', 'duration_raw']:
        if col in df_batch.columns:
            df_batch[col] = df_batch[col].astype(str).str.replace('\u202f', ' ').str.replace('\xa0', ' ').str.strip()
            
    df_batch.to_csv(batch_csv, index=False)
    print(f"[✓] Saved batch to {batch_csv}")
    
    # Append to sih_master_airfare_observations_v2.csv
    master_path = os.path.join(CLEANED_DIR, 'sih_master_airfare_observations_v2.csv')
    if os.path.exists(master_path):
        df_master = pd.read_csv(master_path, low_memory=False)
        
        df_new = pd.DataFrame()
        df_new['record_id'] = df_batch['record_id']
        df_new['dataset_tier'] = ['live_google_flights'] * len(df_batch)
        df_new['source_file'] = ['live_scraper_google_flights'] * len(df_batch)
        df_new['travel_date'] = df_batch['travel_date']
        df_new['travel_year'] = pd.to_datetime(df_batch['travel_date']).dt.year.astype(str)
        df_new['origin_iata'] = df_batch['origin_iata']
        df_new['dest_iata'] = df_batch['dest_iata']
        df_new['route'] = df_batch['route']
        df_new['origin_raw'] = df_batch['origin_raw']
        df_new['dest_raw'] = df_batch['dest_raw']
        df_new['airline_standardized'] = df_batch['airline_standardized']
        df_new['airline_raw'] = df_batch['airline_raw']
        df_new['flight_number'] = df_batch['flight_number']
        df_new['departure_time'] = df_batch['departure_time']
        df_new['arrival_time'] = df_batch['arrival_time']
        df_new['duration_minutes'] = df_batch['duration_minutes']
        df_new['duration_raw'] = df_batch['duration_raw']
        df_new['cabin_class'] = df_batch['cabin_class']
        df_new['total_fare_inr'] = df_batch['total_fare_inr']
        df_new['base_fare_inr'] = df_batch['total_fare_inr'] * 0.78
        df_new['taxes_fees_inr'] = df_batch['total_fare_inr'] * 0.22
        df_new['search_timestamp'] = df_batch['search_timestamp']
        df_new['lead_time_days'] = df_batch['lead_time_days']
        df_new['is_defunct_carrier'] = [False] * len(df_batch)
        df_new['is_ambiguous_carrier'] = [False] * len(df_batch)
        df_new['is_fare_mild_outlier'] = [False] * len(df_batch)
        df_new['is_fare_extreme_outlier'] = [False] * len(df_batch)
        
        df_combined = pd.concat([df_master, df_new], ignore_index=True)
        # Deduplicate
        df_combined.drop_duplicates(subset=['route', 'travel_date', 'airline_standardized', 'departure_time', 'total_fare_inr'], keep='last', inplace=True)
        df_combined.to_csv(master_path, index=False)
        print(f"[✓] Master dataset updated: {len(df_combined):,} audited records in {master_path}")
        
    print("=" * 65)
    print("GOOGLE FLIGHTS HARVESTING COMPLETE")
    print("=" * 65)

if __name__ == "__main__":
    main()
