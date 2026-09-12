import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List
from backend.config import settings
from backend.index_engine.weights import get_basket_routes, DGCA_PSD_ROUTE_WEIGHTS

def build_apix_dataset():
    # 1. Load live scraped data + master cleaned observations
    dfs = []
    live_path = settings.LIVE_SCRAPED_DIR / 'live_scraped_master.csv'
    if live_path.exists():
        try:
            df_live = pd.read_csv(live_path, low_memory=False)
            df_live['source_origin'] = 'LIVE_SCRAPED'
            dfs.append(df_live)
        except Exception as e:
            print("Error loading live csv:", e)
            
    master_path = settings.MASTER_CSV_PATH
    if master_path.exists():
        try:
            df_m = pd.read_csv(master_path, low_memory=False)
            df_m['source_origin'] = 'MASTER_DATA'
            dfs.append(df_m)
        except Exception as e:
            print("Error loading master csv:", e)

    if not dfs:
        return None

    df = pd.concat(dfs, ignore_index=True)
    df['total_fare_inr'] = pd.to_numeric(df['total_fare_inr'], errors='coerce')
    df = df.dropna(subset=['total_fare_inr'])
    df = df[df['total_fare_inr'] > 500]
    
    # Ensure standard route column
    if 'route' not in df.columns:
        df['route'] = df['origin_iata'] + '-' + df['dest_iata']
    df['route'] = df['route'].astype(str).str.upper()
    
    df['travel_date_dt'] = pd.to_datetime(df['travel_date'], errors='coerce')
    df = df.dropna(subset=['travel_date_dt'])
    
    return df

df = build_apix_dataset()
print("Combined valid observations:", len(df))
print("Date range:", df['travel_date_dt'].min(), "to", df['travel_date_dt'].max())
print("Unique routes:", df['route'].nunique())
