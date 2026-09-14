# Business Dashboard Documentation — Phase 7

**Location:** `apps/dashboard/app.py` · **Port:** 8502 · **Framework:** Streamlit

## Purpose

Executive view of the cancellation problem built on the dataset, structured to answer the three
dashboard questions:

1. **What happened?** — KPIs: bookings, cancellation rate, revenue at risk (EUR), average booking value.
2. **Why did it happen?** — four evidence charts mirroring the Phase 5 business questions:
   - Cancellation rate by lead-time band (Q02: 10% → 74%)
   - Cancellation rate by market segment (Q03: Online risk concentration)
   - Monthly lost revenue + cancellation rate (Q04: seasonal losses)
   - Cancellation rate by special requests (Q05: engagement is protective)
3. **What should the business do?** — action table mapping each signal to its recommended action
   (deposits for long-lead, prepayment for online, seasonal buffers, engagement nudges, risk-score
   integration via the Predict app).

## Filters

Sidebar filters by **arrival year**, **arrival month**, and **market segment**; all KPIs and charts
recompute on the filtered data. Empty selections show a warning instead of errors.

## Data source

Reads `data/raw/hotel_reservations.csv` directly (cached with `@st.cache_data`). Derived columns:
`cancel` (0/1), `revenue` (price × nights), `lost_revenue`.

## Run locally

```bash
make run-dashboard   # → http://localhost:8502
```
