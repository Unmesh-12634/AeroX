"""
SIH26056: Real-Time Airfare Price Index for India
Database & Data Repository Layer
"""

import os
import json
import sqlite3
import numpy as np
import pandas as pd
from typing import Optional, List, Dict, Any
from pathlib import Path
from backend.config import settings

class DataRepository:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataRepository, cls).__new__(cls)
            cls._instance._init_repo()
        return cls._instance

    def _init_repo(self):
        self.master_df: Optional[pd.DataFrame] = None
        self.airports_dict: Dict[str, Dict[str, Any]] = {}
        self._load_master_data()
        self._load_airports()

    def _load_master_data(self):
        dfs = []
        if settings.MASTER_CSV_PATH.exists():
            try:
                df = pd.read_csv(settings.MASTER_CSV_PATH, low_memory=False)
                df['total_fare_inr'] = pd.to_numeric(df['total_fare_inr'], errors='coerce')
                df = df.dropna(subset=['total_fare_inr'])
                # Enforce valid commercial domestic airfare floor (>= 1500 INR)
                df = df[df['total_fare_inr'] >= 1500.0]
                dfs.append(df)
            except Exception as e:
                print(f"[-] Error loading master CSV: {e}")

        live_master = settings.LIVE_SCRAPED_DIR / "live_scraped_master.csv"
        if live_master.exists():
            try:
                ldf = pd.read_csv(live_master, low_memory=False)
                ldf['total_fare_inr'] = pd.to_numeric(ldf['total_fare_inr'], errors='coerce')
                ldf = ldf.dropna(subset=['total_fare_inr'])
                dfs.append(ldf)
            except Exception as e:
                print(f"[-] Error loading live scraped CSV: {e}")

        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
            subset_cols = [c for c in ['route', 'travel_date', 'airline_standardized', 'departure_time', 'total_fare_inr'] if c in combined.columns]
            if subset_cols:
                combined = combined.drop_duplicates(subset=subset_cols)
            self.master_df = combined
        else:
            self.master_df = pd.DataFrame()

    def _load_airports(self):
        self.airports_list = [
            {"iata": "DEL", "city": "Delhi (NCR)", "state": "Delhi", "name": "Indira Gandhi International Airport", "lat": 28.5562, "lon": 77.1000, "is_hub": True, "tier": "Tier-1 Metro"},
            {"iata": "BOM", "city": "Mumbai", "state": "Maharashtra", "name": "Chhatrapati Shivaji Maharaj International Airport", "lat": 19.0896, "lon": 72.8656, "is_hub": True, "tier": "Tier-1 Metro"},
            {"iata": "BLR", "city": "Bengaluru (Bangalore)", "state": "Karnataka", "name": "Kempegowda International Airport", "lat": 13.1986, "lon": 77.7066, "is_hub": True, "tier": "Tier-1 Metro"},
            {"iata": "HYD", "city": "Hyderabad", "state": "Telangana", "name": "Rajiv Gandhi International Airport", "lat": 17.2403, "lon": 78.4294, "is_hub": True, "tier": "Tier-1 Metro"},
            {"iata": "CCU", "city": "Kolkata (Calcutta)", "state": "West Bengal", "name": "Netaji Subhash Chandra Bose Intl Airport", "lat": 22.6547, "lon": 88.4467, "is_hub": True, "tier": "Tier-1 Metro"},
            {"iata": "MAA", "city": "Chennai (Madras)", "state": "Tamil Nadu", "name": "Chennai International Airport", "lat": 12.9941, "lon": 80.1709, "is_hub": True, "tier": "Tier-1 Metro"},
            {"iata": "AMD", "city": "Ahmedabad", "state": "Gujarat", "name": "Sardar Vallabhbhai Patel International Airport", "lat": 23.0772, "lon": 72.6347, "is_hub": False, "tier": "Tier-2 Major"},
            {"iata": "COK", "city": "Kochi (Cochin)", "state": "Kerala", "name": "Cochin International Airport", "lat": 10.1556, "lon": 76.3914, "is_hub": False, "tier": "Tier-2 Major"},
            {"iata": "GOI", "city": "Goa (Dabolim)", "state": "Goa", "name": "Dabolim International Airport", "lat": 15.3808, "lon": 73.8314, "is_hub": False, "tier": "Tourist Trunk"},
            {"iata": "GOX", "city": "Goa (Mopa)", "state": "Goa", "name": "Manohar International Airport", "lat": 15.7667, "lon": 73.8667, "is_hub": False, "tier": "Tourist Trunk"},
            {"iata": "PNQ", "city": "Pune", "state": "Maharashtra", "name": "Pune International Airport", "lat": 18.5822, "lon": 73.9197, "is_hub": False, "tier": "Tier-2 Major"},
            {"iata": "JAI", "city": "Jaipur", "state": "Rajasthan", "name": "Jaipur International Airport", "lat": 26.8242, "lon": 75.8122, "is_hub": False, "tier": "Tier-2 Major"},
            {"iata": "LKO", "city": "Lucknow", "state": "Uttar Pradesh", "name": "Chaudhary Charan Singh International Airport", "lat": 26.7606, "lon": 80.8893, "is_hub": False, "tier": "Tier-2 Major"},
            {"iata": "GAU", "city": "Guwahati", "state": "Assam", "name": "Lokpriya Gopinath Bordoloi International Airport", "lat": 26.1061, "lon": 91.5859, "is_hub": False, "tier": "North East Hub"},
            {"iata": "PAT", "city": "Patna", "state": "Bihar", "name": "Jay Prakash Narayan Airport", "lat": 25.5913, "lon": 85.0880, "is_hub": False, "tier": "Regional Capital"},
            {"iata": "BBI", "city": "Bhubaneswar", "state": "Odisha", "name": "Biju Patnaik International Airport", "lat": 20.2444, "lon": 85.8178, "is_hub": False, "tier": "Regional Capital"},
            {"iata": "SXR", "city": "Srinagar", "state": "Jammu and Kashmir", "name": "Sheikh ul-Alam International Airport", "lat": 33.9871, "lon": 74.7741, "is_hub": False, "tier": "Strategic / Tourism"},
            {"iata": "IXC", "city": "Chandigarh", "state": "Punjab & Haryana", "name": "Shaheed Bhagat Singh International Airport", "lat": 30.6735, "lon": 76.7885, "is_hub": False, "tier": "Northern Trunk"},
            {"iata": "ATQ", "city": "Amritsar", "state": "Punjab", "name": "Sri Guru Ram Dass Jee International Airport", "lat": 31.7096, "lon": 74.7973, "is_hub": False, "tier": "International Gateway"},
            {"iata": "IDR", "city": "Indore", "state": "Madhya Pradesh", "name": "Devi Ahilya Bai Holkar Airport", "lat": 22.7217, "lon": 75.8011, "is_hub": False, "tier": "Commercial Center"},
            {"iata": "VTZ", "city": "Visakhapatnam (Vizag)", "state": "Andhra Pradesh", "name": "Visakhapatnam International Airport", "lat": 17.7215, "lon": 83.2245, "is_hub": False, "tier": "Coastal Trunk"},
            {"iata": "IXR", "city": "Ranchi", "state": "Jharkhand", "name": "Birsa Munda Airport", "lat": 23.3143, "lon": 85.3217, "is_hub": False, "tier": "Regional Capital"},
            {"iata": "RPR", "city": "Raipur", "state": "Chhattisgarh", "name": "Swami Vivekananda Airport", "lat": 21.1804, "lon": 81.7388, "is_hub": False, "tier": "Regional Capital"},
            {"iata": "DED", "city": "Dehradun", "state": "Uttarakhand", "name": "Jolly Grant Airport", "lat": 30.1897, "lon": 78.1803, "is_hub": False, "tier": "Himalayan Trunk"},
            {"iata": "VNS", "city": "Varanasi (Kashi)", "state": "Uttar Pradesh", "name": "Lal Bahadur Shastri International Airport", "lat": 25.4524, "lon": 82.8593, "is_hub": False, "tier": "Spiritual / Tourism"},
            {"iata": "TRV", "city": "Thiruvananthapuram (Trivandrum)", "state": "Kerala", "name": "Thiruvananthapuram International Airport", "lat": 8.4821, "lon": 76.9200, "is_hub": False, "tier": "Southern Gateway"},
            {"iata": "IXB", "city": "Bagdogra (Siliguri)", "state": "West Bengal", "name": "Bagdogra International Airport", "lat": 26.6812, "lon": 88.3286, "is_hub": False, "tier": "Eastern Gateway"},
            {"iata": "IXZ", "city": "Port Blair", "state": "Andaman and Nicobar Islands", "name": "Veer Savarkar International Airport", "lat": 11.6410, "lon": 92.7297, "is_hub": False, "tier": "Island Territory"},
            {"iata": "UDR", "city": "Udaipur", "state": "Rajasthan", "name": "Maharana Pratap Airport", "lat": 24.6177, "lon": 73.8961, "is_hub": False, "tier": "Tourism Trunk"},
            {"iata": "NAG", "city": "Nagpur", "state": "Maharashtra", "name": "Dr. Babasaheb Ambedkar International Airport", "lat": 21.0922, "lon": 79.0472, "is_hub": False, "tier": "Central Hub"}
        ]
        for a in self.airports_list:
            self.airports_dict[a['iata']] = a

    def refresh(self):
        self._enriched_df = None
        self._load_master_data()

    def get_airports(self) -> List[Dict[str, Any]]:
        return self.airports_list

    def get_master_df(self) -> pd.DataFrame:
        if self.master_df is None or len(self.master_df) == 0:
            self._load_master_data()
        return self.master_df.copy()

    def get_enriched_master_df(self) -> pd.DataFrame:
        if getattr(self, '_enriched_df', None) is not None:
            return self._enriched_df.copy()
        df = self.get_master_df()
        if len(df) == 0:
            return df
        enriched = df.copy()

        # Clean departure time: normalize non-breaking spaces
        dep_clean = (
            enriched['departure_time']
            .fillna('')
            .astype(str)
            .str.replace('\u202f', ' ', regex=False)
            .str.strip()
        )

        # Normalize flight number: fallback to airline name if missing or short
        airline = (
            enriched['airline_standardized']
            .fillna(enriched['airline_raw'])
            .fillna('Carrier')
            .astype(str)
            .str.strip()
        )
        flight_no = enriched['flight_number'].fillna('').astype(str).str.strip()
        flight_clean = flight_no.where(flight_no.str.len() > 1, airline)

        route = enriched['route'].fillna('').astype(str).str.upper().str.strip()
        travel_dt = enriched['travel_date'].fillna('').astype(str).str.strip()

        enriched['flight_group_key'] = route + '::' + travel_dt + '::' + flight_clean + '::' + dep_clean

        # Group stats
        grp = enriched.groupby('flight_group_key')['total_fare_inr'].agg(
            min_flight_fare='min',
            max_flight_fare='max',
            flight_quotes_count='count'
        ).reset_index()

        # Identify lowest platform per flight group
        sorted_df = enriched.sort_values(by=['flight_group_key', 'total_fare_inr'], ascending=[True, True])
        lowest_recs = sorted_df.drop_duplicates(subset=['flight_group_key'], keep='first')[['flight_group_key', 'source_platform']].rename(
            columns={'source_platform': 'lowest_platform'}
        )

        enriched = enriched.merge(grp, on='flight_group_key', how='left')
        enriched = enriched.merge(lowest_recs, on='flight_group_key', how='left')
        enriched['is_lowest_quote'] = enriched['total_fare_inr'] <= (enriched['min_flight_fare'] + 0.5)
        enriched['fare_start_label'] = 'Starting from ₹' + enriched['min_flight_fare'].astype(int).astype(str)

        self._enriched_df = enriched
        return self._enriched_df.copy()

db = DataRepository()
