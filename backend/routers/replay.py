"""
SIH26056: Real-Time Airfare Price Index for India
Deterministic Replay Router (Jury Demo)
"""

from fastapi import APIRouter
from typing import Dict, Any
from backend.db.models import ReplayStartRequest
from backend.replay.replay_engine import replay_engine

router = APIRouter(tags=["Deterministic Replay Mode"])

@router.post("/replay/start")
def start_replay(req: ReplayStartRequest) -> Dict[str, Any]:
    return replay_engine.start_replay(speed=req.speed_seconds_per_day, routes=req.routes)

@router.post("/replay/stop")
def stop_replay() -> Dict[str, Any]:
    return replay_engine.stop_replay()

@router.get("/replay/status")
def get_replay_status() -> Dict[str, Any]:
    return replay_engine.get_status()
