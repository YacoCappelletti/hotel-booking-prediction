"""FastAPI prediction service.

Endpoints: /health, /v1/predict, /v1/model-card.
Structured logging without raw PII (no identifiers are logged, only counts and latencies).
"""

import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from src.api.predict import PredictionService
from src.api.schemas import (
    HealthResponse,
    ModelCardResponse,
    PredictRequest,
    PredictResponse,
    PredictResponseItem,
)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("api.main")

service: PredictionService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global service
    service = PredictionService()
    logger.info("Prediction service ready")
    yield
    service = None


def get_service() -> PredictionService:
    assert service is not None, "Prediction service not initialized"
    return service


app = FastAPI(
    title="Hotel Booking Cancellation Prediction API",
    version="1.0.0",
    description="Predicts booking cancellation risk with SHAP-based contributing "
    "factors and business recommendations.",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health", response_model=HealthResponse)
def health():
    svc = get_service()
    return HealthResponse(
        status="ok",
        model_version=svc.version,
        model_name=svc.metadata["model_name"],
    )


@app.post("/v1/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    svc = get_service()
    started = time.perf_counter()
    try:
        items = [b.model_dump() for b in request.bookings]
        results = svc.predict(items)
    except ValueError as exc:
        logger.warning("Validation error: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    logger.info(
        "Predicted %d booking(s) in %.1f ms",
        len(items),
        (time.perf_counter() - started) * 1000,
    )
    return PredictResponse(predictions=[PredictResponseItem(**r) for r in results])


@app.get("/v1/model-card", response_model=ModelCardResponse)
def model_card():
    return ModelCardResponse(**get_service().model_card())
