# Model Card

## Overview

| Field | Value |
| --- | --- |
| Model | GradientBoostingClassifier (scikit-learn) |
| Version | 1.0.0 |
| Task | Binary classification: booking cancellation risk |
| Approved target | `booking_status` → Canceled=1 / Not_Canceled=0 |
| Approval reference | `docs/json/target_approval.json` @ 2026-09-13T20:44:07Z |
| Training data | 25,392 bookings (time-based train split, arrival-ordered) |
| Random seed | 42 (all stochastic components) |
| Decision threshold | 0.020 (cost-optimal on validation, FN:FP = 10:1) |

## Intended use

Score hotel bookings **at or after booking time** to prioritize retention actions
(reconfirmation, deposits, overbooking buffers). Output: cancellation probability in [0, 1],
a risk band (low/medium/high), and a recommended action.

## Out-of-scope uses

- Scoring before essential booking fields exist (lead time, segment, price).
- Individual guest credit/character judgments (the model predicts booking outcomes, not persons).
- Properties or markets outside the training distribution without revalidation.

## Features (16)

`no_of_adults, no_of_children, no_of_weekend_nights, no_of_week_nights, required_car_parking_space,
lead_time, repeated_guest, no_of_previous_cancellations, no_of_previous_bookings_not_canceled,
avg_price_per_room, no_of_special_requests, arrival_month, total_nights, type_of_meal_plan,
room_type_reserved, market_segment_type`

Excluded: `Booking_ID` (identifier), `booking_status` (label), `arrival_year`/`arrival_date` (split-only).

## Performance

| Split | ROC-AUC | PR-AUC | Recall @ 0.02 | Precision @ 0.02 |
| --- | --- | --- | --- | --- |
| Validation (Aug–Oct 2018) | 0.914 | 0.917 | 0.992 | 0.593 |
| Test (Oct–Dec 2018, evaluated once) | 0.865 | 0.741 | 0.964 | 0.479 |

Top factors (permutation importance): `lead_time`, `no_of_special_requests`, `avg_price_per_room`.

## Fairness and ethics

- No direct PII; no protected-attribute columns exist in the data.
- Risk scores inform operational actions on bookings, not on individuals.
- Complementary (free) bookings included per user decision; they carry a "never cancel" signal.

## Limitations and risks

- Temporal drift: high-season validation inflates metrics vs test; recalibrate periodically.
- Guest-history features require production lookups; without them, expect reduced recall.
- Cost matrix (10:1) is a documented assumption; threshold must be recomputed if it changes.
- 2017–2018 data; market behavior may have shifted since.

## Maintenance

- Retrain quarterly or on drift alerts (PSI on score distribution).
- Re-run `scripts/p4_evaluate_final_model.py` only with a fresh, never-used test split (G6).
