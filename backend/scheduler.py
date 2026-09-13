"""
SIH26056: Real-Time Airfare Price Index for India (APIx)
Automated Background Scheduler for Dual-Daily Scraping

Schedules:
- 07:00 AM IST (Slot 1: Morning Base Airfare Collection)
- 02:00 PM IST (Slot 2: Afternoon Peak Airfare Collection)

Features:
- Headless automated Playwright/HTTP scraping.
- Scrapes DGCA Top-15 routes across Google Flights, MakeMyTrip & Direct Airlines.
- Persists all records into airfare_index.db & live_scraped_master.csv.
- Re-calculates APIx indices and refreshes database cache.
- Resets manual scrape quota window upon completion.
- Logs run history to data/logs/scheduled_runs_history.json.
"""

import asyncio
import threading
import time
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List

from backend.config import settings
from backend.quota_manager import quota_manager, IST
from backend.db.database import db
from backend.index_engine.weights import get_basket_routes
from scripts.scrapers.scraper_orchestrator import ScraperOrchestrator

HISTORY_FILE = settings.DATA_DIR / "logs" / "scheduled_runs_history.json"

class AirfareScrapingScheduler:
    def __init__(self):
        self._running = False
        self._thread = None
        self._last_executed_slot = self._load_last_executed_slot()

    def _now_ist(self) -> datetime:
        return datetime.now(IST)

    def _load_last_executed_slot(self) -> str:
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and data:
                        return data[-1].get("slot_id", "")
            except Exception:
                pass
        return ""

    def _save_history(self, record: Dict[str, Any]):
        try:
            HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            history = []
            if HISTORY_FILE.exists():
                try:
                    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                        history = json.load(f)
                        if not isinstance(history, list):
                            history = []
                except Exception:
                    history = []
            history.append(record)
            # Keep last 100 scheduled runs
            history = history[-100:]
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, default=str)
        except Exception as e:
            print(f"[-] Failed to save scheduler history: {e}")

    def execute_scheduled_scrape(self, slot_label: str) -> Dict[str, Any]:
        """
        Executes the genuine automated collection for the scheduled slot.
        Collects top DGCA basket routes across Google Flights, MakeMyTrip, and Direct Airlines.
        """
        start_time = time.time()
        now = self._now_ist()
        slot_id = f"{now.strftime('%Y-%m-%d')}_{slot_label}"
        print(f"[+] [Scheduler] Starting automated scheduled airfare scrape for {slot_label} ({slot_id})...")

        routes = get_basket_routes()
        if not routes:
            routes = [("DEL", "BOM"), ("DEL", "BLR"), ("BOM", "BLR")]

        platforms = ["google_flights", "makemytrip", "easemytrip", "indigo", "airindia"]
        lead_times = [1, 7, 15]

        total_obs = 0
        status = "COMPLETED"
        error_msg = None

        try:
            orch = ScraperOrchestrator(headless=True)
            orch.run_collection(
                platforms=platforms,
                routes=routes,
                lead_times=lead_times,
                cabin_class="Economy"
            )
            # Refresh database cache
            db.refresh()
            total_obs = len(db.df) if db.df is not None else 0
            print(f"[+] [Scheduler] Scheduled scrape finished. Total database observations: {total_obs}")
        except Exception as e:
            status = "FAILED"
            error_msg = str(e)
            print(f"[-] [Scheduler] Scheduled scrape error: {e}")

        duration = round(time.time() - start_time, 2)
        record = {
            "slot_id": slot_id,
            "slot_label": slot_label,
            "timestamp": now.isoformat(),
            "status": status,
            "duration_seconds": duration,
            "routes_count": len(routes),
            "platforms": platforms,
            "lead_times": lead_times,
            "observations_count": total_obs,
            "error": error_msg
        }

        self._last_executed_slot = slot_id
        self._save_history(record)
        quota_manager.record_scheduled_run(slot_label, len(routes), total_obs)
        return record

    def _loop(self):
        print("[+] [Scheduler] Airfare background scheduler loop active (Monitoring 07:00 AM & 02:00 PM IST).")
        while self._running:
            try:
                now = self._now_ist()
                h, m = now.hour, now.minute
                date_str = now.strftime("%Y-%m-%d")

                # Slot 1: 07:00 AM IST (Window: 07:00 - 07:05)
                if h == 7 and 0 <= m <= 5:
                    slot_id = f"{date_str}_07:00"
                    if self._last_executed_slot != slot_id:
                        self.execute_scheduled_scrape("07:00 AM IST")

                # Slot 2: 02:00 PM IST (Window: 14:00 - 14:05)
                elif h == 14 and 0 <= m <= 5:
                    slot_id = f"{date_str}_14:00"
                    if self._last_executed_slot != slot_id:
                        self.execute_scheduled_scrape("02:00 PM IST")

            except Exception as e:
                print(f"[-] [Scheduler] Exception in scheduler loop: {e}")

            time.sleep(30)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="AirfareScrapingScheduler")
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

scheduler = AirfareScrapingScheduler()
