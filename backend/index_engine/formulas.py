"""
SIH26056: Real-Time Airfare Price Index for India
Index Mathematical Formulations Module
"""

import numpy as np
from typing import List, Union

def jevons_index(current_prices: Union[List[float], np.ndarray], base_prices: Union[List[float], np.ndarray]) -> float:
    p_curr = np.array(current_prices, dtype=float)
    p_base = np.array(base_prices, dtype=float)
    
    valid_mask = (p_curr > 0) & (p_base > 0)
    if not np.any(valid_mask):
        return 100.0
        
    ratios = p_curr[valid_mask] / p_base[valid_mask]
    geo_mean = np.exp(np.mean(np.log(ratios)))
    return float(geo_mean * 100.0)

def laspeyres_aggregate(sub_indices: Union[List[float], np.ndarray], weights: Union[List[float], np.ndarray]) -> float:
    indices = np.array(sub_indices, dtype=float)
    w = np.array(weights, dtype=float)
    
    w_sum = np.sum(w)
    if w_sum <= 0:
        return float(np.mean(indices))
        
    normalized_w = w / w_sum
    return float(np.sum(indices * normalized_w))

def dutot_index(current_prices: Union[List[float], np.ndarray], base_prices: Union[List[float], np.ndarray]) -> float:
    p_curr = np.array(current_prices, dtype=float)
    p_base = np.array(base_prices, dtype=float)
    
    mean_curr = np.mean(p_curr)
    mean_base = np.mean(p_base)
    if mean_base <= 0:
        return 100.0
    return float((mean_curr / mean_base) * 100.0)

def carli_index(current_prices: Union[List[float], np.ndarray], base_prices: Union[List[float], np.ndarray]) -> float:
    p_curr = np.array(current_prices, dtype=float)
    p_base = np.array(base_prices, dtype=float)
    
    valid_mask = (p_curr > 0) & (p_base > 0)
    if not np.any(valid_mask):
        return 100.0
    return float(np.mean(p_curr[valid_mask] / p_base[valid_mask]) * 100.0)

class JevonsIndex:
    @staticmethod
    def compute(current_prices: Union[List[float], np.ndarray], base_prices: Union[List[float], np.ndarray]) -> float:
        return jevons_index(current_prices, base_prices)

class LaspeyresIndex:
    @staticmethod
    def compute(sub_indices: Union[List[float], np.ndarray], weights: Union[List[float], np.ndarray]) -> float:
        return laspeyres_aggregate(sub_indices, weights)

    @staticmethod
    def compute_from_route_indices(route_indices: dict, weights: dict) -> float:
        common_routes = [r for r in route_indices if r in weights]
        if not common_routes:
            return 100.0
        indices = [route_indices[r] for r in common_routes]
        w = [weights[r] for r in common_routes]
        return laspeyres_aggregate(indices, w)

class DutotIndex:
    @staticmethod
    def compute(current_prices: Union[List[float], np.ndarray], base_prices: Union[List[float], np.ndarray]) -> float:
        return dutot_index(current_prices, base_prices)

class CarliIndex:
    @staticmethod
    def compute(current_prices: Union[List[float], np.ndarray], base_prices: Union[List[float], np.ndarray]) -> float:
        return carli_index(current_prices, base_prices)

