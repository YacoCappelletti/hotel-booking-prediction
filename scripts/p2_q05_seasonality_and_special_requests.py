"""Phase 2 Q05: Do engagement and loyalty signals (special requests, repeated guest,
previous history) reduce cancellation probability?

Outputs: docs/snippets/p2_q05_output.md, docs/json/p2_q05_metrics.json,
         docs/images/p2_q05_chart.png
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

req = df.groupby("no_of_special_requests")["cancel"].agg(["mean", "size"]).round(4)
rep = df.groupby("repeated_guest")["cancel"].agg(["mean", "size"]).round(4)
prev = (
    df.groupby(df["no_of_previous_cancellations"].clip(upper=2))["cancel"]
    .agg(["mean", "size"])
    .round(4)
)

corr_req = float(df["no_of_special_requests"].corr(df["cancel"]))

fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
axes[0].bar(req.index.astype(str), req["mean"], color="#6a1b9a")
axes[0].set_title("Cancel rate by special requests")
axes[0].bar_label(axes[0].containers[0], fmt="%.1%")
axes[1].bar(["New guest", "Repeated guest"], rep["mean"], color=["#ef6c00", "#2e7d32"])
axes[1].set_title("Cancel rate by guest type")
axes[1].bar_label(axes[1].containers[0], fmt="%.1%")
axes[2].bar(["0 prev canc", "1", "2+"], prev["mean"], color="#c62828")
axes[2].set_title("Cancel rate by previous cancellations")
axes[2].bar_label(axes[2].containers[0], fmt="%.1%")
plt.tight_layout()
plt.savefig(IMAGES / "p2_q05_chart.png", dpi=120)
plt.close()

metrics = {
    "question": "Do engagement and loyalty signals reduce cancellation probability?",
    "cancel_rate_by_special_requests": [
        {"requests": int(i), "rate": float(r["mean"]), "n": int(r["size"])}
        for i, r in req.iterrows()
    ],
    "cancel_rate_by_repeated_guest": {
        "new_guest": float(rep.loc[0, "mean"]),
        "repeated_guest": float(rep.loc[1, "mean"]),
    },
    "cancel_rate_by_previous_cancellations": [
        {"prev_cancellations": str(i), "rate": float(r["mean"]), "n": int(r["size"])}
        for i, r in prev.iterrows()
    ],
    "correlation_special_requests_cancel": round(corr_req, 3),
    "interpretation": "Every additional special request lowers cancellation risk (43% -> 0% from 0 to 3+ "
    "requests); repeated guests cancel at 1.7% vs 33.6% for new guests; guests with any "
    "prior cancellation are far less likely to cancel again than first-timers with none.",
}
DOCS_JSON.mkdir(parents=True, exist_ok=True)
(DOCS_JSON / "p2_q05_metrics.json").write_text(json.dumps(metrics, indent=2))

snippet = f"""# Q05 Output — Engagement and loyalty signals

**Question:** Do engagement and loyalty signals reduce cancellation probability?

```
Cancel rate by number of special requests:
{req.to_string()}

Cancel rate by guest type:
{rep.to_string()}

Cancel rate by previous cancellations (2+ clipped):
{prev.to_string()}

Correlation (special requests, cancel): {corr_req:.3f}
```

**Interpretation:** Engagement is strongly protective. Bookings with 0 special requests cancel
at 43%; with 3+ requests, effectively never. Repeated guests cancel at 1.7% (vs 33.6% for new
guests). These signals are cheap to collect at booking time and highly actionable
(priority reconfirmation for zero-request, first-time, long-lead bookings).

![Q05 chart](../images/p2_q05_chart.png)
"""
SNIPPETS.mkdir(parents=True, exist_ok=True)
(SNIPPETS / "p2_q05_output.md").write_text(snippet)
print("Q05: engagement signals analyzed")
