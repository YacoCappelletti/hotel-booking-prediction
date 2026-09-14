.PHONY: setup data-audit business-analysis target-proposal train test run-api run-predict-app run-dashboard docker-build docker-up docker-down

setup:
	python3 -m venv venv && ./venv/bin/pip install -r requirements.txt

data-audit:
	python3 scripts/p1_data_audit.py
	python3 scripts/p1_data_dictionary.py

business-analysis:
	python3 scripts/p2_q01_cancellation_rate_overview.py
	python3 scripts/p2_q02_lead_time_vs_cancellation.py
	python3 scripts/p2_q03_market_segment_behavior.py
	python3 scripts/p2_q04_revenue_impact_of_cancellations.py
	python3 scripts/p2_q05_seasonality_and_special_requests.py

target-proposal:
	python3 scripts/p3_target_proposal.py

train:
	python3 scripts/p4_train_baseline.py
	python3 scripts/p4_train_candidate_models.py
	python3 scripts/p4_evaluate_final_model.py

test:
	pytest tests/ -v

run-api:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000

run-predict-app:
	streamlit run apps/predict_app/app.py --server.port 8501

run-dashboard:
	streamlit run apps/dashboard/app.py --server.port 8502

docker-build:
	docker build -t hotel-booking-cancelations-predict .

docker-up:
	docker compose up -d

docker-down:
	docker compose down
