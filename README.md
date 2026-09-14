# Hotel Booking Cancellations Prediction

End-to-end analytical project: data audit, business analysis, target variable proposal with user approval, machine learning, prediction API, predictive app, business dashboard, and Docker deployment.

## Objective

Predict hotel booking cancellations to reduce revenue loss from last-minute cancellations and enable proactive overbooking/inventory management.

## Dataset

- File: `data/raw/hotel_reservations.csv` (~36,275 bookings, 19 columns)
- Source: [Hotel Reservations dataset (Kaggle)](https://www.kaggle.com/datasets/ahsan81/hotel-reservations-classification-dataset)
- Covers bookings with arrival years 2017–2018, including guest counts, stay length, lead time, market segment, room type, average price, and final booking status.

## Quickstart

```bash
make setup              # create virtualenv and install pinned requirements
make data-audit         # Phase 1: data audit + dictionary
make business-analysis  # Phase 2: business analysis
make target-proposal    # Phase 3: target proposal (stops for approval)
make train              # Phase 4: ML pipeline (requires approved target)
make test               # run pytest on /tests
```

## Full stack with Docker

```bash
make docker-build
make docker-up          # api:8000, predict-app:8501, dashboard:8502
make docker-down
```

## Project structure

```
data/raw|processed|external   datasets
configs/                      project, model, and business rules configs
scripts/                      phase scripts (p1..p4)
src/api/                      FastAPI prediction service
apps/predict_app/             Streamlit predictive app
apps/dashboard/               Streamlit business dashboard
models/                       persisted model artifacts
tests/                        pytest suites
docs/                         markdown reports, snippets, json, images
```

## Key documents

- [Analytical plan](PLAN.md)
- [Data dictionary](docs/data_dictionary.md)
- [Data quality report](docs/data_quality_report.md)
- [Problem statement](docs/problem_statement.md)
- [Business analysis report](docs/business_analysis_report.md)
- [Target proposal](docs/target_proposal.md)
- [Model report](docs/model_report.md) · [Model card](docs/model_card.md)
- [API documentation](docs/api_documentation.md)
- [Predict app documentation](docs/predict_app_documentation.md)
- [Dashboard documentation](docs/dashboard_documentation.md)
- [Deployment documentation](docs/deployment_documentation.md)
