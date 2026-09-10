# SIH26056: Real-Time Airfare Price Index (APIx) — Mathematical Engine & Explainability Report

> **Statistical Framework:** Compliant with MoSPI Consumer Price Index (CPI) Guidelines & UN/ILO CPI Manual.

## 1. Executive Index Summary

- **Latest National Airfare Price Index (APIx):** **150.19** (Base = 100.00)
- **7-Day Moving Average Index:** **154.23**
- **Current Market Pulse:** **Surging / Under Pressure**
- **Price Volatility (CV):** **24.94%**
- **Total Audited Master Observations:** **25,877 records**

## 2. Mathematical Methodology & Formulas

### A. Elementary Route-Carrier Level: Jevons Geometric Mean Formula
$$\text{APIx}_{r, t} = \frac{\left(\prod_{i=1}^{n_r} p_{i, t}\right)^{1/n_r}}{\bar{P}_{r, 0}} \times 100$$
* **Why Jevons:** Unlike simple arithmetic averages (Carli/Dutot), Jevons satisfies the **Axiomatic Time-Reversal Test** and is unaffected by price dispersion swings common in dynamic airline pricing.

### B. Higher-Level National Aggregation: Laspeyres Route-Weighted Index
$$\text{APIx}_{\text{National}, t} = \sum_{r=1}^{R} w_r \times \text{APIx}_{r, t}$$
* Where $w_r$ is the official **DGCA Passenger Traffic Volume Share** for each city-pair corridor.

## 3. Dynamic Pricing Lead-Time Index Curve ($T+1$ to $T+45$)

| Lead Time | Days in Advance | APIx Index | Mean Fare (₹) | Median Fare (₹) | Volatility (CV %) | Market State |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **T+1** | 1 days | **211.90** | ₹8,159.23 | ₹7,600.00 | 36.41% | Last-Minute Surge |
| **T+7** | 7 days | **176.76** | ₹6,685.83 | ₹6,582.00 | 24.58% | Normal Dynamic Curve |
| **T+15** | 15 days | **151.06** | ₹5,752.67 | ₹5,600.00 | 30.31% | Normal Dynamic Curve |
| **T+30** | 30 days | **135.64** | ₹5,157.84 | ₹4,915.00 | 27.04% | Stable Advance Baseline |
| **T+45** | 45 days | **124.83** | ₹4,684.36 | ₹4,440.00 | 24.94% | Stable Advance Baseline |


## 4. Corridor Route Sub-Indices (Top Corridors)

| Route | DGCA Traffic Weight | Observations | Route APIx Index | Mean Fare (₹) | Price Spread (₹) | Volatility (CV) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`DEL-COK`** | 3.52% | 2,893 | **243.45** | ₹9,448.40 | ₹3,552.23 | 37.60% |
| **`DEL-BOM`** | 11.57% | 2,223 | **165.44** | ₹6,428.09 | ₹2,531.34 | 39.38% |
| **`CCU-BLR`** | 2.59% | 1,630 | **177.58** | ₹7,161.31 | ₹3,396.69 | 47.43% |
| **`BLR-DEL`** | 8.15% | 1,399 | **157.09** | ₹6,302.27 | ₹3,381.91 | 53.66% |
| **`BOM-HYD`** | 3.89% | 664 | **119.87** | ₹4,264.77 | ₹3,431.00 | 80.45% |
| **`BOM-DEL`** | 11.11% | 535 | **108.64** | ₹4,445.58 | ₹1,998.00 | 44.94% |
| **`MAA-CCU`** | 1.85% | 421 | **126.72** | ₹4,950.73 | ₹2,188.39 | 44.20% |
| **`BOM-BLR`** | 6.94% | 395 | **124.14** | ₹4,799.38 | ₹2,362.54 | 49.23% |
| **`BLR-BOM`** | 6.67% | 336 | **114.72** | ₹4,365.22 | ₹2,361.10 | 54.09% |
| **`BOM-MAA`** | 1.00% | 236 | **109.04** | ₹4,541.49 | ₹2,379.85 | 52.40% |


## 5. Carrier Sub-Indices & Market Share

| Airline Carrier | DGCA Market Share | Observations | Carrier APIx Index | Mean Fare (₹) | Volatility (CV) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **IndiGo** | 60.50% | 10,836 | **147.47** | ₹5,765.12 | 38.87% |
| **Air India** | 14.50% | 4,176 | **194.69** | ₹7,756.56 | 46.61% |
| **Vistara** | 9.50% | 1,859 | **143.95** | ₹6,004.46 | 47.96% |
| **SpiceJet** | 4.20% | 1,784 | **118.88** | ₹4,974.14 | 44.36% |
| **Multiple Carriers** | 2.00% | 1,196 | **283.75** | ₹10,902.68 | 34.13% |
| **Akasa Air** | 4.80% | 798 | **149.03** | ₹5,687.71 | 31.63% |
| **AirAsia India** | 5.50% | 433 | **143.84** | ₹5,086.36 | 40.86% |
| **AIX Connect** | 2.00% | 194 | **146.98** | ₹5,610.41 | 31.43% |
| **Multiple Carriers (Premium Economy)** | 2.00% | 13 | **310.16** | ₹11,418.85 | 15.04% |
| **Vistara (Premium Economy)** | 2.00% | 3 | **236.64** | ₹8,962.33 | 32.53% |


## 6. MoSPI Official CPI Series Comparison (2024 Base Year)

Official government CPI series for Item `07.3.3.1.2.01` (Passenger Transport by Air, Domestic):

| Year | Month | MoSPI CPI Airfare Index | MoM Inflation (%) | Augmentation Status |
| :---: | :---: | :---: | :---: | :--- |
| 2026 | July | **125.46** | 22.94% | Verified MoSPI Benchmark |
| 2026 | June | **126.09** | 10.14% | Verified MoSPI Benchmark |
| 2026 | May | **127.62** | 15.06% | Verified MoSPI Benchmark |
| 2026 | April | **123.27** | 11.11% | Verified MoSPI Benchmark |
| 2026 | March | **123.55** | 14.20% | Verified MoSPI Benchmark |
| 2026 | February | **122.43** | -7.01% | Verified MoSPI Benchmark |
| 2026 | January | **122.71** | 6.65% | Verified MoSPI Benchmark |
| 2025 | December | **124.23** | N/A | Verified MoSPI Benchmark |
| 2025 | November | **121.45** | N/A | Verified MoSPI Benchmark |
| 2025 | October | **108.19** | N/A | Verified MoSPI Benchmark |
| 2025 | September | **105.22** | N/A | Verified MoSPI Benchmark |
| 2025 | August | **112.11** | N/A | Verified MoSPI Benchmark |

