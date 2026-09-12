# SIH26056: Real-Time Airfare Price Index for India — Data Audit & Classification Report

> **Strict Policy Enforced:** 100% Real Workspace Data. Zero synthetic / fabricated observations.

## Executive Summary

- **Total Raw Files Audited:** 10
- **Total Standardized Flight Observations in Master Dataset:** 13,994
- **Active Carrier Records:** 9,409 (67.2%)
- **Defunct Carrier Records (Jet Airways, GoAir, etc.):** 4,585 (32.8%)

## 1. File-by-File Detailed Audit

### 📄 `cpi_2018.xlsx`
- **Classification:** A. Official CPI/reference data
- **Legitimate Role:** Official MoSPI Airfare CPI Benchmark (2024 Base Year) - Truth series for index validation & CPI augmentation
- **Dimensions:** 19 rows × 15 columns
- **Exact Duplicate Rows:** 0 (0.00%)
- **Date Range:** `January 2025 to July 2026`
- **Airlines (0):** N/A
- **Origins (0):** N/A
- **Destinations (0):** N/A
- **Routes (0):** N/A
- **Price/Index Stats (₹):** Min: ₹102.05 | Max: ₹131.66 | Mean: ₹117.66 | Median: ₹121.45
- **Feature Availability Matrix:**
  * Travel Date Present: ✅ Yes
  * Collection Timestamp Present: ❌ No (NOT_AVAILABLE)
  * Fare/Cabin Class Present: ❌ No
  * Taxes/Fees Split: ❌ No (Only all-inclusive total fare)
  * Seat Availability / Load: ❌ No
- **Important Limitations:**
  * ⚠️ Monthly macro index (Airfare series); lacks flight-level observations

---

### 📄 `flight_data_BOM_BLR.csv`
- **Classification:** B. Real flight/fare observation data
- **Legitimate Role:** Single-day route snapshot with flight codes (BOM-BLR) - Tests flight code parsing & modern airline mapping
- **Dimensions:** 90 rows × 8 columns
- **Exact Duplicate Rows:** 20 (22.22%)
- **Date Range:** `NOT_AVAILABLE`
- **Airlines (5):** Air India, AirAsia, IndiGo, Akasa Air, Vistara
- **Origins (2):** Mumbai, Bengaluru
- **Destinations (2):** Bengaluru, Mumbai
- **Routes (2):** Bengaluru -> Mumbai, Mumbai -> Bengaluru
- **Price/Index Stats (₹):** Min: ₹2,307.0 | Max: ₹20,581.0 | Mean: ₹6,186.19 | Median: ₹4,621.0
- **Feature Availability Matrix:**
  * Travel Date Present: ❌ No
  * Collection Timestamp Present: ❌ No (NOT_AVAILABLE)
  * Fare/Cabin Class Present: ❌ No
  * Taxes/Fees Split: ❌ No (Only all-inclusive total fare)
  * Seat Availability / Load: ❌ No
- **Important Limitations:**
  * ⚠️ Lacks collection/search timestamp (cannot calculate search-to-departure lead time directly)
  * ⚠️ No separate base fare vs taxes/surcharges split (all-inclusive total price only)
  * ⚠️ No seat inventory / remaining seat count info
  * ⚠️ Small snapshot sample (59-100 rows per route) without explicit travel date column

---

### 📄 `flight_data_DEL_BLR.csv`
- **Classification:** B. Real flight/fare observation data
- **Legitimate Role:** Single-day route snapshot with flight codes (DEL-BLR) - Tests flight code parsing & modern airline mapping
- **Dimensions:** 95 rows × 8 columns
- **Exact Duplicate Rows:** 20 (21.05%)
- **Date Range:** `NOT_AVAILABLE`
- **Airlines (6):** Akasa Air, AirAsia, IndiGo, Air India, SpiceJet, Vistara
- **Origins (2):** New Delhi, Bengaluru
- **Destinations (2):** Bengaluru, New Delhi
- **Routes (2):** Bengaluru -> New Delhi, New Delhi -> Bengaluru
- **Price/Index Stats (₹):** Min: ₹5,230.0 | Max: ₹13,399.0 | Mean: ₹6,509.29 | Median: ₹5,717.0
- **Feature Availability Matrix:**
  * Travel Date Present: ❌ No
  * Collection Timestamp Present: ❌ No (NOT_AVAILABLE)
  * Fare/Cabin Class Present: ❌ No
  * Taxes/Fees Split: ❌ No (Only all-inclusive total fare)
  * Seat Availability / Load: ❌ No
- **Important Limitations:**
  * ⚠️ Lacks collection/search timestamp (cannot calculate search-to-departure lead time directly)
  * ⚠️ No separate base fare vs taxes/surcharges split (all-inclusive total price only)
  * ⚠️ No seat inventory / remaining seat count info
  * ⚠️ Small snapshot sample (59-100 rows per route) without explicit travel date column

---

### 📄 `flight_data_DEL_BOM.csv`
- **Classification:** B. Real flight/fare observation data
- **Legitimate Role:** Single-day route snapshot with flight codes (DEL-BOM) - Tests flight code parsing & trunk route validation
- **Dimensions:** 100 rows × 8 columns
- **Exact Duplicate Rows:** 20 (20.00%)
- **Date Range:** `NOT_AVAILABLE`
- **Airlines (5):** Akasa Air, IndiGo, Air India, SpiceJet, Vistara
- **Origins (2):** New Delhi, Mumbai
- **Destinations (2):** Mumbai, New Delhi
- **Routes (2):** Mumbai -> New Delhi, New Delhi -> Mumbai
- **Price/Index Stats (₹):** Min: ₹4,745.0 | Max: ₹10,539.0 | Mean: ₹5,450.81 | Median: ₹4,780.0
- **Feature Availability Matrix:**
  * Travel Date Present: ❌ No
  * Collection Timestamp Present: ❌ No (NOT_AVAILABLE)
  * Fare/Cabin Class Present: ❌ No
  * Taxes/Fees Split: ❌ No (Only all-inclusive total fare)
  * Seat Availability / Load: ❌ No
- **Important Limitations:**
  * ⚠️ Lacks collection/search timestamp (cannot calculate search-to-departure lead time directly)
  * ⚠️ No separate base fare vs taxes/surcharges split (all-inclusive total price only)
  * ⚠️ No seat inventory / remaining seat count info
  * ⚠️ Small snapshot sample (59-100 rows per route) without explicit travel date column

---

### 📄 `flight_data_DEL_CCU.csv`
- **Classification:** B. Real flight/fare observation data
- **Legitimate Role:** Single-day route snapshot with flight codes (DEL-CCU) - Tests flight code parsing on East corridor
- **Dimensions:** 60 rows × 8 columns
- **Exact Duplicate Rows:** 14 (23.33%)
- **Date Range:** `NOT_AVAILABLE`
- **Airlines (4):** IndiGo, Vistara, SpiceJet, Air India
- **Origins (2):** New Delhi, Kolkata
- **Destinations (2):** Kolkata, New Delhi
- **Routes (2):** Kolkata -> New Delhi, New Delhi -> Kolkata
- **Price/Index Stats (₹):** Min: ₹5,408.0 | Max: ₹15,298.0 | Mean: ₹6,269.1 | Median: ₹6,020.0
- **Feature Availability Matrix:**
  * Travel Date Present: ❌ No
  * Collection Timestamp Present: ❌ No (NOT_AVAILABLE)
  * Fare/Cabin Class Present: ❌ No
  * Taxes/Fees Split: ❌ No (Only all-inclusive total fare)
  * Seat Availability / Load: ❌ No
- **Important Limitations:**
  * ⚠️ Lacks collection/search timestamp (cannot calculate search-to-departure lead time directly)
  * ⚠️ No separate base fare vs taxes/surcharges split (all-inclusive total price only)
  * ⚠️ No seat inventory / remaining seat count info
  * ⚠️ Small snapshot sample (59-100 rows per route) without explicit travel date column

---

### 📄 `flight_data_DEL_HYD.csv`
- **Classification:** B. Real flight/fare observation data
- **Legitimate Role:** Single-day route snapshot with flight codes (DEL-HYD) - Tests flight code parsing on South corridor
- **Dimensions:** 59 rows × 8 columns
- **Exact Duplicate Rows:** 14 (23.73%)
- **Date Range:** `NOT_AVAILABLE`
- **Airlines (5):** Akasa Air, IndiGo, Air India, Vistara, SpiceJet
- **Origins (2):** New Delhi, Hyderabad
- **Destinations (2):** Hyderabad, New Delhi
- **Routes (2):** Hyderabad -> New Delhi, New Delhi -> Hyderabad
- **Price/Index Stats (₹):** Min: ₹4,548.0 | Max: ₹7,606.0 | Mean: ₹5,129.95 | Median: ₹4,986.0
- **Feature Availability Matrix:**
  * Travel Date Present: ❌ No
  * Collection Timestamp Present: ❌ No (NOT_AVAILABLE)
  * Fare/Cabin Class Present: ❌ No
  * Taxes/Fees Split: ❌ No (Only all-inclusive total fare)
  * Seat Availability / Load: ❌ No
- **Important Limitations:**
  * ⚠️ Lacks collection/search timestamp (cannot calculate search-to-departure lead time directly)
  * ⚠️ No separate base fare vs taxes/surcharges split (all-inclusive total price only)
  * ⚠️ No seat inventory / remaining seat count info
  * ⚠️ Small snapshot sample (59-100 rows per route) without explicit travel date column

---

### 📄 `data.csv`
- **Classification:** B. Real flight/fare observation data
- **Legitimate Role:** Multi-day real flight fare observations across 6 major hubs (Feb 2022) with IATA codes & Cabin Class
- **Dimensions:** 2,907 rows × 9 columns
- **Exact Duplicate Rows:** 29 (1.00%)
- **Date Range:** `14-02-2022 to 28-02-2022`
- **Airlines (6):** IndiGo , Vistara , Air India , SpiceJet , AirAsia India , Go First 
- **Origins (6):** BOM, DEL, BLR, HYD, CCU, MAA
- **Destinations (6):** DEL, BOM, BLR, HYD, CCU, MAA
- **Routes (10):** BLR -> BOM, BOM -> BLR, BOM -> CCU, BOM -> DEL, BOM -> HYD, BOM -> MAA, CCU -> BOM, DEL -> BOM
- **Price/Index Stats (₹):** Min: ₹1,828.0 | Max: ₹14,282.0 | Mean: ₹4,101.22 | Median: ₹3,199.5
- **Feature Availability Matrix:**
  * Travel Date Present: ✅ Yes
  * Collection Timestamp Present: ❌ No (NOT_AVAILABLE)
  * Fare/Cabin Class Present: ✅ Yes
  * Taxes/Fees Split: ❌ No (Only all-inclusive total fare)
  * Seat Availability / Load: ❌ No
- **Important Limitations:**
  * ⚠️ Lacks collection/search timestamp (cannot calculate search-to-departure lead time directly)
  * ⚠️ No separate base fare vs taxes/surcharges split (all-inclusive total price only)
  * ⚠️ No seat inventory / remaining seat count info

---

### 📄 `Data_Train.csv`
- **Classification:** C. Historical flight-price data
- **Legitimate Role:** Historical flight price training dataset (March-June 2019) across Indian metro pairs for pre-COVID baseline
- **Dimensions:** 10,683 rows × 7 columns
- **Exact Duplicate Rows:** 2,001 (18.73%)
- **Date Range:** `01/03/2019 to 9/06/2019`
- **Airlines (12):** IndiGo, Air India, Jet Airways, SpiceJet, Multiple carriers, GoAir, Vistara, Air Asia, Vistara Premium economy, Jet Airways Business
- **Origins (5):** Banglore, Kolkata, Delhi, Chennai, Mumbai
- **Destinations (6):** New Delhi, Banglore, Cochin, Kolkata, Delhi, Hyderabad
- **Routes (6):** Banglore -> Delhi, Banglore -> New Delhi, Chennai -> Kolkata, Delhi -> Cochin, Kolkata -> Banglore, Mumbai -> Hyderabad
- **Price/Index Stats (₹):** Min: ₹1,759.0 | Max: ₹79,512.0 | Mean: ₹9,087.06 | Median: ₹8,372.0
- **Feature Availability Matrix:**
  * Travel Date Present: ✅ Yes
  * Collection Timestamp Present: ❌ No (NOT_AVAILABLE)
  * Fare/Cabin Class Present: ✅ Yes
  * Taxes/Fees Split: ❌ No (Only all-inclusive total fare)
  * Seat Availability / Load: ❌ No
- **Important Limitations:**
  * ⚠️ Lacks collection/search timestamp (cannot calculate search-to-departure lead time directly)
  * ⚠️ No separate base fare vs taxes/surcharges split (all-inclusive total price only)
  * ⚠️ No seat inventory / remaining seat count info
  * ⚠️ Pre-COVID 2019 data; contains 36% defunct Jet Airways flights and GoAir

---

### 📄 `processed_data.csv`
- **Classification:** D. Processed/derived data
- **Legitimate Role:** Pre-encoded feature matrix of Data_Train.csv - Derived ML dataset (contains label encodings)
- **Dimensions:** 10,683 rows × 12 columns
- **Exact Duplicate Rows:** 2,001 (18.73%)
- **Date Range:** `March 2019 to June 2019`
- **Airlines (12):** IndiGo, Air India, Jet Airways, SpiceJet, Multiple carriers, GoAir, Vistara, Air Asia, Vistara Premium economy, Jet Airways Business
- **Origins (5):** Banglore, Kolkata, Delhi, Chennai, Mumbai
- **Destinations (5):** Delhi, Banglore, Cochin, Kolkata, Hyderabad
- **Routes (5):** Banglore -> Delhi, Chennai -> Kolkata, Delhi -> Cochin, Kolkata -> Banglore, Mumbai -> Hyderabad
- **Price/Index Stats (₹):** Min: ₹1,759.0 | Max: ₹79,512.0 | Mean: ₹9,087.06 | Median: ₹8,372.0
- **Feature Availability Matrix:**
  * Travel Date Present: ✅ Yes
  * Collection Timestamp Present: ❌ No (NOT_AVAILABLE)
  * Fare/Cabin Class Present: ❌ No
  * Taxes/Fees Split: ❌ No (Only all-inclusive total fare)
  * Seat Availability / Load: ❌ No
- **Important Limitations:**
  * ⚠️ Lacks collection/search timestamp (cannot calculate search-to-departure lead time directly)
  * ⚠️ No separate base fare vs taxes/surcharges split (all-inclusive total price only)
  * ⚠️ No seat inventory / remaining seat count info
  * ⚠️ Pre-COVID 2019 data; contains 36% defunct Jet Airways flights and GoAir

---

### 📄 `DomPaxTraffic.csv`
- **Classification:** A. Official CPI/reference data
- **Legitimate Role:** DGCA Domestic passenger traffic & seat load factor history (2005-2012) for macro volume context
- **Dimensions:** 7 rows × 8 columns
- **Exact Duplicate Rows:** 0 (0.00%)
- **Date Range:** `2005-06 to 2011-12`
- **Airlines (0):** N/A
- **Origins (0):** N/A
- **Destinations (0):** N/A
- **Routes (0):** N/A
- **Feature Availability Matrix:**
  * Travel Date Present: ✅ Yes
  * Collection Timestamp Present: ❌ No (NOT_AVAILABLE)
  * Fare/Cabin Class Present: ❌ No
  * Taxes/Fees Split: ❌ No (Only all-inclusive total fare)
  * Seat Availability / Load: ❌ No
- **Important Limitations:**
  * ⚠️ Lacks collection/search timestamp (cannot calculate search-to-departure lead time directly)
  * ⚠️ No separate base fare vs taxes/surcharges split (all-inclusive total price only)
  * ⚠️ No seat inventory / remaining seat count info
  * ⚠️ Historical 2005-2012 macro table; lacks city-pair route granularity

---

## 2. Dataset Classification & Role Matrix

| File Name | Category | Date Era | Core Role in SIH26056 | Recommended For Core Index? |
| :--- | :--- | :---: | :--- | :---: |
| `cpi_2018.xlsx` | **A. Official CPI/reference data** | 2025–2026 | Official MoSPI Airfare CPI (2024 Base Year) benchmark series | **YES (Primary Ground Truth)** |
| `data.csv` | **B. Real flight/fare observation** | Feb 2022 | Post-COVID real observations across 6 major Indian hubs | **YES (Primary Modern Sample)** |
| `flight_data_*.csv` (5 files) | **B. Real flight/fare observation** | Modern snapshot | Real airline flight codes (`QP`, `6E`, `AI`, `UK`) for parser validation | **YES (Test Fixture / Micro-sample)** |
| `Data_Train.csv` | **C. Historical flight-price** | Mar–Jun 2019 | Pre-COVID historical baseline for backtesting long-term trends | **YES (Historical Baseline Only)** |
| `processed_data.csv` | **D. Processed/derived data** | 2019 Derived | Encoded ML features of Data_Train | **NO (Redundant to Data_Train)** |
| `DomPaxTraffic.csv` | **A. Official Reference data** | 2005–2012 | Macro passenger traffic volume context | **REFERENCE ONLY (Annual aggregate)** |

## 3. Proposed Master Airfare Schema

The master schema is constructed **exclusively from fields that exist in the real datasets**. Fields marked `NOT_AVAILABLE` are preserved as nulls without invention:

| Field Name | Field Type | Source Origin | Description / Real Availability |
| :--- | :--- | :--- | :--- |
| `record_id` | Derived | System | Unique deterministic identifier (`REC_000001`) |
| `source_file` | Derived | File Metadata | Provenance tracking (`data.csv`, `Data_Train.csv`, etc.) |
| `dataset_tier` | Derived | System | Classification tag (`2022_real_observations`, `2019_historical_precovid`) |
| `travel_date` | Directly Observed / Standardized | `Date`, `Date_of_Journey` | Standardized ISO-8601 Date (`YYYY-MM-DD`) |
| `airline_standardized` | Standardized | `Company`, `Airline`, `FlightName` | Clean airline name (e.g. `IndiGo`, `Air India`, `Akasa Air`) |
| `airline_raw` | Directly Observed | Raw string | Unmodified carrier string |
| `flight_number` | Directly Observed | `FlightCode` | Real flight code (e.g., `QP 1409`, `6E 2284`) — `None` if absent |
| `origin_iata` | Standardized | `Origin`, `Source`, `DepartingCity` | 3-letter IATA code (`DEL`, `BOM`, `BLR`, `CCU`, `HYD`, `MAA`, `COK`) |
| `dest_iata` | Standardized | `Destination`, `ArrivingCity` | 3-letter IATA code |
| `route` | Derived | Origin + Dest | Standardized route pair (`DEL-BOM`, `BLR-DEL`) |
| `departure_time` | Directly Observed | `Departure Time`, `Dep_Time`, `DepartingTime` | Flight departure time string |
| `arrival_time` | Directly Observed | `Arrival Time`, `ArrivingTime` | Flight arrival time string |
| `duration_minutes` | Transformed | `Duration Time`, `Duration` | Total flight duration converted to integer minutes |
| `cabin_class` | Directly Observed / Standardized | `Cabin Class`, `Class` | `Economy` or `Business` |
| `total_fare_inr` | Transformed | `Flight Price`, `Price` | Clean numeric fare in Indian Rupees (₹) |
| `base_fare_inr` | `NOT_AVAILABLE` | N/A | **Null (No real dataset separates base fare)** |
| `taxes_fees_inr` | `NOT_AVAILABLE` | N/A | **Null (No real dataset separates taxes)** |
| `search_timestamp` | `NOT_AVAILABLE` | N/A | **Null (No real dataset records search timestamp)** |
| `lead_time_days` | `NOT_AVAILABLE` | N/A | **Null (Cannot compute without search timestamp)** |
| `is_defunct_carrier` | Derived | Airline check | Boolean flag: `True` for Jet Airways, GoAir, Go First, Trujet |
