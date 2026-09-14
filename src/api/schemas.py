"""Pydantic schemas for the prediction API (Phase 5)."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class BookingFeatures(BaseModel):
    """Input features for one booking; all fields are known at booking time."""

    no_of_adults: int = Field(ge=0, le=10, description="Number of adults")
    no_of_children: int = Field(ge=0, le=10, description="Number of children")
    no_of_weekend_nights: int = Field(ge=0, le=10, description="Weekend nights booked")
    no_of_week_nights: int = Field(ge=0, le=30, description="Week nights booked")
    type_of_meal_plan: Literal[
        "Meal Plan 1", "Meal Plan 2", "Meal Plan 3", "Not Selected"
    ]
    required_car_parking_space: Literal[0, 1]
    room_type_reserved: Literal[
        "Room_Type 1",
        "Room_Type 2",
        "Room_Type 3",
        "Room_Type 4",
        "Room_Type 5",
        "Room_Type 6",
        "Room_Type 7",
    ]
    lead_time: int = Field(ge=0, le=500, description="Days between booking and arrival")
    arrival_year: int = Field(ge=2015, le=2030)
    arrival_month: int = Field(ge=1, le=12)
    arrival_date: int = Field(ge=1, le=31)
    market_segment_type: Literal[
        "Online", "Offline", "Corporate", "Complementary", "Aviation"
    ]
    repeated_guest: Literal[0, 1]
    no_of_previous_cancellations: int = Field(ge=0, le=100)
    no_of_previous_bookings_not_canceled: int = Field(ge=0, le=100)
    avg_price_per_room: float = Field(
        ge=0, le=1000, description="Average price per night (EUR)"
    )
    no_of_special_requests: int = Field(ge=0, le=10)

    @field_validator("no_of_adults", "no_of_children")
    @classmethod
    def not_all_zero(cls, v, info):
        # Cross-field check happens at the model level in predict.py
        return v


class PredictRequest(BaseModel):
    bookings: list[BookingFeatures] = Field(min_length=1, max_length=100)


class ContributingFactor(BaseModel):
    feature: str
    contribution: float  # SHAP value; positive pushes toward cancellation


class PredictResponseItem(BaseModel):
    predicted_probability: float
    predicted_label: Literal["Canceled", "Not_Canceled"]
    risk_band: Literal["low", "medium", "high"]
    recommendation: str
    contributing_factors: list[ContributingFactor]
    model_version: str
    timestamp: str


class PredictResponse(BaseModel):
    predictions: list[PredictResponseItem]


class HealthResponse(BaseModel):
    status: str
    model_version: str
    model_name: str


class ModelCardResponse(BaseModel):
    model_name: str
    model_version: str
    approved_target: str
    problem_type: str
    features: list[str]
    decision_threshold: float
    training_timestamp: str
    test_metrics: dict
    notes_and_limitations: list[str]
