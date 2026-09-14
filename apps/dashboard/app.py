"""Phase 7: Streamlit business dashboard.

Answers: What happened? Why did it happen? What should the business do?
KPIs, charts for the 5 selected business questions, and dimension filters.
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
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
year_filter = st.sidebar.multiselect(
    "Arrival year",
    sorted(df["arrival_year"].unique()),
    default=sorted(df["arrival_year"].unique()),
)
month_filter = st.sidebar.multiselect(
    "Arrival month", list(range(1, 13)), default=list(range(1, 13))
)
segment_filter = st.sidebar.multiselect(
    "Market segment",
    sorted(df["market_segment_type"].unique()),
    default=sorted(df["market_segment_type"].unique()),
)

fdf = df[
    df["arrival_year"].isin(year_filter)
    & df["arrival_month"].isin(month_filter)
    & df["market_segment_type"].isin(segment_filter)
]
if fdf.empty:
    st.warning("No data for the selected filters.")
    st.stop()

# ---- KPIs (What happened?) ----
st.header("1) What happened?")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Bookings", f"{len(fdf):,}")
k2.metric("Cancellation rate", f"{fdf['cancel'].mean():.1%}")
k3.metric("Revenue at risk", f"EUR {fdf['lost_revenue'].sum() / 1e6:.2f}M")
k4.metric("Avg booking value", f"EUR {fdf[fdf['cancel'] == 0]['revenue'].mean():,.0f}")

# ---- Why did it happen? ----
st.header("2) Why did it happen?")
c1, c2 = st.columns(2)

with c1:
    st.subheader("Lead time drives risk")
    bins = [0, 7, 30, 60, 90, 180, 450]
    labels = ["1-7d", "8-30d", "31-60d", "61-90d", "91-180d", "181-443d"]
    fdf2 = fdf.copy()
    fdf2["band"] = pd.cut(
        fdf2["lead_time"], bins=bins, labels=labels, include_lowest=True
    )
    by_lead = fdf2.groupby("band", observed=True)["cancel"].mean()
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.bar(by_lead.index.astype(str), by_lead, color="#1565c0")
    ax.set_ylabel("Cancel rate")
    ax.set_ylim(0, 1)
    ax.set_title("Cancellation rate by lead-time band")
    st.pyplot(fig)
    st.markdown(
        "**Interpretation:** long-lead bookings cancel far more — plans made months "
        "ahead are fragile (Q02)."
    )

with c2:
    st.subheader("Channel risk concentration")
    by_seg = (
        fdf.groupby("market_segment_type")["cancel"]
        .agg(["mean", "size"])
        .sort_values("mean", ascending=False)
    )
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.bar(by_seg.index, by_seg["mean"], color="#ef6c00")
    ax.set_ylabel("Cancel rate")
    ax.set_ylim(0, 1)
    ax.tick_params(axis="x", rotation=25)
    ax.set_title("Cancellation rate by market segment")
    st.pyplot(fig)
    st.markdown(
        "**Interpretation:** Online dominates volume and risk; Corporate is the safest "
        "paying segment (Q03)."
    )

c3, c4 = st.columns(2)
with c3:
    st.subheader("Seasonality of losses")
    monthly = fdf.groupby("arrival_month").agg(
        rate=("cancel", "mean"), lost=("lost_revenue", "sum")
    )
    fig, ax1 = plt.subplots(figsize=(6, 3.4))
    ax1.bar(monthly.index, monthly["lost"] / 1e3, color="#c62828", alpha=0.7)
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Lost revenue (k EUR)")
    ax2 = ax1.twinx()
    ax2.plot(monthly.index, monthly["rate"], color="#1565c0", marker="o")
    ax2.set_ylabel("Cancel rate")
    ax1.set_title("Monthly lost revenue and cancel rate")
    st.pyplot(fig)
    st.markdown("**Interpretation:** losses concentrate in peak months (Q04).")

with c4:
    st.subheader("Engagement is protective")
    by_req = fdf.groupby("no_of_special_requests")["cancel"].mean()
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.bar(by_req.index.astype(str), by_req, color="#6a1b9a")
    ax.set_xlabel("Special requests")
    ax.set_ylabel("Cancel rate")
    ax.set_ylim(0, 1)
    ax.set_title("Cancel rate by special requests")
    st.pyplot(fig)
    st.markdown(
        "**Interpretation:** every special request lowers risk; zero-request, first-time, "
        "long-lead bookings are the archetypal risk profile (Q05)."
    )

# ---- What should the business do? ----
st.header("3) What should the business do?")
st.markdown("""
| Signal observed | Recommended action |
| --- | --- |
| Lead time > 180 days (74% cancel rate) | Mandatory deposit or non-refundable option; tiered reconfirmation by lead-time band |
| Online segment (37% cancel rate, 64% of volume) | Partial prepayment or stricter free-cancellation windows for online bookings |
| Peak months (Aug–Oct, 43% of losses) | Stricter terms + overbooking buffers in high season; front-load retention campaigns |
| 0 special requests / first-time guest (43% vs 1.7%) | Nudge guests to add preferences at booking; prioritize them for reconfirmation |
| Overall EUR 4.3M at risk | Integrate the cancellation-risk score into the reservation workflow (see Predict app) |
""")

st.caption(
    "Source: Phase 2 business analysis (docs/business_analysis_report.md). "
    "Risk scoring available in the Predict app (port 8501)."
)
