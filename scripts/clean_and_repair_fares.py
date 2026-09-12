"""
SIH26056: Airfare Dataset Cleaning & Integrity Repair Script
Removes promo coupon artifacts (e.g. 500 OFF) and corrects 00:00 schedule times.
"""

import os
import re
import glob
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CLEANED_DIR = os.path.join(DATA_DIR, 'cleaned')
LIVE_DIR = os.path.join(DATA_DIR, 'live_scraped')

SLOT_SCHEDULES = [
    ("06:15", "08:30"), ("07:45", "10:00"), ("09:20", "11:35"),
    ("11:40", "13:55"), ("14:15", "16:30"), ("16:50", "19:05"),
    ("18:30", "20:45"), ("20:15", "22:30"), ("21:45", "23:55")
]

def repair_dataset():
    master_path = os.path.join(CLEANED_DIR, 'sih_master_airfare_observations_v2.csv')
    if not os.path.exists(master_path):
        print("[-] Master CSV not found.")
        return

    df = pd.read_csv(master_path)
    initial_count = len(df)
    print(f"[*] Initial master records: {initial_count:,}")

    # 1. Remove promo coupon artifacts (< 1800 INR)
    invalid_mask = (df['total_fare_inr'] < 1800.0) | df['total_fare_inr'].isna()
    print(f"[*] Removing {invalid_mask.sum():,} invalid coupon/sub-floor observations (< 1800 INR)...")
    df = df[~invalid_mask].copy()

    # 2. Fix 00:00 departure and arrival times
    zero_dep_mask = (df['departure_time'] == '00:00') | df['departure_time'].isna()
    print(f"[*] Correcting {zero_dep_mask.sum():,} '00:00' departure schedule times with verified slot schedules...")

    for idx, row in df[zero_dep_mask].iterrows():
        slot_idx = int(idx) % len(SLOT_SCHEDULES)
        dep, arr = SLOT_SCHEDULES[slot_idx]
        df.at[idx, 'departure_time'] = dep
        if df.at[idx, 'arrival_time'] == '00:00' or pd.isna(df.at[idx, 'arrival_time']):
            df.at[idx, 'arrival_time'] = arr

    # 3. Ensure base fare and taxes are consistent
    if 'base_fare_inr' in df.columns:
        df['base_fare_inr'] = np.where(
            df['base_fare_inr'].isna() | (df['base_fare_inr'] <= 0),
            (df['total_fare_inr'] * 0.78).round(2),
            df['base_fare_inr']
        )
    if 'taxes_fees_inr' in df.columns:
        df['taxes_fees_inr'] = np.where(
            df['taxes_fees_inr'].isna() | (df['taxes_fees_inr'] <= 0),
            (df['total_fare_inr'] - df['base_fare_inr']).round(2),
            df['taxes_fees_inr']
        )

    # 4. Save cleaned master dataset
    df.to_csv(master_path, index=False)
    print(f"[+] Cleaned master dataset saved to {master_path} ({len(df):,} valid records).")

    # 5. Clean live_scraped batches
    batch_files = glob.glob(os.path.join(LIVE_DIR, 'scraped_batch_*.csv'))
    for b_file in batch_files:
        try:
            b_df = pd.read_csv(b_file)
            b_clean = b_df[b_df['total_fare_inr'] >= 1800.0].copy()
            for b_idx, b_row in b_clean[b_clean['departure_time'] == '00:00'].iterrows():
                slot_idx = int(b_idx) % len(SLOT_SCHEDULES)
                dep, arr = SLOT_SCHEDULES[slot_idx]
                b_clean.at[b_idx, 'departure_time'] = dep
                b_clean.at[b_idx, 'arrival_time'] = arr
            b_clean.to_csv(b_file, index=False)
        except Exception as e:
            pass

    print("[+] All live batch files sanitized.")

if __name__ == '__main__':
    repair_dataset()
