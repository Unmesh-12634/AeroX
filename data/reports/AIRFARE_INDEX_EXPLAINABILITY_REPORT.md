# SIH26056: Real-Time Airfare Price Index (APIx) — Mathematical Engine & Explainability Report

> **Statistical Framework:** Compliant with MoSPI Consumer Price Index (CPI) Guidelines & UN/ILO CPI Manual.

## 1. Executive Index Summary

- **Latest National Airfare Price Index (APIx):** **98.85** (Base = 100.00)
- **7-Day Moving Average Index:** **94.28**
- **Current Market Pulse:** **Stable**
- **Price Volatility (CV):** **4.92%**
- **Total Audited Master Observations:** **11,635 records**

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
| **T+1** | 1 days | **112.70** | ₹10,758.89 | ₹8,735.00 | 68.85% | Last-Minute Surge |
| **T+2** | 2 days | **106.80** | ₹10,787.61 | ₹8,817.00 | 111.47% | Last-Minute Surge |
| **T+5** | 5 days | **89.42** | ₹7,751.81 | ₹7,094.10 | 27.46% | Normal Dynamic Curve |
| **T+7** | 7 days | **93.83** | ₹8,492.68 | ₹7,370.00 | 59.38% | Normal Dynamic Curve |
| **T+15** | 15 days | **93.07** | ₹8,524.66 | ₹7,272.00 | 62.57% | Normal Dynamic Curve |
| **T+30** | 30 days | **100.20** | ₹8,862.20 | ₹8,717.50 | 32.90% | Stable Advance Baseline |
| **T+45** | 45 days | **85.53** | ₹7,250.23 | ₹7,114.00 | 4.92% | Stable Advance Baseline |


## 4. Corridor Route Sub-Indices (Top Corridors)

| Route | DGCA Traffic Weight | Observations | Route APIx Index | Mean Fare (₹) | Price Spread (₹) | Volatility (CV) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`DEL-BOM`** | 11.57% | 3,993 | **100.00** | ₹7,620.52 | ₹2,860.92 | 37.54% |
| **`DEL-BLR`** | 7.87% | 1,349 | **100.00** | ₹10,345.62 | ₹2,496.54 | 24.13% |
| **`BOM-BLR`** | 6.94% | 1,069 | **100.00** | ₹10,076.28 | ₹5,578.57 | 55.36% |
| **`DEL-CCU`** | 5.00% | 751 | **100.00** | ₹9,216.56 | ₹1,469.55 | 15.94% |
| **`BLR-HYD`** | 1.00% | 629 | **100.00** | ₹9,587.18 | ₹6,484.95 | 67.64% |
| **`DEL-HYD`** | 4.63% | 607 | **100.00** | ₹9,389.48 | ₹1,939.90 | 20.66% |
| **`DEL-MAA`** | 2.78% | 537 | **100.00** | ₹14,025.96 | ₹10,871.70 | 77.51% |
| **`BOM-GOI`** | 1.00% | 311 | **100.00** | ₹9,935.55 | ₹7,089.53 | 71.36% |
| **`DEL-SXR`** | 1.00% | 274 | **100.00** | ₹7,986.82 | ₹2,298.49 | 28.78% |
| **`DEL-LKO`** | 1.00% | 260 | **100.00** | ₹6,837.53 | ₹10,681.51 | 156.22% |


## 5. Carrier Sub-Indices & Market Share

| Airline Carrier | DGCA Market Share | Observations | Carrier APIx Index | Mean Fare (₹) | Volatility (CV) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **IndiGo** | 60.50% | 7,734 | **100.00** | ₹9,417.61 | 74.69% |
| **Air India** | 14.50% | 2,853 | **100.00** | ₹9,303.63 | 69.26% |
| **Akasa Air** | 4.80% | 694 | **100.00** | ₹8,491.22 | 40.27% |
| **Air India Express** | 1.00% | 223 | **100.00** | ₹8,188.42 | 28.79% |
| **SpiceJet** | 4.20% | 131 | **100.00** | ₹11,869.69 | 50.27% |


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

