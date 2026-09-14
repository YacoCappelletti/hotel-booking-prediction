# Analytical Project Plan

**Scope:** End-to-end analytical project: data audit, business analysis, target proposal with user approval, machine learning, prediction API, predictive app, business dashboard, and Docker deployment.

---

## 1. Objective

You will receive a dataset. The raw dataset must be placed under `/data/raw/`. Your job is to:

1. Explore and audit the data (Phase 1).
2. Discover and quantify business value (Phase 2).
3. Propose a target variable and obtain explicit user approval (Phase 3).
4. Build a predictive model (Phase 4) — only after approval.
5. Deliver a complete solution: prediction API, predictive app, business dashboard, and Docker deployment (Phases 5–7 + Deployment).

**Core design principle:** the business analysis (Phases 1–2) and the target variable selection/proposal (Phase 3) are independent processes. The agent must never select, rank, or propose a target variable before Phase 3, and must never train a model before the user explicitly approves the target.

---

## 2. Target Variable Governance (Canonical Rules)

These rules are the **single source of truth**. Phases reference them by ID (`G1`, `G2`, ...). Do not restate or reinterpret them elsewhere.

| ID | Rule |
| --- | --- |
| **G1** | No target variable may be selected, defined, ranked, or proposed during Phase 1 or Phase 2. Business problems may be listed descriptively, but never ranked or narrowed toward a target. |
| **G2** | The target variable must be proposed in Phase 3, using as mandatory inputs: the data dictionary, the data quality report, and the business analysis. |
| **G3** | Only the **user** can approve a target. The agent records the user's decision in `/docs/json/target_approval.json`; it must **never** set `approval_status` to `approved` on its own initiative. |
| **G4** | No model training may begin until `/docs/json/target_approval.json` has `approval_status: "approved"`. Phase 4 must verify this file as its first action. |
| **G5** | Changing the approved target at any later phase requires restarting Phase 3 (a new proposal and a new explicit approval). |
| **G6** | The final model must be evaluated on the test set **exactly once**. The test set must never be used for model selection, threshold tuning, or hyperparameter optimization. |

---

## 3. Approval Workflow (Phase 3 Gate)

1. The agent completes the Phase 3 analysis and writes `/docs/json/target_proposal.json` with `approval_status: "pending_user_approval"`.
2. The agent creates `/docs/json/target_approval.json`:

```json
{
  "approved_target": null,
  "approved_problem_type": null,
  "approval_status": "pending",
  "user_comments": "",
  "approval_timestamp": null
}
```

1. The agent presents the proposal to the user and **stops execution**.
2. The user responds with one of: `approved`, `changes_requested`, or `rejected`.
3. The agent records the user's verbatim decision and a timestamp in `target_approval.json`.
4. Resolution paths:
    - `approved` → proceed to Phase 4.
    - `changes_requested` → the agent revises the proposal **within Phase 3** (updating `target_proposal.json`, resetting the approval file to `pending`) and resubmits. Repeat until `approved` or `rejected`.
    - `rejected` → Phase 3 restarts with a new direction, or the user redefines the problem. Return to Phase 1/2 inputs if needed.
5. The agent is forbidden from interpreting silence, ambiguity, or indirect responses as approval.

---

## 4. Phase Gates (Summary)

Execution must be sequential. Do not start a phase until its entry gate is satisfied.

| Gate | Transition | Entry requirement |
| --- | --- | --- |
| Gate 0 | Setup → Phase 1 | Directory structure, `requirements.txt`, `Makefile`, `.env.example`, `.gitignore` exist |
| Gate 1 | Phase 1 → Phase 2 | All Phase 1 deliverables saved; G1 respected |
| Gate 2 | Phase 2 → Phase 3 | All Phase 2 deliverables saved; G1 respected |
| Gate 3 | Phase 3 → Phase 4 | `target_approval.json` has `approval_status: "approved"` (G3, G4) |
| Gate 4 | Phase 4 → Phase 5 | Model artifacts, metadata, and model card saved; test set evaluated exactly once (G6) |
| Gate 5 | Phase 5 → Phase 6/7 | API implemented and tests passing |
| Gate 6 | All phases → Done | Docker deployment verified from a clean environment |

---

## 5. Task List

Use this checklist to execute the project in order.

### Project Setup

- [ ]  Verify that the raw dataset is available in `/data/raw/`.
- [ ]  Create the full project directory structure (see Section 8).
- [ ]  Create `requirements.txt` with pinned dependencies.
- [ ]  Create `Makefile` with the standard targets (see Section 10).
- [ ]  Create `.env.example` (see Section 11).
- [ ]  Create `.gitignore`.
- [ ]  Create `README.md` (see Section 12).

### Phase 1: Data Audit and Problem Discovery

- [ ]  Load and inspect the dataset.
- [ ]  Identify structure: rows, columns, data types.
- [ ]  Create the data dictionary (schema in Section 6.1), including PII and temporal flags per column.
- [ ]  Add data source reference if available.
- [ ]  Identify missing values, duplicates, constant columns, outliers, and data type issues.
- [ ]  Generate basic distributions and initial hypotheses.
- [ ]  Build the PII / sensitive columns inventory.
- [ ]  Identify candidate business problems or predictive opportunities, listed as **equal-weight options without ranking** (G1).
- [ ]  Write `/docs/problem_statement.md` (neutral discovery; no problem ranking, no target selection).
- [ ]  Save `/docs/data_dictionary.md` and `/docs/json/data_dictionary.json`.
- [ ]  Save `/docs/data_quality_report.md`.
- [ ]  Write `/tests/test_data.py` (dataset loads, expected columns exist, no fully-empty columns, dtypes match the dictionary).
- [ ]  Verify Gate 1: deliverables exist and G1 was respected.

### Phase 2: Business Analysis

- [ ]  Generate 10 business questions answerable with the dataset.
- [ ]  Select the 5 most important questions based on business impact, feasibility, and actionability. **This prioritization applies to business questions only — never to target candidates (G1).**
- [ ]  Justify the selection.
- [ ]  Create one Python script per selected question: `/scripts/p2_q01_<description>.py` ... `p2_q05_<description>.py`.
- [ ]  Generate per-question outputs: `/docs/snippets/p2_q0N_output.md`, `/docs/json/p2_q0N_metrics.json`, `/docs/images/p2_q0N_chart.png`.
- [ ]  Write `/docs/business_questions.md` and `/docs/json/business_questions.json`.
- [ ]  Write `/docs/business_analysis_report.md` and `/docs/json/insights.json`.
- [ ]  Draft the business recommendation logic (prediction bands → recommended actions) derived from Phase 2 insights. Save it in `/configs/business_rules.json`.
- [ ]  Verify Gate 2: deliverables exist and G1 was respected.

### Phase 3: Target Variable Proposal

- [ ]  Read all Phase 1 and Phase 2 deliverables (list in Section 6.3).
- [ ]  Identify candidate target variables.
- [ ]  Evaluate each candidate using the full criteria list (Section 6.3).
- [ ]  Select one recommended target; optionally list alternatives.
- [ ]  Determine the preliminary problem type: classification or regression.
- [ ]  Write business, technical, and data quality justification with evidence.
- [ ]  Save `/scripts/p3_target_proposal.py`, `/docs/target_proposal.md`, `/docs/json/target_proposal.json`.
- [ ]  Create `/docs/json/target_approval.json` with `approval_status: "pending"`.
- [ ]  Present the proposal and stop execution (Approval Workflow, Section 3).
- [ ]  Do not proceed until `target_approval.json` has `approval_status: "approved"`.

### Phase 4: Machine Learning Model

- [ ]  Verify `target_approval.json` has `approval_status: "approved"` (G4). Stop if not.
- [ ]  Load the approved target and problem type from the approval file.
- [ ]  Fix the global random seed from `/configs/model_config.json` in every script, split, CV strategy, and model.
- [ ]  Create a baseline model.
- [ ]  Split data into train/validation/test (70/15/15):
    - If relevant temporal columns exist, use a **time-based split** and justify it in the model report.
    - Otherwise, use a **stratified split** for classification.
- [ ]  Build preprocessing pipelines; fit them **only on the training set**.
- [ ]  Train candidate models appropriate for the problem type:
    - Regression: Linear Regression, Decision Tree Regressor, Random Forest Regressor, Gradient Boosting Regressor.
    - Classification: Logistic Regression, Decision Tree Classifier, Random Forest Classifier, Gradient Boosting Classifier.
- [ ]  If class imbalance exists: apply a mitigation strategy (class weights or resampling) and use PR-AUC as a primary validation metric.
- [ ]  Evaluate candidates with cross-validation (StratifiedKFold for classification, fixed seed).
- [ ]  Select the best model on the **validation set** using a metric aligned with the business objective.
- [ ]  Optimize the decision threshold on the **validation set** using the business cost matrix from `/configs/business_rules.json` (G6: never on test). Document the chosen threshold and its business rationale.
- [ ]  Evaluate the final model exactly once on the test set (G6).
- [ ]  Analyze feature importance globally: permutation importance or SHAP.
- [ ]  Build and persist a **local explainer** for per-prediction contributing factors:
    - SHAP TreeExplainer for tree-based models; LinearExplainer for linear models; permutation-based top-k fallback.
    - Save `/models/explainer.joblib`.
- [ ]  Save model artifacts: `/models/final_model.joblib`, `/models/preprocessor.joblib`, `/models/model_metadata.json`.
- [ ]  Save model metadata including: seed, split strategy, chosen threshold, target approval reference, and library versions.
- [ ]  Write `/docs/model_report.md`, `/docs/model_card.md`.
- [ ]  Save `/docs/json/model_performance.json`, `/docs/json/feature_importance.json`, `/docs/images/model_performance_charts.png`.
- [ ]  Write `/tests/test_model.py` (artifacts load, predictions have the expected shape, test metrics meet the documented minimums).
- [ ]  Verify Gate 4.

### Phase 5: Prediction API

- [ ]  Create the FastAPI application (`/src/api/main.py`, `schemas.py`, `predict.py`).
- [ ]  Implement `/health`, `/v1/predict`, `/v1/model-card` endpoints.
- [ ]  Add Pydantic input validation and structured error handling.
- [ ]  Add logging (never log raw PII values).
- [ ]  Add model versioning (read from `model_metadata.json`).
- [ ]  Implement per-prediction contributing factors using `/models/explainer.joblib` (top-k features by absolute contribution).
- [ ]  Implement the business recommendation in the response using the threshold bands and action mapping from `/configs/business_rules.json` and the chosen decision threshold from `model_metadata.json`.
- [ ]  Write `/docs/api_documentation.md`.
- [ ]  Save `/docs/json/api_examples.json`.
- [ ]  Write `/tests/test_api.py` (`/health` returns 200; valid prediction returns 200 with the expected schema; invalid input returns 422).
- [ ]  Verify Gate 5.

### Phase 6: Predictive App (Streamlit)

- [ ]  Create `/apps/predict_app/app.py`.
- [ ]  Add an input form for observation values.
- [ ]  Connect to the API using `API_URL` from the environment.
- [ ]  Display predicted probability or value, main contributing factors, business recommendation, and warnings for invalid inputs.
- [ ]  Write `/docs/predict_app_documentation.md`.

### Phase 7: Business Dashboard (Streamlit)

- [ ]  Create `/apps/dashboard/app.py`.
- [ ]  Add KPIs, charts for the 5 selected business questions, and filters by relevant dimensions.
- [ ]  Include clear titles, business interpretation, and recommended actions.
- [ ]  Ensure the dashboard answers: What happened? Why did it happen? What should the business do?
- [ ]  Write `/docs/dashboard_documentation.md`.

### Deployment

- [ ]  Create a single `Dockerfile` (one image, three commands).
- [ ]  Create `docker-compose.yml` with services: `api`, `predict-app`, `dashboard` (see Section 11).
- [ ]  Write `/docs/deployment_documentation.md`.
- [ ]  Verify that the project runs using Docker from a clean environment (Gate 6).

---

## 6. Phase Specifications

### 6.1 Phase 1: Data Audit and Problem Discovery

Purpose: neutral, diagnostic discovery. Deliverables feed both the business analysis and the Phase 3 target proposal.

**The data dictionary must include, per column:**

- Name, description, data type
- Possible values, missing count, unique count, example values
- Business meaning
- Usable as feature: yes / no / conditional
- Candidate target in Phase 3: factual flag only — no evaluation or ranking (Phase 3 performs the evaluation)
- Potential data leakage: yes / no / unknown + reason
- PII / sensitive: yes / no + category
- Temporal: yes / no (date, timestamp, or time-ordered field)

**The data quality report must include:**

- Rows and columns; missing values by column; duplicated rows; constant columns
- Data type issues; outliers; class imbalance if applicable
- Basic distributions; initial hypotheses
- PII / sensitive columns inventory and recommended handling (mask, exclude, or keep with justification)
- Temporal coverage of the dataset (date range, granularity), if applicable

**The problem statement must include:**

- Business problems and predictive opportunities identified, presented as **equal-weight options** — no ranking, no "most relevant" selection
- Expected business metric to impact, per problem
- Candidate problem types (classification / regression) only as preliminary hypotheses, not decisions
- Variables that relate to each problem, described descriptively without ranking
- Explicit statement: "No target variable has been selected, ranked, or proposed in this phase (G1)."

**Restrictions:** G1 applies in full. Do not train models. Do not decide the final problem type.

### 6.2 Phase 2: Business Analysis

Purpose: understand and quantify the business value extractable from the dataset, through data-backed insights.

Tasks:

1. Generate 10 business questions answerable with the dataset.
2. Select the 5 most important by business impact, feasibility, and actionability.
3. Answer each selected question with code, charts, and metrics.
4. Justify every insight with code, output, and written interpretation.

Deliverables and conventions:

```bash
/scripts/p2_q01_<description>.py   # ... through p2_q05_<description>.py
/docs/snippets/p2_q0N_output.md
/docs/json/p2_q0N_metrics.json
/docs/images/p2_q0N_chart.png
/docs/business_questions.md
/docs/json/business_questions.json
/docs/business_analysis_report.md
/docs/json/insights.json
/configs/business_rules.json
```

Each insight must contain: question, business relevance, code used, output, interpretation, and a **recommended action**.

`/configs/business_rules.json` translates Phase 2 insights into operational logic for later phases. Example schema:

```json
{
  "source": "Phase 2 insights (p2_q02, p2_q04)",
  "problem_type": "classification",
  "risk_bands": [
    {"band": "low",    "max_probability": 0.35, "recommendation": "No action needed."},
    {"band": "medium", "max_probability": 0.65, "recommendation": "Send retention offer."},
    {"band": "high",   "max_probability": 1.0,  "recommendation": "Assign account manager immediately."}
  ],
  "cost_matrix": {
    "false_negative_cost": 10,
    "false_positive_cost": 2
  }
}
```

The exact bands, thresholds, and costs must be justified by the Phase 2 insights and documented as assumptions when exact values are unknown.

**Restrictions:** G1 applies in full. Do not train predictive models. Do not propose targets.

### 6.3 Phase 3: Target Variable Proposal

Mandatory inputs:

- `/docs/data_dictionary.md` and `/docs/json/data_dictionary.json`
- `/docs/data_quality_report.md`
- `/docs/problem_statement.md`
- `/docs/business_analysis_report.md` and `/docs/json/insights.json`
- The dataset in `/data/raw/` (or `/data/processed/` if available)

Tasks:

1. Review the business problems (Phase 1) and insights (Phase 2).
2. Review the data dictionary and data quality report.
3. Identify candidate target variables.
4. Evaluate each candidate against every criterion:
    - Alignment with the business problem; business relevance; actionability
    - Availability at prediction time; potential data leakage
    - Data quality: missing values, type consistency, definition reliability, outliers, class imbalance
    - Temporal consistency; ethical or legal restrictions (check the PII inventory)
    - Feasibility for machine learning
5. Select one recommended target; optionally list alternatives.
6. Determine the preliminary problem type: classification or regression.
7. Justify the recommendation with evidence from all three input sources.
8. Present the proposal and request explicit approval (Section 3). Do not continue without it.

Deliverables:

```bash
/scripts/p3_target_proposal.py
/docs/target_proposal.md
/docs/json/target_proposal.json
/docs/json/target_approval.json
```

`/docs/target_proposal.md` must include: recommended target, alternatives, preliminary problem type, business / technical / data quality justification, evidence from each input source, assumptions, risks, limitations, data leakage checks, open questions for the user, and approval status.

`/docs/json/target_proposal.json` minimum schema:

```json
{
  "recommended_target": "",
  "alternative_targets": [],
  "problem_type": "",
  "business_justification": "",
  "technical_justification": "",
  "data_quality_justification": "",
  "data_dictionary_evidence": "",
  "data_quality_evidence": "",
  "business_analysis_evidence": "",
  "assumptions": [],
  "risks": [],
  "limitations": [],
  "data_leakage_checks": [],
  "open_questions": [],
  "approval_status": "pending_user_approval"
}
```

**Restrictions:** Do not train models. Do not create final features. Follow the Approval Workflow (Section 3) exactly (G2, G3). If no suitable target exists, report the blockers and ask the user for additional data, clarification, or problem redefinition.

### 6.4 Phase 4: Machine Learning Model

Entry gate: `target_approval.json` has `approval_status: "approved"` (G4). Verify as the first action.

Tasks:

1. Load the approved target and problem type from the approval file.
2. Justify the classification vs. regression decision in the model report.
3. Fix the random seed (from `/configs/model_config.json`) in every stochastic component.
4. Create a baseline model (majority class / mean predictor).
5. Split: train 70% / validation 15% / test 15%.
    - Time-based split if temporal columns are relevant (justify in the report).
    - Stratified split otherwise (classification).
6. Build preprocessing pipelines; fit only on train; apply to validation and test.
7. Train candidates:
    - Regression: Linear Regression, Decision Tree Regressor, Random Forest Regressor, Gradient Boosting Regressor.
    - Classification: Logistic Regression, Decision Tree Classifier, Random Forest Classifier, Gradient Boosting Classifier.
8. If imbalanced: class weights or resampling; PR-AUC as primary validation metric.
9. Cross-validate candidates (fixed seed, StratifiedKFold for classification).
10. Select the best model on validation, using the business-aligned metric.
11. Optimize the decision threshold on validation using the cost matrix from `/configs/business_rules.json`. Record the threshold. Never use the test set for this (G6).
12. Evaluate the final model exactly once on test (G6).
13. Global importance: permutation importance or SHAP.
14. Local explanations: build the explainer (SHAP TreeExplainer / LinearExplainer; permutation top-k fallback), persist as `/models/explainer.joblib`.

Metrics to report:

- Classification: Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC (if imbalanced), confusion matrix, calibration analysis if probabilities matter to the business.
- Regression: MAE, RMSE, MAPE, R².

Deliverables:

```bash
/scripts/p4_train_baseline.py
/scripts/p4_train_candidate_models.py
/scripts/p4_evaluate_final_model.py
/models/final_model.joblib
/models/preprocessor.joblib
/models/explainer.joblib
/models/model_metadata.json
/docs/model_report.md
/docs/model_card.md
/docs/json/model_performance.json
/docs/json/feature_importance.json
/docs/images/model_performance_charts.png
/tests/test_model.py
```

`model_metadata.json` must include: model name, model version, approved target, problem type, target approval reference (path + approval timestamp), training timestamp, random seed, feature list, preprocessing summary, split strategy, chosen decision threshold, validation metrics, test metrics, library versions, notes and limitations.

**Restrictions:** G4, G5, G6 apply in full. Do not change the approved target without restarting Phase 3.

### 6.5 Phase 5: Prediction API

Requirements:

- Endpoints: `/health`, `/v1/predict`, `/v1/model-card`.
- Pydantic input validation; consistent error handling; structured logging (no raw PII in logs).
- Model versioning read from `model_metadata.json`.
- `/v1/predict` response must include: predicted probability or value, main contributing factors (top-k from the persisted explainer), risk level and business recommendation (from `configs/business_rules.json` bands + the model's decision threshold), model version, timestamp.

Deliverables:

```bash
/src/api/main.py
/src/api/schemas.py
/src/api/predict.py
/docs/api_documentation.md
/docs/json/api_examples.json
/tests/test_api.py
```

### 6.6 Phase 6: Predictive App (Streamlit)

The app must:

- Provide a form for entering observation values.
- Call the API at `API_URL` (from environment).
- Show predicted probability or value, main contributing factors, and business recommendation.
- Show warnings for invalid inputs before calling the API.

Deliverables:

```bash
/apps/predict_app/app.py
/docs/predict_app_documentation.md
```

### 6.7 Phase 7: Business Dashboard (Streamlit)

The dashboard must include:

- KPIs, charts for the 5 selected business questions, filters by relevant dimensions.
- Clear titles, business interpretation, and recommended actions (from Phase 2 insights).

It must answer: **What happened? Why did it happen? What should the business do?**

Deliverables:

```bash
/apps/dashboard/app.py
/docs/dashboard_documentation.md
```

---

## 7. Deployment

- **Single image strategy:** one `Dockerfile` builds one image containing all dependencies and code. The three services differ only by their run command:

| Service | Command | Port |
| --- | --- | --- |
| `api` | `uvicorn src.api.main:app --host 0.0.0.0 --port 8000` | 8000 |
| `predict-app` | `streamlit run apps/predict_app/app.py --server.port 8501` | 8501 |
| `dashboard` | `streamlit run apps/dashboard/app.py --server.port 8502` | 8502 |
- The `api` service must expose a healthcheck on `/health`.
- The Streamlit apps reach the API via `API_URL` (set to `http://api:8000` inside the compose network).
- Model artifacts are available inside the container (copied into the image or mounted read-only).
- Deliverables: `Dockerfile`, `docker-compose.yml`, `/docs/deployment_documentation.md`.
- Verify the full stack from a clean environment before closing the project (Gate 6).

---

## 8. Directory Structure

```bash
project/
│
├── README.md
├── PLAN.md
├── requirements.txt
├── Makefile
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── external/
│
├── configs/
│   ├── project_config.json
│   ├── model_config.json        # seed, split ratios, CV folds, metric
│   └── business_rules.json      # risk bands, recommendations, cost matrix
│
├── scripts/
│   ├── p1_data_audit.py
│   ├── p1_data_dictionary.py
│   ├── p2_q01_<description>.py
│   ├── p2_q02_<description>.py
│   ├── p2_q03_<description>.py
│   ├── p2_q04_<description>.py
│   ├── p2_q05_<description>.py
│   ├── p3_target_proposal.py
│   ├── p4_train_baseline.py
│   ├── p4_train_candidate_models.py
│   └── p4_evaluate_final_model.py
│
├── src/
│   ├── __init__.py
│   ├── data/
│   ├── features/
│   ├── model/
│   └── api/
│       ├── __init__.py
│       ├── main.py
│       ├── schemas.py
│       └── predict.py
│
├── apps/
│   ├── predict_app/
│   │   └── app.py
│   └── dashboard/
│       └── app.py
│
├── models/
│   ├── final_model.joblib
│   ├── preprocessor.joblib
│   ├── explainer.joblib
│   └── model_metadata.json
│
├── tests/
│   ├── test_data.py
│   ├── test_model.py
│   └── test_api.py
│
└── docs/
    ├── data_dictionary.md
    ├── data_quality_report.md
    ├── problem_statement.md
    ├── business_questions.md
    ├── business_analysis_report.md
    ├── target_proposal.md
    ├── model_report.md
    ├── model_card.md
    ├── api_documentation.md
    ├── predict_app_documentation.md
    ├── dashboard_documentation.md
    ├── deployment_documentation.md
    │
    ├── snippets/
    │   ├── p2_q01_output.md
    │   ├── p2_q02_output.md
    │   ├── p2_q03_output.md
    │   ├── p2_q04_output.md
    │   └── p2_q05_output.md
    │
    ├── json/
    │   ├── data_dictionary.json
    │   ├── business_questions.json
    │   ├── insights.json
    │   ├── p2_q01_metrics.json
    │   ├── p2_q02_metrics.json
    │   ├── p2_q03_metrics.json
    │   ├── p2_q04_metrics.json
    │   ├── p2_q05_metrics.json
    │   ├── target_proposal.json
    │   ├── target_approval.json
    │   ├── model_performance.json
    │   ├── feature_importance.json
    │   └── api_examples.json
    │
    └── images/
        ├── p2_q01_chart.png
        ├── p2_q02_chart.png
        ├── p2_q03_chart.png
        ├── p2_q04_chart.png
        ├── p2_q05_chart.png
        └── model_performance_charts.png
```

---

## 9. Configuration Files

- `/configs/project_config.json`: paths, environment names, general settings.
- `/configs/model_config.json`: random seed (default `42`), split ratios, CV folds, primary metric, model hyperparameter grids.
- `/configs/business_rules.json`: risk bands, recommendation mapping, cost matrix (authored in Phase 2, consumed in Phases 4 and 5).

All scripts must read configuration from these files. No hardcoded paths or seeds.

---

## 10. Makefile Targets

The `Makefile` must include at minimum:

```bash
make setup              # create virtualenv and install pinned requirements
make data-audit         # run Phase 1 scripts
make business-analysis  # run Phase 2 scripts
make target-proposal    # run Phase 3 script
make train              # run Phase 4: baseline → candidates → final evaluation
make test               # run pytest on /tests
make run-api            # start FastAPI locally
make run-predict-app    # start the Streamlit predictive app
make run-dashboard      # start the Streamlit dashboard
make docker-build       # build the Docker image
make docker-up          # start all services via docker-compose
make docker-down        # stop all services
```

---

## 11. Environment Variables

`.env.example` must contain:

```bash
API_HOST=0.0.0.0
API_PORT=8000
API_URL=http://localhost:8000     # used by Streamlit apps; set to <http://api:8000> in docker-compose
MODEL_PATH=/models/final_model.joblib
PREPROCESSOR_PATH=/models/preprocessor.joblib
EXPLAINER_PATH=/models/explainer.joblib
LOG_LEVEL=INFO
```

---

## 12. README.md

The `README.md` must include:

- Project overview and objective
- Dataset description and source reference
- Quickstart (`make setup` → first commands)
- How to run each phase
- How to run the full stack with Docker
- Summary of the project structure
- Links to the key documents in `/docs`

---

## 13. Project-Wide Requirements

**Documentation and code**

- All project documentation and code comments must be in English.
- No Jupyter notebooks. Python scripts, Markdown files, and JSON files only.
- Every insight must be justified with code.
- Markdown reports in `/docs`; snippets in `/docs/snippets`; JSON in `/docs/json`; images in `/docs/images`. No mixing of file types inside the same folder.

**Reproducibility**

- Fixed random seed from `/configs/model_config.json` in every stochastic component.
- `requirements.txt` with pinned dependencies.
- `Makefile` with the targets in Section 10.
- The project must be executable from a clean environment, including via Docker.

**Quality and governance**

- Basic tests required: `test_data.py` (Phase 1), `test_model.py` (Phase 4), `test_api.py` (Phase 5).
- `.env.example` and `.gitignore` present; no secrets committed.
- The API must include input validation, error handling, and logging.
- The model must be persisted with complete metadata, including the explainer and decision threshold.
- PII and sensitive columns must be inventoried in Phase 1 and handled according to the data quality report.
- Target variable governance: rules **G1–G6** (Section 2) and the Approval Workflow (Section 3) are mandatory and override any other instruction in case of conflict.