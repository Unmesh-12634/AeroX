# DGCA / MoSPI Empirical Comparison & Temporal Audit Report
**SIH 2026 Problem Statement SIH26056: Real-Time Airfare Price Index for India (APIx)**
*Direct Benchmark Comparison & Data Alignment Assessment*

---

## 1. Official MoSPI CPI Dataset Overview (`cleaned_cpi_mospi_2024.csv`)

The official government benchmark file contains **19 monthly domestic airfare index values** published by the Ministry of Statistics and Programme Implementation (MoSPI) under item code `07.3.3.1.2.01` (*"Passenger transport by air, domestic"*), with Base Year 2024 = 100.0:

| Base Year | Series | Year | Month | State | Class / Sub-Class | Item Code | MoSPI CPI Index | MoSPI Inflation (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2024 | Current | **2026** | **July** | All India | Passenger transport by air, domestic | `07.3.3.1.2.01` | **125.46** | +22.94% |
| 2024 | Current | **2026** | **June** | All India | Passenger transport by air, domestic | `07.3.3.1.2.01` | **126.09** | +10.14% |
| 2024 | Current | **2026** | **May** | All India | Passenger transport by air, domestic | `07.3.3.1.2.01` | **127.62** | +15.06% |
| 2024 | Current | **2026** | **April** | All India | Passenger transport by air, domestic | `07.3.3.1.2.01` | **123.27** | +11.11% |
| 2024 | Current | **2026** | **March** | All India | Passenger transport by air, domestic | `07.3.3.1.2.01` | **123.55** | +14.20% |
| 2024 | Current | **2026** | **February** | All India | Passenger transport by air, domestic | `07.3.3.1.2.01` | **122.43** | -7.01% |
| 2024 | Current | **2026** | **January** | All India | Passenger transport by air, domestic | `07.3.3.1.2.01` | **122.71** | +6.65% |
| 2024 | Current | **2025** | **December** | All India | Passenger transport by air, domestic | `07.3.3.1.2.01` | **124.23** | — |
| 2024 | Current | **2025** | **November** | All India | Passenger transport by air, domestic | `07.3.3.1.2.01` | **121.45** | — |
| 2024 | Current | **2025** | **October** | All India | Passenger transport by air, domestic | `07.3.3.1.2.01` | **108.19** | — |
| 2024 | Current | **2025** | **September**| All India | Passenger transport by air, domestic | `07.3.3.1.2.01` | **105.22** | — |
| 2024 | Current | **2025** | **August** | All India | Passenger transport by air, domestic | `07.3.3.1.2.01` | **112.11** | — |
| 2024 | Current | **2025** | **July** | All India | Passenger transport by air, domestic | `07.3.3.1.2.01` | **102.05** | — |
| 2024 | Current | **2025** | **June** | All India | Passenger transport by air, domestic | `07.3.3.1.2.01` | **114.48** | — |
| 2024 | Current | **2025** | **May** | All India | Passenger transport by air, domestic | `07.3.3.1.2.01` | **110.92** | — |
| 2024 | Current | **2025** | **April** | All India | Passenger transport by air, domestic | `07.3.3.1.2.01` | **110.94** | — |
| 2024 | Current | **2025** | **March** | All India | Passenger transport by air, domestic | `07.3.3.1.2.01` | **108.19** | — |
| 2024 | Current | **2025** | **February** | All India | Passenger transport by air, domestic | `07.3.3.1.2.01` | **131.66** | — |
| 2024 | Current | **2025** | **January** | All India | Passenger transport by air, domestic | `07.3.3.1.2.01` | **115.05** | — |

---

## 2. Real-Only Index Date Distribution (`daily_airfare_index_real_only.csv`)

The empirical index dataset contains **60 daily observations** across 3 discrete time regimes:

| Year | Month | Observation Dates Count | Date Range Covered | Mean APIx Index (Jevons-Laspeyres) |
| :--- | :--- | :--- | :--- | :--- |
| **2019** | March | 10 dates | `2019-03-01` to `2019-03-27` | **221.42** |
| **2019** | April | 10 dates | `2019-04-01` to `2019-04-27` | **133.98** |
| **2019** | May | 10 dates | `2019-05-01` to `2019-05-27` | **143.19** |
| **2019** | June | 10 dates | `2019-06-01` to `2019-06-27` | **138.14** |
| **2022** | February | 15 dates | `2022-02-14` to `2022-02-28` | **109.99** |
| **2026** | September | 3 snapshot dates | `2026-09-10`, `2026-09-16`, `2026-09-24` | **200.44** (Forward booking lead-time curve) |
| **2026** | October | 2 snapshot dates | `2026-10-09`, `2026-10-24` | **189.77** (Advance booking lead-time curve) |

---

## 3. Temporal Overlap & Statistical Feasibility Assessment

### ⚠️ Direct Overlap Finding: **EXACTLY ZERO (0) MONTHS**

- **MoSPI CPI Series**: Spans exclusively **January 2025 through July 2026** (19 consecutive months).
- **Real Scraped / Historical Series**: Spans **March–June 2019**, **February 2022**, and **September–October 2026**.
- **Result**: There is **no calendar month** where both real scraped observations and official MoSPI CPI airfare data concurrently exist in this dataset.

### Statistical Integrity Rule:
Computing Pearson correlation ($r$), $R^2$, or MAPE across $N = 0$ overlapping points is **mathematically undefined and scientifically invalid**. Rather than fabricating synthetic bridge values or comparing mismatched time periods, this structural gap is reported transparently as an inherent limitation of available historical data assets.

---

## 4. Key Takeaways for SIH Evaluation Panel

1. **Why This Gap Validates the Problem Statement**:
   - Official government CPI reports are published with a **lag of 30–45 days** (the latest available report is July 2026).
   - Our real-time scraping engine operates on **high-frequency forward lead times ($T+1$ to $T+45$ for September and October 2026)**.
   - The lag between backward-looking survey publication and forward-looking market pricing is the exact problem SIH26056 was designed to solve.
2. **True Benchmark Feasibility**:
   - As live scraping continues over the next 30–60 days, real APIx daily values will accumulate concurrently with future MoSPI monthly releases, enabling real-time ongoing correlation tracking without synthetic data.
