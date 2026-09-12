"""
SIH26056: Real-Time Airfare Price Index for India
Index Calculation Engine (Jevons-Laspeyres PSD Aggregator)
"""

import os
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.config import settings
from backend.index_engine.weights import get_route_weight, DGCA_PSD_ROUTE_WEIGHTS
from backend.index_engine.formulas import jevons_index, laspeyres_aggregate

def compute_all_indices(df_master: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    if df_master is None or len(df_master) == 0:
        if settings.MASTER_CSV_PATH.exists():
            df_master = pd.read_csv(settings.MASTER_CSV_PATH)
        else:
            return {"status": "error", "message": "Master observations file not found."}

    df = df_master.copy()
    df['total_fare_inr'] = pd.to_numeric(df['total_fare_inr'], errors='coerce')
    df = df.dropna(subset=['total_fare_inr'])
    
    # 1. Establish Baselines
    base_fare_national = settings.BASE_NATIONAL_FARE
    route_baselines = {}
    for r, grp in df.groupby('route'):
        route_baselines[r] = float(grp['total_fare_inr'].mean())

    # 2. Daily National Index Time Series
    df['travel_date'] = pd.to_datetime(df['travel_date'])
    daily_records = []
    
    for date, day_grp in df.groupby('travel_date'):
        route_indices = []
        route_weights = []
        
        for route, r_grp in day_grp.groupby('route'):
            base_f = route_baselines.get(route, base_fare_national)
            curr_fares = r_grp['total_fare_inr'].values
            base_fares = np.full(len(curr_fares), base_f)
            
            r_idx = jevons_index(curr_fares, base_fares)
            r_weight = get_route_weight(route)
            
            route_indices.append(r_idx)
            route_weights.append(r_weight)
            
        daily_apix = laspeyres_aggregate(route_indices, route_weights) if route_indices else 150.0
        daily_records.append({
            "travel_date": date.strftime('%Y-%m-%d'),
            "apix_jevons_laspeyres": round(daily_apix, 2),
            "observations_count": len(day_grp),
            "mean_fare_inr": round(float(day_grp['total_fare_inr'].mean()), 2)
        })

    df_daily = pd.DataFrame(daily_records).sort_values('travel_date').reset_index(drop=True)
    df_daily['apix_7d_moving_avg'] = df_daily['apix_jevons_laspeyres'].rolling(window=7, min_periods=1).mean().round(2)
    df_daily['market_pulse'] = np.where(df_daily['apix_jevons_laspeyres'] > 155, "Surging / High Demand", "Stable Market Dynamics")
    
    # Save daily index
    df_daily.to_csv(settings.DAILY_INDEX_PATH, index=False)

    # 3. Route Sub-Indices (Corridors)
    route_records = []
    for route, r_grp in df.groupby('route'):
        parts = route.split('-')
        o_iata = parts[0] if len(parts) == 2 else "DEL"
        d_iata = parts[1] if len(parts) == 2 else "BOM"
        
        fares = r_grp['total_fare_inr'].values
        mean_f = float(np.mean(fares))
        med_f = float(np.median(fares))
        std_f = float(np.std(fares)) if len(fares) > 1 else 300.0
        cv = (std_f / mean_f * 100) if mean_f > 0 else 12.0
        
        r_weight = get_route_weight(route)
        r_idx = round((mean_f / base_fare_national) * 150.0, 2)
        
        stress_status = "High Pressure" if mean_f >= 7500 else ("Elevated" if mean_f >= 5000 else "Normal")
        
        route_records.append({
            "route": route,
            "origin_iata": o_iata,
            "dest_iata": d_iata,
            "origin_city": r_grp['origin_raw'].iloc[0] if 'origin_raw' in r_grp.columns and pd.notna(r_grp['origin_raw'].iloc[0]) else o_iata,
            "dest_city": r_grp['dest_raw'].iloc[0] if 'dest_raw' in r_grp.columns and pd.notna(r_grp['dest_raw'].iloc[0]) else d_iata,
            "origin_lat": 28.5562 if o_iata == "DEL" else (19.0896 if o_iata == "BOM" else 13.1986),
            "origin_lon": 77.1000 if o_iata == "DEL" else (72.8656 if o_iata == "BOM" else 77.7066),
            "dest_lat": 19.0896 if d_iata == "BOM" else (28.5562 if d_iata == "DEL" else 13.1986),
            "dest_lon": 72.8656 if d_iata == "BOM" else (77.1000 if d_iata == "DEL" else 77.7066),
            "dgca_traffic_weight_pct": round(r_weight * 100, 2),
            "observations_count": len(r_grp),
            "route_apix_index": r_idx,
            "mean_fare_inr": round(mean_f, 2),
            "median_fare_inr": round(med_f, 2),
            "std_dev_inr": round(std_f, 2),
            "coefficient_of_variation_pct": round(cv, 2),
            "stress_status": stress_status,
            "heatmap_intensity": min(1.0, max(0.2, mean_f / 10000.0))
        })

    df_routes = pd.DataFrame(route_records)
    df_routes.to_csv(settings.ROUTE_INDEX_PATH, index=False)

    return {
        "status": "success",
        "total_observations": len(df),
        "total_routes": len(df_routes),
        "daily_index_points": len(df_daily),
        "latest_apix": float(df_daily.iloc[-1]['apix_jevons_laspeyres']),
        "latest_moving_avg": float(df_daily.iloc[-1]['apix_7d_moving_avg'])
    }
