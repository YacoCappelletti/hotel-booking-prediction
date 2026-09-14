"""Phase 6: Streamlit predictive app.

Form for entering booking values, calls the prediction API at API_URL,
and displays probability, contributing factors, and business recommendation.
"""

import os
from datetime import date

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Cancellation Risk Predictor", page_icon="🏨", layout="centered"
)
st.title("🏨 Hotel Booking Cancellation Predictor")
st.caption(f"Model API: {API_URL}")

with st.sidebar:
    st.header("About")
    st.markdown(
        "This app scores a booking's cancellation risk using a Gradient Boosting model "
        "(ROC-AUC 0.865 on the held-out test set). Risk bands and recommendations come from "
        "the business rules defined in Phase 2."
    )

st.header("Booking details")

col1, col2, col3 = st.columns(3)
with col1:
    no_of_adults = st.number_input("Adults", 0, 10, 2)
    no_of_children = st.number_input("Children", 0, 10, 0)
    no_of_weekend_nights = st.number_input("Weekend nights", 0, 10, 1)
    no_of_week_nights = st.number_input("Week nights", 0, 30, 2)
with col2:
    type_of_meal_plan = st.selectbox(
        "Meal plan", ["Meal Plan 1", "Meal Plan 2", "Meal Plan 3", "Not Selected"]
    )
    required_car_parking_space = st.selectbox("Parking space", [0, 1])
    room_type_reserved = st.selectbox(
        "Room type", [f"Room_Type {i}" for i in range(1, 8)]
    )
    lead_time = st.number_input("Lead time (days)", 0, 500, 45)
with col3:
    arrival = st.date_input(
        "Arrival date",
        value=date(2018, 10, 15),
        min_value=date(2015, 1, 1),
        max_value=date(2030, 12, 31),
    )
    market_segment_type = st.selectbox(
        "Market segment",
        ["Online", "Offline", "Corporate", "Complementary", "Aviation"],
    )
    repeated_guest = st.selectbox("Repeated guest", [0, 1])
    no_of_special_requests = st.number_input("Special requests", 0, 10, 0)

col4, col5 = st.columns(2)
with col4:
    no_of_previous_cancellations = st.number_input("Previous cancellations", 0, 100, 0)
    no_of_previous_bookings_not_canceled = st.number_input(
        "Previous fulfilled bookings", 0, 100, 0
    )
with col5:
    avg_price_per_room = st.number_input(
        "Avg price per room (EUR)", 0.0, 1000.0, 110.0, step=1.0
    )

payload = {
    "bookings": [
        {
            "no_of_adults": int(no_of_adults),
            "no_of_children": int(no_of_children),
            "no_of_weekend_nights": int(no_of_weekend_nights),
            "no_of_week_nights": int(no_of_week_nights),
            "type_of_meal_plan": type_of_meal_plan,
            "required_car_parking_space": int(required_car_parking_space),
            "room_type_reserved": room_type_reserved,
            "lead_time": int(lead_time),
            "arrival_year": arrival.year,
            "arrival_month": arrival.month,
            "arrival_date": arrival.day,
            "market_segment_type": market_segment_type,
            "repeated_guest": int(repeated_guest),
            "no_of_previous_cancellations": int(no_of_previous_cancellations),
            "no_of_previous_bookings_not_canceled": int(
                no_of_previous_bookings_not_canceled
            ),
            "avg_price_per_room": float(avg_price_per_room),
            "no_of_special_requests": int(no_of_special_requests),
        }
    ]
}

# Client-side warnings before calling the API
warnings = []
if (
    payload["bookings"][0]["no_of_adults"] + payload["bookings"][0]["no_of_children"]
    == 0
):
    warnings.append("The booking has 0 guests.")
if (
    payload["bookings"][0]["no_of_week_nights"]
    + payload["bookings"][0]["no_of_weekend_nights"]
    == 0
):
    warnings.append("The booking has 0 nights.")
for w in warnings:
    st.warning(w)

if st.button("Predict cancellation risk", type="primary", disabled=bool(warnings)):
    try:
        resp = requests.post(f"{API_URL}/v1/predict", json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()["predictions"][0]
    except requests.RequestException as exc:
        st.error(f"API error: {exc}")
    else:
        prob = result["predicted_probability"]
        band = result["risk_band"]
        colors = {"low": "green", "medium": "orange", "high": "red"}
        st.subheader(f"Cancellation probability: {prob:.1%}")
        st.markdown(f"Risk band: :{colors[band]}[{band.upper()}]")
        st.info(f"**Recommended action:** {result['recommendation']}")
        st.markdown(f"Model version: `{result['model_version']}`")

        st.subheader("Main contributing factors")
        factors = result["contributing_factors"]
        max_abs = max((abs(f["contribution"]) for f in factors), default=1) or 1
        for f in factors:
            share = abs(f["contribution"]) / max_abs
            direction = "→ cancels" if f["contribution"] > 0 else "→ keeps"
            st.write(f"**{f['feature']}** ({f['contribution']:+.2f}) {direction}")
            st.progress(share)
