"""
SIH26056: Real-Time Airfare Price Index for India (APIx)
Scraper Quota Management & Window Tracking Engine

Enforces:
- Automated scheduled runs at 07:00 AM and 02:00 PM IST (07:00 and 14:00 IST).
- Maximum 1 user manual scrape allowed between scheduled runs.
- Real-time calculation of next scheduled scrape time and countdown.
- Persistent state tracking via data/logs/scraper_quota_state.json.
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Tuple
from backend.config import settings

IST = timezone(timedelta(hours=5, minutes=30))
QUOTA_FILE = settings.DATA_DIR / "logs" / "scraper_quota_state.json"
MAX_MANUAL_PER_WINDOW = 1

SCHEDULED_HOURS = [7, 14]  # 07:00 AM IST and 02:00 PM IST

class ScraperQuotaManager:
    def __init__(self, quota_file: Path = QUOTA_FILE):
        self.quota_file = quota_file
        self.state = self._load_state()

    def _now_ist(self) -> datetime:
        return datetime.now(IST)

    def _get_current_window_id(self, now: datetime) -> str:
        """
        Determines the current window identifier string.
        Window 1: 07:00 to 14:00 (e.g. 2026-09-13_07:00)
        Window 2: 14:00 to 07:00 next day (e.g. 2026-09-13_14:00)
        """
        date_str = now.strftime("%Y-%m-%d")
        h = now.hour
        if h < 7:
            # Belongs to previous day's 14:00 window
            prev_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
            return f"{prev_date}_14:00"
        elif h < 14:
            return f"{date_str}_07:00"
        else:
            return f"{date_str}_14:00"

    def get_next_scheduled_run(self, now: datetime = None) -> Tuple[datetime, str]:
        """
        Computes the next scheduled scrape datetime in IST and a human-readable label.
        Scheduled runs are at 07:00 AM and 02:00 PM IST.
        """
        if now is None:
            now = self._now_ist()

        today_7am = now.replace(hour=7, minute=0, second=0, microsecond=0)
        today_2pm = now.replace(hour=14, minute=0, second=0, microsecond=0)
        tomorrow_7am = (now + timedelta(days=1)).replace(hour=7, minute=0, second=0, microsecond=0)

        if now < today_7am:
            return today_7am, "07:00 AM IST"
        elif now < today_2pm:
            return today_2pm, "02:00 PM IST"
        else:
            return tomorrow_7am, "07:00 AM IST"

    def _load_state(self) -> Dict[str, Any]:
        if self.quota_file.exists():
            try:
                with open(self.quota_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"current_window": "", "manual_scrapes_used": 0, "history": []}

    def _save_state(self):
        try:
            self.quota_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.quota_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, default=str)
        except Exception as e:
            print(f"[-] Failed to persist scraper quota state: {e}")

    def _sync_window(self):
        now = self._now_ist()
        current_window = self._get_current_window_id(now)
        if self.state.get("current_window") != current_window:
            self.state["current_window"] = current_window
            self.state["manual_scrapes_used"] = 0
            self._save_state()

    def get_quota_status(self) -> Dict[str, Any]:
        """Returns the current quota status, remaining allowance, and countdown to next run."""
        self._sync_window()
        now = self._now_ist()
        next_run_dt, next_run_label = self.get_next_scheduled_run(now)
        
        diff_seconds = max(0, int((next_run_dt - now).total_seconds()))
        hours = diff_seconds // 3600
        minutes = (diff_seconds % 3600) // 60
        seconds = diff_seconds % 60
        time_left_str = f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

        used = self.state.get("manual_scrapes_used", 0)
        remaining = max(0, MAX_MANUAL_PER_WINDOW - used)
        can_scrape = remaining > 0

        return {
            "can_scrape": can_scrape,
            "quota_remaining": remaining,
            "quota_max": MAX_MANUAL_PER_WINDOW,
            "manual_scrapes_used": used,
            "current_window": self.state.get("current_window"),
            "next_scheduled_run": next_run_label,
            "next_scheduled_timestamp": next_run_dt.isoformat(),
            "time_left_seconds": diff_seconds,
            "time_left_formatted": time_left_str,
            "scheduled_slots": ["07:00 AM IST", "02:00 PM IST"],
            "message": (
                "Manual scrape quota available (1 allowed between scheduled runs)."
                if can_scrape else
                f"Scraping quota has been reached. Next scheduled scraping is at {next_run_label}."
            )
        }

    def try_consume_manual_quota(self, trigger_source: str = "web_ui") -> Tuple[bool, Dict[str, Any]]:
        """
        Attempts to consume 1 manual scrape.
        Returns (success: bool, status_dict).
        """
        status = self.get_quota_status()
        if not status["can_scrape"]:
            return False, status

        self.state["manual_scrapes_used"] = self.state.get("manual_scrapes_used", 0) + 1
        record = {
            "timestamp": self._now_ist().isoformat(),
            "source": trigger_source,
            "window": self.state.get("current_window")
        }
        history = self.state.get("history", [])
        history.append(record)
        self.state["history"] = history[-50:]  # Keep last 50
        self._save_state()

        updated_status = self.get_quota_status()
        return True, updated_status

    def record_scheduled_run(self, slot_label: str, routes_count: int, obs_count: int):
        """Called by background scheduler when 07:00 AM or 02:00 PM run completes."""
        self._sync_window()
        # Reset manual quota for the window starting now
        self.state["manual_scrapes_used"] = 0
        record = {
            "timestamp": self._now_ist().isoformat(),
            "slot": slot_label,
            "routes_count": routes_count,
            "obs_count": obs_count,
            "type": "AUTOMATED_SCHEDULED"
        }
        history = self.state.get("history", [])
        history.append(record)
        self.state["history"] = history[-50:]
        self._save_state()

quota_manager = ScraperQuotaManager()
