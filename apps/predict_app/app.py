"""Streamlit predictive app.

Form for entering booking values, calls the prediction API at API_URL,
and displays probability, contributing factors, and business recommendation.
Also supports batch scoring from a CSV file.
"""

import os
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Cancellation Risk Predictor",
    page_icon="🏨",
    layout="wide",
)

st.title("🏨 Hotel Booking Cancellation Predictor")
st.caption(
    "Score a booking's cancellation risk before arrival and get a recommended retention action."
)

with st.sidebar:
    st.header("About")
    st.markdown(
        "This app scores a booking's cancellation risk using a Gradient Boosting model "
        "(ROC-AUC **0.870** on the held-out test set). Risk bands and recommendations come "
        "from the business rules derived during the analysis."
    )
    st.markdown("🔗 [API docs](http://localhost:8000/docs)")
    try:
        h = requests.get(f"{API_URL}/health", timeout=5).json()
        st.success(f"API online · model v{h['model_version']}")
    except Exception:
        st.error(f"API unreachable at {API_URL}")

tab_single, tab_batch = st.tabs(["Single booking", "Batch scoring (CSV)"])

# ------------------------------------------------------------------ single ---
with tab_single:
    st.subheader("Booking details")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Guests & stay**")
        no_of_adults = st.number_input("Adults", 0, 10, 2)
        no_of_children = st.number_input("Children", 0, 10, 0)
        no_of_weekend_nights = st.number_input("Weekend nights", 0, 10, 1)
        no_of_week_nights = st.number_input("Week nights", 0, 30, 2)
    with col2:
        st.markdown("**Booking**")
        type_of_meal_plan = st.selectbox(
            "Meal plan", ["Meal Plan 1", "Meal Plan 2", "Meal Plan 3", "Not Selected"]
        )
        required_car_parking_space = st.selectbox("Parking space", [0, 1])
        room_type_reserved = st.selectbox(
            "Room type", [f"Room_Type {i}" for i in range(1, 8)]
        )
        avg_price_per_room = st.number_input(
            "Avg price per room (EUR)", 0.0, 1000.0, 110.0, step=1.0
        )
    with col3:
        st.markdown("**Timing & history**")
        lead_time = st.number_input("Lead time (days)", 0, 500, 45)
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
        no_of_previous_cancellations = st.number_input(
            "Previous cancellations", 0, 100, 0
        )
        no_of_previous_bookings_not_canceled = st.number_input(
            "Previous fulfilled bookings", 0, 100, 0
        )
        no_of_special_requests = st.number_input("Special requests", 0, 10, 0)

    if date(2017, 7, 1) > arrival or arrival > date(2018, 12, 31):
        st.warning(
            "The model was trained on arrivals between Jul 2017 and Dec 2018; "
            "predictions outside this period are extrapolations."
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

    if st.button("Predict cancellation risk", type="primary"):
        try:
            with st.spinner("Scoring booking..."):
                resp = requests.post(f"{API_URL}/v1/predict", json=payload, timeout=30)
                resp.raise_for_status()
                result = resp.json()["predictions"][0]
        except requests.RequestException as exc:
            st.error(f"API error: {exc}")
        else:
            prob = result["predicted_probability"]
            band = result["risk_band"]

            col_a, col_b = st.columns([1, 2])
            with col_a:
                fig = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=prob * 100,
                        number={"suffix": "%"},
                        title={"text": "Cancellation risk"},
                        gauge={
                            "axis": {"range": [0, 100]},
                            "bar": {"color": "#1f2937"},
                            "steps": [
                                {"range": [0, 25], "color": "#e8f5e9"},
                                {"range": [25, 55], "color": "#fff3e0"},
                                {"range": [55, 100], "color": "#ffebee"},
                            ],
                            "threshold": {
                                "line": {"color": "#c62828", "width": 4},
                                "thickness": 0.9,
                                "value": 55,
                            },
                        },
                    )
                )
                fig.update_layout(
                    height=280, margin={"t": 40, "b": 0, "l": 20, "r": 20}
                )
                st.plotly_chart(fig, use_container_width=True)
                colors = {"low": "green", "medium": "orange", "high": "red"}
                st.markdown(f"Risk band: :{colors[band]}[{band.upper()}]")
                st.info(f"**Recommended action:** {result['recommendation']}")
                st.caption(f"Model version: {result['model_version']}")
            with col_b:
                st.subheader("Main contributing factors")
                st.caption(
                    "SHAP values: positive pushes the booking toward cancellation, "
                    "negative toward fulfillment."
                )
                factors = result["contributing_factors"][::-1]
                fig2 = go.Figure(
                    go.Bar(
                        x=[f["contribution"] for f in factors],
                        y=[f["feature"] for f in factors],
                        orientation="h",
                        marker_color=[
                            "#c62828" if f["contribution"] > 0 else "#2e7d32"
                            for f in factors
                        ],
                    )
                )
                fig2.update_layout(
                    height=300,
                    margin={"t": 10, "b": 10, "l": 10, "r": 10},
                    xaxis_title="SHAP contribution",
                )
                st.plotly_chart(fig2, use_container_width=True)

# ------------------------------------------------------------------- batch ---
with tab_batch:
    st.subheader("Batch scoring")
    st.markdown(
        "Upload a CSV with one booking per row. Required columns: `no_of_adults, "
        "no_of_children, no_of_weekend_nights, no_of_week_nights, type_of_meal_plan, "
        "required_car_parking_space, room_type_reserved, lead_time, arrival_year, "
        "arrival_month, arrival_date, market_segment_type, repeated_guest, "
        "no_of_previous_cancellations, no_of_previous_bookings_not_canceled, "
        "avg_price_per_room, no_of_special_requests` (max 100 rows per request)."
    )
    template = pd.DataFrame(
        [
            {
                "no_of_adults": 2,
                "no_of_children": 0,
                "no_of_weekend_nights": 1,
                "no_of_week_nights": 2,
                "type_of_meal_plan": "Meal Plan 1",
                "required_car_parking_space": 0,
                "room_type_reserved": "Room_Type 1",
                "lead_time": 45,
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
        ]
    )
    st.download_button(
        "Download CSV template",
        template.to_csv(index=False),
        "bookings_template.csv",
        "text/csv",
    )

    uploaded = st.file_uploader("Upload bookings CSV", type="csv")
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        if df.empty:
            st.warning("The file has no rows.")
        else:
            st.dataframe(df, use_container_width=True, height=200)
            if st.button("Score batch", type="primary", disabled=len(df) == 0):
                results = []
                progress = st.progress(0)
                try:
                    for start in range(0, len(df), 100):
                        chunk = df.iloc[start : start + 100]
                        payload = {"bookings": chunk.to_dict(orient="records")}
                        resp = requests.post(
                            f"{API_URL}/v1/predict", json=payload, timeout=60
                        )
                        resp.raise_for_status()
                        preds = resp.json()["predictions"]
                        results.extend(
                            {
                                "predicted_probability": p["predicted_probability"],
                                "predicted_label": p["predicted_label"],
                                "risk_band": p["risk_band"],
                                "recommendation": p["recommendation"],
                            }
                            for p in preds
                        )
                        progress.progress(min((start + 100) / len(df), 1.0))
                except requests.RequestException as exc:
                    st.error(f"API error: {exc}")
                else:
                    out = pd.concat(
                        [df.reset_index(drop=True), pd.DataFrame(results)], axis=1
                    )
                    st.success(f"Scored {len(out)} bookings.")
                    st.dataframe(out, use_container_width=True, height=300)
                    st.download_button(
                        "Download scored CSV",
                        out.to_csv(index=False),
                        "bookings_scored.csv",
                        "text/csv",
                    )
