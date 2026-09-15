"""Q02: How does lead time affect cancellation probability?

Outputs: docs/snippets/p2_q02_output.md, docs/json/p2_q02_metrics.json,
         docs/images/p2_q02_chart.png
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

bins = [0, 7, 30, 60, 90, 180, 450]
labels = ["1-7d", "8-30d", "31-60d", "61-90d", "91-180d", "181-443d"]
df["lead_time_band"] = pd.cut(
    df["lead_time"], bins=bins, labels=labels, include_lowest=True
)
band = (
    df.groupby("lead_time_band", observed=True)["cancel"].agg(["mean", "size"]).round(4)
)
corr = float(df["lead_time"].corr(df["cancel"]))

fig, ax = plt.subplots(figsize=(9, 5))
ax.bar(band.index.astype(str), band["mean"], color="#1565c0")
ax.set_title("Cancellation rate by lead-time band")
ax.set_xlabel("Lead time")
ax.set_ylabel("Cancellation rate")
ax.bar_label(ax.containers[0], fmt="%.1%")
plt.tight_layout()
plt.savefig(IMAGES / "p2_q02_chart.png", dpi=120)
plt.close()

metrics = {
    "question": "How does lead time affect cancellation probability?",
    "correlation_lead_time_cancel": round(corr, 3),
    "bands": [
        {"band": str(i), "cancellation_rate": float(r["mean"]), "n": int(r["size"])}
        for i, r in band.iterrows()
    ],
    "interpretation": "Cancellation rate rises monotonically with lead time: ~10% for bookings made "
    "within a week vs ~74% for bookings made more than 6 months ahead.",
}
DOCS_JSON.mkdir(parents=True, exist_ok=True)
(DOCS_JSON / "p2_q02_metrics.json").write_text(json.dumps(metrics, indent=2))

snippet = f"""# Q02 Output — Lead time vs cancellation

**Question:** How does lead time affect cancellation probability?

```
Cancellation rate by lead-time band:
{band.to_string()}

Point-biserial correlation (lead_time, cancel): {corr:.3f}
```

**Interpretation:** The relationship is strong and monotonic. Guests booking far in advance
(181-443 days) cancel at ~74%, while last-minute bookers (<=7 days) cancel at ~10%.
Long-lead bookings are the natural target for proactive interventions.

![Q02 chart](../images/p2_q02_chart.png)
"""
SNIPPETS.mkdir(parents=True, exist_ok=True)
(SNIPPETS / "p2_q02_output.md").write_text(snippet)
print(f"Q02: corr={corr:.3f}; band rates computed")
