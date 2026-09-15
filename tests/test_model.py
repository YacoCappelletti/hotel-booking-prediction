"""Model artifact tests: artifacts load, prediction shape, documented test minimums.

Test metrics are read from docs/json/model_performance.json (the single
test-set evaluation); this suite never re-evaluates the test set.
"""

import json
from pathlib import Path

import joblib
import pandas as pd
import pytest

from src.features.build_features import add_engineered_features

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
PERF = json.loads((ROOT / "docs" / "json" / "model_performance.json").read_text())
METADATA = json.loads((MODELS / "model_metadata.json").read_text())

SAMPLE_BOOKING = {
    "no_of_adults": 2,
    "no_of_children": 0,
    "no_of_weekend_nights": 1,
    "no_of_week_nights": 2,
    "required_car_parking_space": 0,
    "lead_time": 200,
    "repeated_guest": 0,
    "no_of_previous_cancellations": 0,
    "no_of_previous_bookings_not_canceled": 0,
    "avg_price_per_room": 110.0,
    "no_of_special_requests": 0,
    "arrival_month": 10,
    "type_of_meal_plan": "Meal Plan 1",
    "room_type_reserved": "Room_Type 1",
    "market_segment_type": "Online",
}


@pytest.fixture(scope="module")
def artifacts():
    model = joblib.load(MODELS / "final_model.joblib")
    preprocessor = joblib.load(MODELS / "preprocessor.joblib")
    explainer_bundle = joblib.load(MODELS / "explainer.joblib")
    return model, preprocessor, explainer_bundle


@pytest.fixture(scope="module")
def sample_input():
    return add_engineered_features(pd.DataFrame([SAMPLE_BOOKING]))


def test_artifacts_load(artifacts):
    model, preprocessor, bundle = artifacts
    assert model is not None and preprocessor is not None
    assert "explainer" in bundle and "feature_names" in bundle


def test_metadata_complete():
    required = [
        "model_name",
        "model_version",
        "target",
        "problem_type",
        "random_seed",
        "feature_list",
        "split_strategy",
        "chosen_decision_threshold",
        "validation_metrics",
        "test_metrics",
        "library_versions",
    ]
    for key in required:
        assert key in METADATA, f"missing metadata key: {key}"
    assert METADATA["test_metrics"] is not None, "test evaluation missing"


def test_engineered_features_consistent(sample_input):
    assert set(METADATA["feature_list"]).issubset(sample_input.columns)
    assert "arrival_month_sin" in sample_input.columns
    assert "arrival_month_cos" in sample_input.columns


def test_prediction_shape_and_range(artifacts, sample_input):
    model, preprocessor, _ = artifacts
    X_t = preprocessor.transform(sample_input)
    proba = model.predict_proba(X_t)
    assert proba.shape == (1, 2)
    assert 0.0 <= float(proba[0, 1]) <= 1.0


def test_explainer_produces_factors(artifacts, sample_input):
    _, preprocessor, bundle = artifacts
    X_t = preprocessor.transform(sample_input)
    sv = bundle["explainer"](X_t)
    assert sv.values.shape[0] == 1
    assert len(bundle["feature_names"]) == X_t.shape[1]


def test_test_metrics_meet_documented_minimums():
    """Minimums documented in docs/model_report.md (temporal-drift-adjusted)."""
    tm = PERF["test_metrics"]
    assert tm["roc_auc"] >= 0.80, f"ROC-AUC {tm['roc_auc']} below minimum 0.80"
    assert tm["pr_auc"] >= 0.65, f"PR-AUC {tm['pr_auc']} below minimum 0.65"
    assert tm["recall"] >= 0.90, (
        f"Recall {tm['recall']} below minimum 0.90 (cost policy 10:1)"
    )
    assert tm["accuracy"] >= 0.60


def test_validation_beats_baseline():
    baseline_acc = PERF["baseline"]["validation_metrics"]["accuracy"]
    assert PERF["validation_metrics"]["accuracy"] > baseline_acc
    assert PERF["validation_metrics"]["pr_auc"] > 0.80
