"""Shared feature engineering and data utilities for the hotel cancellations project.

Loads raw data, builds the feature matrix, and performs the time-based split
ordered by arrival date (see docs/model_report.md for the rationale).
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads((ROOT / "configs" / "project_config.json").read_text())
MODEL_CONFIG = json.loads((ROOT / "configs" / "model_config.json").read_text())
RAW = ROOT / CONFIG["paths"]["raw_data"]

TARGET = "booking_status"
POSITIVE_LABEL = "Canceled"

EXCLUDED_FROM_FEATURES = ["Booking_ID", TARGET]
# arrival_year and arrival_date are used for the temporal split only; they are
# excluded from features to avoid year-level drift and day-of-month noise.
SPLIT_ONLY_COLUMNS = ["arrival_year", "arrival_date"]

NUMERIC_FEATURES = [
    "no_of_adults",
    "no_of_children",
    "no_of_weekend_nights",
    "no_of_week_nights",
    "required_car_parking_space",
    "lead_time",
    "repeated_guest",
    "no_of_previous_cancellations",
    "no_of_previous_bookings_not_canceled",
    "avg_price_per_room",
    "no_of_special_requests",
    "arrival_month_sin",
    "arrival_month_cos",
    "total_nights",
]
CATEGORICAL_FEATURES = [
    "type_of_meal_plan",
    "room_type_reserved",
    "market_segment_type",
]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

RARE_CATEGORY_MAP = {
    "type_of_meal_plan": {"Meal Plan 3": "Other"},
    "room_type_reserved": {"Room_Type 3": "Other"},
}


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of `df` with the engineered feature columns.

    Shared by the training pipeline and the prediction API so both always
    produce identical inputs for the model.
    """
    out = df.copy()
    out["total_nights"] = out["no_of_week_nights"] + out["no_of_weekend_nights"]
    month = out["arrival_month"].to_numpy(dtype=float)
    out["arrival_month_sin"] = np.sin(2.0 * np.pi * month / 12.0)
    out["arrival_month_cos"] = np.cos(2.0 * np.pi * month / 12.0)
    for col, mapping in RARE_CATEGORY_MAP.items():
        out[col] = out[col].replace(mapping)
    return out


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RAW)
    return add_engineered_features(df)


def arrival_datetime(df: pd.DataFrame) -> pd.Series:
    """Reconstruct the arrival date from year/month/day components.

    A handful of rows have impossible day-of-month values (e.g., Feb 29-31 in
    non-leap months); those are coerced to NaT and ordered last within their
    year-month via a sentinel date, so the temporal split stays deterministic.
    """
    parsed = pd.to_datetime(
        df["arrival_year"].astype(str)
        + "-"
        + df["arrival_month"].astype(str).str.zfill(2)
        + "-"
        + df["arrival_date"].astype(str).str.zfill(2),
        format="%Y-%m-%d",
        errors="coerce",
    )
    sentinel = pd.to_datetime(
        df["arrival_year"].astype(str)
        + "-"
        + df["arrival_month"].astype(str).str.zfill(2)
        + "-28"
    ) + pd.Timedelta(days=4)
    return parsed.fillna(sentinel)


def temporal_split(df: pd.DataFrame):
    """Time-based split ordered by arrival date.

    Returns train (70%), validation (15%), test (15%) sorted by arrival date.
    """
    ratios = MODEL_CONFIG["split_ratios"]
    order = (
        df.assign(_arrival=arrival_datetime(df))
        .sort_values("_arrival")
        .reset_index(drop=True)
    )
    n = len(order)
    train_end = int(n * ratios["train"])
    val_end = int(n * (ratios["train"] + ratios["validation"]))
    train = order.iloc[:train_end].drop(columns="_arrival")
    val = order.iloc[train_end:val_end].drop(columns="_arrival")
    test = order.iloc[val_end:].drop(columns="_arrival")
    return train, val, test


def xy(df: pd.DataFrame):
    X = df[FEATURES]
    y = (df[TARGET] == POSITIVE_LABEL).astype(int)
    return X, y


def class_sample_weights(y: pd.Series) -> np.ndarray:
    """Balanced sample weights for models without a class_weight parameter."""
    counts = np.bincount(y)
    weights = np.where(y == 1, len(y) / (2.0 * counts[1]), len(y) / (2.0 * counts[0]))
    return weights
