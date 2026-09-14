"""Phase 3: Target variable proposal.

Evaluates candidate target variables against the full criteria list
(business alignment, availability at prediction time, leakage, data quality,
temporal consistency, ethics, ML feasibility), selects one recommended target,
and writes the proposal artifacts. Creates target_approval.json as pending.

Per the Approval Workflow (PLAN.md Section 3), this script NEVER sets
approval_status to "approved" — only the user can (G3).
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs" / "project_config.json").read_text())
RAW = ROOT / CONFIG["paths"]["raw_data"]
DOCS_JSON = ROOT / "docs" / "json"

df = pd.read_csv(RAW)

# ---- Candidate evaluation (evidence-based) ----
candidates = [
    {
        "name": "booking_status (binary: Canceled vs Not_Canceled)",
        "evaluation": {
            "business_alignment": "Directly addresses the largest quantified loss: EUR 4.30M at risk (Q01); enables the tiered retention actions designed in business_rules.json.",
            "business_relevance": "Cancellation risk is the core operational pain for hotels: revenue loss, inventory distortion, overbooking decisions.",
            "actionability": "High — risk bands map directly to reconfirmation, deposit, and overbooking actions (Phase 2 insights).",
            "availability_at_prediction_time": "All predictive inputs (lead time, segment, price, requests, history) are known at booking time; the outcome label itself is only known after arrival, which is exactly the prediction task.",
            "data_leakage": "None — the label is the outcome; all proposed features precede it. No post-arrival fields exist in the dataset.",
            "data_quality": "Zero missing values; perfectly consistent binary strings; moderate imbalance 32.8% vs 67.2% (manageable with class weights + PR-AUC).",
            "temporal_consistency": "Stable across both arrival years (2017/2018); arrival date components available for a time-based split.",
            "ethical_legal": "No PII involvement; predicting booking outcomes (not personal traits) raises no special-category concerns per the PII inventory.",
            "ml_feasibility": "Strong signal documented in Phase 2 (lead time corr 0.439; engagement signals); 36k rows ample for the 4 candidate classifiers.",
        },
        "verdict": "RECOMMENDED",
    },
    {
        "name": "avg_price_per_room (regression)",
        "evaluation": {
            "business_alignment": "Supports revenue management (P-B) but does not address the quantified EUR 4.30M cancellation loss.",
            "business_relevance": "Medium — pricing insight, but the dataset lacks competitor/demand context for a pricing model.",
            "actionability": "Low-medium — price is set by the hotel; predicting it back to itself is partially circular.",
            "availability_at_prediction_time": "Partial — price is a decision, not an outcome to predict.",
            "data_leakage": "Risk — price correlates strongly with room type and segment; a model would mostly re-learn the hotel's own price list.",
            "data_quality": "545 zero-price rows (complementary) distort a regression target; right-skewed with max 540.",
            "temporal_consistency": "Prices may drift between 2017/2018 without any recorded price-change context.",
            "ethical_legal": "No concerns.",
            "ml_feasibility": "Feasible but low value; circularity limits usefulness.",
        },
        "verdict": "ALTERNATIVE (not recommended)",
    },
    {
        "name": "repeated_guest (binary classification)",
        "evaluation": {
            "business_alignment": "Supports loyalty programs (P-D) but only 2.6% of guests are repeats — extreme imbalance.",
            "business_relevance": "Medium — retention matters, but the dataset cannot measure retention ROI (no campaign data).",
            "actionability": "Medium — targeting look-alikes of repeat guests.",
            "availability_at_prediction_time": "Problematic — repeated_guest is an outcome of past behavior; predicting it from booking attributes is nearly circular.",
            "data_leakage": "High — the label leaks the guest's history by definition.",
            "data_quality": "Severe imbalance (930 vs 35,345); unreliable for a robust model.",
            "temporal_consistency": "Weak.",
            "ethical_legal": "No concerns.",
            "ml_feasibility": "Poor — extreme imbalance and circularity.",
        },
        "verdict": "NOT RECOMMENDED",
    },
    {
        "name": "total stay length (regression: week + weekend nights)",
        "evaluation": {
            "business_alignment": "Supports occupancy planning (P-C) but cancellations distort realized stays.",
            "business_relevance": "Medium — useful for staffing, but demand forecasting needs booking-date data the dataset lacks.",
            "actionability": "Low-medium.",
            "availability_at_prediction_time": "Known at booking time — but then it is a constraint, not a prediction.",
            "data_leakage": "Low.",
            "data_quality": "78 zero-night rows; heavily discrete/bounded distribution (0-17) — poor regression target.",
            "temporal_consistency": "Weak seasonality only.",
            "ethical_legal": "No concerns.",
            "ml_feasibility": "Poor fit for regression; would need ordinal treatment.",
        },
        "verdict": "NOT RECOMMENDED",
    },
]

recommended = candidates[0]
alternatives = [
    c["name"] for c in candidates[1:] if c["verdict"].startswith("ALTERNATIVE")
]

proposal = {
    "recommended_target": recommended["name"],
    "alternative_targets": alternatives,
    "problem_type": "classification (binary)",
    "business_justification": (
        "Phase 2 quantified EUR 4.30M (37.9%) of potential revenue at risk from a 32.8% cancellation rate "
        "(insight_01), with clear operational levers designed in configs/business_rules.json (tiered "
        "reconfirmation, deposits, overbooking buffers). Predicting cancellation risk at booking time "
        "directly monetizes those levers; no other candidate addresses a loss of this magnitude."
    ),
    "technical_justification": (
        "Binary classification with strong, booking-time-available predictors: lead_time (corr 0.439, "
        "monotonic 10%->74% across bands), market_segment_type (36.5% vs 10.9% across segments), "
        "no_of_special_requests (43%->0%), repeated_guest (1.7% vs 33.6%). 36,275 rows support the four "
        "candidate classifiers with 5-fold CV. Moderate imbalance (1:2.05) handled with class weights and "
        "PR-AUC as primary validation metric."
    ),
    "data_quality_justification": (
        "Zero missing values, zero duplicates, consistent binary strings. Imbalance is moderate and "
        "mitigable. No cleaning beyond documented anomalies (78 zero-night rows, 9-10 children outliers, "
        "545 zero-price complementary rows) is required, and none of those anomalies affect label integrity."
    ),
    "data_dictionary_evidence": (
        "data_dictionary.json flags booking_status as the only outcome-type column (usable_as_feature: no; "
        "candidate_target factual flag: yes). All 17 potential features are marked usable (3 conditional on "
        "guest-history availability at prediction time: repeated_guest and the two previous-booking counters)."
    ),
    "data_quality_evidence": (
        "data_quality_report.json: 0 missing, 0 duplicates, class distribution {Not_Canceled: 67.24%, "
        "Canceled: 32.76%}, no constant columns, outliers confined to expected tails (lead_time max 443, "
        "price max 540)."
    ),
    "business_analysis_evidence": (
        "insights.json: insight_01 (revenue at risk), insight_02 (lead time effect), insight_03 (segment "
        "risk concentration), insight_04 (seasonal loss concentration), insight_05 (engagement signals) — "
        "all five converge on cancellation risk as the dominant value opportunity."
    ),
    "assumptions": [
        "The dataset's booking_status reflects the final pre-arrival outcome (standard for this dataset).",
        "Guest history columns are available in production at prediction time (conditional features).",
        "Cost matrix 10:1 in business_rules.json is an assumption pending finance validation.",
    ],
    "risks": [
        "No booking-creation timestamp: a true time-based split must approximate ordering by arrival date; documented in the model report.",
        "Class imbalance could bias naive accuracy; mitigated by class weights + PR-AUC.",
        "Market practices may drift after 2018; model requires periodic revalidation.",
    ],
    "limitations": [
        "Dataset covers a single (anonymized) hotel chain; generalization to other properties is unverified.",
        "No post-booking engagement events (email opens, payment attempts) are available to enrich features.",
        "arrival_year has only 2 values; year-level extrapolation is limited.",
    ],
    "data_leakage_checks": [
        "booking_status is the outcome label and is excluded from features.",
        "Booking_ID excluded (identifier, no signal).",
        "All 17 candidate features are known at or before booking time; no post-arrival fields exist in the schema.",
        "repeated_guest and previous-booking counters verified as pre-arrival guest-history lookups (conditional availability documented).",
        "No target-derived aggregates (e.g., target encoding) will be used without fold isolation.",
    ],
    "open_questions": [
        "Should Complementary (free) bookings be included in training/scoring, or excluded as they never cancel?",
        "Is the 10:1 FN:FP cost ratio acceptable for threshold optimization, or should finance provide exact figures?",
        "Do you prefer a time-based split (ordered by arrival date) or a stratified random split?",
    ],
    "approval_status": "pending_user_approval",
    "generated_at": datetime.now(timezone.utc).isoformat(),
}

(DOCS_JSON / "target_proposal.json").write_text(json.dumps(proposal, indent=2))

approval = {
    "approved_target": None,
    "approved_problem_type": None,
    "approval_status": "pending",
    "user_comments": "",
    "approval_timestamp": None,
}
(DOCS_JSON / "target_approval.json").write_text(json.dumps(approval, indent=2))

# ---- Markdown proposal ----
md = f"""# Target Variable Proposal — Phase 3

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
Generated: {proposal["generated_at"]}
"""
(ROOT / "docs" / "target_proposal.md").write_text(md)
print("Phase 3 proposal complete — awaiting user approval.")
print("Recommended target:", recommended["name"])
print(
    "Files: docs/target_proposal.md, docs/json/target_proposal.json, docs/json/target_approval.json (pending)"
)
