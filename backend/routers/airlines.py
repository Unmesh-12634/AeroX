"""
SIH26056: Real-Time Airfare Price Index for India
Airline Analytics & Carrier Fare Intelligence Router
Provides deep-dive empirical analytics: Time-of-Day flight splits (when flights get high vs low),
lead-time booking yield curves (T-45 down to T-1), nonstop vs connecting dispersion,
and corridor price benchmarking across all scheduled domestic carriers.
"""

from fastapi import APIRouter
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import re
from backend.config import settings
from backend.db.database import db

router = APIRouter(tags=["Airline Intelligence"])

def _parse_hour(t_str: Any) -> Optional[int]:
    """Robustly parse 12-hour AM/PM (including non-breaking spaces) or 24-hour departure time."""
    if pd.isna(t_str):
        return None
    clean = str(t_str).replace('\u202f', ' ').replace('\xa0', ' ').strip()
    m = re.match(r'(\d+):(\d+)\s*(AM|PM)', clean, re.IGNORECASE)
    if m:
        h, _, period = int(m.group(1)), int(m.group(2)), m.group(3).upper()
        if period == 'PM' and h != 12:
            h += 12
        elif period == 'AM' and h == 12:
            h = 0
        return h
    m2 = re.match(r'(\d+):(\d+)', clean)
    if m2:
        return int(m2.group(1))
    return None

def _get_tod_key(h: Optional[int]) -> str:
    if h is None:
        return 'mid_day'
    if 4 <= h < 8:
        return 'early_morning'
    elif 8 <= h < 16:
        return 'mid_day'
    elif 16 <= h < 21:
        return 'peak_evening'
    else:
        return 'late_night'

TOD_CONFIG = [
    {
        'key': 'early_morning',
        'label': 'Early Morning',
        'hours': '04:00 – 07:59',
        'desc': 'Corporate commuter & first wave departures',
        'badge': 'Value / Commute',
        'color': '#10B981'
    },
    {
        'key': 'mid_day',
        'label': 'Mid-Day & Afternoon',
        'hours': '08:00 – 15:59',
        'desc': 'Sustained daytime schedules & leisure traffic',
        'badge': 'Balanced Volume',
        'color': '#0284C7'
    },
    {
        'key': 'peak_evening',
        'label': 'Peak Evening',
        'hours': '16:00 – 20:59',
        'desc': 'High-demand return rush & premium yield window',
        'badge': 'Surge Window',
        'color': '#EF4444'
    },
    {
        'key': 'late_night',
        'label': 'Late Night / Red-Eye',
        'hours': '21:00 – 03:59',
        'desc': 'Off-peak & repositioning flights with high dispersion',
        'badge': 'Deep Discount / Late',
        'color': '#D97706'
    }
]

def _build_analytics_payload(sub: pd.DataFrame, total_market_rows: int) -> Dict[str, Any]:
    """Compute deep-dive empirical analytics and flight splits for a dataframe slice."""
    cnt = len(sub)
    if cnt == 0:
        return {}

    mean_f = float(sub['total_fare_inr'].mean())
    med_f = float(sub['total_fare_inr'].median())
    min_f = float(sub['total_fare_inr'].min())
    max_f = float(sub['total_fare_inr'].max())
    std_f = float(sub['total_fare_inr'].std()) if cnt > 1 else 0.0
    cv = (std_f / mean_f * 100) if mean_f > 0 else 0.0

    # Percentile spreads for deeper insight
    p10_f = float(sub['total_fare_inr'].quantile(0.10))
    p90_f = float(sub['total_fare_inr'].quantile(0.90))
    iqr_f = float(sub['total_fare_inr'].quantile(0.75) - sub['total_fare_inr'].quantile(0.25))

    # 1. TIME OF DAY FLIGHT SPLITS
    tod_splits = []
    highest_tod = None
    lowest_tod = None
    max_tod_avg = -1.0
    min_tod_avg = float('inf')

    for cfg in TOD_CONFIG:
        w_df = sub[sub['tod_key'] == cfg['key']]
        w_cnt = len(w_df)
        if w_cnt > 0:
            w_avg = float(w_df['total_fare_inr'].mean())
            w_med = float(w_df['total_fare_inr'].median())
            w_min = float(w_df['total_fare_inr'].min())
            w_max = float(w_df['total_fare_inr'].max())
            w_share = round((w_cnt / cnt) * 100, 1)

            if w_avg > max_tod_avg:
                max_tod_avg = w_avg
                highest_tod = cfg['label']
            if w_avg < min_tod_avg:
                min_tod_avg = w_avg
                lowest_tod = cfg['label']
        else:
            w_avg = mean_f
            w_med = med_f
            w_min = min_f
            w_max = max_f
            w_share = 0.0

        tod_splits.append({
            'key': cfg['key'],
            'label': cfg['label'],
            'hours': cfg['hours'],
            'desc': cfg['desc'],
            'badge': cfg['badge'],
            'color': cfg['color'],
            'count': w_cnt,
            'share_pct': w_share,
            'avg_fare': round(w_avg),
            'median_fare': round(w_med),
            'min_fare': round(w_min),
            'max_fare': round(w_max),
        })

    spread_inr = round(max_tod_avg - min_tod_avg) if (max_tod_avg > 0 and min_tod_avg < float('inf')) else 0
    spread_pct = round((spread_inr / min_tod_avg * 100), 1) if (min_tod_avg > 0 and min_tod_avg < float('inf')) else 0.0

    # 2. LEAD TIME PRICING CURVES (T-45 down to T-1)
    lead_times = sorted(sub['lead_time_days'].dropna().unique())
    lead_splits = []
    for lt in [1, 2, 5, 7, 15, 30, 45]:
        lt_df = sub[sub['lead_time_days'] == lt]
        if len(lt_df) > 0:
            lead_splits.append({
                'lead_days': int(lt),
                'label': f"T-{lt}d" if lt > 0 else "Departure Day",
                'avg_fare': round(float(lt_df['total_fare_inr'].mean())),
                'median_fare': round(float(lt_df['total_fare_inr'].median())),
                'min_fare': round(float(lt_df['total_fare_inr'].min())),
                'max_fare': round(float(lt_df['total_fare_inr'].max())),
                'count': len(lt_df)
            })

    t1_avg = next((x['avg_fare'] for x in lead_splits if x['lead_days'] == 1), mean_f)
    t7_avg = next((x['avg_fare'] for x in lead_splits if x['lead_days'] == 7), mean_f)
    t30_avg = next((x['avg_fare'] for x in lead_splits if x['lead_days'] >= 30), mean_f)
    t45_avg = next((x['avg_fare'] for x in lead_splits if x['lead_days'] >= 45), t30_avg)
    surge_pct = round(((t1_avg - t30_avg) / t30_avg * 100), 1) if t30_avg > 0 else 0.0
    surge_inr = round(t1_avg - t30_avg)
    # Surge risk: how severe is last-minute pricing
    if surge_pct >= 70:
        surge_risk = 'Extreme'
        surge_risk_class = 'critical'
    elif surge_pct >= 40:
        surge_risk = 'High'
        surge_risk_class = 'elevated'
    elif surge_pct >= 20:
        surge_risk = 'Moderate'
        surge_risk_class = 'normal'
    else:
        surge_risk = 'Low'
        surge_risk_class = 'stable'

    # 3. NONSTOP VS CONNECTING FLIGHT SPLIT
    direct_df = sub[sub['is_nonstop'] == True]
    connect_df = sub[sub['is_nonstop'] == False]
    nonstop_split = {
        'direct': {
            'count': len(direct_df),
            'share_pct': round((len(direct_df) / cnt) * 100, 1) if cnt > 0 else 0,
            'avg_fare': round(float(direct_df['total_fare_inr'].mean())) if len(direct_df) > 0 else round(mean_f),
            'median_fare': round(float(direct_df['total_fare_inr'].median())) if len(direct_df) > 0 else round(med_f),
            'min_fare': round(float(direct_df['total_fare_inr'].min())) if len(direct_df) > 0 else round(min_f),
            'max_fare': round(float(direct_df['total_fare_inr'].max())) if len(direct_df) > 0 else round(max_f)
        },
        'connecting': {
            'count': len(connect_df),
            'share_pct': round((len(connect_df) / cnt) * 100, 1) if cnt > 0 else 0,
            'avg_fare': round(float(connect_df['total_fare_inr'].mean())) if len(connect_df) > 0 else round(mean_f),
            'median_fare': round(float(connect_df['total_fare_inr'].median())) if len(connect_df) > 0 else round(med_f),
            'min_fare': round(float(connect_df['total_fare_inr'].min())) if len(connect_df) > 0 else round(min_f),
            'max_fare': round(float(connect_df['total_fare_inr'].max())) if len(connect_df) > 0 else round(max_f)
        }
    }

    # 4. PRICE TIER BRACKETS
    b1 = len(sub[sub['total_fare_inr'] < 6000])
    b2 = len(sub[(sub['total_fare_inr'] >= 6000) & (sub['total_fare_inr'] < 9000)])
    b3 = len(sub[(sub['total_fare_inr'] >= 9000) & (sub['total_fare_inr'] < 15000)])
    b4 = len(sub[sub['total_fare_inr'] >= 15000])

    fare_brackets = [
        {'label': 'Budget (< ₹6k)', 'count': b1, 'pct': round((b1 / cnt) * 100, 1), 'color': '#10B981'},
        {'label': 'Standard (₹6k-₹9k)', 'count': b2, 'pct': round((b2 / cnt) * 100, 1), 'color': '#0284C7'},
        {'label': 'Surge (₹9k-₹15k)', 'count': b3, 'pct': round((b3 / cnt) * 100, 1), 'color': '#D97706'},
        {'label': 'Extreme Peak (> ₹15k)', 'count': b4, 'pct': round((b4 / cnt) * 100, 1), 'color': '#EF4444'}
    ]

    # 5. ROUTE CORRIDORS: CHEAPEST VS HIGHEST SURGE
    route_grp = sub.groupby('route')['total_fare_inr'].agg(['count', 'mean', 'min', 'max']).reset_index()
    cheapest_routes = []
    highest_routes = []
    if len(route_grp) > 0:
        cheapest_sorted = route_grp.sort_values('mean', ascending=True).head(3)
        for _, r in cheapest_sorted.iterrows():
            cheapest_routes.append({
                'route': str(r['route']),
                'avg_fare': round(float(r['mean'])),
                'min_fare': round(float(r['min'])),
                'count': int(r['count'])
            })
        highest_sorted = route_grp.sort_values('mean', ascending=False).head(3)
        for _, r in highest_sorted.iterrows():
            highest_routes.append({
                'route': str(r['route']),
                'avg_fare': round(float(r['mean'])),
                'max_fare': round(float(r['max'])),
                'count': int(r['count'])
            })

    # Nonstop percentage
    nonstop_pct = round(len(direct_df) / cnt * 100, 1) if cnt > 0 else 0.0

    # Extreme surge count (>15k fares)
    extreme_surge_count = len(sub[sub['total_fare_inr'] >= 15000])
    extreme_surge_pct = round(extreme_surge_count / cnt * 100, 1) if cnt > 0 else 0.0

    # Volatility label (correct thresholds based on real CV values 20-80+)
    if cv >= 60:
        vol_label = f'Extreme ({cv:.0f}% CV)'
        vol_class = 'critical'
    elif cv >= 35:
        vol_label = f'High ({cv:.0f}% CV)'
        vol_class = 'elevated'
    elif cv >= 20:
        vol_label = f'Moderate ({cv:.0f}% CV)'
        vol_class = 'normal'
    else:
        vol_label = f'Low ({cv:.0f}% CV)'
        vol_class = 'stable'

    return {
        'observations_count': cnt,
        'market_share_pct': round((cnt / total_market_rows) * 100, 1) if total_market_rows > 0 else 0,
        'mean_fare_inr': round(mean_f),
        'median_fare_inr': round(med_f),
        'min_fare_inr': round(min_f),
        'max_fare_inr': round(max_f),
        'p10_fare_inr': round(p10_f),
        'p90_fare_inr': round(p90_f),
        'iqr_fare_inr': round(iqr_f),
        'std_fare_inr': round(std_f),
        'cv_pct': round(cv, 1),
        'volatility': vol_label,
        'volatility_class': vol_class,
        'nonstop_pct': nonstop_pct,
        'extreme_surge_pct': extreme_surge_pct,
        'extreme_surge_count': extreme_surge_count,
        'tod_splits': tod_splits,
        'highest_tod_window': highest_tod,
        'lowest_tod_window': lowest_tod,
        'tod_spread_inr': spread_inr,
        'tod_spread_pct': spread_pct,
        'lead_splits': lead_splits,
        't1_avg_fare': round(t1_avg),
        't7_avg_fare': round(t7_avg),
        't30_avg_fare': round(t30_avg),
        't45_avg_fare': round(t45_avg),
        'last_minute_surge_pct': surge_pct,
        'last_minute_premium_inr': surge_inr,
        'surge_risk': surge_risk,
        'surge_risk_class': surge_risk_class,
        'nonstop_split': nonstop_split,
        'fare_brackets': fare_brackets,
        'cheapest_routes': cheapest_routes,
        'highest_routes': highest_routes,
        'routes_operated_count': sub['route'].nunique()
    }

CARRIER_META = {
    'IndiGo': {
        'code': '6E',
        'color': '#0284C7',
        'class': 'indigo',
        'logo': '/static/logos/indigo.png',
        'full_name': 'IndiGo (InterGlobe Aviation)',
        'type': 'LCC (Low-Cost Carrier)'
    },
    'Air India': {
        'code': 'AI',
        'color': '#DC2626',
        'class': 'airindia',
        'logo': '/static/logos/airindia.jpg',
        'full_name': 'Air India (Tata Group)',
        'type': 'FSC (Full-Service Carrier)'
    },
    'Akasa Air': {
        'code': 'QP',
        'color': '#EA580C',
        'class': 'akasa',
        'logo': '/static/logos/Akasaair.png',
        'full_name': 'Akasa Air (SNV Aviation)',
        'type': 'Ultra LCC'
    },
    'SpiceJet': {
        'code': 'SG',
        'color': '#E11D48',
        'class': 'spicejet',
        'logo': '/static/logos/spicejet.png',
        'full_name': 'SpiceJet Ltd',
        'type': 'LCC'
    },
    'Air India Express': {
        'code': 'IX',
        'color': '#C2410C',
        'class': 'aix',
        'logo': '/static/logos/airindiaexpress.png',
        'full_name': 'Air India Express',
        'type': 'Regional / LCC'
    }
}

@router.get("/airlines")
@router.get("/airlines/analytics")
def get_airline_analytics(route: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns empirical airline analytics including flight splits (time-of-day, lead-time yield,
    nonstop vs connecting), route corridors, and carrier comparative performance.
    """
    df = db.get_enriched_master_df()
    if len(df) == 0:
        return {"data": [], "market_overview": {}, "total_records": 0}

    # Filter by route if requested
    filtered_df = df.copy()
    if route and route != 'ALL':
        parts = route.upper().split('-')
        if len(parts) == 2:
            r1 = f"{parts[0]}-{parts[1]}"
            r2 = f"{parts[1]}-{parts[0]}"
            filtered_df = filtered_df[(filtered_df['route'].str.upper() == r1) | (filtered_df['route'].str.upper() == r2)]
        else:
            filtered_df = filtered_df[filtered_df['route'].str.upper() == route.upper()]

    if len(filtered_df) == 0:
        filtered_df = df.copy()

    # Pre-parse departure hours and time-of-day windows
    filtered_df['dep_hour'] = filtered_df['departure_time'].apply(_parse_hour)
    filtered_df['tod_key'] = filtered_df['dep_hour'].apply(_get_tod_key)

    total_market_rows = len(filtered_df)

    # 1. Compute Overall Market-Wide Splits
    market_overview = _build_analytics_payload(filtered_df, total_market_rows)
    market_overview['airline'] = 'All Airlines (National Airspace)'
    market_overview['code'] = 'ALL'
    market_overview['color'] = '#0F172A'
    market_overview['logo'] = ''
    market_overview['full_name'] = 'National Commercial Airspace Overview'
    market_overview['routes_served'] = f"{filtered_df['route'].nunique()}/21 corridors"

    # 2. Compute Individual Carrier Analytics
    carrier_results = []
    # Discover actual airlines in dataset
    carrier_order = ['IndiGo', 'Air India', 'Akasa Air', 'SpiceJet', 'Air India Express']
    other_carriers = [c for c in filtered_df['airline_standardized'].unique() if c not in carrier_order and pd.notna(c)]
    all_carrier_keys = carrier_order + other_carriers

    for airline_name in all_carrier_keys:
        sub = filtered_df[filtered_df['airline_standardized'].str.lower() == airline_name.lower()]
        if len(sub) == 0:
            continue

        meta = CARRIER_META.get(airline_name, {
            'code': airline_name[:2].upper(),
            'color': '#0284C7',
            'class': 'generic',
            'logo': '/static/logos/indigo.png',
            'full_name': airline_name,
            'type': 'Domestic Carrier'
        })

        analysis = _build_analytics_payload(sub, total_market_rows)
        if not analysis:
            continue

        analysis['airline'] = airline_name
        analysis['code'] = meta['code']
        analysis['color'] = meta['color']
        analysis['class_name'] = meta['class']
        analysis['logo'] = meta['logo']
        analysis['full_name'] = meta['full_name']
        analysis['carrier_type'] = meta['type']
        analysis['routes_served'] = f"{analysis['routes_operated_count']}/21 routes"
        analysis['delta_pct'] = round(((analysis['mean_fare_inr'] - market_overview['mean_fare_inr']) / market_overview['mean_fare_inr'] * 100), 1)

        carrier_results.append(analysis)

    # Sort carriers by market share descending
    carrier_results.sort(key=lambda x: x['market_share_pct'], reverse=True)

    return {
        "status": "success",
        "total_records": total_market_rows,
        "active_route": route or "ALL",
        "market_overview": market_overview,
        "data": carrier_results
    }
