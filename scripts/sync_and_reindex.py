"""
SIH26056: Real-Time Airfare Price Index for India (APIx)
Scraping Ledger Synchronization, Partitioning, Sorting & Index Recalculation Engine
"""

import os
import sys
import glob
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import settings, CLEANED_DIR, LIVE_SCRAPED_DIR, INDEX_RESULTS_DIR
from backend.db.scraping_ledger import scraping_ledger, MAX_RECORDS_PER_PARTITION
from backend.db.database import db
from scripts.index_engine.calculator import AirfareIndexEngine

def sync_batches_to_ledger():
    print("=" * 65)
    print("SIH26056: SCRAPING LEDGER SYNC & PARTITION MANAGER")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    # 1. Discover all batch files
    batch_files = sorted(LIVE_SCRAPED_DIR.glob("scraped_batch_*.csv"))
    print(f"[+] Found {len(batch_files)} scraped batch files in {LIVE_SCRAPED_DIR}")

    all_batch_records = []
    for bf in batch_files:
        try:
            df = pd.read_csv(bf, low_memory=False)
            if not df.empty:
                all_batch_records.extend(df.to_dict('records'))
        except Exception as e:
            print(f"[-] Warning reading {bf.name}: {e}")

    print(f"[+] Consolidated {len(all_batch_records):,} total raw observations from batches.")

    # 2. Also read existing live_scraped_master if available
    master_file = LIVE_SCRAPED_DIR / "live_scraped_master.csv"
    if master_file.exists():
        try:
            mdf = pd.read_csv(master_file, low_memory=False)
            all_batch_records.extend(mdf.to_dict('records'))
        except Exception as e:
            print(f"[-] Warning reading live_scraped_master: {e}")

    # 3. Deduplicate and partition
    df_all = pd.DataFrame(all_batch_records)
    if df_all.empty:
        print("[!] No records to process.")
        return

    # Clean total_fare_inr
    df_all['total_fare_inr'] = pd.to_numeric(df_all['total_fare_inr'], errors='coerce')
    df_all = df_all.dropna(subset=['total_fare_inr'])
    df_all = df_all[df_all['total_fare_inr'] >= 1500.0]

    # Deduplicate
    dedup_cols = [c for c in ['source_platform', 'travel_date', 'route', 'departure_time', 'airline_standardized', 'total_fare_inr'] if c in df_all.columns]
    if dedup_cols:
        df_all = df_all.drop_duplicates(subset=dedup_cols, keep='last')

    # Sort chronologically
    sort_cols = [c for c in ['search_timestamp', 'travel_date'] if c in df_all.columns]
    if sort_cols:
        df_all = df_all.sort_values(by=sort_cols, ascending=True)

    df_all = df_all.reset_index(drop=True)
    total_records = len(df_all)
    print(f"[OK] Cleaned, deduplicated and sorted: {total_records:,} distinct observations.")

    # 4. Partition into chunks of MAX_RECORDS_PER_PARTITION
    num_partitions = max(1, (total_records // MAX_RECORDS_PER_PARTITION) + (1 if total_records % MAX_RECORDS_PER_PARTITION != 0 else 0))
    print(f"[+] Writing into {num_partitions} partition file(s) (Cap: {MAX_RECORDS_PER_PARTITION:,} per file)...")

    for i in range(num_partitions):
        part_idx = i + 1
        start_row = i * MAX_RECORDS_PER_PARTITION
        end_row = min((i + 1) * MAX_RECORDS_PER_PARTITION, total_records)
        part_df = df_all.iloc[start_row:end_row]

        part_file = LIVE_SCRAPED_DIR / f"live_scraped_master_part{part_idx}.csv"
        part_df.to_csv(part_file, index=False)
        print(f"   --> Partition {part_idx}: {part_file.name} ({len(part_df):,} rows)")

    # Also keep live_scraped_master.csv as a convenient aggregated master alias
    df_all.to_csv(master_file, index=False)
    print(f"[OK] Master Alias updated: {master_file.name} ({total_records:,} rows)")

    # 5. Reload in-memory database
    db.reload_master_data()
    print(f"[OK] In-memory database reloaded: {len(db.master_df):,} active observations.")

    # 6. Recompute Jevons-Laspeyres Index Series
    print("\n" + "=" * 65)
    print("SIH26056: RECOMPUTING AIRFARE PRICE INDICES (APIx)")
    print("=" * 65)
    engine = AirfareIndexEngine()
    engine.run_full_pipeline()
    print("[OK] All APIx indices (daily, route, airline, lead-time) successfully recomputed.")

    # 7. Refresh ML Training Baseline
    print("\n" + "=" * 65)
    print("SIH26056: REFRESHING ML TRAINING BASELINE")
    print("=" * 65)
    try:
        from backend.ml_engine.trainer import train_and_save_model
        ml_meta = train_and_save_model()
        print(f"[OK] ML training baseline refreshed: R2={ml_meta.get('r2_score')}, samples={ml_meta.get('training_samples')}")
    except Exception as e:
        print(f"[-] Note on ML training: {e}")

    # 8. Print Final Verification Metrics
    daily_csv = INDEX_RESULTS_DIR / "daily_airfare_index.csv"
    if daily_csv.exists():
        df_daily = pd.read_csv(daily_csv)
        print(f"\n[SUMMARY] Daily Index Points: {len(df_daily)}")
        print(f"    Travel Dates Range: {df_daily['travel_date'].min()} to {df_daily['travel_date'].max()}")
        print(f"    Latest 5 Index Days:\n{df_daily[['travel_date', 'apix_jevons_laspeyres', 'market_pulse']].tail(5).to_string(index=False)}")

    latest_ts = scraping_ledger.get_latest_timestamp()
    print(f"\n[OK] Partitioned Ledger Status: {len(scraping_ledger.get_partition_files())} partition file(s).")
    print(f"[OK] Latest Scraped Timestamp: {latest_ts}")
    print("=" * 65)

if __name__ == "__main__":
    sync_batches_to_ledger()
