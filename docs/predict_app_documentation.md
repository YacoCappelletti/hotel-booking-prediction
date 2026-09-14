# Predict App Documentation — Phase 6

**Location:** `apps/predict_app/app.py` · **Port:** 8501 · **Framework:** Streamlit

## Purpose

Operational tool for hotel staff to score a single booking's cancellation risk before arrival
and receive the business-recommended action.

## Usage

1. Fill the form with the booking's details (party size, nights, meal plan, room type, lead time,
   arrival date, market segment, guest history, price, special requests).
2. Client-side warnings appear for invalid profiles (0 guests or 0 nights) **before** calling the API;
   the predict button is disabled until fixed.
3. Press **Predict cancellation risk**.

## Output

- **Cancellation probability** (0–100%).
- **Risk band** (low / medium / high) color-coded.
- **Recommended action** from `configs/business_rules.json`:
  - low → no action needed
  - medium → proactive reconfirmation + flexible-date incentive
  - high → immediate retention workflow (personal contact, deposit, inventory review)
- **Main contributing factors:** top-5 SHAP contributions with direction (→ cancels / → keeps).

## API connection

- Reads `API_URL` from the environment (default `http://localhost:8000`; set to `http://api:8000`
  inside Docker Compose).
- Calls `POST /v1/predict` with the form values; errors from the API are surfaced with `st.error`.

## Run locally

```bash
make run-api        # terminal 1
make run-predict-app  # terminal 2 → http://localhost:8501
```
