"""Q04: What is the revenue impact of cancellations by arrival month (seasonality)?

Outputs: docs/snippets/p2_q04_output.md, docs/json/p2_q04_metrics.json,
         docs/images/p2_q04_chart.png
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

monthly = (
    df.groupby("arrival_month")
    .agg(
        bookings=("cancel", "size"),
        cancellation_rate=("cancel", "mean"),
        lost_revenue=(
            "revenue",
            lambda s: float(s[df.loc[s.index, "cancel"] == 1].sum()),
        ),
    )
    .round(4)
)

top_loss = monthly.sort_values("lost_revenue", ascending=False).head(3)
top_loss_share = float(top_loss["lost_revenue"].sum() / monthly["lost_revenue"].sum())
total_lost = float(monthly["lost_revenue"].sum())

fig, ax1 = plt.subplots(figsize=(11, 5))
ax1.bar(
    monthly.index,
    monthly["lost_revenue"] / 1e3,
    color="#c62828",
    alpha=0.75,
    label="Lost revenue (k EUR)",
)
ax1.set_xlabel("Arrival month")
ax1.set_ylabel("Lost revenue (k EUR)")
ax2 = ax1.twinx()
ax2.plot(
    monthly.index,
    monthly["cancellation_rate"],
    color="#1565c0",
    marker="o",
    label="Cancellation rate",
)
ax2.set_ylabel("Cancellation rate")
ax1.set_title("Monthly lost revenue and cancellation rate")
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc="upper left")
plt.tight_layout()
plt.savefig(IMAGES / "p2_q04_chart.png", dpi=120)
plt.close()

metrics = {
    "question": "What is the revenue impact of cancellations by arrival month?",
    "total_lost_revenue_eur": round(total_lost, 0),
    "top_loss_months": [
        {
            "month": int(m),
            "lost_revenue_eur": round(float(r["lost_revenue"]), 0),
            "cancellation_rate": float(r["cancellation_rate"]),
            "bookings": int(r["bookings"]),
        }
        for m, r in top_loss.iterrows()
    ],
    "top3_months_share_of_lost_revenue": round(top_loss_share, 4),
    "monthly": [
        {
            "month": int(m),
            "bookings": int(r["bookings"]),
            "cancellation_rate": float(r["cancellation_rate"]),
            "lost_revenue_eur": round(float(r["lost_revenue"]), 0),
        }
        for m, r in monthly.iterrows()
    ],
    "interpretation": "Lost revenue concentrates in the high-season months (Aug/Oct peak in volume); "
    "the top-3 months account for a disproportionate share of the total loss.",
}
DOCS_JSON.mkdir(parents=True, exist_ok=True)
(DOCS_JSON / "p2_q04_metrics.json").write_text(json.dumps(metrics, indent=2))

snippet = f"""# Q04 Output — Revenue impact of cancellations by month

**Question:** What is the revenue impact of cancellations by arrival month?

```
Total lost revenue: EUR {total_lost / 1e6:.2f}M

Top-3 loss months:
{top_loss.round(2).to_string()}

Top-3 months share of total lost revenue: {top_loss_share:.1%}
```

**Interpretation:** Losses concentrate in peak-demand months (highest absolute lost revenue in
months with the most bookings). Protecting revenue in these months (overbooking buffers,
deposits, proactive reconfirmation) has the highest financial leverage.

![Q04 chart](../images/p2_q04_chart.png)
"""
SNIPPETS.mkdir(parents=True, exist_ok=True)
(SNIPPETS / "p2_q04_output.md").write_text(snippet)
print(f"Q04: total lost EUR {total_lost / 1e6:.2f}M; top-3 share {top_loss_share:.1%}")
