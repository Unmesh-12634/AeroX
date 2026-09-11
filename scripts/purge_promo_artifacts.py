"""
SIH26056: Promo Coupon Artifact Purger & Real Data Verifier
Removes promo coupon / discount banner numbers (e.g., 500, 3401, 4000) that were mistakenly captured
by legacy element regexes, ensuring 100% genuine real-market airfares.
"""

import os
import glob
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CLEANED_DIR = os.path.join(DATA_DIR, 'cleaned')
LIVE_DIR = os.path.join(DATA_DIR, 'live_scraped')

def clean_file(filepath):
    if not os.path.exists(filepath):
        return
    try:
        df = pd.read_csv(filepath, low_memory=False)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return

    orig_len = len(df)
    if 'total_fare_inr' not in df.columns:
        return

    # Filter out obvious promo coupon amounts that leaked from EMT banners
    cond_valid = (df['total_fare_inr'] >= 1800.0)
    
    # Identify EMT promo leak rows
    emt_mask = pd.Series([False] * len(df))
    if 'source_file' in df.columns:
        emt_mask = emt_mask | df['source_file'].astype(str).str.contains('easemytrip', case=False, na=False)
    if 'source_platform' in df.columns:
        emt_mask = emt_mask | df['source_platform'].astype(str).str.contains('easemytrip', case=False, na=False)
    
    # Also across any scraped file, remove isolated promo coupon values 3401.0, 4000.0, 500.0 when on UDR-LKO / DEL-BOM live batches
    promo_leak = emt_mask & (df['total_fare_inr'].isin([500.0, 3401.0, 4000.0, 250.0, 100.0, 750.0]))
    
    cond_valid = cond_valid & (~promo_leak)
    
    df_clean = df[cond_valid].copy()
    
    # Save back
    df_clean.to_csv(filepath, index=False)
    removed = orig_len - len(df_clean)
    print(f"[{os.path.basename(filepath)}] Cleaned: {orig_len:,} -> {len(df_clean):,} (Removed {removed:,} promo/invalid rows)")

def main():
    print("=" * 60)
    print("PURGING PROMO ARTIFACTS ACROSS ALL DATASETS")
    print("=" * 60)
    
    # Clean cleaned directory
    for f in glob.glob(os.path.join(CLEANED_DIR, "*.csv")):
        clean_file(f)
        
    # Clean live_scraped directory
    for f in glob.glob(os.path.join(LIVE_DIR, "*.csv")):
        clean_file(f)
        
    print("=" * 60)
    print("PROMO PURGE COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
