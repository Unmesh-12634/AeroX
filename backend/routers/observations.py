"""
SIH26056: Real-Time Airfare Price Index for India
Flight Observations & Cross-OTA Ingestion Router
"""

from fastapi import APIRouter, Query
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from backend.db.database import db
from backend.cleaner.normalizer import CITY_SYNONYMS

router = APIRouter(tags=["Master Flight Ledger"])

@router.get("/observations")
def get_observations(
    search: Optional[str] = None,
    route: Optional[str] = None,
    airline: Optional[str] = None,
    source: Optional[str] = None,
    cabin: Optional[str] = None,
    lead_time: Optional[int] = None,
    min_fare: Optional[float] = None,
    max_fare: Optional[float] = None,
    sort_by: str = "travel_date",
    sort_desc: bool = True,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    df = db.get_master_df()
    if len(df) == 0:
        return {"total": 0, "limit": limit, "offset": offset, "observations": []}

    if search:
        s = search.lower().strip()
        matched_iata = CITY_SYNONYMS.get(s, '')
        cond = (
            df['route'].str.lower().str.contains(s, na=False) |
            df['airline_standardized'].str.lower().str.contains(s, na=False) |
            df['record_id'].str.lower().str.contains(s, na=False) |
            df['origin_iata'].str.lower().str.contains(s, na=False) |
            df['dest_iata'].str.lower().str.contains(s, na=False)
        )
        if matched_iata:
            cond = cond | (df['origin_iata'] == matched_iata) | (df['dest_iata'] == matched_iata)
        df = df[cond]

    if route and route != 'ALL':
        parts = route.upper().split('-')
        if len(parts) == 2:
            r1, r2 = f"{parts[0]}-{parts[1]}", f"{parts[1]}-{parts[0]}"
            df = df[(df['route'].str.upper() == r1) | (df['route'].str.upper() == r2)]
        else:
            df = df[df['route'].str.upper() == route.upper()]

    if airline and airline != 'ALL':
        df = df[df['airline_standardized'].str.lower() == airline.lower()]
        
    if source and source != 'ALL':
        src_kw = 'direct' if source.lower() in ['airline_direct', 'direct'] else source.lower()
        df = df[df['source_file'].str.lower().str.contains(src_kw, na=False) | df['dataset_tier'].str.lower().str.contains(src_kw, na=False)]
        
    if cabin and cabin != 'ALL':
        df = df[df['cabin_class'].str.lower() == cabin.lower()]
        
    if lead_time is not None:
        df = df[df['lead_time_days'] == lead_time]
        
    if min_fare is not None:
        df = df[df['total_fare_inr'] >= min_fare]
        
    if max_fare is not None:
        df = df[df['total_fare_inr'] <= max_fare]

    total = len(df)
    if sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=not sort_desc)

    sliced = df.iloc[offset : offset + limit].replace({np.nan: None})
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "observations": sliced.to_dict(orient="records")
    }
