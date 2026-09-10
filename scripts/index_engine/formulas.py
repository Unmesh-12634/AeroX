"""
SIH26056: Real-Time Airfare Price Index for India
Statistical Price Index Mathematical Formulas (MoSPI / IMF / ILO Standards)
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Union

def geometric_mean(arr: Union[List[float], np.ndarray, pd.Series]) -> float:
    """Computes geometric mean handling positive values."""
    clean = np.array([x for x in arr if pd.notna(x) and x > 0], dtype=float)
    if len(clean) == 0:
        return np.nan
    return float(np.exp(np.mean(np.log(clean))))

def jevons_index(current_prices: Union[List[float], pd.Series], base_prices: Union[List[float], pd.Series]) -> float:
    """
    Jevons Elementary Price Index Formula:
    I_Jevons = GeometricMean(current_prices) / GeometricMean(base_prices) * 100
    Satisfies Axiomatic tests, Time Reversal, and Circularity.
    """
    gm_curr = geometric_mean(current_prices)
    gm_base = geometric_mean(base_prices)
    if np.isnan(gm_curr) or np.isnan(gm_base) or gm_base == 0:
        return np.nan
    return float((gm_curr / gm_base) * 100.0)

def dutot_index(current_prices: Union[List[float], pd.Series], base_prices: Union[List[float], pd.Series]) -> float:
    """
    Dutot Price Index Formula:
    I_Dutot = Mean(current_prices) / Mean(base_prices) * 100
    """
    curr_clean = [x for x in current_prices if pd.notna(x) and x > 0]
    base_clean = [x for x in base_prices if pd.notna(x) and x > 0]
    if len(curr_clean) == 0 or len(base_clean) == 0:
        return np.nan
    mean_curr = np.mean(curr_clean)
    mean_base = np.mean(base_clean)
    if mean_base == 0:
        return np.nan
    return float((mean_curr / mean_base) * 100.0)

def carli_index(current_prices: Union[List[float], pd.Series], base_prices: Union[List[float], pd.Series]) -> float:
    """
    Carli Price Index Formula:
    I_Carli = Mean(current_price_i / base_price_i) * 100 (for matched pairs)
    """
    relatives = []
    for c, b in zip(current_prices, base_prices):
        if pd.notna(c) and pd.notna(b) and b > 0 and c > 0:
            relatives.append(c / b)
    if len(relatives) == 0:
        return np.nan
    return float(np.mean(relatives) * 100.0)

def laspeyres_weighted_index(route_indices: Dict[str, float], route_weights: Dict[str, float]) -> float:
    """
    Laspeyres Higher-Level Index Aggregation:
    APIx = Sum(w_r * I_r) / Sum(w_r for available routes)
    """
    weighted_sum = 0.0
    total_weight = 0.0
    for route, index_val in route_indices.items():
        if pd.notna(index_val) and route in route_weights:
            w = route_weights[route]
            weighted_sum += w * index_val
            total_weight += w
    if total_weight == 0:
        return np.nan
    return float(weighted_sum / total_weight)

def calculate_volatility_metrics(prices: Union[List[float], pd.Series]) -> Dict[str, float]:
    """Calculates price dispersion, standard deviation, IQR, and Coefficient of Variation (CV)."""
    clean = np.array([x for x in prices if pd.notna(x) and x > 0], dtype=float)
    if len(clean) < 2:
        return {"mean": np.nan, "std": np.nan, "cv": np.nan, "iqr": np.nan, "min": np.nan, "max": np.nan}
    
    mean_p = float(np.mean(clean))
    std_p = float(np.std(clean, ddof=1))
    cv_p = float((std_p / mean_p) * 100.0) if mean_p > 0 else 0.0
    q75, q25 = np.percentile(clean, [75, 25])
    iqr_p = float(q75 - q25)
    
    return {
        "mean": round(mean_p, 2),
        "std": round(std_p, 2),
        "cv": round(cv_p, 2),
        "iqr": round(iqr_p, 2),
        "min": round(float(np.min(clean)), 2),
        "max": round(float(np.max(clean)), 2)
    }

def classify_market_pulse(index_change_pct: float, cv: float) -> str:
    """Classifies airfare market state into standardized pulses."""
    if pd.isna(index_change_pct) or pd.isna(cv):
        return "Unknown"
    if cv > 35.0:
        return "Highly Volatile"
    elif index_change_pct > 10.0:
        return "Surging / Under Pressure"
    elif index_change_pct < -10.0:
        return "Sharp Decline / Discounting"
    elif abs(index_change_pct) <= 3.0:
        return "Stable"
    elif index_change_pct > 0:
        return "Moderate Rise"
    else:
        return "Moderate Cooling"
