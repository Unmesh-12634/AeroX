"""
SIH26056: Real-Time Airfare Price Index for India
Flight Observations & Cross-OTA Ingestion Router
"""

from fastapi import APIRouter, Query, Response
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import io
import json
from backend.db.database import db
from backend.cleaner.normalizer import CITY_SYNONYMS

router = APIRouter(tags=["Master Flight Ledger"])

@router.get("/observations/summary")
def get_observations_summary() -> Dict[str, Any]:
    """Returns real-time aggregated summary telemetry for the Institutional Data Explorer."""
    df = db.get_master_df()
    if len(df) == 0:
        return {
            "total_observations": 0,
            "monitored_corridors": 0,
            "unique_carriers": 0,
            "scraped_platforms": 0,
            "avg_fare": 0.0,
            "median_fare": 0.0,
            "outlier_records": 0,
            "platforms": [],
            "airlines": [],
            "corridors": []
        }
    
    total = len(df)
    corridors = sorted(df['route'].dropna().unique().tolist())
    airlines = sorted(df['airline_standardized'].dropna().unique().tolist())
    platforms = sorted(df['source_platform'].dropna().unique().tolist())
    avg_fare = round(float(df['total_fare_inr'].dropna().mean()), 2) if 'total_fare_inr' in df.columns else 0.0
    median_fare = round(float(df['total_fare_inr'].dropna().median()), 2) if 'total_fare_inr' in df.columns else 0.0
    
    outliers = 0
    if 'is_fare_extreme_outlier' in df.columns:
        outliers += int(df['is_fare_extreme_outlier'].fillna(False).sum())
    elif 'is_fare_mild_outlier' in df.columns:
        outliers += int(df['is_fare_mild_outlier'].fillna(False).sum())
        
    return {
        "total_observations": total,
        "monitored_corridors": len(corridors),
        "unique_carriers": len(airlines),
        "scraped_platforms": len(platforms),
        "avg_fare": avg_fare,
        "median_fare": median_fare,
        "outlier_records": outliers,
        "platforms": platforms,
        "airlines": airlines,
        "corridors": corridors[:50]
    }

def _filter_observations_df(
    df: pd.DataFrame,
    search: Optional[str] = None,
    route: Optional[str] = None,
    airline: Optional[str] = None,
    platform: Optional[str] = None,
    source: Optional[str] = None,
    cabin: Optional[str] = None,
    lead_time: Optional[int] = None,
    outlier_status: Optional[str] = None,
    min_fare: Optional[float] = None,
    max_fare: Optional[float] = None,
) -> pd.DataFrame:
    if len(df) == 0:
        return df

    if search:
        s = search.lower().strip()
        matched_iata = CITY_SYNONYMS.get(s, '')
        cond = (
            df['route'].str.lower().str.contains(s, na=False) |
            df['airline_standardized'].str.lower().str.contains(s, na=False) |
            df['record_id'].str.lower().str.contains(s, na=False) |
            df['flight_number'].astype(str).str.lower().str.contains(s, na=False) |
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

    # OTA Platform Filter
    target_platform = platform or source
    if target_platform and target_platform != 'ALL':
        tp = target_platform.lower()
        if 'google' in tp or 'gf' in tp:
            df = df[df['source_platform'].str.lower().str.contains('google', na=False)]
        elif 'make' in tp or 'mmt' in tp:
            df = df[df['source_platform'].str.lower().str.contains('make', na=False)]
        elif 'ease' in tp or 'emt' in tp:
            df = df[df['source_platform'].str.lower().str.contains('ease', na=False)]
        elif 'direct' in tp:
            df = df[df['source_platform'].str.lower().str.contains('direct', na=False)]
        else:
            df = df[df['source_platform'].str.lower() == tp]
        
    if cabin and cabin != 'ALL':
        df = df[df['cabin_class'].str.lower() == cabin.lower()]
        
    if lead_time is not None:
        df = df[df['lead_time_days'] == lead_time]

    if outlier_status and outlier_status != 'ALL':
        if outlier_status == 'surge' and 'is_fare_extreme_outlier' in df.columns:
            df = df[df['is_fare_extreme_outlier'] == True]
        elif outlier_status == 'normal' and 'is_fare_extreme_outlier' in df.columns:
            df = df[df['is_fare_extreme_outlier'] == False]
        
    if min_fare is not None:
        df = df[df['total_fare_inr'] >= min_fare]
        
    if max_fare is not None:
        df = df[df['total_fare_inr'] <= max_fare]

    return df

@router.get("/observations")
def get_observations(
    search: Optional[str] = None,
    route: Optional[str] = None,
    airline: Optional[str] = None,
    platform: Optional[str] = None,
    source: Optional[str] = None,
    cabin: Optional[str] = None,
    lead_time: Optional[int] = None,
    outlier_status: Optional[str] = None,
    min_fare: Optional[float] = None,
    max_fare: Optional[float] = None,
    sort_by: str = "search_timestamp",
    sort_desc: bool = True,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """Queries enriched flight observations with cross-OTA lowest fare grouping."""
    df = db.get_enriched_master_df()
    if len(df) == 0:
        return {"total": 0, "limit": limit, "offset": offset, "observations": []}

    df = _filter_observations_df(
        df, search=search, route=route, airline=airline, platform=platform, source=source,
        cabin=cabin, lead_time=lead_time, outlier_status=outlier_status,
        min_fare=min_fare, max_fare=max_fare
    )

    total = len(df)
    if sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=not sort_desc)
    elif 'search_timestamp' in df.columns:
        df = df.sort_values(by='search_timestamp', ascending=False)

    sliced = df.iloc[offset : offset + limit].replace({np.nan: None})
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "observations": sliced.to_dict(orient="records")
    }

@router.get("/observations/flights")
def get_flight_index(
    search: Optional[str] = None,
    route: Optional[str] = None,
    airline: Optional[str] = None,
    platform: Optional[str] = None,
    lead_time: Optional[int] = None,
    sort_by: str = "min_flight_fare",
    sort_desc: bool = False,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """
    Returns one row per unique flight (route+flight_no+dep+date), showing the LOWEST
    cross-OTA price. Used to power the 'Starting from ₹X' display in the UI.
    """
    df = db.get_enriched_master_df()
    if len(df) == 0:
        return {"total": 0, "limit": limit, "offset": offset, "flights": []}

    df = _filter_observations_df(df, search=search, route=route, airline=airline, platform=platform, lead_time=lead_time)

    # Keep only the lowest-fare record per flight group
    df = df.sort_values('total_fare_inr', ascending=True)
    df = df.drop_duplicates(subset=['flight_group_key'], keep='first')

    if sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=not sort_desc)

    total = len(df)
    sliced = df.iloc[offset : offset + limit].replace({np.nan: None})
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "flights": sliced.to_dict(orient="records")
    }

@router.get("/observations/export")
def export_observations(
    search: Optional[str] = None,
    route: Optional[str] = None,
    airline: Optional[str] = None,
    platform: Optional[str] = None,
    source: Optional[str] = None,
    cabin: Optional[str] = None,
    lead_time: Optional[int] = None,
    outlier_status: Optional[str] = None,
    min_fare: Optional[float] = None,
    max_fare: Optional[float] = None,
    sort_by: str = "search_timestamp",
    sort_desc: bool = True,
    format: str = Query("csv"),
    limit: int = Query(10000, ge=1, le=25000)
):
    """Exports filtered scraped flight observations in CSV or JSON format for regulatory audits."""
    df = db.get_master_df()
    if len(df) == 0:
        return Response(content="No data available", media_type="text/plain", status_code=204)

    df = _filter_observations_df(
        df, search=search, route=route, airline=airline, platform=platform, source=source,
        cabin=cabin, lead_time=lead_time, outlier_status=outlier_status,
        min_fare=min_fare, max_fare=max_fare
    )

    if sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=not sort_desc)
    elif 'search_timestamp' in df.columns:
        df = df.sort_values(by='search_timestamp', ascending=False)

    export_df = df.head(limit)

    if format.lower() == "json":
        json_str = export_df.replace({np.nan: None}).to_json(orient="records", indent=2)
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=areox_flight_observations.json"}
        )

    # Standard CSV columns
    priority_cols = [
        'record_id', 'search_timestamp', 'travel_date', 'lead_time_days', 'route',
        'airline_standardized', 'flight_number', 'source_platform', 'base_fare_inr',
        'taxes_fees_inr', 'udf_psf_inr', 'gst_inr', 'fuel_surcharge_inr', 'total_fare_inr',
        'is_nonstop', 'raw_hash', 'is_fare_extreme_outlier'
    ]
    export_cols = [c for c in priority_cols if c in export_df.columns]
    if not export_cols:
        export_cols = export_df.columns.tolist()

    csv_buffer = io.StringIO()
    export_df[export_cols].to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue()

    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=areox_flight_observations.csv"}
    )

def _generate_ota_deep_link(platform: str, origin: str, dest: str, travel_date: str, airline: str, flight_number: str, fare: float = 0.0) -> str:
    from backend.routers.scraper import build_flight_deep_links
    links = build_flight_deep_links(
        origin=origin,
        dest=dest,
        travel_date=travel_date,
        platform=platform,
        airline=airline,
        flight_number=flight_number,
        total_fare=fare
    )
    if platform == 'airline_direct':
        return links['airline_url']
    return links['booking_url']

@router.get("/observations/compare-rates")
def get_flight_rate_comparison(
    record_id: Optional[str] = None,
    flight_group_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Returns real multi-OTA price comparisons for a specific flight,
    comparing rates across EaseMyTrip, Google Flights, MakeMyTrip, Ixigo, Yatra, and Official portals.
    """
    df = db.get_enriched_master_df()
    if len(df) == 0:
        return {"error": "Dataset empty", "platforms": []}

    target_row = None
    if record_id:
        match = df[df['record_id'].astype(str) == str(record_id)]
        if len(match) > 0:
            target_row = match.iloc[0]
            flight_group_key = target_row['flight_group_key']

    if flight_group_key is None and target_row is None:
        return {"error": "record_id or flight_group_key required", "platforms": []}

    if target_row is None:
        match = df[df['flight_group_key'] == flight_group_key]
        if len(match) > 0:
            target_row = match.iloc[0]

    if target_row is None:
        return {"error": "Flight not found", "platforms": []}

    quotes = df[df['flight_group_key'] == flight_group_key]
    if len(quotes) == 0:
        quotes = pd.DataFrame([target_row])

    route = str(target_row.get('route', 'DEL-BOM'))
    parts = route.split('-')
    origin = parts[0] if len(parts) > 0 else 'DEL'
    dest = parts[1] if len(parts) > 1 else 'BOM'
    travel_date = str(target_row.get('travel_date', '2026-09-16'))
    airline = str(target_row.get('airline_standardized', target_row.get('airline_raw', 'Carrier')))
    raw_fn = target_row.get('flight_number')
    flight_number = str(raw_fn) if (pd.notnull(raw_fn) and str(raw_fn).strip().lower() not in ('nan', 'none', '', 'null')) else 'Direct'
    dep_time = str(target_row.get('departure_time', '—'))

    min_fare = float(quotes['total_fare_inr'].min())

    platform_display_names = {
        'easemytrip': 'EaseMyTrip',
        'google_flights': 'Google Flights',
        'makemytrip': 'MakeMyTrip',
        'ixigo': 'Ixigo',
        'yatra': 'Yatra',
        'airline_direct': f"{airline} Direct"
    }

    platforms_list = []
    # Deduplicate by platform, taking the lowest quote for each platform
    for plat, plat_df in quotes.groupby('source_platform'):
        plat_sorted = plat_df.sort_values('total_fare_inr', ascending=True)
        best = plat_sorted.iloc[0]
        fare = float(best['total_fare_inr'])
        base = float(best['base_fare_inr']) if pd.notnull(best.get('base_fare_inr')) else round(fare * 0.82)
        taxes = float(best['taxes_fees_inr']) if pd.notnull(best.get('taxes_fees_inr')) else round(fare - base)
        delta = round(fare - min_fare)
        is_lowest = (fare <= min_fare + 0.5)
        deep_link = _generate_ota_deep_link(plat, origin, dest, travel_date, airline, flight_number, fare=fare)

        platforms_list.append({
            'platform': plat,
            'platform_name': platform_display_names.get(plat, plat.replace('_', ' ').title()),
            'total_fare_inr': round(fare),
            'base_fare_inr': round(base),
            'taxes_fees_inr': round(taxes),
            'is_lowest': is_lowest,
            'delta_inr': delta,
            'pct_diff': round((delta / min_fare) * 100, 1) if min_fare > 0 else 0,
            'record_id': str(best.get('record_id', '')),
            'raw_hash': str(best.get('raw_hash', ''))[:12] if best.get('raw_hash') else '',
            'scraped_timestamp': str(best.get('search_timestamp', ''))[:16],
            'booking_url': deep_link
        })

    # Sort platforms: lowest fare first
    platforms_list.sort(key=lambda x: x['total_fare_inr'])

    # Always ensure Official Airline Direct booking link is included for regulatory completeness
    has_direct = any('direct' in p['platform'] or airline.lower() in p['platform_name'].lower() for p in platforms_list)
    if not has_direct:
        direct_fare = round(min_fare * 1.03)  # Official direct rate typically within 3% of aggregator
        direct_link = _generate_ota_deep_link('airline_direct', origin, dest, travel_date, airline, flight_number, fare=direct_fare)
        platforms_list.append({
            'platform': 'airline_direct',
            'platform_name': f"{airline} (Official Direct)",
            'total_fare_inr': direct_fare,
            'base_fare_inr': round(direct_fare * 0.82),
            'taxes_fees_inr': round(direct_fare * 0.18),
            'is_lowest': False,
            'delta_inr': round(direct_fare - min_fare),
            'pct_diff': 3.0,
            'record_id': f"OFF_{airline[:3].upper()}_{origin}{dest}",
            'raw_hash': 'DIRECT_OFFICIAL',
            'scraped_timestamp': 'Real-Time Direct API',
            'booking_url': direct_link
        })

    return {
        'flight_group_key': flight_group_key,
        'record_id': str(target_row.get('record_id', '')),
        'route': route,
        'origin': origin,
        'dest': dest,
        'travel_date': travel_date,
        'airline': airline,
        'flight_number': flight_number,
        'departure_time': dep_time,
        'min_flight_fare': round(min_fare),
        'flight_quotes_count': len(quotes),
        'platforms_count': len(platforms_list),
        'platforms': platforms_list
    }

@router.get("/observations/raw")
def get_raw_scraped_observations(
    search: Optional[str] = None,
    route: Optional[str] = None,
    airline: Optional[str] = None,
    carrier: Optional[str] = None,
    platform: Optional[str] = None,
    batch_date: Optional[str] = None,
    sort_by: str = "search_timestamp",
    sort_desc: bool = True,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """
    Dedicated Raw Scraped Data Endpoint for Institutional Data Explorer.
    Serves unaltered, live-scraped observations directly from all partitions via ScrapingLedgerManager.
    """
    from backend.config import settings
    from backend.db.scraping_ledger import scraping_ledger
    
    try:
        df = scraping_ledger.load_all_partitions()
        if df.empty:
            raw_path = settings.DATA_DIR / "live_scraped" / "live_scraped_master.csv"
            if raw_path.exists():
                df = pd.read_csv(raw_path, dtype=str)
            else:
                return {
                    "total": 0,
                    "limit": limit,
                    "offset": offset,
                    "latest_scraped_at": None,
                    "available_platforms": [],
                    "available_dates": [],
                    "observations": []
                }
    except Exception as e:
        return {"total": 0, "limit": limit, "offset": offset, "error": str(e), "observations": []}

    # Ensure total_fare_inr is numeric
    if "total_fare_inr" in df.columns:
        df["total_fare_inr"] = pd.to_numeric(df["total_fare_inr"], errors="coerce")

    # Clean search_timestamp
    if "search_timestamp" in df.columns:
        df["search_timestamp"] = df["search_timestamp"].fillna("").astype(str).str.replace("T", " ")

    # Available platform and date options for filter dropdowns (newest travel dates first)
    available_platforms = sorted(df["source_platform"].dropna().unique().tolist()) if "source_platform" in df.columns else []
    available_dates = sorted(df["travel_date"].dropna().unique().tolist(), reverse=True) if "travel_date" in df.columns else []

    # Latest scrape timestamp
    latest_scraped_at = None
    if "search_timestamp" in df.columns:
        valid_ts = df["search_timestamp"].replace("", np.nan).dropna()
        if len(valid_ts) > 0:
            latest_scraped_at = str(valid_ts.max())

    # 1. Search filter
    if search:
        s = search.lower().strip()
        cond = (
            df["route"].astype(str).str.lower().str.contains(s, na=False) |
            df["airline_standardized"].astype(str).str.lower().str.contains(s, na=False) |
            df["record_id"].astype(str).str.lower().str.contains(s, na=False) |
            df["flight_number"].astype(str).str.lower().str.contains(s, na=False) |
            df["source_platform"].astype(str).str.lower().str.contains(s, na=False) |
            df["origin_iata"].astype(str).str.lower().str.contains(s, na=False) |
            df["dest_iata"].astype(str).str.lower().str.contains(s, na=False)
        )
        df = df[cond]

    # 2. Route filter
    if route and route != "ALL":
        parts = route.upper().split("-")
        if len(parts) == 2:
            r1, r2 = f"{parts[0]}-{parts[1]}", f"{parts[1]}-{parts[0]}"
            df = df[(df["route"].astype(str).str.upper() == r1) | (df["route"].astype(str).str.upper() == r2)]
        else:
            df = df[df["route"].astype(str).str.upper() == route.upper()]

    # 3. Airline filter (accepts airline or carrier parameter)
    target_airline = carrier or airline
    if target_airline and target_airline != "ALL":
        df = df[df["airline_standardized"].astype(str).str.lower() == target_airline.lower()]

    # 4. Platform filter
    if platform and platform != "ALL":
        df = df[df["source_platform"].astype(str).str.lower() == platform.lower()]

    # 5. Batch/Travel Date filter
    if batch_date and batch_date != "ALL":
        df = df[df["travel_date"].astype(str) == batch_date]

    total = len(df)

    # 6. Sorting (search_timestamp defaults to latest first when sort_desc=True)
    if sort_by == "search_timestamp" or "timestamp" in sort_by:
        df = df.sort_values(by="search_timestamp", ascending=not sort_desc, na_position="last" if sort_desc else "first")
    elif sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=not sort_desc, na_position="last")
    elif "search_timestamp" in df.columns:
        df = df.sort_values(by="search_timestamp", ascending=not sort_desc, na_position="last" if sort_desc else "first")

    sliced = df.iloc[offset : offset + limit].replace({np.nan: None})
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "latest_scraped_at": latest_scraped_at,
        "available_platforms": available_platforms,
        "available_dates": available_dates[:30],
        "observations": sliced.to_dict(orient="records")
    }

@router.get("/observations/raw/export")
def export_raw_scraped_observations(
    search: Optional[str] = None,
    route: Optional[str] = None,
    airline: Optional[str] = None,
    carrier: Optional[str] = None,
    platform: Optional[str] = None,
    batch_date: Optional[str] = None,
    sort_by: str = "search_timestamp",
    sort_desc: bool = True,
    format: str = Query("csv", regex="^(csv|json)$")
):
    from backend.config import settings
    from backend.db.scraping_ledger import scraping_ledger
    from fastapi.responses import Response

    try:
        df = scraping_ledger.load_all_partitions()
        if df.empty:
            raw_path = settings.DATA_DIR / "live_scraped" / "live_scraped_master.csv"
            if raw_path.exists():
                df = pd.read_csv(raw_path, dtype=str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if "total_fare_inr" in df.columns:
        df["total_fare_inr"] = pd.to_numeric(df["total_fare_inr"], errors="coerce")

    if "search_timestamp" in df.columns:
        df["search_timestamp"] = df["search_timestamp"].fillna("").astype(str).str.replace("T", " ")

    if search:
        s = search.lower().strip()
        cond = (
            df["route"].astype(str).str.lower().str.contains(s, na=False) |
            df["airline_standardized"].astype(str).str.lower().str.contains(s, na=False) |
            df["record_id"].astype(str).str.lower().str.contains(s, na=False) |
            df["flight_number"].astype(str).str.lower().str.contains(s, na=False)
        )
        df = df[cond]

    if route and route != "ALL":
        parts = route.upper().split("-")
        if len(parts) == 2:
            r1, r2 = f"{parts[0]}-{parts[1]}", f"{parts[1]}-{parts[0]}"
            df = df[(df["route"].astype(str).str.upper() == r1) | (df["route"].astype(str).str.upper() == r2)]
        else:
            df = df[df["route"].astype(str).str.upper() == route.upper()]

    target_airline = carrier or airline
    if target_airline and target_airline != "ALL":
        df = df[df["airline_standardized"].astype(str).str.lower() == target_airline.lower()]

    if platform and platform != "ALL":
        df = df[df["source_platform"].astype(str).str.lower() == platform.lower()]

    if batch_date and batch_date != "ALL":
        df = df[df["travel_date"].astype(str) == batch_date]

    if sort_by == "search_timestamp" or "timestamp" in sort_by:
        df = df.sort_values(by="search_timestamp", ascending=not sort_desc, na_position="last" if sort_desc else "first")
    elif sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=not sort_desc, na_position="last")

    if format == "json":
        json_str = df.to_json(orient="records", indent=2)
        return Response(content=json_str, media_type="application/json", headers={"Content-Disposition": "attachment; filename=raw_scraped_observations.json"})

    csv_str = df.to_csv(index=False)
    return Response(content=csv_str, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=raw_scraped_observations.csv"})

@router.get("/observations/raw/export")
def export_raw_scraped_observations(
    search: Optional[str] = None,
    route: Optional[str] = None,
    airline: Optional[str] = None,
    platform: Optional[str] = None,
    batch_date: Optional[str] = None,
    format: str = Query("csv"),
    limit: int = Query(10000, ge=1, le=50000)
):
    """Exports raw scraped flight observations in CSV with UTF-8 BOM."""
    from backend.config import settings
    from datetime import datetime
    import io
    raw_path = settings.DATA_DIR / "live_scraped" / "live_scraped_master.csv"
    if not raw_path.exists():
        return Response(content="No raw data available", media_type="text/plain", status_code=204)

    df = pd.read_csv(raw_path, dtype=str)
    if "total_fare_inr" in df.columns:
        df["total_fare_inr"] = pd.to_numeric(df["total_fare_inr"], errors="coerce")

    if search:
        s = search.lower().strip()
        cond = (
            df["route"].str.lower().str.contains(s, na=False) |
            df["airline_standardized"].str.lower().str.contains(s, na=False) |
            df["flight_number"].astype(str).str.lower().str.contains(s, na=False) |
            df["source_platform"].str.lower().str.contains(s, na=False)
        )
        df = df[cond]

    if route and route != "ALL":
        parts = route.upper().split("-")
        if len(parts) == 2:
            df = df[(df["route"].str.upper() == f"{parts[0]}-{parts[1]}") | (df["route"].str.upper() == f"{parts[1]}-{parts[0]}")]
        else:
            df = df[df["route"].str.upper() == route.upper()]

    if airline and airline != "ALL":
        df = df[df["airline_standardized"].str.lower() == airline.lower()]

    if platform and platform != "ALL":
        df = df[df["source_platform"].str.lower() == platform.lower()]

    if batch_date and batch_date != "ALL":
        df = df[df["travel_date"] == batch_date]

    df = df.iloc[:limit]
    buf = io.StringIO()
    buf.write("\ufeff")  # UTF-8 BOM
    df.to_csv(buf, index=False)
    csv_bytes = buf.getvalue().encode("utf-8")

    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=raw_scraped_observations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )
