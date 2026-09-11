"""
SIH26056: Real-Time Airfare Price Index for India
Dynamic Pricing & Lead-Time Elasticity Engine
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List

def calculate_lead_time_elasticity(df: pd.DataFrame, route: str = "DEL-BOM") -> Dict[str, Any]:
    if route and route != "ALL":
        parts = route.upper().split('-')
        if len(parts) == 2:
            sub = df[(df['route'] == f"{parts[0]}-{parts[1]}") | (df['route'] == f"{parts[1]}-{parts[0]}")]
        else:
            sub = df[df['route'] == route.upper()]
    else:
        sub = df

    if len(sub) < 10 or 'lead_time_days' not in sub.columns:
        return {
            "route": route,
            "elasticity_coefficient": None,
            "elasticity_interpretation": "Insufficient data to calculate empirical elasticity",
            "urgency_premium_pct": None,
            "lead_time_decay_curve": []
        }

    # Empirical calculation from observed quotes
    grouped = sub.groupby('lead_time_days')['total_fare_inr'].mean().reset_index()
    grouped = grouped.sort_values('lead_time_days')

    if len(grouped) >= 2:
        p_near = float(grouped.iloc[0]['total_fare_inr'])
        p_far = float(grouped.iloc[-1]['total_fare_inr'])
        lt_near = float(grouped.iloc[0]['lead_time_days'])
        lt_far = float(grouped.iloc[-1]['lead_time_days'])
        
        pct_price_change = (p_near - p_far) / p_far if p_far > 0 else 0.5
        pct_lt_change = (lt_near - lt_far) / lt_far if lt_far > 0 else -0.9
        
        elasticity = round(pct_price_change / pct_lt_change, 3) if pct_lt_change != 0 else -0.42
    else:
        elasticity = -0.42

    curve = []
    for _, row in grouped.iterrows():
        lt = int(row['lead_time_days'])
        fare = float(row['total_fare_inr'])
        curve.append({
            "lead_time": f"T+{lt}",
            "days": lt,
            "mean_fare": round(fare),
            "price_multiplier": round(fare / 6000.0, 2)
        })

    return {
        "route": route,
        "elasticity_coefficient": elasticity,
        "elasticity_interpretation": f"Dynamic pricing curve elasticity {elasticity} (higher fare escalation within 7 days of departure)",
        "urgency_premium_pct": round(abs(elasticity) * 100, 1),
        "lead_time_decay_curve": curve
    }

class BookingLeadTimeElasticity:
    """Class wrapper for lead-time elasticity modeling."""

    @staticmethod
    def get_lead_time_multipliers() -> Dict[int, float]:
        return {
            1: 1.55,
            3: 1.30,
            7: 1.16,
            14: 1.00,
            30: 0.86,
            45: 0.80
        }

    @staticmethod
    def calculate(df: pd.DataFrame, route: str = "DEL-BOM") -> Dict[str, Any]:
        return calculate_lead_time_elasticity(df, route)

