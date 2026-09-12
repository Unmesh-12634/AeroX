"""
SIH26056: Real-Time Airfare Price Index for India (APIx)
Configuration & Global Settings Module
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
CLEANED_DIR = DATA_DIR / "cleaned"
INDEX_RESULTS_DIR = DATA_DIR / "index_results"
LOGS_DIR = DATA_DIR / "logs"
REPORTS_DIR = DATA_DIR / "reports"
LIVE_SCRAPED_DIR = DATA_DIR / "live_scraped"
FRONTEND_DIR = BASE_DIR / "frontend"

for directory in [DATA_DIR, RAW_DIR, CLEANED_DIR, INDEX_RESULTS_DIR, LOGS_DIR, REPORTS_DIR, LIVE_SCRAPED_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "SIH26056 - Real-Time Airfare Price Index for India (APIx)"
    VERSION: str = "3.0.0"
    DESCRIPTION: str = "Ministry of Statistics (MoSPI) & DGCA High-Frequency Airfare Price Index & Analytics Engine"
    API_V1_PREFIX: str = "/api/v1"
    
    # Statistical Baseline
    BASE_YEAR: int = 2024
    BASE_INDEX_VALUE: float = 100.0
    BASE_NATIONAL_FARE: float = 6250.0  # National benchmark in INR
    
    # Storage
    BASE_DIR: Path = BASE_DIR
    FRONTEND_DIR: Path = FRONTEND_DIR
    MASTER_CSV_PATH: Path = CLEANED_DIR / "sih_master_airfare_observations_v2.csv"
    DB_PATH: Path = DATA_DIR / "airfare_index.db"
    DAILY_INDEX_PATH: Path = INDEX_RESULTS_DIR / "daily_airfare_index.csv"
    ROUTE_INDEX_PATH: Path = INDEX_RESULTS_DIR / "route_airfare_indices.csv"
    LEAD_TIME_INDEX_PATH: Path = INDEX_RESULTS_DIR / "lead_time_index_curve.csv"
    AIRLINE_INDEX_PATH: Path = INDEX_RESULTS_DIR / "airline_airfare_indices.csv"
    CPI_BENCHMARK_PATH: Path = CLEANED_DIR / "cleaned_cpi_mospi_2024.csv"
    SCHEDULER_HISTORY_PATH: Path = LOGS_DIR / "scheduled_runs_history.json"
    LIVE_SCRAPED_DIR: Path = LIVE_SCRAPED_DIR
    
    # Scraping
    DEFAULT_LEAD_TIMES: list[int] = [1, 3, 7, 14, 30, 45]
    SCRAPE_RATE_LIMIT_SECONDS: float = 1.5
    USER_AGENTS: list[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ]

settings = Settings()
