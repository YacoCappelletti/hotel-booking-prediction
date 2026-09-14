# Model Report — Phase 4

## 1. Gate verification

- `docs/json/target_approval.json` had `approval_status: "approved"` before any training (G4 ✓).
- Approved target: **`booking_status` (Canceled=1 vs Not_Canceled=0)**, problem type: **classification**.
- Test set evaluated **exactly once**, by `scripts/p4_evaluate_final_model.py` only (G6 ✓). The training
  script never touches test data; `model_metadata.json` guards re-evaluation with an assertion.

## 2. Problem type decision

Binary classification (user-approved in Phase 3). `booking_status` is a binary outcome; regression
alternatives were rejected in the proposal (`docs/target_proposal.md`).

## 3. Data and split

- **Split: time-based, ordered by arrival date** (user-approved option 3 in Phase 3).
  - Train: 25,392 rows (2017 → mid-2018), positive rate 30.2%
  - Validation: 5,441 rows (Aug–Oct 2018), positive rate **46.4%**
  - Test: 5,442 rows (Oct–Dec 2018), positive rate 30.8%
- Justification: with no booking-creation timestamp, arrival date is the best temporal proxy;
  a time-based split mimics production (train on the past, score the future).
- **Documented drift:** validation covers the high season with a materially higher cancellation
  rate than train. This is realistic and explains the validation→test metric gap.
- `arrival_year` and `arrival_date` are used for the split only, excluded from features (year drift,
  day-of-month noise). `arrival_month` is kept (seasonality signal).

## 4. Features and preprocessing

- 13 numeric + 3 categorical features; engineered `total_nights`.
- Rare categories grouped: `Meal Plan 3 → Other`, `Room_Type 3 → Other`.
- Numeric: median imputer + standard scaler; categorical: most-frequent imputer + one-hot
  (`handle_unknown="ignore"`). **Fit on train only.**
- Excluded: `Booking_ID` (identifier), `booking_status` (label).

## 5. Baseline

Majority-class baseline (always "Not_Canceled"): validation accuracy 0.536, F1 0.0 — trivially
useless for the business objective, as expected under the 46.4% validation positive rate.

## 6. Candidate models and cross-validation

StratifiedKFold (5 folds, shuffle, seed 42) on train; class imbalance handled with
`class_weight="balanced"` (LR/DT/RF) or balanced `sample_weight` (GB). Primary CV metric: PR-AUC.

| Model | Best params | CV PR-AUC (mean) | Val PR-AUC | Val ROC-AUC |
| --- | --- | --- | --- | --- |
| LogisticRegression | C=1.0 | 0.728 | 0.875 | 0.894 |
| DecisionTreeClassifier | depth=15, leaf=20 | 0.864 | 0.832 | 0.840 |
| RandomForestClassifier | 400 trees, depth=None, leaf=2 | 0.907 | 0.907 | 0.906 |
| **GradientBoostingClassifier** | 400 est, lr=0.1, depth=5 | 0.908 | **0.917** | **0.914** |

**Selected: GradientBoostingClassifier** (highest validation PR-AUC, the business-aligned metric
for imbalanced data).

## 7. Decision threshold (validation only, G6)

Optimized on validation with the approved cost matrix (FN=10, FP=1 from `configs/business_rules.json`):

- **Chosen threshold: 0.020** — expected cost 1,920 vs 8,820 at the default 0.5 (4.6x reduction).
- Business rationale: with FN 10x costlier than FP, the optimal operating point accepts many false
  alarms (precision 0.59) to catch 99.2% of true cancellations (recall). Every flagged booking
  receives a graded action via the risk bands, so false alarms mostly trigger cheap reconfirmations.
- Bands from `configs/business_rules.json` (low < 0.25, medium < 0.55, high ≥ 0.55) provide the
  graded response; the threshold is the "act vs no action" cut.

## 8. Global feature importance (permutation, validation)

Top drivers: `lead_time` (0.373), `no_of_special_requests` (0.100), `avg_price_per_room` (0.075),
`market_segment_type_Offline` (0.011), `no_of_weekend_nights` (0.007) — consistent with Phase 2
insights. Full list: `docs/json/feature_importance.json`.

## 9. Local explanations

SHAP TreeExplainer persisted at `models/explainer.joblib` (with feature names), fitted on a 500-row
train background sample. The API uses it for top-k contributing factors per prediction.

## 10. Final test evaluation (exactly once)

| Metric | Validation | Test |
| --- | --- | --- |
| ROC-AUC | 0.914 | **0.865** |
| PR-AUC | 0.917 | **0.741** |
| Accuracy (thr 0.02) | 0.680 | 0.666 |
| Precision | 0.593 | 0.479 |
| Recall | 0.992 | 0.964 |
| F1 | 0.742 | 0.640 |
| Brier | 0.126 | 0.164 |
| Confusion (tn/fp/fn/tp) | 1194/1720/20/2507 | 2005/1760/60/1617 |

**Interpretation:** the validation→test gap is explained by temporal drift: validation covers the
high-cancellation season (Aug–Oct, 46.4% positives) while test covers Oct–Dec (30.8%). The model
still catches 96.4% of true cancellations in unseen future data at the cost-oriented threshold.
Calibration degrades out-of-season (Brier 0.164); recalibration on rolling windows is recommended
before production use.

## 11. Notes and limitations

- Single anonymized hotel; 2017–2018 only; no booking-creation timestamps.
- Guest-history features assume production lookups exist.
- Threshold is cost-policy-dependent; recompute if the cost matrix changes.
