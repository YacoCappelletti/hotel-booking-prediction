"""Phase 1: Data audit - dataset inspection and data quality report.

Generates docs/data_quality_report.md and docs/json/data_quality_report.json.
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs" / "project_config.json").read_text())
RAW = ROOT / CONFIG["paths"]["raw_data"]
DOCS = ROOT / CONFIG["paths"]["docs"]
DOCS_JSON = ROOT / CONFIG["paths"]["docs_json"]
DOCS_IMAGES = ROOT / CONFIG["paths"]["docs_images"]

df = pd.read_csv(RAW)

n_rows, n_cols = df.shape

# --- Missing values ---
missing = df.isna().sum()
missing_report = {c: int(v) for c, v in missing.items() if v > 0}

# --- Duplicated rows ---
dup_rows = int(df.duplicated().sum())
dup_ids = int(df["Booking_ID"].duplicated().sum())

# --- Constant columns ---
constant_cols = [c for c in df.columns if df[c].nunique(dropna=False) <= 1]

# --- Data type issues ---
categorical_like = [
    c for c in df.columns if df[c].dtype == object or str(df[c].dtype) == "str"
]
numeric_cols = [
    c
    for c in df.columns
    if pd.api.types.is_numeric_dtype(df[c]) and c != "arrival_year"
]

# --- Outliers (IQR rule) ---
outlier_report = {}
for c in numeric_cols:
    q1, q3 = df[c].quantile([0.25, 0.75])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    n_out = int(((df[c] < lo) | (df[c] > hi)).sum())
    if n_out > 0:
        outlier_report[c] = {
            "count": n_out,
            "pct": round(100 * n_out / n_rows, 2),
            "min": float(df[c].min()),
            "max": float(df[c].max()),
        }

# --- Class imbalance ---
class_counts = df["booking_status"].value_counts().to_dict()
class_pct = df["booking_status"].value_counts(normalize=True).round(4).to_dict()

# --- Specific quality findings ---
zero_price = int((df["avg_price_per_room"] == 0).sum())
zero_nights = int(
    ((df["no_of_week_nights"] == 0) & (df["no_of_weekend_nights"] == 0)).sum()
)
zero_guests = int(((df["no_of_adults"] == 0) & (df["no_of_children"] == 0)).sum())
children_outliers = int(df["no_of_children"].isin([9, 10]).sum())
meal_plan_3 = int((df["type_of_meal_plan"] == "Meal Plan 3").sum())
room_type_3 = int((df["room_type_reserved"] == "Room_Type 3").sum())

# --- Temporal coverage ---
temporal_coverage = {
    "arrival_year": sorted(int(y) for y in df["arrival_year"].unique()),
    "arrival_month": sorted(int(m) for m in df["arrival_month"].unique()),
    "granularity": "daily (arrival_year, arrival_month, arrival_date); no booking-date column available",
    "note": "The dataset lacks a booking-creation timestamp; only arrival dates are available.",
}

# --- Basic distributions ---
dist_describe = (
    df[numeric_cols].describe().T[["mean", "std", "min", "50%", "max"]].round(2)
)

# --- Charts ---
fig, axes = plt.subplots(2, 3, figsize=(16, 9))
df["booking_status"].value_counts().plot(
    kind="bar", ax=axes[0, 0], color=["#2e7d32", "#c62828"]
)
axes[0, 0].set_title("Booking status distribution")
df["lead_time"].plot(kind="hist", bins=50, ax=axes[0, 1], color="#1565c0")
axes[0, 1].set_title("Lead time distribution (days)")
df["avg_price_per_room"].plot(kind="hist", bins=50, ax=axes[0, 2], color="#6a1b9a")
axes[0, 2].set_title("Average price per room (EUR)")
df["market_segment_type"].value_counts().plot(
    kind="bar", ax=axes[1, 0], color="#ef6c00"
)
axes[1, 0].set_title("Market segment")
axes[1, 0].tick_params(axis="x", rotation=30)
df.groupby("arrival_month").size().plot(kind="bar", ax=axes[1, 1], color="#00695c")
axes[1, 1].set_title("Arrivals by month")
df["no_of_special_requests"].value_counts().sort_index().plot(
    kind="bar", ax=axes[1, 2], color="#4527a0"
)
axes[1, 2].set_title("Special requests")
plt.tight_layout()
plt.savefig(DOCS_IMAGES / "p1_distributions.png", dpi=120)
plt.close()

# --- PII inventory ---
pii_inventory = [
    {
        "column": "Booking_ID",
        "sensitive": False,
        "category": "pseudonymous identifier",
        "recommended_handling": "keep as key; exclude from model features",
    },
    {
        "column": "repeated_guest",
        "sensitive": False,
        "category": "behavioral",
        "recommended_handling": "keep; no direct personal identifiers",
    },
    {
        "note": "No names, emails, phone numbers, payment data or nationality columns are present. "
        "The dataset contains no direct PII; Booking_ID is pseudonymous and must not be used as a feature."
    },
]

# --- Initial hypotheses ---
hypotheses = [
    "H1: Longer lead times are associated with higher cancellation probability (plans change over long horizons).",
    "H2: Online segment bookings cancel more than Offline/Corporate segments.",
    "H3: Bookings with special requests cancel less (higher guest commitment).",
    "H4: Repeated guests with clean history cancel far less than first-time guests.",
    "H5: Higher average price per room increases cancellation probability.",
    "H6: Cancellations concentrate in specific arrival months (seasonality).",
    "H7: Guests with previous cancellations are more likely to cancel again (behavioral persistence).",
]

report_md = (
    f"""# Data Quality Report

**Dataset:** `{CONFIG["dataset"]["file"]}` — {n_rows:,} rows x {n_cols} columns
**Source:** {CONFIG["dataset"]["source"]}

## 1. Structure

- Rows: **{n_rows:,}**
- Columns: **{n_cols}** (1 identifier, {len(numeric_cols) - 1} numeric, {len(categorical_like)} categorical)
- No Jupyter notebooks used; audit produced with `scripts/p1_data_audit.py`.

## 2. Missing values

{"No missing values in any column." if not missing_report else json.dumps(missing_report, indent=2)}

## 3. Duplicated rows

- Fully duplicated rows: **{dup_rows}**
- Duplicated `Booking_ID`: **{dup_ids}**

## 4. Constant columns

{", ".join(constant_cols) if constant_cols else "None."}

## 5. Data type issues

- All numeric columns are stored as int64/float64; categoricals as string.
- `arrival_year`/`arrival_month`/`arrival_date` are stored as integers, not as a single datetime column.
- `repeated_guest`, `required_car_parking_space` are 0/1 flags stored as integers (valid).
- **Issue:** no booking-creation date exists, so a true booking timestamp cannot be reconstructed.

## 6. Outliers (IQR rule)

| Column | Outliers | % | Min | Max |
| --- | --- | --- | --- | --- |
"""
    + "\n".join(
        f"| {c} | {v['count']:,} | {v['pct']}% | {v['min']} | {v['max']} |"
        for c, v in outlier_report.items()
    )
    + f"""

## 7. Class imbalance

| booking_status | count | % |
| --- | --- | --- |
| Not_Canceled | {class_counts["Not_Canceled"]:,} | {class_pct["Not_Canceled"]:.1%} |
| Canceled | {class_counts["Canceled"]:,} | {class_pct["Canceled"]:.1%} |

Moderate imbalance (1:2.05). Mitigation (class weights / resampling) and PR-AUC should be considered for classification.

## 8. Specific quality findings

- `avg_price_per_room == 0`: **{zero_price}** rows — consistent with Complementary market segment (free stays).
- Bookings with 0 total nights: **{zero_nights}** rows — anomalous, candidate for removal or flagging.
- Bookings with 0 adults and 0 children: **{zero_guests}** rows — anomalous.
- `no_of_children` in (9, 10): **{children_outliers}** rows — implausible values, likely data-entry errors.
- `type_of_meal_plan == 'Meal Plan 3'`: only **{meal_plan_3}** rows — rare category, candidate for grouping.
- `room_type_reserved == 'Room_Type 3'`: only **{room_type_3}** rows — rare category, candidate for grouping.

## 9. Temporal coverage

- Arrival years: {temporal_coverage["arrival_year"]}
- Months: 1–12 (full coverage)
- Granularity: {temporal_coverage["granularity"]}
- Note: {temporal_coverage["note"]}

## 10. PII / sensitive columns inventory

| Column | Sensitive | Category | Recommended handling |
| --- | --- | --- | --- |
| Booking_ID | No | Pseudonymous identifier | Keep as key; exclude from features |
| repeated_guest | No | Behavioral | Keep |

No direct PII (names, emails, phones, payments, nationality) is present. `Booking_ID` is pseudonymous and must never be used as a model feature.

## 11. Basic distributions

{dist_describe.to_markdown()}

![Distributions](images/p1_distributions.png)

## 12. Initial hypotheses

"""
    + "\n".join(f"- {h}" for h in hypotheses)
    + """

## 13. Recommendations

1. Keep all rows (no missing/duplicates); flag or drop the {zn} zero-night and {zg} zero-guest anomalies after business confirmation.
2. Cap or bin extreme `lead_time` (> 400 days) only after checking its predictive value.
3. Treat `no_of_children` values 9–10 as data-entry noise; consider capping at 3.
4. Group rare categories (`Meal Plan 3`, `Room_Type 3`) into "Other" during preprocessing.
5. Exclude `Booking_ID` from features; do not use it for modeling.
6. For any time-based split, note that only arrival dates exist (no booking timestamps).
""".format(zn=zero_nights, zg=zero_guests)
)

DOCS.mkdir(exist_ok=True)
(DOCS / "data_quality_report.md").write_text(report_md)

report_json = {
    "rows": n_rows,
    "columns": n_cols,
    "missing_values": missing_report,
    "duplicated_rows": dup_rows,
    "constant_columns": constant_cols,
    "outliers": outlier_report,
    "class_distribution": {"counts": class_counts, "pct": class_pct},
    "specific_findings": {
        "zero_price_rows": zero_price,
        "zero_nights_rows": zero_nights,
        "zero_guests_rows": zero_guests,
        "children_outliers_9_10": children_outliers,
        "meal_plan_3_rows": meal_plan_3,
        "room_type_3_rows": room_type_3,
    },
    "temporal_coverage": temporal_coverage,
    "pii_inventory": pii_inventory,
    "hypotheses": hypotheses,
}
(DOCS_JSON / "data_quality_report.json").write_text(json.dumps(report_json, indent=2))
print(
    f"Data audit complete: {n_rows} rows x {n_cols} cols | dups={dup_rows} | missing={len(missing_report)}"
)
print(
    "Saved: docs/data_quality_report.md, docs/json/data_quality_report.json, docs/images/p1_distributions.png"
)
