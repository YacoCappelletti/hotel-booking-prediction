"""Phase 2 Q01: What is the overall cancellation rate and how much revenue is at risk?

Outputs: docs/snippets/p2_q01_output.md, docs/json/p2_q01_metrics.json,
         docs/images/p2_q01_chart.png
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs" / "project_config.json").read_text())
RAW = ROOT / CONFIG["paths"]["raw_data"]
SNIPPETS = ROOT / "docs" / "snippets"
DOCS_JSON = ROOT / "docs" / "json"
IMAGES = ROOT / "docs" / "images"

df = pd.read_csv(RAW)
df["cancel"] = (df["booking_status"] == "Canceled").astype(int)
df["revenue"] = df["avg_price_per_room"] * (
    df["no_of_week_nights"] + df["no_of_weekend_nights"]
)

total_bookings = len(df)
canceled = int(df["cancel"].sum())
cancel_rate = df["cancel"].mean()
total_revenue = float(df["revenue"].sum())
lost_revenue = float(df.loc[df["cancel"] == 1, "revenue"].sum())
pct_revenue_at_risk = lost_revenue / total_revenue
avg_booking_value = float(df.loc[df["cancel"] == 0, "revenue"].mean())

by_year = df.groupby("arrival_year")["cancel"].agg(["mean", "size"]).round(4)

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
axes[0].bar(
    ["Not_Canceled", "Canceled"],
    df["booking_status"].value_counts(),
    color=["#2e7d32", "#c62828"],
)
axes[0].set_title(f"Booking outcomes (cancel rate = {cancel_rate:.1%})")
axes[0].set_ylabel("Bookings")
axes[1].bar(
    ["Total potential", "Lost to cancellations"],
    [total_revenue / 1e6, lost_revenue / 1e6],
    color=["#1565c0", "#c62828"],
)
axes[1].set_title("Revenue at risk (M EUR)")
axes[1].set_ylabel("Million EUR")
for ax in axes:
    ax.bar_label(ax.containers[0], fmt="%.2f")
plt.tight_layout()
plt.savefig(IMAGES / "p2_q01_chart.png", dpi=120)
plt.close()

metrics = {
    "question": "What is the overall cancellation rate and how much revenue is at risk?",
    "total_bookings": total_bookings,
    "canceled_bookings": canceled,
    "cancellation_rate": round(float(cancel_rate), 4),
    "total_potential_revenue_eur": round(total_revenue, 0),
    "lost_revenue_eur": round(lost_revenue, 0),
    "pct_revenue_at_risk": round(float(pct_revenue_at_risk), 4),
    "avg_booking_value_eur": round(avg_booking_value, 0),
    "by_year": {
        str(y): {"rate": float(r["mean"]), "n": int(r["size"])}
        for y, r in by_year.iterrows()
    },
}
DOCS_JSON.mkdir(parents=True, exist_ok=True)
(DOCS_JSON / "p2_q01_metrics.json").write_text(json.dumps(metrics, indent=2))

snippet = f"""# Q01 Output — Overall cancellation rate and revenue at risk

**Question:** What is the overall cancellation rate and how much revenue is at risk?

```
Total bookings:          {total_bookings:,}
Canceled bookings:       {canceled:,}
Cancellation rate:       {cancel_rate:.2%}
Total potential revenue: EUR {total_revenue / 1e6:.2f}M
Lost to cancellations:   EUR {lost_revenue / 1e6:.2f}M  ({pct_revenue_at_risk:.1%} of potential)
Avg booking value:       EUR {avg_booking_value:,.0f}

Cancellation rate by year:
{by_year.to_string()}
```

![Q01 chart](../images/p2_q01_chart.png)
"""
SNIPPETS.mkdir(parents=True, exist_ok=True)
(SNIPPETS / "p2_q01_output.md").write_text(snippet)
print(
    f"Q01: rate={cancel_rate:.2%}, lost revenue=EUR {lost_revenue / 1e6:.2f}M ({pct_revenue_at_risk:.1%})"
)
