# SIH26056: Real-Time Airfare Price Index (APIx) — Mathematical Engine & Explainability Report

> **Statistical Framework:** Compliant with MoSPI Consumer Price Index (CPI) Guidelines & UN/ILO CPI Manual.

## 1. Executive Index Summary

- **Latest National Airfare Price Index (APIx):** **149.70** (Base = 100.00)
- **7-Day Moving Average Index:** **202.54**
- **Current Market Pulse:** **Surging / Under Pressure**
- **Price Volatility (CV):** **23.89%**
- **Total Audited Master Observations:** **35,131 records**

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
| **T+1** | 1 days | **226.01** | ₹8,755.51 | ₹7,900.00 | 54.84% | Last-Minute Surge |
| **T+2** | 2 days | **251.85** | ₹11,244.02 | ₹8,817.00 | 116.71% | Last-Minute Surge |
| **T+7** | 7 days | **183.85** | ₹6,981.62 | ₹6,576.00 | 41.59% | Normal Dynamic Curve |
| **T+15** | 15 days | **158.74** | ₹6,119.86 | ₹5,600.00 | 52.16% | Normal Dynamic Curve |
| **T+30** | 30 days | **133.07** | ₹4,985.40 | ₹4,770.00 | 24.35% | Stable Advance Baseline |
| **T+45** | 45 days | **123.00** | ₹4,607.55 | ₹4,400.00 | 23.89% | Stable Advance Baseline |


## 4. Corridor Route Sub-Indices (Top Corridors)

| Route | DGCA Traffic Weight | Observations | Route APIx Index | Mean Fare (₹) | Price Spread (₹) | Volatility (CV) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`DEL-COK`** | 3.52% | 2,681 | **241.16** | ₹9,370.24 | ₹3,557.39 | 37.96% |
| **`DEL-BOM`** | 11.57% | 1,758 | **167.90** | ₹6,610.35 | ₹3,057.81 | 46.26% |
| **`CCU-BLR`** | 2.59% | 1,520 | **170.45** | ₹6,853.31 | ₹3,273.13 | 47.76% |
| **`BLR-DEL`** | 8.15% | 1,383 | **156.22** | ₹6,254.26 | ₹3,310.01 | 52.92% |
| **`BOM-HYD`** | 3.89% | 835 | **142.16** | ₹5,659.31 | ₹8,446.89 | 149.26% |
| **`BOM-BLR`** | 6.94% | 685 | **175.64** | ₹7,391.40 | ₹5,581.48 | 75.51% |
| **`BOM-DEL`** | 11.11% | 565 | **111.81** | ₹4,579.21 | ₹2,038.92 | 44.53% |
| **`DEL-BLR`** | 7.87% | 492 | **240.26** | ₹8,918.62 | ₹1,597.83 | 17.92% |
| **`MAA-CCU`** | 1.85% | 461 | **130.14** | ₹5,083.66 | ₹2,177.92 | 42.84% |
| **`BLR-BOM`** | 6.67% | 365 | **118.66** | ₹4,483.15 | ₹2,273.95 | 50.72% |


## 5. Carrier Sub-Indices & Market Share

| Airline Carrier | DGCA Market Share | Observations | Carrier APIx Index | Mean Fare (₹) | Volatility (CV) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **IndiGo** | 60.50% | 18,032 | **158.24** | ₹6,281.67 | 65.12% |
| **Air India** | 14.50% | 5,884 | **191.08** | ₹7,624.96 | 60.18% |
| **SpiceJet** | 4.20% | 2,550 | **124.20** | ₹5,145.33 | 40.23% |
| **Vistara** | 9.50% | 2,288 | **148.79** | ₹6,117.81 | 44.85% |
| **Akasa Air** | 4.80% | 1,467 | **149.42** | ₹5,769.63 | 38.99% |
| **Multiple Carriers** | 2.00% | 1,100 | **282.34** | ₹10,856.09 | 34.36% |
| **AirAsia India** | 5.50% | 400 | **139.69** | ₹4,936.59 | 41.10% |
| **AIX Connect** | 2.00% | 388 | **146.89** | ₹5,610.41 | 31.38% |
| **Multiple Carriers (Premium Economy)** | 2.00% | 12 | **310.05** | ₹11,431.33 | 15.68% |
| **Vistara (Premium Economy)** | 2.00% | 3 | **236.49** | ₹8,962.33 | 32.53% |


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

