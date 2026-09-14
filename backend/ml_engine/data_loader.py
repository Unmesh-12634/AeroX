"""
SIH26056: Real-Time Airfare Price Index for India (APIx)
Empirical Flight Data Consolidation & Feature Engineering Pipeline
Combines:
- 10,679 historical records from cleaned_historical_fares_2019.csv
- 2,906 historical records from cleaned_flight_observations_2022.csv
- 7,245 live scraped multi-OTA records from live_scraped_master.csv
Total: 20,830 genuine observations.
"""

import pandas as pd
import numpy as np
import math
from pathlib import Path
from datetime import datetime, date
from typing import Tuple, List, Dict, Any

from backend.config import settings
from backend.ml_engine.festive_calendar import get_festive_surge_factor, get_weather_disruption_risk

# Realistic Airport Coordinates for Haversine Distance
AIRPORT_COORDS = {
    "DEL": (28.5562, 77.1000), "BOM": (19.0896, 72.8656),
    "BLR": (13.1986, 77.7066), "HYD": (17.2403, 78.4294),
    "CCU": (22.6547, 88.4467), "MAA": (12.9941, 80.1709),
    "AMD": (23.0772, 72.6347), "GOI": (15.3800, 73.8314),
    "GOX": (15.7483, 73.8658), "SXR": (33.9871, 74.7741),
    "PAT": (25.5912, 85.0880), "LKO": (26.7606, 80.8893),
    "GAU": (26.1061, 91.5859), "JAI": (26.8242, 75.8122),
    "UDR": (24.6178, 73.8961), "IXZ": (11.6412, 92.7297),
    "VNS": (25.4524, 82.8593), "RPR": (21.1804, 81.7388),
    "BBI": (20.2444, 85.8178), "TRV": (8.4821, 76.9200)
}

def calculate_distance_km(orig: str, dest: str) -> float:
    if orig in AIRPORT_COORDS and dest in AIRPORT_COORDS:
        lat1, lon1 = AIRPORT_COORDS[orig]
        lat2, lon2 = AIRPORT_COORDS[dest]
        r = 6371.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp = math.radians(lat2 - lat1)
        dl = math.radians(lon2 - lon1)
        a = math.sin(dp / 2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2)**2
        return round(2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)
    return 1150.0  # National median corridor distance

def parse_hour(time_str: Any) -> int:
    if not time_str or pd.isna(time_str):
        return 10  # default morning peak
    s = str(time_str).strip().upper()
    try:
        if "AM" in s or "PM" in s:
            is_pm = "PM" in s
            s_clean = s.replace("AM", "").replace("PM", "").strip()
            parts = s_clean.split(":")
            h = int(parts[0])
            if is_pm and h < 12:
                h += 12
            elif not is_pm and h == 12:
                h = 0
            return max(0, min(23, h))
        elif ":" in s:
            return max(0, min(23, int(s.split(":")[0])))
    except Exception:
        pass
    return 10

def safe_int_lead(val: Any, default: int = 14) -> int:
    if val is None or pd.isna(val):
        return default
    try:
        f = float(val)
        if math.isnan(f):
            return default
        return max(1, min(45, int(f)))
    except Exception:
        return default

def load_consolidated_dataset() -> pd.DataFrame:
    """
    Loads and standardizes historical and live real flight records.
    """
    data_dir = settings.DATA_DIR
    records = []

    # 1. 2019 Cleaned Dataset
    p2019 = data_dir / "cleaned" / "cleaned_historical_fares_2019.csv"
    if p2019.exists():
        try:
            df19 = pd.read_csv(p2019)
            for _, row in df19.iterrows():
                fare = float(row.get("total_fare_inr", 0) or 0)
                if fare < 1500 or fare > 90000:
                    continue
                orig = str(row.get("origin_iata", "DEL")).strip().upper()
                dest = str(row.get("dest_iata", "BOM")).strip().upper()
                carrier = str(row.get("airline_standardized", "IndiGo")).strip()
                t_date = str(row.get("travel_date", "2019-05-15")).strip()
                lead = safe_int_lead(row.get("lead_time_days"), default=14)
                dep_hour = parse_hour(row.get("departure_time"))

                records.append({
                    "origin": orig,
                    "dest": dest,
                    "route": f"{orig}-{dest}",
                    "carrier": carrier,
                    "travel_date": t_date,
                    "lead_time_days": lead,
                    "departure_hour": dep_hour,
                    "total_fare_inr": fare,
                    "dataset_source": "2019_historical"
                })
        except Exception as e:
            print(f"[-] Error loading 2019 dataset: {e}")

    # 2. 2022 Cleaned Dataset
    p2022 = data_dir / "cleaned" / "cleaned_flight_observations_2022.csv"
    if p2022.exists():
        try:
            df22 = pd.read_csv(p2022)
            for _, row in df22.iterrows():
                fare = float(row.get("total_fare_inr", 0) or 0)
                if fare < 1500 or fare > 90000:
                    continue
                orig = str(row.get("origin_iata", "DEL")).strip().upper()
                dest = str(row.get("dest_iata", "BOM")).strip().upper()
                carrier = str(row.get("airline_standardized", "Air India")).strip()
                t_date = str(row.get("travel_date", "2022-03-20")).strip()
                lead = safe_int_lead(row.get("lead_time_days"), default=7)
                dep_hour = parse_hour(row.get("departure_time"))

                records.append({
                    "origin": orig,
                    "dest": dest,
                    "route": f"{orig}-{dest}",
                    "carrier": carrier,
                    "travel_date": t_date,
                    "lead_time_days": lead,
                    "departure_hour": dep_hour,
                    "total_fare_inr": fare,
                    "dataset_source": "2022_historical"
                })
        except Exception as e:
            print(f"[-] Error loading 2022 dataset: {e}")

    # 3. Live Scraped Partitions (Contemporary Multi-OTA)
    try:
        from backend.db.scraping_ledger import scraping_ledger
        dflive = scraping_ledger.load_all_partitions()
        if dflive.empty:
            p_live = data_dir / "live_scraped" / "live_scraped_master.csv"
            if p_live.exists():
                dflive = pd.read_csv(p_live, low_memory=False)

        for _, row in dflive.iterrows():
            fare = float(row.get("total_fare_inr", 0) or 0)
            if fare < 1500 or fare > 90000:
                continue
            orig = str(row.get("origin_iata", "DEL")).strip().upper()
            dest = str(row.get("dest_iata", "BOM")).strip().upper()
            carrier = str(row.get("airline_standardized", "IndiGo")).strip()
            t_date = str(row.get("travel_date", "2026-09-20")).strip()
            lead = safe_int_lead(row.get("lead_time_days"), default=1)
            dep_hour = parse_hour(row.get("departure_time"))

            records.append({
                "origin": orig,
                "dest": dest,
                "route": f"{orig}-{dest}",
                "carrier": carrier,
                "travel_date": t_date,
                "lead_time_days": lead,
                "departure_hour": dep_hour,
                "total_fare_inr": fare,
                "dataset_source": "2026_live_scraped"
            })
    except Exception as e:
        print(f"[-] Error loading live scraped partitions in ML data loader: {e}")

    df = pd.DataFrame(records)
    if len(df) == 0:
        raise ValueError("No flight records found in data directories.")

    # Feature Engineering
    df["distance_km"] = df.apply(lambda r: calculate_distance_km(r["origin"], r["dest"]), axis=1)

    # Parse travel dates
    parsed_dates = []
    days_of_week = []
    months = []
    is_weekends = []

    for d_str in df["travel_date"]:
        try:
            # Handle various date formats (YYYY-MM-DD or DD/MM/YYYY)
            if "/" in d_str:
                d_obj = datetime.strptime(d_str, "%d/%m/%Y").date()
            else:
                d_obj = datetime.strptime(d_str[:10], "%Y-%m-%d").date()
        except Exception:
            d_obj = date(2026, 9, 25)

        parsed_dates.append(d_obj)
        dow = d_obj.weekday()
        days_of_week.append(dow)
        months.append(d_obj.month)
        is_weekends.append(1 if dow in [4, 5, 6] else 0)  # Fri, Sat, Sun peak travel

    df["parsed_date"] = parsed_dates
    df["day_of_week"] = days_of_week
    df["travel_month"] = months
    df["is_weekend"] = is_weekends

    # Enrich with Indian Festive & Weather Factors
    festive_factors = []
    weather_risks = []

    for _, row in df.iterrows():
        f_info = get_festive_surge_factor(row["route"], row["parsed_date"])
        w_info = get_weather_disruption_risk(row["route"], row["travel_month"])
        festive_factors.append(f_info["surge_multiplier"])
        weather_risks.append(w_info["composite_risk_score"])

    df["festive_surge_factor"] = festive_factors
    df["weather_risk_score"] = weather_risks

    return df
