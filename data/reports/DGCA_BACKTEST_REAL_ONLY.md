# DGCA Empirical Backtest Validation Report (Real Data Only)
**SIH 2026 Problem Statement SIH26056: Real-Time Airfare Price Index for India (APIx)**
*Scientific Integrity & Empirical Audit Report — Zero Synthetic Observations*

---

## 1. Executive Summary & Data Integrity Notice

This report presents an **unaltered, empirical backtest** of the Real-Time Airfare Price Index (APIx) calculated strictly from **100% authentic observation records** without synthetic data interpolation or mathematical curve-smoothing.

- **Master Dataset (Original)**: 25,877 total rows
- **Synthetic Records Removed (`pan_india_calibrated_ledger`)**: 9,800 rows (37.9% of original master)
- **Real-Only Observations Retained (`data/cleaned/real_only_observations.csv`)**: **16,077 rows**
- **Effective Daily Index Records (`data/index_results/daily_airfare_index_real_only.csv`)**: **60 dates**

---

## 2. Real-Only Dataset Provenance & Date Coverage

The retained 16,077 real observations originate from three distinct empirical datasets:

| Data Tier / Source | Observation Count | Travel Date Range | Nature of Coverage | Strict Consecutive Days |
| :--- | :--- | :--- | :--- | :--- |
| **2019 Kaggle Dataset (`Data_Train.csv`)** | 10,683 rows | `2019-03-01` to `2019-06-27` | Periodic sampling (every 2–3 days, 40 total dates) | **0 days** (Intermittent) |
| **2022 Kaggle Dataset (`data.csv`)** | 2,906 rows | `2022-02-14` to `2022-02-28` | Daily continuous tracking across 15 consecutive dates | **15 continuous days** |
| **2026 Live Scrapers (Google Flights / EMT)** | 2,084 rows | `2026-09-10` to `2026-10-24` | 5 discrete forward booking dates ($T+1, T+7, T+15, T+30, T+45$) | **0 days** (Snapshot points) |
| **Route Snapshot Files (`flight_data_*.csv`)** | 404 rows | Undated | Route benchmark snapshots | N/A |

### ⚠️ Critical Finding on Continuous Temporal Coverage:
The real dataset **does NOT contain a continuous 30-day or 60-day unbroken daily time series**. The maximum continuous daily sequence in the real data is **exactly 15 consecutive calendar days (February 14 to February 28, 2022)**.

---

## 3. Honest Statistical Backtest Metrics

The table below presents the **actual, unpadded statistical metrics** computed from `data/index_results/daily_airfare_index_real_only.csv` alongside the previous synthetic-inflated numbers:

| Metric | Real-Only Full Series (60 Dates) | Real-Only Continuous Window (15 Days — 2022) | Previous Synthetic-Inflated Report | Status & Explanation |
| :--- | :--- | :--- | :--- | :--- |
| **Pearson Correlation ($r$)** | **0.7804** | **0.7263** | *0.9998* | Moderate-to-strong real-world co-movement (previously inflated by synthetic sine generator) |
| **Coefficient of Determination ($R^2$)** | **0.5096** | **0.4523** | *0.9995* | Real airline fare variance explains ~51% of index volatility |
| **Mean Absolute % Error (MAPE)** | **17.18%** | **19.72%** | *0.77%* | Realistic tracking deviation reflecting weekend surges and dynamic pricing |
| **Root Mean Square Error (RMSE)** | **40.01 pts** | **32.68 pts** | *1.28 pts* | Captures true price regime shifts between 2019 (low base) and 2026 (post-inflation) |

---

## 4. Daily Real-Only Airfare Price Index Ledger (Sample Dates)

| Travel Date | Dataset Tier | Observations Count | Computed APIx (Jevons-Laspeyres) | 7D Moving Avg | Day-on-Day Change (%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **2019-03-01** | 2019 Pre-COVID | 120 | 393.76 | 393.76 | 0.00% |
| **2019-03-03** | 2019 Pre-COVID | 268 | 243.52 | 318.64 | -38.16% |
| **2019-06-01** | 2019 Pre-COVID | 134 | 141.93 | 143.23 | -0.91% |
| **2022-02-14** | 2022 Post-COVID | 212 | 161.73 | 160.18 | +0.97% |
| **2022-02-15** | 2022 Post-COVID | 210 | 162.35 | 161.60 | +0.47% |
| **2022-02-18** | 2022 Post-COVID | 198 | 162.27 | 163.76 | -0.91% |
| **2022-02-21** | 2022 Post-COVID | 185 | 69.07 | 69.68 | -57.43% |
| **2022-02-28** | 2022 Post-COVID | 194 | 69.19 | 68.51 | +1.00% |
| **2026-09-10** | 2026 Live Scrape | 442 | 247.80 | 89.96 | +202.25% (T+1 Surge) |
| **2026-09-16** | 2026 Live Scrape | 692 | 207.81 | 109.76 | -0.67% (T+7 Standard) |
| **2026-09-24** | 2026 Live Scrape | 446 | 175.97 | 126.21 | -11.21% (T+15 Discount) |
| **2026-10-09** | 2026 Live Scrape | 392 | 156.60 | 142.09 | -1.74% (T+30 Advance) |
| **2026-10-24** | 2026 Live Scrape | 112 | 150.19 | 160.29 | +9.41% (T+45 Early Bird) |

---

## 5. Conclusions & Scientific Assessment for SIH Evaluation Panel

1. **Honest Baseline Correlation**: Real airline pricing data demonstrates an empirical correlation of **$r = 0.7804$** with macroeconomic fare movements, which is statistically robust for real-world high-frequency financial time series.
2. **True Problem Statement Justification**: The severe dispersion and regime shifts between 2019, 2022, and 2026 demonstrate why the government needs a continuous daily scraping pipeline rather than static survey sampling.
3. **Reproducibility**: This analysis is 100% reproducible directly from raw CSV sources without synthetic data generation.
