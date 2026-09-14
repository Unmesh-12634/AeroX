# SIH26056: Real-Time Airfare Price Index (APIx) — Mathematical Engine & Explainability Report

> **Statistical Framework:** Compliant with MoSPI Consumer Price Index (CPI) Guidelines & UN/ILO CPI Manual.

## 1. Executive Index Summary

- **Latest National Airfare Price Index (APIx):** **98.83** (Base = 100.00)
- **7-Day Moving Average Index:** **94.36**
- **Current Market Pulse:** **Stable**
- **Price Volatility (CV):** **4.92%**
- **Total Audited Master Observations:** **10,388 records**

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
| **T+1** | 1 days | **113.49** | ₹10,868.88 | ₹8,817.00 | 70.35% | Last-Minute Surge |
| **T+2** | 2 days | **107.05** | ₹10,787.61 | ₹8,817.00 | 111.47% | Last-Minute Surge |
| **T+5** | 5 days | **89.29** | ₹7,716.51 | ₹7,094.10 | 27.08% | Normal Dynamic Curve |
| **T+7** | 7 days | **93.79** | ₹8,469.53 | ₹7,327.00 | 60.09% | Normal Dynamic Curve |
| **T+15** | 15 days | **93.17** | ₹8,522.42 | ₹7,261.00 | 64.07% | Normal Dynamic Curve |
| **T+30** | 30 days | **100.44** | ₹8,862.20 | ₹8,717.50 | 32.90% | Stable Advance Baseline |
| **T+45** | 45 days | **85.74** | ₹7,250.23 | ₹7,114.00 | 4.92% | Stable Advance Baseline |


## 4. Corridor Route Sub-Indices (Top Corridors)

| Route | DGCA Traffic Weight | Observations | Route APIx Index | Mean Fare (₹) | Price Spread (₹) | Volatility (CV) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`DEL-BOM`** | 11.57% | 3,784 | **100.00** | ₹7,625.65 | ₹2,877.42 | 37.73% |
| **`DEL-BLR`** | 7.87% | 1,195 | **100.00** | ₹10,044.85 | ₹2,079.24 | 20.70% |
| **`BOM-BLR`** | 6.94% | 938 | **100.00** | ₹10,401.85 | ₹5,863.76 | 56.37% |
| **`DEL-CCU`** | 5.00% | 701 | **100.00** | ₹9,224.58 | ₹1,500.79 | 16.27% |
| **`BLR-HYD`** | 1.00% | 518 | **100.00** | ₹9,680.21 | ₹6,641.24 | 68.61% |
| **`DEL-HYD`** | 4.63% | 500 | **100.00** | ₹9,196.45 | ₹1,232.01 | 13.40% |
| **`DEL-MAA`** | 2.78% | 372 | **100.00** | ₹14,311.16 | ₹10,999.06 | 76.86% |
| **`BOM-GOI`** | 1.00% | 244 | **100.00** | ₹11,006.69 | ₹7,567.16 | 68.75% |
| **`BOM-HYD`** | 3.89% | 241 | **100.00** | ₹11,861.26 | ₹16,577.43 | 139.76% |
| **`DEL-LKO`** | 1.00% | 239 | **100.00** | ₹6,867.51 | ₹10,963.88 | 159.65% |


## 5. Carrier Sub-Indices & Market Share

| Airline Carrier | DGCA Market Share | Observations | Carrier APIx Index | Mean Fare (₹) | Volatility (CV) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **IndiGo** | 60.50% | 7,190 | **100.00** | ₹9,377.41 | 74.92% |
| **Air India** | 14.50% | 2,388 | **100.00** | ₹9,322.80 | 73.78% |
| **Akasa Air** | 4.80% | 565 | **100.00** | ₹8,507.20 | 40.80% |
| **Air India Express** | 1.00% | 140 | **100.00** | ₹8,063.59 | 25.96% |
| **SpiceJet** | 4.20% | 105 | **100.00** | ₹12,683.57 | 47.87% |


## 6. MoSPI Official CPI Series Comparison (2024 Base Year)

Official government CPI series for Item `07.3.3.1.2.01` (Passenger Transport by Air, Domestic):

| Year | Month | MoSPI CPI Airfare Index | MoM Inflation (%) | Augmentation Status |
| :---: | :---: | :---: | :---: | :--- |
| 2026 | July | **134.43** | 30.18% | Verified MoSPI Benchmark |
| 2026 | July | **119.60** | 18.12% | Verified MoSPI Benchmark |
| 2026 | July | **125.46** | 22.94% | Verified MoSPI Benchmark |
| 2026 | July | **97.37** | 41.06% | Verified MoSPI Benchmark |
| 2026 | July | **97.37** | 41.06% | Verified MoSPI Benchmark |
| 2026 | July | **97.37** | 41.06% | Verified MoSPI Benchmark |
| 2026 | July | **56.60** | -35.57% | Verified MoSPI Benchmark |
| 2026 | July | **56.60** | -35.57% | Verified MoSPI Benchmark |
| 2026 | July | **56.60** | -35.57% | Verified MoSPI Benchmark |
| 2026 | July | **130.27** | -6.79% | Verified MoSPI Benchmark |
| 2026 | July | **130.27** | -6.79% | Verified MoSPI Benchmark |
| 2026 | July | **130.27** | -6.79% | Verified MoSPI Benchmark |

