---
type: project
created: 2026-09-08
updated: 2026-09-08
---

# SIH26056 — Real-Time Airfare Price Index for India

## 1. Problem Definition & Objectives
- **Problem Statement (SIH26056)**: Development of a Real-time Airfare Price Index for India through automated collection/web scraping of airline and OTA portals for augmentation of the Consumer Price Index (CPI).
- **Core Mission**: Transform volatile, multi-dimensional domestic airfare observations into a representative, statistically rigorous, and auditable Airfare Price Index (APIx) and market intelligence platform for MoSPI / NSO / RBI.
- **Identity**: A national airfare data, statistical analysis, and intelligence platform (NOT a consumer flight booking/search engine).

## 1.1 Core PS Mandates (Handwritten Notes Specification)
1. **Data Scraping**: Automatically web-scrape real airfare data directly from Google Flights and OTA portals.
2. **Cleaning & Normalization**: Standardize airlines, airports, clean invalid fares, and de-duplicate records.
3. **Fare Component Separation**: Separate Base Fare from Taxes, User Development Fees (UDF/PSF), and Convenience Charges.
4. **Route Basket & Weights**: Select and weight routes on the basis of official DGCA passenger traffic volume.
5. **Multiple Advance Windows**: Collect prices across booking lead times (T+1, T+7, T+15, T+30, T+45).
6. **Multi-Frequency APIx**: Calculate Airfare Price Index on Daily, Weekly, and Monthly frequencies.
7. **NSO / RBI API**: Provide structured API feeds for National Statistical Office (NSO/MoSPI) and Reserve Bank of India (RBI).

## 2. Key Stakeholders
- **Primary**: MoSPI / NSO (Consumer Price Index augmentation, transportation inflation analytics).
- **Secondary**: RBI & Economic Policymakers (macroeconomic inflation tracking).
- **Domain Users**: DGCA, Ministry of Civil Aviation, aviation/statistical analysts.

## 3. Data Architecture & Pipeline
1. **Fare Sources**:
   - Airlines: IndiGo, Air India, Air India Express, Akasa Air, SpiceJet.
   - OTAs (where permitted): MakeMyTrip, Yatra, EaseMyTrip, Cleartrip, Ixigo, Goibibo.
2. **Official Reference Datasets**:
   - MoSPI / eSankhyiki (CPI inflation baselines, statistical frameworks).
   - DGCA / Ministry of Civil Aviation (passenger traffic volume for route weights, route baskets, average fare references).
   - data.gov.in (verified GoI civil aviation datasets).
3. **Observation Schema & Dimensions**:
   - Dimensions: Origin/Destination airport & city, Search timestamp, Travel date, Airline, Flight number, Fare class, Base fare, Taxes, Fees, Total fare, Availability/status, Source, Booking lead time ($T+1, T+7, T+15, T+30, T+45$), Collection method, Data quality status.
   - Dual-layer storage: Raw observation (immutable) + Normalized observation.
4. **Data Quality & Hygiene**:
   - Explicit validation pipeline (duplicate detection, impossible fares, missing values, route/timestamp checks, anomaly/outlier filtering).
   - Never silently drop records: log rejections with explicit diagnostic reasons.

## 4. Analytical & Index Engine (APIx)
- **Index Granularity**: Daily, weekly, and monthly index series with reproducible weighting and aggregation.
- **Explainability**: Complete audit trail from raw observation → normalization → route weights → final index number.
- **The 5 Guiding Questions**:
  1. *What* is happening? (Airfare Index & Market Pulse)
  2. *Where* is it happening? (Route Intelligence & Regional Pressure)
  3. *How much* is it happening? (Magnitude & Volatility Index)
  4. *Why* might it be happening? (Evidence-ba
  sed factor attribution: lead time, seasonal, capacity, demand)
  5. *What* could happen next? (Early surge warnings & What-If policy simulations)

## 5. Innovation & SIH WOW Features
- **Airfare Market Pulse**: State classification (Stable, Rising, Falling, Volatile, Under Pressure, Unusual).
- **Airfare Shock & Anomaly Detection**: Statistical change-point and outlier detection with evidence attribution.
- **Airfare DNA**: Route-level behavioral profile (volatility, lead-time sensitivity, seasonal/weekend sensitivity).
- **Deterministic Replay Mode**: Replay historical recorded observations step-by-step for resilient, fail-proof live demos.
- **What-If Policy Simulator**: Simulating route-level fare surges and measuring national index impact.
- **Confidence & Coverage Metrics**: Communicating sample size, coverage, and uncertainty on all metrics.

## 6. Development & Ethical Governance
- **Responsible Scraping**: Strict adherence to robots.txt, rate limits, terms of service, and public data APIs. Zero bypass of CAPTCHA/anti-bot mechanisms.
- **Demo Strategy**: Dual capability — live collection + deterministic replay of verified real observations.
- **Implementation Strategy**: Phased rollout (Problem understanding → Official data acquisition → Schema & Data model → Collection & Cleaning → Index Engine → Baseline Dashboard → Analytical Intelligence → Back-testing & Verification).
