# Target Variable Proposal — Phase 3

> **Status: PENDING USER APPROVAL.** Per the Approval Workflow (PLAN.md Section 3) and rule G3,
> only the user can approve this target. No model training may begin until
> `docs/json/target_approval.json` has `approval_status: "approved"` (G4).

## Recommended target

**`booking_status` → binary label: `Canceled` (1) vs `Not_Canceled` (0)**

**Preliminary problem type:** binary classification.

## Alternatives considered

1. `avg_price_per_room` (regression) — circular (price is a decision), 545 zero-price rows, low business value vs the quantified cancellation loss.
2. `repeated_guest` (classification) — extreme imbalance (2.6%), label leaks guest history by definition.
3. Total stay length (regression) — discrete bounded distribution, 78 zero-night rows, weak actionability.

## Candidate evaluation (full criteria)

| Criterion | booking_status (RECOMMENDED) | avg_price_per_room | repeated_guest | stay length |
| --- | --- | --- | --- | --- |
| Business alignment | Direct: EUR 4.30M at risk (Q01) | Medium | Medium | Medium |
| Availability at prediction time | All inputs known at booking | Partial (circular) | Problematic | Constraint, not prediction |
| Data leakage | None | Risk (re-learns price list) | High | Low |
| Data quality | 0 missing, binary, moderate imbalance | 545 zeros, skew | 1:38 imbalance | 78 zeros, discrete |
| Temporal consistency | Stable 2017-2018 | Price drift unrecorded | Weak | Weak |
| Ethical/legal | No concerns (no PII) | None | None | None |
| ML feasibility | Strong signal, 36k rows | Low value | Poor | Poor fit |

## Justification

### Business
Phase 2 quantified the loss: **EUR 4.30M (37.9%) of potential revenue at risk**, with operational
levers already designed in `configs/business_rules.json`. Predicting cancellation risk at booking
time directly monetizes tiered reconfirmation, deposits, and overbooking buffers.

### Technical
Strong booking-time predictors documented in Phase 2: `lead_time` (corr 0.439, monotonic 10%→74%),
`market_segment_type` (36.5% vs 10.9%), `no_of_special_requests` (43%→0%), `repeated_guest`
(1.7% vs 33.6%). 36,275 rows support 4 candidate classifiers with 5-fold CV. Moderate imbalance
(1:2.05) → class weights + PR-AUC as primary metric.

### Data quality
Zero missing values, zero duplicates, consistent labels. Documented anomalies (zero-night rows,
children outliers, zero-price complementary rows) do not affect label integrity.

## Evidence from mandatory inputs

- **Data dictionary** (`docs/json/data_dictionary.json`): `booking_status` is the only outcome-type column; 17 usable features (3 conditional on guest-history availability).
- **Data quality report** (`docs/json/data_quality_report.json`): 0 missing, 0 duplicates, class split 67.2%/32.8%, outliers in expected tails.
- **Business analysis** (`docs/json/insights.json`): all five insights converge on cancellation risk as the dominant value opportunity.

## Data leakage checks

1. `booking_status` excluded from features (it IS the label).
2. `Booking_ID` excluded (identifier).
3. All candidate features known at/before booking time; no post-arrival fields exist in the schema.
4. Guest-history columns verified as pre-arrival lookups (conditional availability documented).
5. No target-derived aggregates without fold isolation.

## Assumptions, risks, limitations

- **Assumptions:** final pre-arrival outcome semantics; guest history available in production; 10:1 cost ratio pending finance validation.
- **Risks:** no booking-creation timestamp (time-based split approximated by arrival date); imbalance; 2018-era drift.
- **Limitations:** single anonymized hotel chain; no engagement-event features; only 2 arrival years.

## Open questions for the user

1. Include Complementary (free) bookings in training/scoring, or exclude them (they never cancel)?
2. Is the 10:1 FN:FP cost ratio acceptable for threshold optimization?
3. Time-based split (by arrival date) or stratified random split?

## Approval status

`pending_user_approval` — awaiting explicit user decision (`approved` / `changes_requested` / `rejected`).
Generated: 2026-09-13T20:40:25.772434+00:00
