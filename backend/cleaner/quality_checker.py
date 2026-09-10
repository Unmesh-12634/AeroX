"""
SIH26056: Real-Time Airfare Price Index for India
Data Quality Assurance & Statistical Outlier Engine
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

def detect_fare_outliers_iqr(df: pd.DataFrame, fare_col: str = "total_fare_inr", group_col: str = "route") -> pd.DataFrame:
    df = df.copy()
    df['is_fare_mild_outlier'] = False
    df['is_fare_extreme_outlier'] = False

    for route, grp in df.groupby(group_col):
        fares = grp[fare_col].dropna()
        if len(fares) < 4:
            continue
        
        q25 = np.percentile(fares, 25)
        q75 = np.percentile(fares, 75)
        iqr = q75 - q25
        
        # 1.5x IQR (Mild Outlier / Surge)
        lower_mild = max(1000.0, q25 - 1.5 * iqr)
        upper_mild = q75 + 1.5 * iqr
        
        # 3.0x IQR (Extreme Outlier / Error)
        lower_extreme = max(500.0, q25 - 3.0 * iqr)
        upper_extreme = q75 + 3.0 * iqr
        
        mild_mask = (df[group_col] == route) & ((df[fare_col] < lower_mild) | (df[fare_col] > upper_mild))
        extreme_mask = (df[group_col] == route) & ((df[fare_col] < lower_extreme) | (df[fare_col] > upper_extreme))
        
        df.loc[mild_mask, 'is_fare_mild_outlier'] = True
        df.loc[extreme_mask, 'is_fare_extreme_outlier'] = True

    df['is_outlier'] = df['is_fare_mild_outlier'] | df['is_fare_extreme_outlier']
    return df


def deduplicate_quotes(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    initial_count = len(df)
    subset_keys = ['route', 'travel_date', 'airline_standardized', 'flight_number', 'departure_time', 'cabin_class', 'source_file']
    valid_keys = [k for k in subset_keys if k in df.columns]
    
    if len(valid_keys) >= 4:
        df_clean = df.drop_duplicates(subset=valid_keys, keep='last').copy()
    else:
        df_clean = df.drop_duplicates().copy()
        
    dropped_count = initial_count - len(df_clean)
    return df_clean, dropped_count

def audit_data_quality_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    total_records = len(df)
    if total_records == 0:
        return {"total_records": 0, "quality_score": 100.0}

    valid_routes = df['route'].dropna().count()
    valid_fares = df['total_fare_inr'].dropna().count()
    outlier_count = df['is_fare_extreme_outlier'].sum() if 'is_fare_extreme_outlier' in df.columns else 0
    defunct_count = df['is_defunct_carrier'].sum() if 'is_defunct_carrier' in df.columns else 0
    
    route_completeness = (valid_routes / total_records) * 100
    fare_validity = (valid_fares / total_records) * 100
    clean_usable_pct = ((total_records - outlier_count - defunct_count) / total_records) * 100

    return {
        "total_records": total_records,
        "valid_routes_pct": round(route_completeness, 2),
        "valid_fares_pct": round(fare_validity, 2),
        "outliers_detected": int(outlier_count),
        "defunct_quarantined": int(defunct_count),
        "clean_usable_pct": round(clean_usable_pct, 2),
        "overall_quality_score": round((route_completeness * 0.4 + fare_validity * 0.4 + clean_usable_pct * 0.2), 1)
    }

class QualityChecker:
    """Class wrapper for quality assurance operations."""

    @staticmethod
    def detect_outliers_iqr(df: pd.DataFrame, group_cols: list = None) -> pd.DataFrame:
        if group_cols and len(group_cols) > 0:
            return detect_fare_outliers_iqr(df, group_col=group_cols[0])
        return detect_fare_outliers_iqr(df)

    @staticmethod
    def deduplicate_observations(df: pd.DataFrame) -> pd.DataFrame:
        clean_df, _ = deduplicate_quotes(df)
        return clean_df

    @staticmethod
    def calculate_quality_score(df: pd.DataFrame) -> Dict[str, Any]:
        metrics = audit_data_quality_metrics(df)
        return {
            "total_records": metrics["total_records"],
            "valid_records": metrics["total_records"] - metrics.get("defunct_quarantined", 0) - metrics.get("outliers_detected", 0),
            "quality_score_pct": metrics.get("overall_quality_score", 98.5)
        }

