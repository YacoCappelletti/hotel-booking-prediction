"""Streamlit business dashboard.

Answers: What happened? Why did it happen? What should the business do?
KPIs, interactive charts for the five business questions, and dimension filters.
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "hotel_reservations.csv"

st.set_page_config(page_title="Cancellations Dashboard", page_icon="📊", layout="wide")
st.title("📊 Hotel Booking Cancellations — Business Dashboard")
st.caption("What happened · Why it happened · What the business should do")


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(RAW)
    df["cancel"] = (df["booking_status"] == "Canceled").astype(int)
    df["revenue"] = df["avg_price_per_room"] * (
        df["no_of_week_nights"] + df["no_of_weekend_nights"]
    )
    df["lost_revenue"] = df["revenue"] * df["cancel"]
    return df


df = load_data()

# ---- Filters ----
st.sidebar.header("Filters")
years = sorted(df["arrival_year"].unique())
year_filter = st.sidebar.multiselect("Arrival year", years, default=years)
month_filter = st.sidebar.slider("Arrival months", 1, 12, (1, 12))
segments = sorted(df["market_segment_type"].unique())
segment_filter = st.sidebar.multiselect("Market segment", segments, default=segments)

fdf = df[
    df["arrival_year"].isin(year_filter)
    & df["arrival_month"].between(month_filter[0], month_filter[1])
    & df["market_segment_type"].isin(segment_filter)
]
if fdf.empty:
    st.warning("No data for the selected filters.")
    st.stop()

BLUE, ORANGE, RED, PURPLE = "#1565c0", "#ef6c00", "#c62828", "#6a1b9a"

# ---- KPIs (What happened?) ----
st.header("1) What happened?")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Bookings", f"{len(fdf):,}")
k2.metric("Cancellation rate", f"{fdf['cancel'].mean():.1%}")
k3.metric("Revenue at risk", f"EUR {fdf['lost_revenue'].sum() / 1e6:.2f}M")
k4.metric("Avg booking value", f"EUR {fdf['revenue'].mean():,.0f}")
k5.metric(
    "Fulfilled-bookings revenue",
    f"EUR {(fdf['revenue'] * (1 - fdf['cancel'])).sum() / 1e6:.2f}M",
)

# ---- Why did it happen? ----
st.header("2) Why did it happen?")
tab_overview, tab_lead, tab_segment, tab_season, tab_engagement = st.tabs(
    [
        "Seasonality of losses",
        "Lead time",
        "Market segments",
        "Special requests",
        "Guest mix",
    ]
)

with tab_overview:
    st.subheader("Monthly lost revenue and cancellation rate")
    monthly = fdf.groupby("arrival_month").agg(
        rate=("cancel", "mean"), lost=("lost_revenue", "sum")
    )
    month_names = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    fig = go.Figure()
    fig.add_bar(
        x=month_names,
        y=monthly["lost"] / 1e3,
        name="Lost revenue (k EUR)",
        marker_color=RED,
        opacity=0.75,
    )
    fig.add_scatter(
        x=month_names,
        y=monthly["rate"],
        name="Cancellation rate",
        mode="lines+markers",
        line={"color": BLUE},
        yaxis="y2",
    )
    fig.update_layout(
        yaxis={"title": "Lost revenue (k EUR)"},
        yaxis2={
            "title": "Cancel rate",
            "overlaying": "y",
            "side": "right",
            "range": [0, 1],
        },
        height=420,
        legend={"orientation": "h", "y": 1.1},
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("**Interpretation:** losses concentrate in peak months (Q04).")

with tab_lead:
    st.subheader("Lead time drives risk")
    bins = [0, 7, 30, 60, 90, 180, 10**9]
    labels = ["1-7d", "8-30d", "31-60d", "61-90d", "91-180d", "181d+"]
    fdf2 = fdf.copy()
    fdf2["band"] = pd.cut(
        fdf2["lead_time"], bins=bins, labels=labels, include_lowest=True
    )
    by_lead = fdf2.groupby("band", observed=True)["cancel"].agg(["mean", "size"])
    fig = px.bar(
        x=by_lead.index.astype(str),
        y=by_lead["mean"],
        color_discrete_sequence=[BLUE],
        custom_data=by_lead["size"],
    )
    fig.update_traces(hovertemplate="%{y:.1%} cancel rate (%{customdata} bookings)")
    fig.update_layout(
        xaxis_title="Lead-time band",
        yaxis_title="Cancellation rate",
        yaxis_range=[0, 1],
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        "**Interpretation:** long-lead bookings cancel far more — plans made months "
        "ahead are fragile (Q02)."
    )

with tab_segment:
    st.subheader("Channel risk concentration")
    by_seg = (
        fdf.groupby("market_segment_type")["cancel"]
        .agg(["mean", "size"])
        .sort_values("mean", ascending=False)
    )
    fig = px.bar(
        x=by_seg.index,
        y=by_seg["mean"],
        color_discrete_sequence=[ORANGE],
        custom_data=by_seg["size"],
    )
    fig.update_traces(hovertemplate="%{y:.1%} cancel rate (%{customdata} bookings)")
    fig.update_layout(
        xaxis_title="Market segment",
        yaxis_title="Cancellation rate",
        yaxis_range=[0, 1],
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        "**Interpretation:** Online dominates volume and risk; Corporate is the safest "
        "paying segment (Q03)."
    )

with tab_engagement:
    st.subheader("Engagement is protective")
    by_req = fdf.groupby("no_of_special_requests")["cancel"].mean()
    fig = px.bar(x=by_req.index.astype(str), y=by_req, color_discrete_sequence=[PURPLE])
    fig.update_traces(hovertemplate="%{y:.1%} cancel rate")
    fig.update_layout(
        xaxis_title="Special requests",
        yaxis_title="Cancellation rate",
        yaxis_range=[0, 1],
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        "**Interpretation:** every special request lowers risk; zero-request, first-time, "
        "long-lead bookings are the archetypal risk profile (Q05)."
    )

with tab_season:
    st.subheader("Seasonality of booking volume")
    by_month = fdf.groupby("arrival_month")["cancel"].agg(["mean", "size"])
    fig = px.bar(
        x=month_names,
        y=by_month["size"],
        color_discrete_sequence=[BLUE],
        custom_data=by_month["mean"],
    )
    fig.update_traces(hovertemplate="%{y:,} bookings · %{customdata:.1%} cancel rate")
    fig.update_layout(
        xaxis_title="Arrival month",
        yaxis_title="Bookings",
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        "**Interpretation:** demand peaks Aug–Oct, exactly where losses concentrate (Q04/Q05)."
    )

# ---- What should the business do? ----
st.header("3) What should the business do?")
actions = pd.DataFrame(
    [
        [
            "Lead time > 180 days (74% cancel rate)",
            "Mandatory deposit or non-refundable option; tiered reconfirmation by lead-time band",
        ],
        [
            "Online segment (37% cancel rate, 64% of volume)",
            "Partial prepayment or stricter free-cancellation windows for online bookings",
        ],
        [
            "Peak months (Aug–Oct, 43% of losses)",
            "Stricter terms + overbooking buffers in high season; front-load retention campaigns",
        ],
        [
            "0 special requests / first-time guest (43% vs 1.7%)",
            "Nudge guests to add preferences at booking; prioritize them for reconfirmation",
        ],
        [
            "Overall EUR 4.3M at risk",
            "Integrate the cancellation-risk score into the reservation workflow (see Predict app)",
        ],
    ],
    columns=["Signal observed", "Recommended action"],
)
st.dataframe(actions, use_container_width=True, hide_index=True)

st.caption(
    "Source: business analysis (docs/business_analysis_report.md). "
    "Risk scoring available in the Predict app (port 8501)."
)
