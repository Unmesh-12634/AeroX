"""
SIH26056: Real-Time Airfare Price Index for India
Automated Scheduled Scraping Daemon & Pipeline Manager

Features:
- Configurable interval (minutes/hours) or standard cron-style schedule.
- Multi-route and multi-lead-time sweeps (T+1, T+7, T+15, T+30, T+45).
- Automatic post-scrape trigger: Updates Master v2 dataset and recalculates the Airfare Price Index (APIx).
- Health monitoring, structured execution logs, and run history tracking.
- Graceful shutdown handling.
"""

import os
import sys
import time
import json
import signal
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from scripts.scrapers.scraper_orchestrator import ScraperOrchestrator, DEFAULT_TOP_ROUTES, DEFAULT_LEAD_TIMES
from scripts.index_engine.calculator import AirfareIndexEngine

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOGS_DIR = os.path.join(DATA_DIR, 'logs')
RESULTS_DIR = os.path.join(DATA_DIR, 'index_results')

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

class ScheduledScraperDaemon:
    def __init__(
        self,
        interval_minutes: int = 60,
        platforms: List[str] = None,
        routes: List[tuple] = None,
        lead_times: List[int] = None,
        recalculate_index: bool = True,
        max_iterations: int = 0 # 0 = infinite loop
    ):
        self.interval_seconds = max(60, interval_minutes * 60)
        self.interval_minutes = interval_minutes
        self.platforms = platforms or ["google_flights"]
        self.routes = routes or DEFAULT_TOP_ROUTES
        self.lead_times = lead_times or DEFAULT_LEAD_TIMES
        self.recalculate_index = recalculate_index
        self.max_iterations = max_iterations
        self.is_running = True
        self.run_history_file = os.path.join(LOGS_DIR, "scheduled_runs_history.json")
        self.daemon_log_file = os.path.join(LOGS_DIR, "scraper_daemon.log")
        
        self.orchestrator = ScraperOrchestrator(headless=True)
        self.index_engine = AirfareIndexEngine() if recalculate_index else None

        # Register termination signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        print("\n[!] Received shutdown signal. Gracefully stopping daemon...")
        self.is_running = False
        self._log("Daemon shutdown requested by user/system.")

    def _log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        print(f"[*] {message}")
        with open(self.daemon_log_file, "a", encoding="utf-8") as f:
            f.write(log_line)

    def _record_run_history(self, run_meta: Dict[str, Any]):
        history = []
        if os.path.exists(self.run_history_file):
            try:
                with open(self.run_history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except:
                history = []
        
        history.append(run_meta)
        # Keep last 100 runs in history
        history = history[-100:]
        with open(self.run_history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

    def execute_single_cycle(self, iteration: int) -> Dict[str, Any]:
        start_time = time.time()
        start_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self._log(f"=== Starting Scheduled Scrape Cycle #{iteration} ===")
        self._log(f"Platforms: {self.platforms} | Routes: {[f'{o}-{d}' for o, d in self.routes]} | Lead Times: {[f'T+{lt}' for lt in self.lead_times]}")

        scraped_count = 0
        error_msg = None
        apix_val = None

        try:
            # 1. Run live data collection
            observations = self.orchestrator.run_collection(
                platforms=self.platforms,
                routes=self.routes,
                lead_times=self.lead_times,
                cabin_class="Economy"
            )
            scraped_count = len(observations)
            self._log(f"Collection complete: {scraped_count} live flight observations retrieved.")

            # 2. Trigger automatic Index Recalculation if enabled
            if self.recalculate_index and scraped_count > 0:
                self._log("Triggering automated Airfare Price Index (APIx) recalculation...")
                self.index_engine.run_full_pipeline()
                
                # Fetch latest APIx number
                daily_path = os.path.join(RESULTS_DIR, "daily_airfare_index.csv")
                if os.path.exists(daily_path):
                    df_d = pd.read_csv(daily_path)
                    if len(df_d) > 0:
                        apix_val = float(df_d['apix_jevons_laspeyres'].iloc[-1])
                        self._log(f"APIx Index successfully recalculated: Latest APIx = {apix_val:.2f}")

        except Exception as e:
            error_msg = str(e)
            self._log(f"ERROR during cycle #{iteration}: {e}")

        duration_sec = round(time.time() - start_time, 2)
        run_meta = {
            "iteration": iteration,
            "start_timestamp": start_ts,
            "end_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": duration_sec,
            "scraped_observations": scraped_count,
            "latest_apix_index": apix_val,
            "status": "SUCCESS" if not error_msg else "ERROR",
            "error": error_msg
        }
        self._record_run_history(run_meta)
        self._log(f"=== Completed Cycle #{iteration} in {duration_sec}s. Status: {run_meta['status']} ===\n")
        return run_meta

    def start_daemon(self):
        self._log(f"SIH26056 Automated Scraper Daemon Initialized.")
        self._log(f"Interval: Every {self.interval_minutes} minutes ({self.interval_seconds} seconds).")
        self._log(f"Max Iterations: {'Infinite (Continuous)' if self.max_iterations == 0 else self.max_iterations}")

        iteration = 1
        while self.is_running:
            # Run cycle
            self.execute_single_cycle(iteration=iteration)

            if self.max_iterations > 0 and iteration >= self.max_iterations:
                self._log(f"Reached max iterations limit ({self.max_iterations}). Daemon stopping.")
                break

            iteration += 1
            next_run_time = datetime.now() + timedelta(seconds=self.interval_seconds)
            self._log(f"Sleeping for {self.interval_minutes}m. Next scheduled run at: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")

            # Sleep in short increments to respond promptly to SIGINT
            sleep_elapsed = 0
            while sleep_elapsed < self.interval_seconds and self.is_running:
                time.sleep(2)
                sleep_elapsed += 2

        self._log("Daemon process exited successfully.")

def main():
    parser = argparse.ArgumentParser(description="SIH26056 Automated Scheduled Scraping Daemon")
    parser.add_argument("--interval", type=int, default=60, help="Interval between scrapes in minutes (default: 60)")
    parser.add_argument("--platform", type=str, default="google_flights", help="Platform(s): 'google_flights', 'makemytrip', 'easemytrip', 'ota', 'airlines', 'all'")
    parser.add_argument("--routes", type=str, default=None, help="Comma-separated routes e.g. 'DEL-BOM,BOM-BLR'")
    parser.add_argument("--lead-times", type=str, default="1,7,15,30,45", help="Comma-separated lead times in days e.g. '1,7,15,30,45'")
    parser.add_argument("--iterations", type=int, default=0, help="Max iterations to run (0 = continuous infinite daemon)")
    parser.add_argument("--no-index", action="store_true", help="Skip automatic index recalculation after scrape")
    parser.add_argument("--once", action="store_true", help="Run exactly one scheduled cycle immediately and exit")

    args = parser.parse_args()

    platforms = [p.strip().lower() for p in args.platform.split(",")]
    
    if args.routes:
        routes = []
        for r in args.routes.split(","):
            parts = r.strip().upper().split("-")
            if len(parts) == 2:
                routes.append((parts[0], parts[1]))
    else:
        routes = DEFAULT_TOP_ROUTES

    lead_times = [int(lt.strip()) for lt in args.lead_times.split(",")]
    max_iter = 1 if args.once else args.iterations

    daemon = ScheduledScraperDaemon(
        interval_minutes=args.interval,
        platforms=platforms,
        routes=routes,
        lead_times=lead_times,
        recalculate_index=not args.no_index,
        max_iterations=max_iter
    )
    daemon.start_daemon()

if __name__ == "__main__":
    main()
