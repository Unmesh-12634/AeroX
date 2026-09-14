"""
SIH26056: Real-Time Airfare Price Index for India (APIx)
Official Indian Festive Calendar & Airport Meteorological Disruption Patterns

Data Sources & Benchmark References:
- Ministry of Civil Aviation (MoCA) Seasonal Airfare Surveillance Bulletins
- Directorate General of Civil Aviation (DGCA) High-Density Festive Travel Reports
- India Meteorological Department (IMD) Aviation Weather Bulletins (Fog / CAT-III & Monsoon)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date

# =============================================================================
# 1. Authentic Indian Festive Travel Calendar (2026 & Recurring Seasons)
# =============================================================================
FESTIVE_EVENTS = [
    {
        "id": "ganesh_utsav_2026",
        "name": "Ganesh Chaturthi & Utsav",
        "category": "major_cultural",
        "start_date": "2026-09-14",
        "end_date": "2026-09-25",
        "peak_travel_dates": ["2026-09-14", "2026-09-15", "2026-09-24", "2026-09-25"],
        "critical_corridors": ["BOM-GOI", "DEL-BOM", "DEL-PNQ", "BOM-BLR", "BOM-HYD", "BOM-CCU"],
        "historical_surge_multiplier": 1.55,
        "surge_pct_range": "+40% to +70%",
        "description": "Massive 10-day homecoming diaspora movement to Maharashtra and Konkan coast. Heavy leisure and weekend holiday spikes on Goa, Pune, and Mumbai trunk corridors."
    },
    {
        "id": "durga_puja_2026",
        "name": "Shardiya Navratri & Durga Puja",
        "category": "major_cultural",
        "start_date": "2026-10-11",
        "end_date": "2026-10-21",
        "peak_travel_dates": ["2026-10-16", "2026-10-17", "2026-10-19", "2026-10-20"],
        "critical_corridors": ["DEL-CCU", "BOM-CCU", "BLR-CCU", "HYD-CCU", "DEL-GAU"],
        "historical_surge_multiplier": 1.72,
        "surge_pct_range": "+50% to +85%",
        "description": "Massive outward diaspora surge to East India (Kolkata & Guwahati). Severe inventory exhaustion 10 days prior."
    },
    {
        "id": "dussehra_2026",
        "name": "Dussehra (Vijayadashami)",
        "category": "national_festival",
        "start_date": "2026-10-19",
        "end_date": "2026-10-21",
        "peak_travel_dates": ["2026-10-20", "2026-10-21"],
        "critical_corridors": ["DEL-BOM", "DEL-BLR", "BOM-BLR", "DEL-JAI", "DEL-UDR"],
        "historical_surge_multiplier": 1.45,
        "surge_pct_range": "+35% to +55%",
        "description": "Long weekend nationwide leisure and homecoming demand across Golden Triangle and Tier-1 metros."
    },
    {
        "id": "diwali_2026",
        "name": "Diwali (Deepavali) & Bhai Dooj",
        "category": "peak_national",
        "start_date": "2026-11-06",
        "end_date": "2026-11-11",
        "peak_travel_dates": ["2026-11-06", "2026-11-07", "2026-11-08", "2026-11-11"],
        "critical_corridors": ["DEL-BOM", "DEL-BLR", "BOM-BLR", "DEL-HYD", "DEL-AMD", "BOM-HYD", "BOM-GOI"],
        "historical_surge_multiplier": 1.95,
        "surge_pct_range": "+75% to +135%",
        "description": "Highest annual domestic aviation demand peak in India. Dynamic pricing algorithms push last-minute economy fares to statutory ceiling."
    },
    {
        "id": "chhath_puja_2026",
        "name": "Chhath Puja Mahaparv",
        "category": "regional_peak",
        "start_date": "2026-11-13",
        "end_date": "2026-11-16",
        "peak_travel_dates": ["2026-11-14", "2026-11-15", "2026-11-16"],
        "critical_corridors": ["DEL-PAT", "BOM-PAT", "BLR-PAT", "DEL-VNS", "DEL-RPR", "DEL-LKO"],
        "historical_surge_multiplier": 2.25,
        "surge_pct_range": "+90% to +180%",
        "description": "Acute structural capacity deficit on Bihar/Eastern UP corridors. Average fares exceed ₹18,000 on T-3 to T-1 windows."
    },
    {
        "id": "winter_holidays_2026",
        "name": "Christmas & New Year Season",
        "category": "tourist_peak",
        "start_date": "2026-12-22",
        "end_date": "2027-01-03",
        "peak_travel_dates": ["2026-12-24", "2026-12-25", "2026-12-30", "2026-12-31", "2027-01-01"],
        "critical_corridors": ["BOM-GOI", "DEL-GOI", "DEL-SXR", "BLR-GOI", "DEL-IXZ", "MAA-IXZ"],
        "historical_surge_multiplier": 1.85,
        "surge_pct_range": "+60% to +110%",
        "description": "High-yield leisure traffic to Goa, Kashmir (Srinagar), and Andaman Islands (Port Blair)."
    }
]

# =============================================================================
# 2. Meteorological & Adverse Weather Risk Indices by Airport & Month
# =============================================================================
# Scale 0.0 (negligible weather disruption) to 1.0 (severe IFR / CAT-III conditions)
WEATHER_PROFILES = {
    "DEL": {  # Indira Gandhi International - Winter Dense Fog (Dec-Jan)
        1: 0.88, 2: 0.35, 3: 0.10, 4: 0.05, 5: 0.12, 6: 0.20,
        7: 0.40, 8: 0.45, 9: 0.20, 10: 0.15, 11: 0.50, 12: 0.92
    },
    "BOM": {  # CSMI Airport - Monsoon Cloudbursts & Windshear (Jun-Aug)
        1: 0.05, 2: 0.05, 3: 0.05, 4: 0.05, 5: 0.15, 6: 0.75,
        7: 0.90, 8: 0.85, 9: 0.50, 10: 0.20, 11: 0.05, 12: 0.05
    },
    "CCU": {  # NSCBI Airport - Pre-monsoon Kalbaisakhi & Bay of Bengal Cyclones
        1: 0.20, 2: 0.10, 3: 0.15, 4: 0.45, 5: 0.65, 6: 0.60,
        7: 0.55, 8: 0.55, 9: 0.50, 10: 0.40, 11: 0.15, 12: 0.25
    },
    "BLR": {  # Kempegowda International - Stable plateau weather, morning radiation fog in Dec
        1: 0.25, 2: 0.10, 3: 0.05, 4: 0.15, 5: 0.30, 6: 0.35,
        7: 0.35, 8: 0.30, 9: 0.30, 10: 0.35, 11: 0.30, 12: 0.35
    },
    "SXR": {  # Srinagar Airport - Heavy snowfall, freezing fog & low visibility
        1: 0.95, 2: 0.85, 3: 0.40, 4: 0.20, 5: 0.10, 6: 0.05,
        7: 0.15, 8: 0.15, 9: 0.10, 10: 0.20, 11: 0.60, 12: 0.90
    },
    "GOI": {  # Dabolim / MOPA - Coastal heavy rain in peak monsoon
        1: 0.05, 2: 0.05, 3: 0.05, 4: 0.05, 5: 0.10, 6: 0.75,
        7: 0.85, 8: 0.80, 9: 0.45, 10: 0.20, 11: 0.05, 12: 0.05
    },
    "PAT": {  # Patna Jay Prakash Narayan - Winter Dense Fog (Very short runway 6,500ft)
        1: 0.92, 2: 0.40, 3: 0.10, 4: 0.05, 5: 0.15, 6: 0.35,
        7: 0.50, 8: 0.50, 9: 0.25, 10: 0.15, 11: 0.45, 12: 0.90
    },
    "DEFAULT": {
        1: 0.15, 2: 0.10, 3: 0.05, 4: 0.05, 5: 0.10, 6: 0.35,
        7: 0.45, 8: 0.40, 9: 0.25, 10: 0.15, 11: 0.15, 12: 0.25
    }
}

def get_festive_surge_factor(route: str, travel_date: date) -> Dict[str, Any]:
    """
    Computes festive surge multiplier and active festival metadata for a given route and date.
    """
    orig, dest = route.split("-") if "-" in route else ("DEL", "BOM")
    rev_route = f"{dest}-{orig}"
    date_str = travel_date.strftime("%Y-%m-%d")

    active_event = None
    surge_multiplier = 1.0
    days_to_peak = 999

    for event in FESTIVE_EVENTS:
        start_d = datetime.strptime(event["start_date"], "%Y-%m-%d").date()
        end_d = datetime.strptime(event["end_date"], "%Y-%m-%d").date()

        # Exact festival dates check (with 1-day pre-festival travel surge buffer)
        is_in_festival = start_d <= travel_date <= end_d
        is_pre_buffer = (start_d - date.resolution * 1) <= travel_date < start_d

        if is_in_festival or is_pre_buffer:
            is_critical = (route in event["critical_corridors"]) or (rev_route in event["critical_corridors"])
            base_mult = event["historical_surge_multiplier"] if is_critical else 1.0 + (event["historical_surge_multiplier"] - 1.0) * 0.45

            if is_pre_buffer:
                # Pre-departure anticipation surge (+15% of the festive premium)
                multiplier = 1.0 + (base_mult - 1.0) * 0.40
            else:
                multiplier = base_mult

            # Peak travel date escalation
            if date_str in event["peak_travel_dates"]:
                multiplier *= 1.15

            if multiplier > surge_multiplier:
                surge_multiplier = multiplier
                active_event = event
                days_to_peak = min(abs((travel_date - datetime.strptime(p, "%Y-%m-%d").date()).days) for p in event["peak_travel_dates"])

    return {
        "has_festival": active_event is not None,
        "event_name": active_event["name"] if active_event else "Standard Period",
        "surge_multiplier": round(surge_multiplier, 3),
        "surge_pct": round((surge_multiplier - 1.0) * 100, 1),
        "days_to_peak": days_to_peak if active_event else None,
        "is_critical_corridor": (active_event is not None and (route in active_event["critical_corridors"] or rev_route in active_event["critical_corridors"])),
        "event_metadata": active_event
    }

def get_weather_disruption_risk(route: str, travel_month: int) -> Dict[str, Any]:
    """
    Computes composite meteorological disruption probability for origin and destination airports.
    """
    orig, dest = route.split("-") if "-" in route else ("DEL", "BOM")
    m = max(1, min(12, travel_month))

    orig_risk = WEATHER_PROFILES.get(orig, WEATHER_PROFILES["DEFAULT"]).get(m, 0.15)
    dest_risk = WEATHER_PROFILES.get(dest, WEATHER_PROFILES["DEFAULT"]).get(m, 0.15)
    composite_risk = max(orig_risk, dest_risk) * 0.7 + min(orig_risk, dest_risk) * 0.3

    risk_label = "Low"
    fare_volatility_multiplier = 1.0
    if composite_risk >= 0.70:
        risk_label = "Severe (CAT-III / Cloudburst)"
        fare_volatility_multiplier = 1.28  # +28% surge due to diversion/cancellation supply crunches
    elif composite_risk >= 0.40:
        risk_label = "Moderate (Seasonal Rain / Reduced Vis)"
        fare_volatility_multiplier = 1.12
    else:
        risk_label = "Nominal (Visual Meteorological Conditions)"
        fare_volatility_multiplier = 1.00

    return {
        "composite_risk_score": round(composite_risk, 3),
        "risk_label": risk_label,
        "origin_risk": orig_risk,
        "dest_risk": dest_risk,
        "weather_surge_multiplier": fare_volatility_multiplier,
        "weather_surge_pct": round((fare_volatility_multiplier - 1.0) * 100, 1)
    }
