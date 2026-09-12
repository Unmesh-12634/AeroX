"""
SIH26056: Real-Time Airfare Price Index for India
Route Analytics & Corridor Sub-Indices Router
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from backend.config import settings
from backend.db.database import db

router = APIRouter(tags=["Route Analytics"])

def compute_route_metrics(r_key: str, df_master: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes honest, empirical Route Analytics metrics strictly from real observations:
    1. Corridor HHI: Herfindahl-Hirschman Index using observed carrier quote shares.
    2. Surge Multiplier: T+1 mean fare / T+30 mean fare.
    Strictly returns None if sample is insufficient.
    """
    if df_master.empty:
        return {
            "hhi": None,
            "hhi_classification": None,
            "hhi_notes": "No observations in master ledger",
            "hhi_carrier_shares": {},
            "surge_multiplier": None,
            "surge_status": None,
            "surge_notes": "No observations in master ledger",
            "surge_t1_mean_fare": None,
            "surge_t30_mean_fare": None,
            "surge_t1_obs_count": 0,
            "surge_t30_obs_count": 0,
            "real_observations_count": 0
        }

    parts = r_key.upper().split('-')
    if len(parts) == 2:
        r1, r2 = f"{parts[0]}-{parts[1]}", f"{parts[1]}-{parts[0]}"
        sub = df_master[(df_master['route'].str.upper() == r1) | (df_master['route'].str.upper() == r2)]
    else:
        sub = df_master[df_master['route'].str.upper() == r_key.upper()]

    # Strictly exclude invalid promo coupon fragments / malformed scrapes (< 1500 INR floor)
    sub = sub[sub['total_fare_inr'] >= 1500.0]
    n = len(sub)

    # 1. Corridor HHI (Antitrust Concentration)
    # Threshold: At least 20 real observations required
    if n < 20:
        hhi = None
        hhi_class = None
        hhi_notes = "Insufficient data for concentration analysis (< 20 observations)"
        hhi_shares = {}
    else:
        carrier_counts = sub['airline_standardized'].value_counts()
        hhi_shares = {k: round(float(v / n * 100), 1) for k, v in carrier_counts.items()}
        hhi = round(float(sum((v / n * 100.0) ** 2 for v in carrier_counts)), 1)
        if hhi < 1500:
            hhi_class = "Competitive"
        elif hhi <= 2500:
            hhi_class = "Moderate Concentration"
        else:
            hhi_class = "High Concentration (Duopoly/Monopoly Risk)"
        hhi_notes = "Carrier concentration based on observed flight frequency in our scraped data"

    # 2. Surge Multiplier (T+1 vs T+30 Fare Ratio)
    # Threshold: Requires real data at BOTH T+1 and T+30
    t1_fares = sub[sub['lead_time_days'] == 1]['total_fare_inr'].dropna()
    t30_fares = sub[sub['lead_time_days'] == 30]['total_fare_inr'].dropna()

    if len(t1_fares) == 0 or len(t30_fares) == 0:
        surge_mult = None
        surge_status = None
        surge_notes = "Insufficient data at both T+1 and T+30"
        t1_mean = round(float(t1_fares.mean()), 2) if len(t1_fares) > 0 else None
        t30_mean = round(float(t30_fares.mean()), 2) if len(t30_fares) > 0 else None
    else:
        t1_mean = round(float(t1_fares.mean()), 2)
        t30_mean = round(float(t30_fares.mean()), 2)
        surge_mult = round(t1_mean / t30_mean, 2)
        surge_status = "High-Stress / Surge Pricing" if surge_mult > 2.0 else "Normal"
        surge_notes = "Observed ratio in our own scraped sample, not an official regulatory finding"

    # 3. Empirical Lead-Time Curve for Horizons [T+1, T+7, T+30]
    lead_time_horizons = [1, 7, 30]
    lead_time_curve = []
    for lt in lead_time_horizons:
        lt_sub = sub[sub['lead_time_days'] == lt]['total_fare_inr'].dropna()
        cnt = len(lt_sub)
        if cnt > 0:
            m = round(float(lt_sub.mean()), 2)
            med = round(float(lt_sub.median()), 2)
            min_f = round(float(lt_sub.min()), 2)
            max_f = round(float(lt_sub.max()), 2)
            mult = round(m / t30_mean, 2) if (t30_mean and t30_mean > 0) else None
        else:
            m, med, min_f, max_f, mult = None, None, None, None, None
        lead_time_curve.append({
            "lead_time_days": lt,
            "tag": f"T+{lt}",
            "mean_fare": m,
            "median_fare": med,
            "min_fare": min_f,
            "max_fare": max_f,
            "yield_multiplier": mult,
            "obs_count": cnt
        })

    # Airline curves across T+1, T+7, T+30 (carriers with >= 3 quotes on route)
    carrier_lead_time_curves = {}
    if n >= 20:
        for carrier, count in carrier_counts.items():
            if count >= 3:
                c_df = sub[sub['airline_standardized'] == carrier]
                c_fares_by_lt = []
                for lt in lead_time_horizons:
                    c_lt = c_df[c_df['lead_time_days'] == lt]['total_fare_inr'].dropna()
                    c_fares_by_lt.append(round(float(c_lt.mean()), 2) if len(c_lt) > 0 else None)
                carrier_lead_time_curves[carrier] = c_fares_by_lt

    # 4. Airline Yield & Fare Dispersion on Corridor (strictly real scraped quotes)
    airline_dispersion = []
    if n >= 20:
        for carrier in carrier_counts.index:
            c_df = sub[sub['airline_standardized'] == carrier]
            c_fares = c_df['total_fare_inr'].dropna()
            cnt = len(c_df)
            airline_dispersion.append({
                "airline": carrier,
                "min_fare": round(float(c_fares.min()), 2),
                "mean_fare": round(float(c_fares.mean()), 2),
                "max_fare": round(float(c_fares.max()), 2),
                "obs_count": cnt,
                "quote_share_pct": round(cnt / n * 100.0, 1)
            })

    return {
        "hhi": hhi,
        "hhi_classification": hhi_class,
        "hhi_notes": hhi_notes,
        "hhi_carrier_shares": hhi_shares,
        "surge_multiplier": surge_mult,
        "surge_status": surge_status,
        "surge_notes": surge_notes,
        "surge_t1_mean_fare": t1_mean,
        "surge_t30_mean_fare": t30_mean,
        "surge_t1_obs_count": len(t1_fares),
        "surge_t30_obs_count": len(t30_fares),
        "real_observations_count": n,
        "lead_time_curve": lead_time_curve,
        "carrier_lead_time_curves": carrier_lead_time_curves,
        "airline_dispersion": airline_dispersion
    }

@router.get("/routes")
def get_routes(origin: Optional[str] = None, dest: Optional[str] = None) -> Dict[str, Any]:
    if not settings.ROUTE_INDEX_PATH.exists():
        return {"data": []}
    df = pd.read_csv(settings.ROUTE_INDEX_PATH)
    
    if origin and origin != "ALL":
        df = df[df['origin_iata'].str.upper() == origin.upper()]
    if dest and dest != "ALL":
        df = df[df['dest_iata'].str.upper() == dest.upper()]
        
    df = df.replace({np.nan: None})
    records = df.to_dict(orient="records")

    # Enrich records with real HHI and Surge Multiplier from master observations
    df_master = db.get_master_df()
    for rec in records:
        r_code = rec.get("route", "")
        metrics = compute_route_metrics(r_code, df_master)
        rec.update(metrics)

    return {"data": records}

@router.get("/routes/{route_code}")
def get_route_detail(route_code: str) -> Dict[str, Any]:
    if not settings.ROUTE_INDEX_PATH.exists():
        raise HTTPException(status_code=404, detail="Route index file not found")
    df = pd.read_csv(settings.ROUTE_INDEX_PATH)
    
    parts = route_code.upper().split('-')
    if len(parts) == 2:
        r1, r2 = f"{parts[0]}-{parts[1]}", f"{parts[1]}-{parts[0]}"
        match = df[(df['route'].str.upper() == r1) | (df['route'].str.upper() == r2)]
    else:
        match = df[df['route'].str.upper() == route_code.upper()]
        
    if len(match) == 0:
        raise HTTPException(status_code=404, detail=f"Route {route_code} not found")
        
    rec = match.replace({np.nan: None}).iloc[0].to_dict()
    df_master = db.get_master_df()
    metrics = compute_route_metrics(route_code, df_master)
    rec.update(metrics)

    return {"route": rec}
