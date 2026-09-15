# SIH26056: Real-Time Airfare Price Index (APIx) — Mathematical Engine & Explainability Report

> **Statistical Framework:** Compliant with MoSPI Consumer Price Index (CPI) Guidelines & UN/ILO CPI Manual.

## 1. Executive Index Summary

- **Latest National Airfare Price Index (APIx):** **99.46** (Base = 100.00)
- **7-Day Moving Average Index:** **94.77**
- **Current Market Pulse:** **Stable**
- **Price Volatility (CV):** **4.92%**
- **Total Audited Master Observations:** **13,575 records**

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
| **T+1** | 1 days | **111.29** | ₹10,464.78 | ₹8,703.00 | 67.84% | Last-Minute Surge |
| **T+2** | 2 days | **107.80** | ₹10,787.61 | ₹8,817.00 | 111.47% | Last-Minute Surge |
| **T+5** | 5 days | **90.27** | ₹7,751.81 | ₹7,094.10 | 27.46% | Normal Dynamic Curve |
| **T+7** | 7 days | **93.89** | ₹8,397.46 | ₹7,353.00 | 57.35% | Normal Dynamic Curve |
| **T+15** | 15 days | **94.18** | ₹8,504.13 | ₹7,370.00 | 59.19% | Normal Dynamic Curve |
| **T+30** | 30 days | **101.15** | ₹8,862.20 | ₹8,717.50 | 32.90% | Stable Advance Baseline |
| **T+45** | 45 days | **86.34** | ₹7,250.23 | ₹7,114.00 | 4.92% | Stable Advance Baseline |


## 4. Corridor Route Sub-Indices (Top Corridors)

| Route | DGCA Traffic Weight | Observations | Route APIx Index | Mean Fare (₹) | Price Spread (₹) | Volatility (CV) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`DEL-BOM`** | 11.57% | 4,388 | **100.00** | ₹7,561.83 | ₹2,793.37 | 36.94% |
| **`DEL-BLR`** | 7.87% | 1,571 | **100.00** | ₹10,298.23 | ₹2,448.60 | 23.78% |
| **`BOM-BLR`** | 6.94% | 1,266 | **100.00** | ₹9,686.49 | ₹5,255.44 | 54.26% |
| **`DEL-CCU`** | 5.00% | 901 | **100.00** | ₹9,174.67 | ₹1,528.09 | 16.66% |
| **`DEL-HYD`** | 4.63% | 775 | **100.00** | ₹9,373.59 | ₹1,939.43 | 20.69% |
| **`BLR-HYD`** | 1.00% | 736 | **100.00** | ₹9,292.69 | ₹6,327.90 | 68.10% |
| **`DEL-MAA`** | 2.78% | 660 | **100.00** | ₹13,851.74 | ₹10,738.32 | 77.52% |
| **`BOM-GOI`** | 1.00% | 405 | **100.00** | ₹9,492.28 | ₹6,475.17 | 68.22% |
| **`DEL-PNQ`** | 1.00% | 397 | **100.00** | ₹7,544.59 | ₹1,061.14 | 14.06% |
| **`DEL-SXR`** | 1.00% | 344 | **100.00** | ₹7,973.35 | ₹2,239.50 | 28.09% |


## 5. Carrier Sub-Indices & Market Share

| Airline Carrier | DGCA Market Share | Observations | Carrier APIx Index | Mean Fare (₹) | Volatility (CV) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **IndiGo** | 60.50% | 8,693 | **100.00** | ₹9,318.20 | 73.48% |
| **Air India** | 14.50% | 3,512 | **100.00** | ₹9,127.33 | 64.86% |
| **Akasa Air** | 4.80% | 886 | **100.00** | ₹8,381.13 | 38.80% |
| **Air India Express** | 1.00% | 318 | **100.00** | ₹8,035.91 | 28.56% |
| **SpiceJet** | 4.20% | 166 | **100.00** | ₹11,659.40 | 51.14% |


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

