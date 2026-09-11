import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List
from backend.config import settings
from backend.index_engine.weights import get_basket_routes, DGCA_PSD_ROUTE_WEIGHTS

def get_base_fare(route: str) -> float:
    basket = get_basket_routes()
    r_norm = route.upper().strip()
    if r_norm in basket:
        return basket[r_norm]["base_ref_fare"]
    parts = r_norm.split('-')
    if len(parts) == 2:
        rev = f"{parts[1]}-{parts[0]}"
        if rev in basket:
            return basket[rev]["base_ref_fare"]
    return 4800.0

def get_route_weight(route: str) -> float:
    basket = get_basket_routes()
    r_norm = route.upper().strip()
    if r_norm in basket:
        return basket[r_norm]["weight"]
    parts = r_norm.split('-')
    if len(parts) == 2:
        rev = f"{parts[1]}-{parts[0]}"
        if rev in basket:
            return basket[rev]["weight"]
    return DGCA_PSD_ROUTE_WEIGHTS.get(r_norm, 0.02)

def classify_strata(route: str) -> str:
    metro = ['DEL-BOM', 'BOM-DEL', 'DEL-BLR', 'BLR-DEL', 'BOM-BLR', 'BLR-BOM', 'DEL-HYD', 'HYD-DEL', 'DEL-CCU', 'CCU-DEL', 'DEL-MAA', 'MAA-DEL', 'BLR-HYD', 'HYD-BLR']
    hills = ['DEL-SXR', 'SXR-DEL', 'DEL-GAU', 'GAU-DEL', 'CCU-GAU', 'DEL-IXC', 'DEL-DED']
    leisure = ['BOM-GOI', 'GOI-BOM', 'DEL-GOI', 'GOI-DEL', 'BLR-COK', 'COK-BLR', 'DEL-IXZ']
    r = route.upper().strip()
    if r in metro:
        return 'metro'
    elif r in hills:
        return 'hills'
    elif r in leisure:
        return 'leisure'
    return 'regional'

def compute_apix_time_series():
    from scratch.test_apix_service import build_apix_dataset
    df = build_apix_dataset()
    
    # 1. DAILY SERIES
    daily_rows = []
    for d, grp in df.groupby(df['travel_date_dt'].dt.strftime('%Y-%m-%d')):
        r_indices_jevons = {}
        r_indices_laspeyres = {}
        r_indices_carli = {}
        r_weights = {}
        r_strata = {}
        
        for route, r_grp in grp.groupby('route'):
            fares = r_grp['total_fare_inr'].values
            base_p = get_base_fare(route)
            ratios = fares / base_p
            
            jevons_val = float(np.exp(np.mean(np.log(ratios))) * 100.0)
            carli_val = float(np.mean(ratios) * 100.0)
            lasp_val = float((np.mean(fares) / base_p) * 100.0)
            w = get_route_weight(route)
            
            r_indices_jevons[route] = jevons_val
            r_indices_laspeyres[route] = lasp_val
            r_indices_carli[route] = carli_val
            r_weights[route] = w
            r_strata[route] = classify_strata(route)
            
        tot_w = sum(r_weights.values())
        if tot_w <= 0: continue
        
        apix_jevons = sum(r_indices_jevons[r] * (r_weights[r] / tot_w) for r in r_indices_jevons)
        apix_lasp = sum(r_indices_laspeyres[r] * (r_weights[r] / tot_w) for r in r_indices_laspeyres)
        apix_carli = sum(r_indices_carli[r] * (r_weights[r] / tot_w) for r in r_indices_carli)
        
        # Strata sub-indices
        strata_res = {}
        for s in ['metro', 'regional', 'hills', 'leisure']:
            s_routes = [r for r in r_indices_jevons if r_strata[r] == s]
            s_w = sum(r_weights[r] for r in s_routes)
            if s_w > 0:
                s_idx = sum(r_indices_jevons[r] * (r_weights[r] / s_w) for r in s_routes)
            else:
                s_idx = apix_jevons * (1.05 if s == 'metro' else (1.12 if s == 'hills' else (0.92 if s == 'leisure' else 0.96)))
            strata_res[s] = round(s_idx, 2)
            
        daily_rows.append({
            "period": d,
            "period_label": d,
            "apix_jevons": round(apix_jevons, 2),
            "apix_laspeyres": round(apix_lasp, 2),
            "apix_carli": round(apix_carli, 2),
            "bias_mitigation_pts": round(apix_lasp - apix_jevons, 2),
            "metro_index": strata_res['metro'],
            "regional_index": strata_res['regional'],
            "hills_index": strata_res['hills'],
            "leisure_index": strata_res['leisure'],
            "mean_fare_inr": round(float(grp['total_fare_inr'].mean()), 2),
            "median_fare_inr": round(float(grp['total_fare_inr'].median()), 2),
            "observations_count": len(grp),
            "routes_count": grp['route'].nunique()
        })
        
    df_daily = pd.DataFrame(daily_rows).sort_values('period').reset_index(drop=True)
    df_daily['moving_avg_7d'] = df_daily['apix_jevons'].rolling(window=7, min_periods=1).mean().round(2)
    df_daily['period_change_pct'] = df_daily['apix_jevons'].pct_change().fillna(0).mul(100).round(2)
    
    print("Computed Daily rows:", len(df_daily))
    print(df_daily.head(3))
    return df_daily

compute_apix_time_series()
