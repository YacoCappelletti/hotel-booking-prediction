"""Phase 1 tests: dataset loads, expected columns exist, no fully-empty columns,
dtypes match the data dictionary."""

import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs" / "project_config.json").read_text())
RAW = ROOT / CONFIG["paths"]["raw_data"]
DICT_JSON = ROOT / "docs" / "json" / "data_dictionary.json"

EXPECTED_COLUMNS = [
    "Booking_ID",
    "no_of_adults",
    "no_of_children",
    "no_of_weekend_nights",
    "no_of_week_nights",
    "type_of_meal_plan",
    "required_car_parking_space",
    "room_type_reserved",
    "lead_time",
    "arrival_year",
    "arrival_month",
    "arrival_date",
    "market_segment_type",
    "repeated_guest",
    "no_of_previous_cancellations",
    "no_of_previous_bookings_not_canceled",
    "avg_price_per_room",
    "no_of_special_requests",
    "booking_status",
]


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(RAW)


@pytest.fixture(scope="module")
def dictionary():
    return json.loads(DICT_JSON.read_text())


def test_dataset_loads(df):
    assert len(df) > 0
    assert df.shape == (36275, 19)


def test_expected_columns_exist(df):
    assert list(df.columns) == EXPECTED_COLUMNS


def test_no_fully_empty_columns(df):
    empty = [c for c in df.columns if df[c].isna().all()]
    assert empty == []


def test_no_missing_values(df):
    assert df.isna().sum().sum() == 0


def test_no_duplicate_rows(df):
    assert df.duplicated().sum() == 0


def test_dtypes_match_dictionary(df, dictionary):
    dict_map = {c["name"]: c["dtype"] for c in dictionary["columns"]}
    assert set(dict_map) == set(df.columns)
    for col, dtype in dict_map.items():
        actual = str(df[col].dtype)
        if dtype == "str":
            assert actual in ("object", "str"), (
                f"{col}: expected string-like, got {actual}"
            )
        else:
            assert actual == dtype, f"{col}: expected {dtype}, got {actual}"


def test_target_flag_is_factual_only(dictionary):
    """G1 check: dictionary flags must be factual, no ranking or proposal."""
    flags = [c["candidate_target_flag"] for c in dictionary["columns"]]
    assert all(
        f in ("yes (factual flag only — evaluation deferred to Phase 3)", "no")
        for f in flags
    )
