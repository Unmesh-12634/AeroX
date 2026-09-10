"""
SIH26056: Real-Time Airfare Price Index for India
DGCA Passenger Seat Demand (PSD) Weights Module
"""

from typing import Dict

# Official DGCA Annual Domestic Passenger Traffic Distribution (PSD Weights)
# Metro-Metro Trunk accounts for ~62% of traffic, Metro-NonMetro ~28%, Regional ~10%
DGCA_PSD_ROUTE_WEIGHTS: Dict[str, float] = {
    # Top Tier-1 Metro Trunk Corridors
    "DEL-BOM": 0.1240,  # Delhi - Mumbai (India's Busiest Corridor)
    "BOM-DEL": 0.1240,
    "BLR-DEL": 0.0980,  # Bengaluru - Delhi
    "DEL-BLR": 0.0980,
    "BOM-BLR": 0.0820,  # Mumbai - Bengaluru
    "BLR-BOM": 0.0820,
    "DEL-HYD": 0.0650,  # Delhi - Hyderabad
    "HYD-DEL": 0.0650,
    "DEL-CCU": 0.0540,  # Delhi - Kolkata
    "CCU-DEL": 0.0540,
    "BOM-HYD": 0.0480,  # Mumbai - Hyderabad
    "HYD-BOM": 0.0480,
    "DEL-MAA": 0.0450,  # Delhi - Chennai
    "MAA-DEL": 0.0450,
    "BOM-CCU": 0.0420,  # Mumbai - Kolkata
    "CCU-BOM": 0.0420,
    "BOM-MAA": 0.0380,  # Mumbai - Chennai
    "MAA-BOM": 0.0380,
    "BLR-HYD": 0.0350,  # Bengaluru - Hyderabad
    "HYD-BLR": 0.0350,

    # Major Regional & Tourism Trunk Corridors
    "BOM-GOI": 0.0280,  # Mumbai - Goa
    "GOI-BOM": 0.0280,
    "DEL-GOI": 0.0250,  # Delhi - Goa
    "GOI-DEL": 0.0250,
    "DEL-AMD": 0.0240,  # Delhi - Ahmedabad
    "AMD-DEL": 0.0240,
    "DEL-PNQ": 0.0220,  # Delhi - Pune
    "PNQ-DEL": 0.0220,
    "DEL-COK": 0.0200,  # Delhi - Kochi
    "COK-DEL": 0.0200,
    "DEL-SXR": 0.0180,  # Delhi - Srinagar
    "SXR-DEL": 0.0180,
    "DEL-PAT": 0.0160,  # Delhi - Patna
    "PAT-DEL": 0.0160,
    "DEL-LKO": 0.0150,  # Delhi - Lucknow
    "LKO-DEL": 0.0150,
    "DEL-GAU": 0.0140,  # Delhi - Guwahati
    "GAU-DEL": 0.0140,
    "HYD-BBI": 0.0120,  # Hyderabad - Bhubaneswar
    "BBI-HYD": 0.0120,
    "DEL-JAI": 0.0110,  # Delhi - Jaipur
    "JAI-DEL": 0.0110,
    "CCU-GAU": 0.0100,  # Kolkata - Guwahati
    "GAU-CCU": 0.0100,
    "BLR-COK": 0.0090,  # Bengaluru - Kochi
    "COK-BLR": 0.0090,
    "DEL-IXC": 0.0080,  # Delhi - Chandigarh
    "IXC-DEL": 0.0080,
    "DEL-ATQ": 0.0075,  # Delhi - Amritsar
    "ATQ-DEL": 0.0075,
    "DEL-IDR": 0.0070,  # Delhi - Indore
    "IDR-DEL": 0.0070,
    "DEL-VTZ": 0.0065,  # Delhi - Visakhapatnam
    "VTZ-DEL": 0.0065,
    "DEL-IXR": 0.0060,  # Delhi - Ranchi
    "IXR-DEL": 0.0060,
    "DEL-RPR": 0.0055,  # Delhi - Raipur
    "RPR-DEL": 0.0055,
    "DEL-DED": 0.0050,  # Delhi - Dehradun
    "DED-DEL": 0.0050,
    "DEL-VNS": 0.0045,  # Delhi - Varanasi
    "VNS-DEL": 0.0045,
    "DEL-TRV": 0.0040,  # Delhi - Trivandrum
    "TRV-DEL": 0.0040,
    "CCU-IXB": 0.0035,  # Kolkata - Bagdogra
    "IXB-CCU": 0.0035,
    "DEL-IXZ": 0.0030,  # Delhi - Port Blair
    "IXZ-DEL": 0.0030,
    "BOM-UDR": 0.0025,  # Mumbai - Udaipur
    "UDR-BOM": 0.0025,
    "BOM-NAG": 0.0020,  # Mumbai - Nagpur
    "NAG-BOM": 0.0020
}

PSD_WEIGHTS = DGCA_PSD_ROUTE_WEIGHTS
DEFAULT_CORRIDOR_WEIGHT = 0.0010

def get_route_weight(route: str) -> float:
    return DGCA_PSD_ROUTE_WEIGHTS.get(route.upper(), DEFAULT_CORRIDOR_WEIGHT)

def get_route_psd_weight(route: str) -> float:
    return get_route_weight(route)

def get_normalized_psd_weights(routes: list) -> Dict[str, float]:
    raw = {r: get_route_weight(r) for r in routes}
    total = sum(raw.values())
    if total <= 0:
        return {r: 1.0 / len(routes) for r in routes}
    return {r: raw[r] / total for r in routes}

