# API Documentation — Prediction Service

Base URL (local): `http://localhost:8000` · Interactive docs: `http://localhost:8000/docs`

## Endpoints

### `GET /health`

Liveness probe with model version.

```json
{"status": "ok", "model_version": "1.0.0", "model_name": "GradientBoostingClassifier"}
```

### `POST /v1/predict`

Predicts cancellation risk for 1–100 bookings.

**Request body:** `{"bookings": [ <BookingFeatures>, ... ]}`

`BookingFeatures` fields (all required, validated by Pydantic):

| Field | Type | Constraints |
| --- | --- | --- |
| no_of_adults | int | 0–10 |
| no_of_children | int | 0–10 |
| no_of_weekend_nights | int | 0–10 |
| no_of_week_nights | int | 0–30 |
| type_of_meal_plan | enum | Meal Plan 1/2/3, Not Selected |
| required_car_parking_space | 0/1 | — |
| room_type_reserved | enum | Room_Type 1–7 |
| lead_time | int | 0–500 |
| arrival_year / arrival_month / arrival_date | int | 2015–2030 / 1–12 / 1–31 |
| market_segment_type | enum | Online, Offline, Corporate, Complementary, Aviation |
| repeated_guest | 0/1 | — |
| no_of_previous_cancellations | int | 0–100 |
| no_of_previous_bookings_not_canceled | int | 0–100 |
| avg_price_per_room | float | 0–1000 (EUR) |
| no_of_special_requests | int | 0–10 |

**Response (per booking):**

- `predicted_probability` — cancellation probability [0, 1]
- `predicted_label` — Canceled / Not_Canceled at the model threshold (0.020)
- `risk_band` — low / medium / high (from `configs/business_rules.json`)
- `recommendation` — business action for the band
- `contributing_factors` — top-5 SHAP contributions (positive = pushes toward cancellation)
- `model_version`, `timestamp`

**Errors:** 422 on invalid input (constraint or enum violations); 500 on unexpected failures
(structured, no PII logged).

### `GET /v1/model-card`

Returns model metadata: name, version, approved target, features, threshold, test metrics, limitations.

## Examples

See `docs/json/api_examples.json` for full request/response pairs:

- **Low risk:** corporate, repeated guest, 3-day lead, 3 special requests → probability ~0.00, band `low`.
- **High risk:** online, first-time guest, 380-day lead, 0 special requests → probability ~0.997, band `high`;
  top factors: `lead_time` (+5.54), `market_segment_type_Online` (+1.03), `arrival_month` (−0.98).

## Logging policy

Structured logs contain request counts and latencies only. No booking payloads, identifiers,
or personal data are ever logged.

## Run locally

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000   # or: make run-api
```
