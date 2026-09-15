"""API tests: /health returns 200; valid prediction returns 200 with the
expected schema; invalid input returns 422."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

ROOT = Path(__file__).resolve().parents[1]

VALID_BOOKING = {
    "no_of_adults": 2,
    "no_of_children": 0,
    "no_of_weekend_nights": 1,
    "no_of_week_nights": 2,
    "type_of_meal_plan": "Meal Plan 1",
    "required_car_parking_space": 0,
    "room_type_reserved": "Room_Type 1",
    "lead_time": 200,
    "arrival_year": 2018,
    "arrival_month": 10,
    "arrival_date": 15,
    "market_segment_type": "Online",
    "repeated_guest": 0,
    "no_of_previous_cancellations": 0,
    "no_of_previous_bookings_not_canceled": 0,
    "avg_price_per_room": 110.0,
    "no_of_special_requests": 0,
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_returns_200(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "model_version" in body


def test_valid_prediction_returns_200_with_schema(client):
    r = client.post("/v1/predict", json={"bookings": [VALID_BOOKING]})
    assert r.status_code == 200
    body = r.json()
    assert len(body["predictions"]) == 1
    p = body["predictions"][0]
    for key in [
        "predicted_probability",
        "predicted_label",
        "risk_band",
        "recommendation",
        "contributing_factors",
        "model_version",
        "timestamp",
    ]:
        assert key in p
    assert 0.0 <= p["predicted_probability"] <= 1.0
    assert p["risk_band"] in ("low", "medium", "high")
    assert len(p["contributing_factors"]) >= 1
    assert all(
        "feature" in f and "contribution" in f for f in p["contributing_factors"]
    )


def test_high_risk_booking_gets_high_band(client):
    risky = {
        **VALID_BOOKING,
        "lead_time": 400,
        "no_of_special_requests": 0,
        "repeated_guest": 0,
        "market_segment_type": "Online",
    }
    r = client.post("/v1/predict", json={"bookings": [risky]})
    assert r.status_code == 200
    assert r.json()["predictions"][0]["risk_band"] in ("medium", "high")


def test_invalid_input_returns_422(client):
    bad = {**VALID_BOOKING, "lead_time": -5}
    r = client.post("/v1/predict", json={"bookings": [bad]})
    assert r.status_code == 422


def test_unknown_category_returns_422(client):
    bad = {**VALID_BOOKING, "market_segment_type": "Mystery"}
    r = client.post("/v1/predict", json={"bookings": [bad]})
    assert r.status_code == 422


def test_model_card_returns_200(client):
    r = client.get("/v1/model-card")
    assert r.status_code == 200
    body = r.json()
    assert body["decision_threshold"] is not None
    assert body["test_metrics"] is not None
    assert len(body["features"]) > 0
