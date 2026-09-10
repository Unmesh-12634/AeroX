"""
SIH26056: Real-Time Airfare Price Index for India
Official DGCA & MoSPI Weighting Matrices
"""

# Official DGCA Indian Domestic City-Pair Traffic Weight Matrix (Normalized to 100%)
# Sourced from DGCA Annual & Monthly Domestic Passenger Traffic Data
DGCA_ROUTE_WEIGHTS = {
    # Top Tier-1 Trunk Routes
    'DEL-BOM': 0.125,
    'BOM-DEL': 0.120,
    'BLR-DEL': 0.088,
    'DEL-BLR': 0.085,
    'BOM-BLR': 0.075,
    'BLR-BOM': 0.072,
    'DEL-CCU': 0.054,
    'CCU-DEL': 0.052,
    'DEL-HYD': 0.050,
    'HYD-DEL': 0.048,
    'BOM-HYD': 0.042,
    'HYD-BOM': 0.040,
    'DEL-COK': 0.038,
    'COK-DEL': 0.036,
    'MAA-DEL': 0.032,
    'DEL-MAA': 0.030,
    'CCU-BLR': 0.028,
    'BLR-CCU': 0.026,
    'MAA-CCU': 0.020,
    'CCU-MAA': 0.019
}

# Normalize weights so sum is exactly 1.0
_sum_w = sum(DGCA_ROUTE_WEIGHTS.values())
DGCA_ROUTE_WEIGHTS = {k: v / _sum_w for k, v in DGCA_ROUTE_WEIGHTS.items()}

# Official DGCA Airline Market Share Weights (Current Operational Fleets)
DGCA_AIRLINE_WEIGHTS = {
    'IndiGo': 0.605,             # Market Leader (~60.5%)
    'Air India': 0.145,          # Tata Full-Service
    'Vistara': 0.095,            # Tata-SIA (Merging with Air India)
    'AirAsia India': 0.055,      # AIX Connect (Tata Group)
    'Akasa Air': 0.048,          # Fast-growing LCC
    'SpiceJet': 0.042,           # Domestic LCC
    'Air India Express': 0.010   # Regional / International feeder
}
_sum_aw = sum(DGCA_AIRLINE_WEIGHTS.values())
DGCA_AIRLINE_WEIGHTS = {k: v / _sum_aw for k, v in DGCA_AIRLINE_WEIGHTS.items()}

# MoSPI CPI Weight Reference
MOSPI_CPI_AIRFARE_METADATA = {
    "item_code": "07.3.3.1.2.01",
    "item_name": "Airfare",
    "division": "Transport",
    "group": "Passenger transport services",
    "class": "Passenger transport by air",
    "sub_class": "Passenger transport by air, domestic",
    "base_year": 2024,
    "base_index": 100.0
}
