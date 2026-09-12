"""
SIH26056: Real-Time Airfare Price Index for India
Core Index Calculation Engine (APIx)

Computes:
1. Daily & Monthly National Airfare Price Index (Jevons Elementary + Laspeyres Route Weighted).
2. Advance Booking Lead-Time Curve Index (T+1, T+7, T+15, T+30, T+45).
3. Route-Specific Corridor Sub-Indices (DEL-BOM, BOM-BLR, etc.).
4. Airline-Specific Sub-Indices (IndiGo, Air India, Akasa Air, SpiceJet).
5. Price Volatility & Market Pulse Classification.
6. MoSPI CPI Augmentation Benchmark (Base 2024 = 100).
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Tuple

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

try:
    from scripts.index_engine.formulas import (
        geometric_mean,
        jevons_index,
        dutot_index,
        laspeyres_weighted_index,
        calculate_volatility_metrics,
        classify_market_pulse
    )
    from scripts.index_engine.weights import (
        DGCA_ROUTE_WEIGHTS,
        DGCA_AIRLINE_WEIGHTS,
        MOSPI_CPI_AIRFARE_METADATA
    )
except ImportError:
    from formulas import (
        geometric_mean,
        jevons_index,
        dutot_index,
        laspeyres_weighted_index,
        calculate_volatility_metrics,
        classify_market_pulse
    )
    from weights import (
        DGCA_ROUTE_WEIGHTS,
        DGCA_AIRLINE_WEIGHTS,
        MOSPI_CPI_AIRFARE_METADATA
    )

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CLEANED_DIR = os.path.join(DATA_DIR, 'cleaned')
RESULTS_DIR = os.path.join(DATA_DIR, 'index_results')
REPORTS_DIR = os.path.join(DATA_DIR, 'reports')

AIRPORT_COORDINATES = {
    'DEL': {'lat': 28.5562, 'lon': 77.1000, 'city': 'New Delhi', 'name': 'Indira Gandhi Int Airport'},
    'BOM': {'lat': 19.0896, 'lon': 72.8656, 'city': 'Mumbai', 'name': 'Chhatrapati Shivaji Maharaj Int Airport'},
    'BLR': {'lat': 13.1986, 'lon': 77.7066, 'city': 'Bengaluru', 'name': 'Kempegowda Int Airport'},
    'HYD': {'lat': 17.2403, 'lon': 78.4294, 'city': 'Hyderabad', 'name': 'Rajiv Gandhi Int Airport'},
    'CCU': {'lat': 22.6547, 'lon': 88.4467, 'city': 'Kolkata', 'name': 'Netaji Subhash Chandra Bose Int Airport'},
    'MAA': {'lat': 12.9941, 'lon': 80.1709, 'city': 'Chennai', 'name': 'Chennai Int Airport'},
    'COK': {'lat': 10.1520, 'lon': 76.4019, 'city': 'Kochi', 'name': 'Cochin Int Airport'},
    'GOI': {'lat': 15.3808, 'lon': 73.8314, 'city': 'Goa (Dabolim)', 'name': 'Dabolim Airport'},
    'GOX': {'lat': 15.7725, 'lon': 73.8686, 'city': 'Goa (Mopa)', 'name': 'Manohar Int Airport'},
    'AMD': {'lat': 23.0772, 'lon': 72.6347, 'city': 'Ahmedabad', 'name': 'Sardar Vallabhbhai Patel Int Airport'},
    'PNQ': {'lat': 18.5822, 'lon': 73.9197, 'city': 'Pune', 'name': 'Pune Airport'},
    'JAI': {'lat': 26.8242, 'lon': 75.8122, 'city': 'Jaipur', 'name': 'Jaipur Int Airport'},
    'LKO': {'lat': 26.7606, 'lon': 80.8893, 'city': 'Lucknow', 'name': 'Chaudhary Charan Singh Int Airport'},
    'GAU': {'lat': 26.1061, 'lon': 91.5859, 'city': 'Guwahati', 'name': 'Lokpriya Gopinath Bordoloi Int Airport'},
    'PAT': {'lat': 25.5913, 'lon': 85.0880, 'city': 'Patna', 'name': 'Jay Prakash Narayan Airport'},
    'SXR': {'lat': 33.9871, 'lon': 74.7741, 'city': 'Srinagar', 'name': 'Sheikh ul-Alam Int Airport'},
    'BBI': {'lat': 20.2444, 'lon': 85.8178, 'city': 'Bhubaneswar', 'name': 'Biju Patnaik Int Airport'},
    'VNS': {'lat': 25.4524, 'lon': 82.8587, 'city': 'Varanasi', 'name': 'Lal Bahadur Shastri Airport'},
    'ATQ': {'lat': 31.7096, 'lon': 74.7973, 'city': 'Amritsar', 'name': 'Sri Guru Ram Dass Jee Int Airport'},
    'IDR': {'lat': 22.7217, 'lon': 75.8011, 'city': 'Indore', 'name': 'Devi Ahilya Bai Holkar Airport'},
    'TRV': {'lat': 8.4821, 'lon': 76.9200, 'city': 'Thiruvananthapuram', 'name': 'Trivandrum Int Airport'},
    'IXB': {'lat': 26.6812, 'lon': 88.3286, 'city': 'Bagdogra', 'name': 'Bagdogra Int Airport'},
    'IXC': {'lat': 30.6735, 'lon': 76.7885, 'city': 'Chandigarh', 'name': 'Shaheed Bhagat Singh Int Airport'},
    'IXE': {'lat': 12.9613, 'lon': 74.8900, 'city': 'Mangaluru', 'name': 'Mangalore Int Airport'},
    'CJB': {'lat': 11.0299, 'lon': 77.0434, 'city': 'Coimbatore', 'name': 'Coimbatore Int Airport'},
    'NAG': {'lat': 21.0922, 'lon': 79.0472, 'city': 'Nagpur', 'name': 'Dr. Babasaheb Ambedkar Int Airport'},
    'VTZ': {'lat': 17.7212, 'lon': 83.2245, 'city': 'Visakhapatnam', 'name': 'Visakhapatnam Int Airport'},
    'IXR': {'lat': 23.3143, 'lon': 85.3217, 'city': 'Ranchi', 'name': 'Birsa Munda Airport'},
    'RPR': {'lat': 21.1804, 'lon': 81.7389, 'city': 'Raipur', 'name': 'Swami Vivekananda Airport'},
    'BDQ': {'lat': 22.3362, 'lon': 73.2263, 'city': 'Vadodara', 'name': 'Vadodara Airport'},
    'IXA': {'lat': 23.8870, 'lon': 91.2405, 'city': 'Agartala', 'name': 'Maharaja Bir Bikram Airport'},
    'IXZ': {'lat': 11.6410, 'lon': 92.7297, 'city': 'Port Blair', 'name': 'Veer Savarkar Int Airport'},
    'DED': {'lat': 30.1897, 'lon': 78.1803, 'city': 'Dehradun', 'name': 'Jolly Grant Airport'},
    'IXJ': {'lat': 32.6891, 'lon': 74.8374, 'city': 'Jammu', 'name': 'Jammu Airport'},
    'UDR': {'lat': 24.6177, 'lon': 73.8961, 'city': 'Udaipur', 'name': 'Maharana Pratap Airport'},
    'IXM': {'lat': 9.8345, 'lon': 78.0934, 'city': 'Madurai', 'name': 'Madurai Airport'},
    'TIR': {'lat': 13.6325, 'lon': 79.5434, 'city': 'Tirupati', 'name': 'Tirupati Airport'},
    'CCJ': {'lat': 11.1368, 'lon': 75.9553, 'city': 'Kozhikode', 'name': 'Calicut Int Airport'},
    'VGA': {'lat': 16.5304, 'lon': 80.7968, 'city': 'Vijayawada', 'name': 'Vijayawada Airport'},
    'IXU': {'lat': 19.8631, 'lon': 75.3981, 'city': 'Aurangabad', 'name': 'Aurangabad Airport'}
}

class AirfareIndexEngine:
    def __init__(self):
        self.master_df = None
        self.cpi_df = None
        self.base_prices_by_route = {}
        self.base_prices_by_airline = {}
        self.overall_base_price = 1.0

    def load_data(self):
        master_path = os.path.join(CLEANED_DIR, 'sih_master_airfare_observations_v2.csv')
        cpi_path = os.path.join(CLEANED_DIR, 'cleaned_cpi_mospi_2024.csv')
        
        if not os.path.exists(master_path):
            raise FileNotFoundError(f"Master dataset not found at {master_path}")
        
        self.master_df = pd.read_csv(master_path, low_memory=False)
        
        if os.path.exists(cpi_path):
            self.cpi_df = pd.read_csv(cpi_path)
            
        print(f"[✓] Data loaded successfully: {len(self.master_df):,} master observations.")

    def establish_baselines(self, baseline_tier: str = '2022_real_observations'):
        """
        Establishes base reference geometric mean prices (P_0) by route and airline.
        Uses the clean 2022 post-COVID active fleet observations as the primary modern base.
        """
        base_slice = self.master_df[
            (self.master_df['dataset_tier'] == baseline_tier) & 
            (~self.master_df['is_defunct_carrier']) &
            (self.master_df['cabin_class'] == 'Economy')
        ]
        
        # Fallback if baseline tier slice is small
        if len(base_slice) < 50:
            base_slice = self.master_df[
                (~self.master_df['is_defunct_carrier']) &
                (self.master_df['cabin_class'] == 'Economy')
            ]

        # 1. Base price per route
        for route, group in base_slice.groupby('route'):
            gm = geometric_mean(group['total_fare_inr'])
            if pd.notna(gm) and gm > 0:
                self.base_prices_by_route[route] = gm

        # 2. Base price per airline
        for airline, group in base_slice.groupby('airline_standardized'):
            gm = geometric_mean(group['total_fare_inr'])
            if pd.notna(gm) and gm > 0:
                self.base_prices_by_airline[airline] = gm

        # 3. Overall national base price
        self.overall_base_price = geometric_mean(base_slice['total_fare_inr'])
        print(f"[✓] Baselines established across {len(self.base_prices_by_route)} routes (Overall Base: ₹{self.overall_base_price:,.2f})")

    def compute_daily_index_series(self) -> pd.DataFrame:
        """
        Computes Daily National Airfare Price Index (APIx) using Jevons + Laspeyres formulas.
        """
        df_active = self.master_df[
            (~self.master_df['is_defunct_carrier']) & 
            (self.master_df['travel_date'].notna()) &
            (self.master_df['cabin_class'] == 'Economy')
        ].copy()

        daily_results = []
        for travel_date, day_group in df_active.groupby('travel_date'):
            route_indices = {}
            route_fares = {}
            
            # Compute route-level Jevons elementary index
            for route, r_group in day_group.groupby('route'):
                curr_fares = r_group['total_fare_inr'].dropna().tolist()
                base_fare = self.base_prices_by_route.get(route, self.overall_base_price)
                if curr_fares and base_fare > 0:
                    curr_gm = geometric_mean(curr_fares)
                    j_idx = (curr_gm / base_fare) * 100.0
                    route_indices[route] = j_idx
                    route_fares[route] = curr_gm

            # Aggregate to National Index via Laspeyres Route Weights
            apix_national_laspeyres = laspeyres_weighted_index(route_indices, DGCA_ROUTE_WEIGHTS)
            
            # Dutot unweighted benchmark
            day_fares = day_group['total_fare_inr'].dropna()
            apix_dutot = (np.mean(day_fares) / self.overall_base_price) * 100.0 if len(day_fares) > 0 else np.nan
            
            # Volatility & CV
            vol = calculate_volatility_metrics(day_fares)
            pulse = classify_market_pulse(apix_national_laspeyres - 100.0, vol['cv'])

            daily_results.append({
                'travel_date': travel_date,
                'observations_count': len(day_group),
                'active_routes_count': len(route_indices),
                'apix_jevons_laspeyres': round(apix_national_laspeyres, 2),
                'apix_dutot_benchmark': round(apix_dutot, 2),
                'mean_fare_inr': vol['mean'],
                'median_fare_inr': float(np.median(day_fares)) if len(day_fares) > 0 else np.nan,
                'fare_std_inr': vol['std'],
                'coefficient_of_variation_pct': vol['cv'],
                'market_pulse': pulse
            })

        df_daily = pd.DataFrame(daily_results).sort_values('travel_date').reset_index(drop=True)
        # Compute 7-day Moving Average of APIx
        df_daily['apix_7d_moving_avg'] = df_daily['apix_jevons_laspeyres'].rolling(window=7, min_periods=1).mean().round(2)
        # Compute Day-on-Day % Change
        df_daily['apix_dod_change_pct'] = df_daily['apix_jevons_laspeyres'].pct_change().fillna(0).map(lambda x: round(x * 100, 2))
        
        return df_daily

    def compute_lead_time_index_curve(self) -> pd.DataFrame:
        """
        Computes Advance Booking Lead-Time Curve Index (T+1, T+7, T+15, T+30, T+45).
        """
        df_lead = self.master_df[
            (self.master_df['lead_time_days'].notna()) &
            (~self.master_df['is_defunct_carrier']) &
            (self.master_df['cabin_class'] == 'Economy')
        ].copy()

        if len(df_lead) == 0:
            return pd.DataFrame()

        lead_results = []
        for lt, lt_group in df_lead.groupby('lead_time_days'):
            fares = lt_group['total_fare_inr'].dropna()
            gm = geometric_mean(fares)
            j_idx = (gm / self.overall_base_price) * 100.0 if self.overall_base_price > 0 else np.nan
            vol = calculate_volatility_metrics(fares)
            
            lead_results.append({
                'lead_time_tag': f"T+{int(lt)}",
                'lead_time_days': int(lt),
                'observations_count': len(lt_group),
                'apix_lead_time_index': round(j_idx, 2),
                'mean_fare_inr': vol['mean'],
                'median_fare_inr': float(np.median(fares)),
                'min_fare_inr': vol['min'],
                'max_fare_inr': vol['max'],
                'price_spread_inr': round(vol['max'] - vol['min'], 2),
                'coefficient_of_variation_pct': vol['cv']
            })

        df_lt = pd.DataFrame(lead_results).sort_values('lead_time_days').reset_index(drop=True)
        return df_lt

    def compute_route_sub_indices(self) -> pd.DataFrame:
        """
        Computes Corridor-specific Route Airfare Indices with geographic coordinates & stress heatmap scores.
        """
        df_active = self.master_df[
            (~self.master_df['is_defunct_carrier']) &
            (self.master_df['cabin_class'] == 'Economy')
        ].copy()

        route_results = []
        for route, r_group in df_active.groupby('route'):
            fares = r_group['total_fare_inr'].dropna()
            gm = geometric_mean(fares)
            base_p = self.base_prices_by_route.get(route, self.overall_base_price)
            j_idx = (gm / base_p) * 100.0 if base_p > 0 else np.nan
            vol = calculate_volatility_metrics(fares)
            
            parts = route.split('-')
            orig = parts[0] if len(parts) > 0 else 'DEL'
            dest = parts[1] if len(parts) > 1 else 'BOM'
            route_weight = DGCA_ROUTE_WEIGHTS.get(route, 0.01)

            orig_geo = AIRPORT_COORDINATES.get(orig, {'lat': 28.5562, 'lon': 77.1000, 'city': orig, 'name': f'{orig} Airport'})
            dest_geo = AIRPORT_COORDINATES.get(dest, {'lat': 19.0896, 'lon': 72.8656, 'city': dest, 'name': f'{dest} Airport'})

            # Compute real stress score & status
            mean_f = vol['mean']
            cv_val = vol['cv']
            stress_score = min(100, max(20, int((j_idx / 2.0) + (cv_val * 1.5))))
            if stress_score >= 80:
                stress_status = 'High Pressure'
            elif stress_score >= 65:
                stress_status = 'Elevated'
            elif stress_score >= 45:
                stress_status = 'Normal'
            else:
                stress_status = 'Stable'

            route_results.append({
                'route': route,
                'origin_iata': orig,
                'dest_iata': dest,
                'origin_city': orig_geo['city'],
                'dest_city': dest_geo['city'],
                'origin_lat': orig_geo['lat'],
                'origin_lon': orig_geo['lon'],
                'dest_lat': dest_geo['lat'],
                'dest_lon': dest_geo['lon'],
                'dgca_traffic_weight_pct': round(route_weight * 100, 2),
                'observations_count': len(r_group),
                'route_apix_index': round(j_idx, 2),
                'mean_fare_inr': vol['mean'],
                'median_fare_inr': float(np.median(fares)),
                'std_dev_inr': vol['std'],
                'coefficient_of_variation_pct': vol['cv'],
                'stress_score': stress_score,
                'stress_status': stress_status,
                'heatmap_intensity': round(min(1.0, mean_f / 10000.0), 3)
            })

        df_routes = pd.DataFrame(route_results).sort_values('observations_count', ascending=False).reset_index(drop=True)
        return df_routes

    def compute_airline_sub_indices(self) -> pd.DataFrame:
        """
        Computes Airline-specific Carrier Airfare Price Indices.
        """
        df_active = self.master_df[
            (~self.master_df['is_defunct_carrier']) &
            (self.master_df['cabin_class'] == 'Economy')
        ].copy()

        airline_results = []
        for airline, a_group in df_active.groupby('airline_standardized'):
            fares = a_group['total_fare_inr'].dropna()
            gm = geometric_mean(fares)
            base_p = self.base_prices_by_airline.get(airline, self.overall_base_price)
            j_idx = (gm / base_p) * 100.0 if base_p > 0 else np.nan
            vol = calculate_volatility_metrics(fares)
            
            market_share = DGCA_AIRLINE_WEIGHTS.get(airline, 0.02)

            airline_results.append({
                'airline': airline,
                'dgca_market_share_pct': round(market_share * 100, 2),
                'observations_count': len(a_group),
                'airline_apix_index': round(j_idx, 2),
                'mean_fare_inr': vol['mean'],
                'median_fare_inr': float(np.median(fares)),
                'min_fare_inr': vol['min'],
                'max_fare_inr': vol['max'],
                'coefficient_of_variation_pct': vol['cv']
            })

        df_airlines = pd.DataFrame(airline_results).sort_values('observations_count', ascending=False).reset_index(drop=True)
        return df_airlines

    def run_full_pipeline(self):
        self.load_data()
        self.establish_baselines()

        print("\n⚙️ Computing Daily National Airfare Price Index (APIx)...")
        df_daily = self.compute_daily_index_series()
        daily_path = os.path.join(RESULTS_DIR, 'daily_airfare_index.csv')
        df_daily.to_csv(daily_path, index=False)
        print(f"[✓] Daily Index saved: {daily_path} ({len(df_daily)} daily series points)")

        print("⚙️ Computing Lead-Time Advance Curve Index (T+1 to T+45)...")
        df_lead = self.compute_lead_time_index_curve()
        lead_path = os.path.join(RESULTS_DIR, 'lead_time_index_curve.csv')
        df_lead.to_csv(lead_path, index=False)
        print(f"[✓] Lead-Time Index Curve saved: {lead_path}")

        print("⚙️ Computing Route-Specific Sub-Indices...")
        df_routes = self.compute_route_sub_indices()
        routes_path = os.path.join(RESULTS_DIR, 'route_airfare_indices.csv')
        df_routes.to_csv(routes_path, index=False)
        print(f"[✓] Route Sub-Indices saved: {routes_path}")

        print("⚙️ Computing Airline-Specific Sub-Indices...")
        df_airlines = self.compute_airline_sub_indices()
        airlines_path = os.path.join(RESULTS_DIR, 'airline_airfare_indices.csv')
        df_airlines.to_csv(airlines_path, index=False)
        print(f"[✓] Airline Sub-Indices saved: {airlines_path}")

        print("⚙️ Generating MoSPI CPI Comparison & Explainability Report...")
        self.generate_explainability_report(df_daily, df_lead, df_routes, df_airlines)

    def generate_explainability_report(
        self,
        df_daily: pd.DataFrame,
        df_lead: pd.DataFrame,
        df_routes: pd.DataFrame,
        df_airlines: pd.DataFrame
    ):
        report_path = os.path.join(REPORTS_DIR, 'AIRFARE_INDEX_EXPLAINABILITY_REPORT.md')
        
        md = []
        md.append("# SIH26056: Real-Time Airfare Price Index (APIx) — Mathematical Engine & Explainability Report\n")
        md.append("> **Statistical Framework:** Compliant with MoSPI Consumer Price Index (CPI) Guidelines & UN/ILO CPI Manual.\n")
        
        # 1. Executive Summary
        latest_daily = df_daily.iloc[-1] if len(df_daily) > 0 else None
        md.append("## 1. Executive Index Summary\n")
        if latest_daily is not None:
            md.append(f"- **Latest National Airfare Price Index (APIx):** **{latest_daily['apix_jevons_laspeyres']:.2f}** (Base = 100.00)")
            md.append(f"- **7-Day Moving Average Index:** **{latest_daily['apix_7d_moving_avg']:.2f}**")
            md.append(f"- **Current Market Pulse:** **{latest_daily['market_pulse']}**")
            md.append(f"- **Price Volatility (CV):** **{latest_daily['coefficient_of_variation_pct']:.2f}%**")
            md.append(f"- **Total Audited Master Observations:** **{len(self.master_df):,} records**\n")

        # 2. Formula Explainability
        md.append("## 2. Mathematical Methodology & Formulas\n")
        md.append("### A. Elementary Route-Carrier Level: Jevons Geometric Mean Formula")
        md.append("$$\\text{APIx}_{r, t} = \\frac{\\left(\\prod_{i=1}^{n_r} p_{i, t}\\right)^{1/n_r}}{\\bar{P}_{r, 0}} \\times 100$$")
        md.append("* **Why Jevons:** Unlike simple arithmetic averages (Carli/Dutot), Jevons satisfies the **Axiomatic Time-Reversal Test** and is unaffected by price dispersion swings common in dynamic airline pricing.\n")
        
        md.append("### B. Higher-Level National Aggregation: Laspeyres Route-Weighted Index")
        md.append("$$\\text{APIx}_{\\text{National}, t} = \\sum_{r=1}^{R} w_r \\times \\text{APIx}_{r, t}$$")
        md.append("* Where $w_r$ is the official **DGCA Passenger Traffic Volume Share** for each city-pair corridor.\n")

        # 3. Lead Time Sensitivity
        md.append("## 3. Dynamic Pricing Lead-Time Index Curve ($T+1$ to $T+45$)\n")
        md.append("| Lead Time | Days in Advance | APIx Index | Mean Fare (₹) | Median Fare (₹) | Volatility (CV %) | Market State |")
        md.append("| :---: | :---: | :---: | :---: | :---: | :---: | :--- |")
        for _, row in df_lead.iterrows():
            pulse = "Last-Minute Surge" if row['lead_time_days'] <= 3 else ("Normal Dynamic Curve" if row['lead_time_days'] <= 15 else "Stable Advance Baseline")
            md.append(f"| **{row['lead_time_tag']}** | {row['lead_time_days']} days | **{row['apix_lead_time_index']:.2f}** | ₹{row['mean_fare_inr']:,.2f} | ₹{row['median_fare_inr']:,.2f} | {row['coefficient_of_variation_pct']:.2f}% | {pulse} |")
        md.append("\n")

        # 4. Route Sub-Indices
        md.append("## 4. Corridor Route Sub-Indices (Top Corridors)\n")
        md.append("| Route | DGCA Traffic Weight | Observations | Route APIx Index | Mean Fare (₹) | Price Spread (₹) | Volatility (CV) |")
        md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
        for _, row in df_routes.head(10).iterrows():
            md.append(f"| **`{row['route']}`** | {row['dgca_traffic_weight_pct']:.2f}% | {row['observations_count']:,} | **{row['route_apix_index']:.2f}** | ₹{row['mean_fare_inr']:,.2f} | ₹{row['std_dev_inr']:,.2f} | {row['coefficient_of_variation_pct']:.2f}% |")
        md.append("\n")

        # 5. Airline Sub-Indices
        md.append("## 5. Carrier Sub-Indices & Market Share\n")
        md.append("| Airline Carrier | DGCA Market Share | Observations | Carrier APIx Index | Mean Fare (₹) | Volatility (CV) |")
        md.append("| :--- | :---: | :---: | :---: | :---: | :---: |")
        for _, row in df_airlines.iterrows():
            md.append(f"| **{row['airline']}** | {row['dgca_market_share_pct']:.2f}% | {row['observations_count']:,} | **{row['airline_apix_index']:.2f}** | ₹{row['mean_fare_inr']:,.2f} | {row['coefficient_of_variation_pct']:.2f}% |")
        md.append("\n")

        # 6. MoSPI CPI Comparison
        if self.cpi_df is not None:
            md.append("## 6. MoSPI Official CPI Series Comparison (2024 Base Year)\n")
            md.append("Official government CPI series for Item `07.3.3.1.2.01` (Passenger Transport by Air, Domestic):\n")
            md.append("| Year | Month | MoSPI CPI Airfare Index | MoM Inflation (%) | Augmentation Status |")
            md.append("| :---: | :---: | :---: | :---: | :--- |")
            for _, row in self.cpi_df.head(12).iterrows():
                infl = f"{row['inflation']:.2f}%" if pd.notna(row['inflation']) else "N/A"
                md.append(f"| {row['year']} | {row['month']} | **{row['index']:.2f}** | {infl} | Verified MoSPI Benchmark |")
            md.append("\n")

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md))
        print(f"[✓] Explainability Report generated: {report_path}")

def main():
    engine = AirfareIndexEngine()
    engine.run_full_pipeline()

if __name__ == "__main__":
    main()
