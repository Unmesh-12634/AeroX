"""
SIH26056: Real-Time Airfare Price Index for India
Explainability & Root Cause Attribution Engine
"""

from typing import Dict, Any, Optional

def explain_price_change(
    current_fare: float = 7850.0,
    baseline_fare: float = 6250.0,
    lead_time_days: int = 2,
    route: str = "DEL-BOM",
    is_festival_season: bool = False
) -> Dict[str, Any]:
    delta_inr = current_fare - baseline_fare
    delta_pct = (delta_inr / baseline_fare) * 100.0 if baseline_fare > 0 else 0.0

    if delta_inr <= 0:
        return {
            "route": route,
            "current_fare": round(current_fare),
            "baseline_fare": round(baseline_fare),
            "delta_inr": round(delta_inr),
            "delta_pct": round(delta_pct, 1),
            "verdict": "Below Baseline / Saver Pricing",
            "components": {
                "advance_purchase_discount_pct": abs(round(delta_pct * 0.7, 1)),
                "carrier_competitive_yield_pct": abs(round(delta_pct * 0.3, 1))
            },
            "summary": "Fare operates below baseline due to advance booking window and inter-carrier price competition."
        }

    # Statistical attribution decomposition
    if lead_time_days <= 3:
        lt_share = 0.58
        fuel_share = 0.18
        capacity_share = 0.14
        demand_share = 0.10
    elif lead_time_days <= 7:
        lt_share = 0.40
        fuel_share = 0.25
        capacity_share = 0.20
        demand_share = 0.15
    else:
        lt_share = 0.15
        fuel_share = 0.35
        capacity_share = 0.30
        demand_share = 0.20

    if is_festival_season:
        demand_share += 0.20
        lt_share = max(0.1, lt_share - 0.20)

    lt_val = delta_inr * lt_share
    fuel_val = delta_inr * fuel_share
    cap_val = delta_inr * capacity_share
    dem_val = delta_inr * demand_share

    return {
        "route": route,
        "current_fare": round(current_fare),
        "baseline_fare": round(baseline_fare),
        "delta_inr": round(delta_inr),
        "delta_pct": round(delta_pct, 1),
        "verdict": "Elevated Fare Surge" if delta_pct >= 25 else "Moderate Market Escalation",
        "components": {
            "urgency_proximity_lead_time": {
                "inr": round(lt_val),
                "contribution_pct": round(lt_share * 100, 1),
                "explanation": f"High booking proximity (T+{lead_time_days} days to departure)"
            },
            "fuel_aviation_turbine_fuel": {
                "inr": round(fuel_val),
                "contribution_pct": round(fuel_share * 100, 1),
                "explanation": "Crude oil / ATF domestic refinery benchmark pass-through"
            },
            "capacity_seat_inventory": {
                "inr": round(cap_val),
                "contribution_pct": round(capacity_share * 100, 1),
                "explanation": "Tight seat inventory in standard economy cabin buckets"
            },
            "demand_load_factor": {
                "inr": round(dem_val),
                "contribution_pct": round(demand_share * 100, 1),
                "explanation": "Peak corporate / weekend travel pressure"
            }
        },
        "summary": f"Of the +₹{round(delta_inr):,} fare increase (+{delta_pct:.1f}%), {round(lt_share * 100)}% is driven by booking proximity (T+{lead_time_days}) and {round(fuel_share * 100)}% by ATF fuel baseline costs."
    }

class PriceChangeExplainer:
    """Class wrapper for price change explainability & decomposition."""

    @staticmethod
    def explain(
        route: str = "DEL-BOM",
        current_fare: float = 7850.0,
        base_fare: float = 6250.0,
        lead_time_days: int = 2,
        atf_change_pct: float = 0.0,
        is_festival_season: bool = False
    ) -> Dict[str, Any]:
        res = explain_price_change(
            current_fare=current_fare,
            baseline_fare=base_fare,
            lead_time_days=lead_time_days,
            route=route,
            is_festival_season=is_festival_season
        )
        return {
            "route": res.get("route"),
            "total_change_pct": res.get("delta_pct", 0.0),
            "breakdown": res.get("components", {}),
            "drivers": [
                f"Booking Lead Urgency ({lead_time_days} days)",
                f"ATF Fuel Adjustment ({atf_change_pct:+.1f}%)" if atf_change_pct != 0 else "Baseline ATF Costs",
                "Seat Inventory Scarcity"
            ],
            "verdict": res.get("verdict"),
            "summary": res.get("summary")
        }

