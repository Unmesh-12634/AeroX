# ✈️ AEROX — India Airfare Intelligence Platform
## 🚀 Overview

**AEROX** is an end-to-end **India Airfare Intelligence Platform** developed for **Smart India Hackathon 2026 — Problem Statement SIH26056: Real-Time Airfare Price Index for India Smart Automation**.

Airfare prices change rapidly and vary according to route, airline, travel date, booking lead time, demand, seasonality, taxes, fees, availability, and other market factors. At the same time, airfare observations are fragmented across airlines, online travel portals, public aviation datasets, and other data sources.

AEROX addresses this problem by building a complete and reproducible data pipeline that transforms fragmented airfare observations into:

- A representative **India Airfare Price Index**
- Route-level airfare intelligence
- Booking lead-time analytics
- Airline comparisons
- Anomaly detection
- Data-quality metrics
- Historical trends
- Backtesting and validation
- API-ready analytical data
- An interactive web dashboard

AEROX is **not a flight booking platform** and is not intended to replace existing travel portals.

Instead, it acts as an **aviation data and market-intelligence layer**.

---

# 🎯 Problem Statement

### SIH26056

**Real-Time Airfare Price Index for India Smart Automation**

Airfare prices in India are dynamic and fragmented. Different sources may report different prices for the same route, while prices can change significantly according to booking lead time, travel date, airline, availability, demand, and other factors.

The objective is to develop a reproducible statistical pipeline that:

1. Collects airfare observations.
2. Cleans and normalizes the observations.
3. Performs data-quality validation.
4. Constructs a representative Airfare Price Index.
5. Produces daily, weekly, and monthly trends.
6. Provides route and lead-time analytics.
7. Detects unusual fare movements.
8. Supports historical analysis and backtesting.
9. Exposes analytical results through APIs.
10. Provides an intuitive dashboard for users.

---

# 💡 Our Solution

AEROX converts fragmented airfare observations into a structured analytical system.

### Core workflow

```text
Airline / OTA / Public Data Sources
                ↓
       Scheduled Collection
                ↓
           Raw Data Store
                ↓
       Cleaning & Normalization
                ↓
         Data Quality Checks
                ↓
       Airfare Index Engine
                ↓
     Historical / Analytical Store
                ↓
       Analytics & Intelligence
                ↓
             FastAPI
                ↓
         React Dashboard
