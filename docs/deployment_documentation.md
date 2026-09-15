# Deployment Documentation

## Architecture

Single Docker image (`hotel-booking-cancellation-prediction`) built from one `Dockerfile`; the three
services differ only by their run command:

| Service | Command | Port | Purpose |
| --- | --- | --- | --- |
| `api` | `uvicorn src.api.main:app --host 0.0.0.0 --port 8000` | 8000 | Prediction API (`/health`, `/v1/predict`, `/v1/model-card`) |
| `predict-app` | `streamlit run apps/predict_app/app.py --server.port 8501` | 8501 | Operational risk-scoring app |
| `dashboard` | `streamlit run apps/dashboard/app.py --server.port 8502` | 8502 | Business dashboard |

- The `api` service exposes a healthcheck on `/health`; `predict-app` and `dashboard` start only
  after the API is healthy (`depends_on.condition: service_healthy`).
- Streamlit apps reach the API via `API_URL=http://api:8000` inside the compose network.
- Model artifacts (`models/*.joblib`, `model_metadata.json`), configs, and the raw dataset are
  copied into the image.

## Quickstart

```bash
make docker-build     # build the single image
make docker-up        # start api + predict-app + dashboard
make docker-down      # stop everything
```

Or directly: `docker compose up --build`

## Verification checklist

1. `curl http://localhost:8000/health` → `{"status": "ok", ...}`
2. `curl -X POST http://localhost:8000/v1/predict -H 'Content-Type: application/json' -d @docs/json/api_examples.json` (extract a request) → 200 with prediction
3. Open `http://localhost:8501` → predict app form works end-to-end against the API
4. Open `http://localhost:8502` → dashboard renders KPIs and charts

## Environment variables

In Docker, only `LOG_LEVEL` (api) and `API_URL` (predict-app) are set by compose; artifact paths
are resolved relative to `/app` inside the image.

## Notes

- The image is based on `python:3.13-slim` with pinned dependencies from `requirements.txt`.
- No secrets are required; nothing sensitive is baked into the image.
- For production, mount `models/` as a read-only volume instead of baking artifacts, and put the
  API behind a reverse proxy with TLS.
