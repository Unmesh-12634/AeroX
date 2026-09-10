"""
SIH26056: Real-Time Airfare Price Index for India
Route Analytics & Corridor Sub-Indices Router
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from backend.config import settings
from backend.db.database import db

router = APIRouter(tags=["Route Analytics"])

@router.get("/routes")
def get_routes(origin: Optional[str] = None, dest: Optional[str] = None) -> Dict[str, Any]:
    if not settings.ROUTE_INDEX_PATH.exists():
        return {"data": []}
    df = pd.read_csv(settings.ROUTE_INDEX_PATH)
    
    if origin and origin != "ALL":
        df = df[df['origin_iata'].str.upper() == origin.upper()]
    if dest and dest != "ALL":
        df = df[df['dest_iata'].str.upper() == dest.upper()]
        
    df = df.replace({np.nan: None})
    return {"data": df.to_dict(orient="records")}

@router.get("/routes/{route_code}")
def get_route_detail(route_code: str) -> Dict[str, Any]:
    if not settings.ROUTE_INDEX_PATH.exists():
        raise HTTPException(status_code=404, detail="Route index file not found")
    df = pd.read_csv(settings.ROUTE_INDEX_PATH)
    
    parts = route_code.upper().split('-')
    if len(parts) == 2:
        r1, r2 = f"{parts[0]}-{parts[1]}", f"{parts[1]}-{parts[0]}"
        match = df[(df['route'].str.upper() == r1) | (df['route'].str.upper() == r2)]
    else:
        match = df[df['route'].str.upper() == route_code.upper()]
        
    if len(match) == 0:
        raise HTTPException(status_code=404, detail=f"Route {route_code} not found")
        
    return {"route": match.replace({np.nan: None}).iloc[0].to_dict()}
