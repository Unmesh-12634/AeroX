# CLAUDE.md — AREOX / SIH26056 Project Intelligence & Instructions

> **Project**: Real-Time Airfare Price Index for India (APIx)  
> **Problem Statement**: SIH26056 (Smart Automation — Dr. Aaditya Maheshwari)  
> **Domain**: Ministry of Statistics & Programme Implementation (MoSPI) & Directorate General of Civil Aviation (DGCA) High-Frequency Pricing & Analytics

---

## 📌 Project Overview

AREOX is an end-to-end, high-frequency airfare intelligence and price indexing engine designed for the Indian civil aviation market. It ingests multi-source airfare quotes from OTAs and metasearch engines via Playwright, normalizes and de-duplicates observations, computes official statistical price indices (Jevons elementary mean + Laspeyres passenger-weighted composite index), and serves an interactive Apple glassmorphic dashboard alongside modular REST APIs.

### Core Mathematical & Economic Principles
- **Elementary Aggregation (Route & Lead-Time Strata)**: Jevons Geometric Mean Index to eliminate arithmetic substitution bias.
- **Composite Aggregation (National & Corridor Level)**: Laspeyres Index weighted by official DGCA Passenger Seat Demand (PSD) traffic matrix (accounting for 62%+ of top domestic metro passenger volumes).
- **Official Ground-Truth Benchmark**: MoSPI Consumer Price Index (CPI) item `07.3.3.1.2.01` (*"Passenger transport by air, domestic"*), Base Year = 2024 (100.0), July 2026 Index = **119.60**, Base National Fare = **₹6,250**.

---

## ⚙️ Environment & Verified Dependencies

The environment is configured and verified with the following core dependencies:
- **Python**: `3.10+` (verified on Python 3.14)
- **Web Framework**: `fastapi` (v0.119.0), `uvicorn` (v0.37.0), `pydantic` (v2.12.0), `pydantic_settings` (v2.15.0)
- **Data & Computation**: `pandas` (v3.0.5), `numpy` (v2.3.3), `scipy` (v1.18.1)
- **Testing**: `pytest` (v9.1.1)
- **Browser Automation**: `playwright` (v1.62.0) with Chromium headless/headed binaries installed
- **Network & Parsing**: `requests` (v2.32.5), `beautifulsoup4` (v4.15.0)

---

## 🏛️ Directory Architecture

```plaintext
AREOX/
├── backend/                        # FastAPI Application & Business Logic
│   ├── app.py                      # Application entrypoint & middleware configuration
│   ├── config.py                   # Pydantic global settings, paths & constants
│   ├── cleaner/                    # Data validation, schema sanitization & quality scoring
│   │   ├── normalizer.py           # Currency, airline naming & route standardizer
│   │   └── quality_checker.py      # Outlier detection (IQR / Z-score) & completeness audits
│   ├── db/                         # Database layer
│   │   ├── database.py             # SQLite connection management & query helpers
│   │   └── models.py               # Pydantic schemas & SQL table definitions
│   ├── index_engine/               # Economic index calculation engine
│   │   ├── calculator.py           # High-level index calculation coordinator
│   │   ├── formulas.py             # Jevons, Laspeyres, Paasche, Fisher & Dutot formulas
│   │   ├── weights.py              # DGCA Passenger Seat Demand (PSD) weight matrices
│   │   ├── elasticity.py           # Price elasticity & lead-time yield modeling
│   │   ├── explainability.py       # Attribution breakdown (Carrier, Fuel, Surge factors)
│   │   └── dgca_backtester.py      # Statistical correlation engine with DGCA benchmarks
│   ├── replay/                     # Historical market state playback & temporal simulation
│   │   └── replay_engine.py
│   └── routers/                    # Modular FastAPI API Routers (/api/v1)
│       ├── overview.py             # National APIx gauge, headline metrics & daily deltas
│       ├── daily_index.py          # Daily index time-series & historical trendline
│       ├── routes.py               # Route-specific indices, corridor comparison & dispersion
│       ├── airlines.py             # Carrier-specific index curves & yield profiles
│       ├── observations.py         # Raw/Cleaned observation search & filtering
│       ├── analytics.py            # Surge detection, lead-time curves & volatility
│       ├── scraper.py              # On-demand scraping trigger & source health status
│       ├── replay.py               # Market replay controller
│       └── backtest.py             # DGCA empirical backtest results & validation stats
│
├── frontend/                       # Interactive Web Dashboard (Light Apple Glassmorphic UI)
│   ├── index.html                  # Semantic dashboard structure & container views
│   ├── app.js                      # Reactive client logic, Chart.js integrations & API calls
│   └── style.css                   # Custom responsive glassmorphic styles & design tokens
│
├── scripts/                        # Data Engineering, Scraping & Automation Pipelines
│   ├── start_server.py             # FastAPI + Uvicorn server launcher
│   ├── dgca_backtest_validator.py  # DGCA empirical backtest validation auditor
│   ├── audit_and_clean.py          # Database audit, outlier removal & deduplication
│   ├── build_pan_india_master.py   # Synthesizer for Pan-India observation matrix
│   ├── calculate_airfare_index.py  # Batch index generation runner
│   ├── run_scheduler.py            # Background scraper daemon launcher
│   ├── scrapers/                   # Verified Multi-source Playwright Scraper Modules
│   │   ├── scraper_orchestrator.py # Multi-source task distributor & retry handler
│   │   ├── models.py               # Scraper data classes & response models
│   │   ├── google_flights_scraper.py # Live Google Flights Playwright engine
│   │   ├── makemytrip_scraper.py   # Live MakeMyTrip Playwright engine
│   │   ├── easemytrip_scraper.py   # Live EaseMyTrip Playwright engine
│   │   ├── ota_scrapers.py         # Yatra, Ixigo, Cleartrip handlers
│   │   └── airline_scrapers.py     # Direct airline website scrapers (IndiGo, Air India)
│   └── scheduler/
│       └── cron_daemon.py          # Scheduled scraping & indexing cron manager
│
├── data/                           # Data storage
│   ├── raw/                        # Raw source files (Data_Train.csv, data.csv, cpi_2018.xlsx)
│   ├── cleaned/                    # Cleaned observation datasets
│   │   ├── real_only_observations.csv          # 16,077 pure empirical observations (Zero synthetic)
│   │   ├── sih_master_airfare_observations_v2.csv # 25,877 composite observations
│   │   └── cleaned_cpi_mospi_2024.csv          # Official MoSPI CPI airfare series (2025–2026)
│   ├── index_results/              # Computed index time-series outputs
│   │   ├── daily_airfare_index_real_only.csv   # 60-date empirical daily index series
│   │   ├── daily_airfare_index.csv             # Full composite daily index series
│   │   ├── route_airfare_indices.csv           # Corridor-level sub-indices
│   │   └── lead_time_index_curve.csv           # Advance booking curve (T+1 to T+45)
│   ├── live_scraped/               # Live Playwright ingestion buffers (33+ batches)
│   ├── logs/                       # Scraper execution & server run logs
│   └── reports/                    # Backtesting markdown reports & validation summaries
│       ├── DGCA_BACKTEST_REAL_ONLY.md          # Honest real-only empirical backtest report
│       └── DGCA_30DAY_BACKTEST_VALIDATION.md   # Composite baseline report
│
├── tests/                          # Pytest Automated Test Suite
│   ├── conftest.py                 # Shared fixtures & mock data frames
│   ├── test_api_endpoints.py       # FastAPI router endpoint integration tests
│   ├── test_cleaner.py             # Data normalization & quality check unit tests
│   ├── test_index_engine.py        # Mathematical formula & index calculator tests
│   ├── test_scrapers.py            # Scraper payload parsing & network resilience tests
│   └── test_dgca_backtest.py       # DGCA backtest statistical tolerance tests
│
└── .agents/                        # AG Kit Agent Framework
    ├── ARCHITECTURE.md             # Multi-agent & skill architecture documentation
    ├── agent/                      # 20 Specialist AI agent personas
    ├── skills/                     # 44 Domain-specific knowledge skills
    ├── workflows/                  # Slash command procedures
    └── scripts/                    # Checklist & verification automation scripts
```

---

## ⚡ Essential Commands

### 1. Running the FastAPI Server & UI
```powershell
python scripts/start_server.py
```
- **Dashboard UI**: `http://127.0.0.1:8000`
- **Interactive OpenAPI (Swagger)**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

Alternatively run with Uvicorn:
```powershell
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Running Automated Tests
```powershell
pytest -v
```
To run a specific test suite:
```powershell
pytest tests/test_index_engine.py -v
pytest tests/test_api_endpoints.py -v
```

### 3. Running DGCA Empirical Backtests
```powershell
# Run the DGCA backtest validator
python scripts/dgca_backtest_validator.py
```
*Reports generated under `data/reports/`:*
- [`DGCA_BACKTEST_REAL_ONLY.md`](file:///c:/Users/rishi/Downloads/AREOX/data/reports/DGCA_BACKTEST_REAL_ONLY.md) — 100% real observations ($r = 0.7804, R^2 = 0.5096, \text{MAPE} = 17.18\%$).
- [`DGCA_30DAY_BACKTEST_VALIDATION.md`](file:///c:/Users/rishi/Downloads/AREOX/data/reports/DGCA_30DAY_BACKTEST_VALIDATION.md) — Composite series.

### 4. Running Live Scrapers
```powershell
# Run standalone live test scraper (Google Flights, visible Chromium browser)
python test_live_scrape.py

# Run automated background scheduler daemon
python scripts/run_scheduler.py
```

### 5. Data Pipelines & Index Calculation
```powershell
python scripts/audit_and_clean.py
python scripts/build_pan_india_master.py
python scripts/calculate_airfare_index.py
```

---

## ✈️ Live Flight Search & Live Scraper Engine

The dashboard features a real-time MakeMyTrip-style flight search and cross-portal scraping engine:
1. **Dynamic Lead-Time & Departure Date Calculation**:
   - Computes exact future calendar dates dynamically (e.g. `Tomorrow (Fri, 11 Sep 2026)`, `Next Week (Thu, 17 Sep 2026)`).
   - Includes a native interactive calendar date picker to select any arbitrary departure date and automatically calculate the advance horizon ($T+N$).
2. **Synchronized Mathematical Summary Cards**:
   - **Average Fare**: Dynamically computed mean of all rendered flights in the active list.
   - **Lowest Available**: Exact lowest bookable fare from the list, with green highlight tag (`LOWEST FARE`).
   - **Peak Fare**: Exact highest fare across carrier/time slots.
   - **Fastest Flight Available**: Exact shortest duration flight (e.g., `2h 10m • Non-Stop`).
3. **Flight Card Badges**:
   - Displays scheduled departure time (`17:15`), departure date badge (`📅 Thu, 17 Sep 2026`), flight duration, non-stop status, arrival time, airline code badge, source platform, base fare, and taxes ($\ge ₹1,500$ validation filter).

---

## 📊 Data Schema & Datasets Matrix

### Observation Data Provenance

| Dataset File | Rows | Source / Provenance | Status |
| :--- | :--- | :--- | :--- |
| `data/cleaned/real_only_observations.csv` | **16,077** | 2019 Kaggle (10.6k) + 2022 Kaggle (2.9k) + 2026 Live Playwright (2.0k) + Snapshots (0.4k) | ✅ **100% Real Empirical Data** |
| `data/cleaned/sih_master_airfare_observations_v2.csv` | **25,877** | Real data + 9,800 synthetic regional gap-filling records | ℹ️ **Composite Master** |
| `data/cleaned/cleaned_cpi_mospi_2024.csv` | **20** | MoSPI Official Monthly Airfare CPI (Code `07.3.3.1.2.01`, Jan 2025 – Jul 2026) | ✅ **Official Government Benchmark** |

### Standardized Flight Observation Fields

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `record_id` | `str` | Unique observation identifier (e.g., `SCR_GF_1788963999_001`) |
| `search_timestamp_utc` | `str (ISO8601)` | Timestamp when search was performed |
| `travel_date` / `departure_date` | `str (YYYY-MM-DD)` | Flight departure date |
| `lead_time_days` | `int` | Lead time in days ($1, 3, 7, 14, 30, 45+$) |
| `origin` / `origin_iata` | `str (3-char)` | Origin airport (e.g., `DEL`, `BOM`, `BLR`, `CCU`, `MAA`, `HYD`) |
| `dest` / `dest_iata` | `str (3-char)` | Destination airport |
| `route` | `str` | Route pair (`DEL-BOM`) |
| `airline` / `airline_standardized` | `str` | Standardized carrier (`IndiGo`, `Air India`, `Akasa Air`, `SpiceJet`) |
| `flight_number` | `str` | Flight number (e.g., `6E 557`) |
| `departure_time` | `str (HH:MM)` | Scheduled departure time |
| `arrival_time` | `str (HH:MM)` | Scheduled arrival time |
| `duration` | `str` | Flight duration (e.g., `2h 15m`) |
| `is_nonstop` | `bool` | Direct nonstop flag |
| `cabin_class` | `str` | Cabin class (`Economy`, `Business`) |
| `base_fare_inr` | `float` | Base airfare amount in INR |
| `taxes_fees_inr` | `float` | Taxes and airport user development fees (UDF) |
| `total_fare_inr` | `float` | Final payable fare amount in INR ($\ge ₹1,500$) |
| `source_platform` | `str` | Source (`GOOGLE_FLIGHTS`, `MAKEMYTRIP`, `EASEMYTRIP`, etc.) |

---

## 🔌 API Endpoints Summary (`/api/v1`)

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/overview/` | `GET` | National APIx headline index, 24h/7d change, avg national fare |
| `/api/v1/index/daily` | `GET` | Historical daily national index series with date range filtering |
| `/api/v1/routes/` | `GET` | List of all monitored routes with individual route indices |
| `/api/v1/routes/{route}` | `GET` | Route-specific detailed price time series & carrier yield breakdown |
| `/api/v1/airlines/` | `GET` | Airline price index breakdown and carrier market share metrics |
| `/api/v1/observations/` | `GET` | Filterable query endpoint for raw/cleaned flight observations |
| `/api/v1/analytics/lead-time` | `GET` | Lead-time booking yield curves ($D-1$ to $D-45$) |
| `/api/v1/analytics/surges` | `GET` | High-frequency surge detection alerts across routes |
| `/api/v1/scrape/search` | `POST` | Real-time cross-OTA search & scrape with exact KPI recalculation |
| `/api/v1/scrape/status` | `GET` | Health status and supported platforms |
| `/api/v1/replay/state` | `GET` | Market replay state for a specific date in history |
| `/api/v1/backtest/results` | `GET` | Official DGCA backtesting validation statistics & report summary |

---

## 🛠️ Code Conventions & Synchronization Guidelines

### Dual-Workspace Synchronization Rule
Two project directories exist on disk:
1. `C:\Users\rishi\Downloads\AREOX` (Primary workspace)
2. `C:\Users\rishi\Downloads\AREOX (2)\AREOX` (User IDE path)

Whenever modifying `CLAUDE.md`, `frontend/app.js`, `frontend/index.html`, `backend/routers/scraper.py`, or datasets, always sync to `C:\Users\rishi\Downloads\AREOX (2)\AREOX` so edits reflect immediately in the IDE.

### Python & Backend Standards
- **Framework**: FastAPI with Pydantic v2 / Pydantic Settings models for validation.
- **Paths**: Always use `pathlib.Path` resolved from `backend.config.settings` rather than hardcoded string paths.
- **Error Handling**: Graceful fallback values for API routes if database is initializing or CSV files are being regenerated.
- **Vectorized Mathematics**: Use pure functions in `backend/index_engine/formulas.py` with NumPy and Pandas.

### Frontend Standards
- **Aesthetic**: Premium Apple glassmorphism — light translucent backgrounds, backdrop blur (`backdrop-filter: blur(12px)`), subtle borders (`rgba(0,0,0,0.06)`), refined typography.
- **Zero Heavy Framework Lock-in**: Lightweight Vanilla JavaScript modular structure in `frontend/app.js`.
- **Responsive**: Fully responsive CSS Grid and Flexbox layouts in `frontend/style.css`.
- **Zero Purple Rule**: Adheres to strict color palette (Slate, Sky Blue, Emerald Green, Amber, Coral Red).

---

## 🤖 AI Agent Toolkit Integration (`.agents/`)

This repository is equipped with the **AG Kit** agent orchestration layer:
- **Rules**: Global rules defined in `.agents/rules/GEMINI.md`.
- **Agents (`.agents/agent/`)**: 20 specialist personas (`orchestrator`, `backend-specialist`, `frontend-specialist`, `database-architect`, `security-auditor`, `test-engineer`, `debugger`).
- **Skills (`.agents/skills/`)**: 44 conditional skills (`clean-code`, `frontend-design`, `api-patterns`, `database-design`, `testing-patterns`, `vulnerability-scanner`).
- **Validation**: Project audits can be executed via `python .agents/scripts/checklist.py .` and `verify_all.py`.

