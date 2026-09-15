PY := $(shell if [ -x venv/bin/python ]; then echo venv/bin/python; else echo python3; fi)
PIP := $(PY) -m pip

.PHONY: setup download-data data-audit business-analysis train test lint run-api run-predict-app run-dashboard docker-build docker-up docker-down

setup:
	python3 -m venv venv && ./venv/bin/pip install -r requirements-dev.txt

download-data:
	$(PY) scripts/download_data.py

data-audit:
	$(PY) scripts/p1_data_audit.py
	$(PY) scripts/p1_data_dictionary.py

business-analysis:
	$(PY) scripts/p2_q01_cancellation_rate_overview.py
	$(PY) scripts/p2_q02_lead_time_vs_cancellation.py
	$(PY) scripts/p2_q03_market_segment_behavior.py
	$(PY) scripts/p2_q04_revenue_impact_of_cancellations.py
	$(PY) scripts/p2_q05_seasonality_and_special_requests.py

train:
	$(PY) scripts/p4_train_baseline.py
	$(PY) scripts/p4_train_candidate_models.py
	$(PY) scripts/p4_evaluate_final_model.py

test:
	$(PY) -m pytest tests/ -v

lint:
	$(PY) -m ruff check .

run-api:
	$(PY) -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

run-predict-app:
	$(PY) -m streamlit run apps/predict_app/app.py --server.port 8501

run-dashboard:
	$(PY) -m streamlit run apps/dashboard/app.py --server.port 8502

docker-build:
	docker build -t hotel-booking-cancellation-prediction .

docker-up:
	docker compose up -d

docker-down:
	docker compose down
