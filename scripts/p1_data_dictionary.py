"""Phase 1: Data dictionary generator.

Generates docs/data_dictionary.md and docs/json/data_dictionary.json with
per-column metadata: description, dtype, values, missing/unique counts,
business meaning, feature usability, factual target-candidate flag,
leakage potential, PII, and temporal flags.
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs" / "project_config.json").read_text())
RAW = ROOT / CONFIG["paths"]["raw_data"]
DOCS = ROOT / CONFIG["paths"]["docs"]
DOCS_JSON = ROOT / CONFIG["paths"]["docs_json"]

df = pd.read_csv(RAW)

# Column metadata. candidate_target is a FACTUAL flag only (G1): no evaluation,
# ranking, or proposal happens here — that is Phase 3's responsibility.
META = {
    "Booking_ID": {
        "description": "Unique booking identifier.",
        "business_meaning": "Traceability key for each reservation record.",
        "possible_values": "INN##### (unique per row)",
        "usable_as_feature": "no",
        "candidate_target": "no",
        "leakage": {
            "potential": "no",
            "reason": "Unique identifier with no predictive signal; excluded by policy.",
        },
        "pii": {"sensitive": "no", "category": "pseudonymous identifier"},
        "temporal": "no",
    },
    "no_of_adults": {
        "description": "Number of adults in the booking.",
        "business_meaning": "Party size; drives room allocation and pricing.",
        "possible_values": "0-4 (int)",
        "usable_as_feature": "yes",
        "candidate_target": "no",
        "leakage": {"potential": "no", "reason": "Known at booking time."},
        "pii": {"sensitive": "no", "category": "none"},
        "temporal": "no",
    },
    "no_of_children": {
        "description": "Number of children in the booking.",
        "business_meaning": "Party composition; family segment indicator.",
        "possible_values": "0-10 (int; values 9-10 are rare, likely entry errors)",
        "usable_as_feature": "yes",
        "candidate_target": "no",
        "leakage": {"potential": "no", "reason": "Known at booking time."},
        "pii": {"sensitive": "no", "category": "none"},
        "temporal": "no",
    },
    "no_of_weekend_nights": {
        "description": "Number of weekend nights (Saturday/Sunday) booked.",
        "business_meaning": "Stay length component; leisure-travel indicator.",
        "possible_values": "0-7 (int)",
        "usable_as_feature": "yes",
        "candidate_target": "no",
        "leakage": {"potential": "no", "reason": "Known at booking time."},
        "pii": {"sensitive": "no", "category": "none"},
        "temporal": "no",
    },
    "no_of_week_nights": {
        "description": "Number of week nights (Monday-Friday) booked.",
        "business_meaning": "Stay length component; business-travel indicator.",
        "possible_values": "0-17 (int)",
        "usable_as_feature": "yes",
        "candidate_target": "no",
        "leakage": {"potential": "no", "reason": "Known at booking time."},
        "pii": {"sensitive": "no", "category": "none"},
        "temporal": "no",
    },
    "type_of_meal_plan": {
        "description": "Meal plan selected by the guest.",
        "business_meaning": "Ancillary spend and commitment signal.",
        "possible_values": "Meal Plan 1, Meal Plan 2, Meal Plan 3, Not Selected",
        "usable_as_feature": "yes",
        "candidate_target": "no",
        "leakage": {"potential": "no", "reason": "Selected at booking time."},
        "pii": {"sensitive": "no", "category": "none"},
        "temporal": "no",
    },
    "required_car_parking_space": {
        "description": "Whether the guest requires a parking space (0/1).",
        "business_meaning": "Arrival-mode proxy; commitment signal.",
        "possible_values": "0, 1",
        "usable_as_feature": "yes",
        "candidate_target": "no",
        "leakage": {"potential": "no", "reason": "Requested at booking time."},
        "pii": {"sensitive": "no", "category": "none"},
        "temporal": "no",
    },
    "room_type_reserved": {
        "description": "Room type reserved by the guest (anonymized categories).",
        "business_meaning": "Product mix and price-tier proxy.",
        "possible_values": "Room_Type 1..7",
        "usable_as_feature": "yes",
        "candidate_target": "no",
        "leakage": {"potential": "no", "reason": "Chosen at booking time."},
        "pii": {"sensitive": "no", "category": "none"},
        "temporal": "no",
    },
    "lead_time": {
        "description": "Days between booking date and arrival date.",
        "business_meaning": "Planning horizon; strong behavioral driver of cancellations.",
        "possible_values": "0-443 (int)",
        "usable_as_feature": "yes",
        "candidate_target": "no",
        "leakage": {"potential": "no", "reason": "Fully known at booking time."},
        "pii": {"sensitive": "no", "category": "none"},
        "temporal": "conditional (derived from an implicit booking date; the booking date itself is not in the data)",
    },
    "arrival_year": {
        "description": "Year of arrival.",
        "business_meaning": "Temporal context for seasonality and trend analysis.",
        "possible_values": "2017, 2018",
        "usable_as_feature": "conditional",
        "candidate_target": "no",
        "leakage": {"potential": "no", "reason": "Known at booking time."},
        "pii": {"sensitive": "no", "category": "none"},
        "temporal": "yes",
    },
    "arrival_month": {
        "description": "Month of arrival (1-12).",
        "business_meaning": "Seasonality driver for demand and cancellations.",
        "possible_values": "1-12 (int)",
        "usable_as_feature": "yes",
        "candidate_target": "no",
        "leakage": {"potential": "no", "reason": "Known at booking time."},
        "pii": {"sensitive": "no", "category": "none"},
        "temporal": "yes",
    },
    "arrival_date": {
        "description": "Day of month of arrival (1-31).",
        "business_meaning": "Fine-grained timing; combined with year/month gives arrival day.",
        "possible_values": "1-31 (int)",
        "usable_as_feature": "yes",
        "candidate_target": "no",
        "leakage": {"potential": "no", "reason": "Known at booking time."},
        "pii": {"sensitive": "no", "category": "none"},
        "temporal": "yes",
    },
    "market_segment_type": {
        "description": "Market segment designation of the booking.",
        "business_meaning": "Channel strategy; different segments show different cancellation behavior.",
        "possible_values": "Online, Offline, Corporate, Complementary, Aviation",
        "usable_as_feature": "yes",
        "candidate_target": "no",
        "leakage": {"potential": "no", "reason": "Assigned at booking time."},
        "pii": {"sensitive": "no", "category": "none"},
        "temporal": "no",
    },
    "repeated_guest": {
        "description": "Whether the guest is a repeat customer (0/1).",
        "business_meaning": "Loyalty signal; repeat guests behave differently.",
        "possible_values": "0, 1",
        "usable_as_feature": "yes",
        "candidate_target": "no",
        "leakage": {
            "potential": "conditional",
            "reason": "Known at booking time for actual repeat guests; for new guests it is 0 by definition, which is valid at prediction time.",
        },
        "pii": {"sensitive": "no", "category": "behavioral"},
        "temporal": "no",
    },
    "no_of_previous_cancellations": {
        "description": "Number of previous bookings canceled by this guest.",
        "business_meaning": "Guest cancellation history; behavioral risk signal.",
        "possible_values": "0-13 (int)",
        "usable_as_feature": "yes",
        "candidate_target": "no",
        "leakage": {
            "potential": "conditional",
            "reason": "Requires guest history lookup at prediction time; valid if history is available in production.",
        },
        "pii": {"sensitive": "no", "category": "behavioral"},
        "temporal": "no",
    },
    "no_of_previous_bookings_not_canceled": {
        "description": "Number of previous bookings not canceled by this guest.",
        "business_meaning": "Guest fulfillment history; reliability signal.",
        "possible_values": "0-58 (int)",
        "usable_as_feature": "yes",
        "candidate_target": "no",
        "leakage": {
            "potential": "conditional",
            "reason": "Requires guest history lookup at prediction time; valid if history is available in production.",
        },
        "pii": {"sensitive": "no", "category": "behavioral"},
        "temporal": "no",
    },
    "avg_price_per_room": {
        "description": "Average price per day of the reservation (EUR).",
        "business_meaning": "Price sensitivity driver; direct revenue input.",
        "possible_values": "0-540 (float; 0 for complementary stays)",
        "usable_as_feature": "yes",
        "candidate_target": "no",
        "leakage": {
            "potential": "no",
            "reason": "Known at booking time (quoted rate).",
        },
        "pii": {"sensitive": "no", "category": "none"},
        "temporal": "no",
    },
    "no_of_special_requests": {
        "description": "Number of special requests made by the guest (e.g., high floor, view).",
        "business_meaning": "Engagement/commitment signal.",
        "possible_values": "0-5 (int)",
        "usable_as_feature": "yes",
        "candidate_target": "no",
        "leakage": {"potential": "no", "reason": "Known before arrival."},
        "pii": {"sensitive": "no", "category": "none"},
        "temporal": "no",
    },
    "booking_status": {
        "description": "Final status of the booking: Canceled or Not_Canceled.",
        "business_meaning": "Outcome of the reservation lifecycle; measures realized revenue loss when Canceled.",
        "possible_values": "Canceled, Not_Canceled",
        "usable_as_feature": "no (outcome label)",
        "candidate_target": "yes (factual flag only — evaluation deferred to Phase 3)",
        "leakage": {
            "potential": "n/a",
            "reason": "This is the outcome label, not a feature.",
        },
        "pii": {"sensitive": "no", "category": "none"},
        "temporal": "no",
    },
}

records = []
for col in df.columns:
    m = META.get(col, {})
    s = df[col]
    records.append(
        {
            "name": col,
            "dtype": str(s.dtype),
            "description": m.get("description", ""),
            "business_meaning": m.get("business_meaning", ""),
            "possible_values": m.get("possible_values", "see data"),
            "missing_count": int(s.isna().sum()),
            "unique_count": int(s.nunique()),
            "example_values": [str(x) for x in s.dropna().unique()[:3]],
            "usable_as_feature": m.get("usable_as_feature", "unknown"),
            "candidate_target_flag": m.get("candidate_target", "no"),
            "leakage": m.get("leakage", {"potential": "unknown", "reason": ""}),
            "pii": m.get("pii", {"sensitive": "no", "category": "none"}),
            "temporal": m.get("temporal", "no"),
        }
    )

# --- Markdown ---
lines = [
    "# Data Dictionary",
    "",
    f"**Dataset:** `{CONFIG['dataset']['file']}` — {len(df):,} rows x {len(df.columns)} columns",
    "",
    "> Note: the `candidate_target` column is a **factual flag only** (rule G1).",
    "> No target evaluation, ranking, or selection is performed in Phase 1.",
    "",
    "| Name | Type | Description | Possible values | Missing | Unique | Example | Usable as feature | Candidate target (factual) | Leakage | PII | Temporal |",
    "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
]
for r in records:
    ex = ", ".join(r["example_values"][:2])
    lines.append(
        f"| `{r['name']}` | {r['dtype']} | {r['description']} | {r['possible_values']} | "
        f"{r['missing_count']} | {r['unique_count']:,} | {ex} | {r['usable_as_feature']} | "
        f"{r['candidate_target_flag']} | {r['leakage']['potential']} | {r['pii']['sensitive']} | {r['temporal']} |"
    )

lines += [
    "",
    "## Business meaning per column",
    "",
]
for r in records:
    lines.append(f"- **`{r['name']}`** — {r['business_meaning']}")

lines += [
    "",
    "## PII / sensitive columns",
    "",
    "- `Booking_ID`: pseudonymous identifier — keep as key, exclude from features.",
    "- No direct PII (names, emails, phones, payments, nationality) present.",
    "",
    "## Temporal columns",
    "",
    "- `arrival_year`, `arrival_month`, `arrival_date`: arrival date components (temporal).",
    "- `lead_time`: derived temporal feature (days between booking and arrival).",
    "- No booking-creation timestamp exists in the dataset.",
]

(DOCS / "data_dictionary.md").write_text("\n".join(lines) + "\n")
(DOCS_JSON / "data_dictionary.json").write_text(
    json.dumps({"columns": records}, indent=2)
)
print(f"Data dictionary: {len(records)} columns documented")
print("Saved: docs/data_dictionary.md, docs/json/data_dictionary.json")
