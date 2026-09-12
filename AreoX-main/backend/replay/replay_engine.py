"""
SIH26056: Real-Time Airfare Price Index for India
Deterministic Replay Engine (Hackathon Jury Demonstration Mode)
"""

import time
import threading
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.config import settings
from backend.db.database import db

class ReplayEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ReplayEngine, cls).__new__(cls)
            cls._instance._init_engine()
        return cls._instance

    def _init_engine(self):
        self.is_running: bool = False
        self.current_step: int = 0
        self.total_steps: int = 0
        self.current_date: Optional[str] = None
        self.speed: float = 1.0  # seconds per day
        self.target_routes: List[str] = ["DEL-BOM", "BLR-DEL", "HYD-BBI", "DEL-JAI"]
        self._thread: Optional[threading.Thread] = None
        self.history_records: List[Dict[str, Any]] = []

    def start_replay(self, speed: float = 1.0, routes: Optional[List[str]] = None) -> Dict[str, Any]:
        if self.is_running:
            return {"status": "already_running", "current_step": self.current_step, "total_steps": self.total_steps}

        df = db.get_master_df()
        if len(df) == 0:
            return {"status": "error", "message": "Master dataset not loaded"}

        df['travel_date'] = pd.to_datetime(df['travel_date'])
        dates = df['travel_date'].sort_values().unique()
        
        self.is_running = True
        self.current_step = 0
        self.total_steps = len(dates)
        self.speed = max(0.2, speed)
        if routes:
            self.target_routes = routes

        self._thread = threading.Thread(target=self._run_replay_loop, args=(dates,), daemon=True)
        self._thread.start()

        return {
            "status": "started",
            "speed_seconds_per_day": self.speed,
            "total_days": self.total_steps,
            "start_date": dates[0].strftime('%Y-%m-%d') if len(dates) > 0 else None,
            "end_date": dates[-1].strftime('%Y-%m-%d') if len(dates) > 0 else None
        }

    def stop_replay(self) -> Dict[str, Any]:
        self.is_running = False
        return {"status": "stopped", "current_step": self.current_step}

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "current_date": self.current_date,
            "progress_pct": round((self.current_step / max(1, self.total_steps)) * 100, 1),
            "speed": self.speed
        }

    def _run_replay_loop(self, dates):
        for idx, d in enumerate(dates):
            if not self.is_running:
                break
            self.current_step = idx + 1
            self.current_date = d.strftime('%Y-%m-%d')
            time.sleep(self.speed)
        self.is_running = False

replay_engine = ReplayEngine()
