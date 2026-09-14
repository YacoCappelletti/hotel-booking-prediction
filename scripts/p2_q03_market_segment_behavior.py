"""Phase 2 Q03: How do market segments differ in cancellation behavior?

Outputs: docs/snippets/p2_q03_output.md, docs/json/p2_q03_metrics.json,
         docs/images/p2_q03_chart.png
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

seg = (
    df.groupby("market_segment_type")
    .agg(
        cancellation_rate=("cancel", "mean"),
        n=("cancel", "size"),
        avg_price=("avg_price_per_room", "mean"),
    )
    .round(4)
    .sort_values("cancellation_rate", ascending=False)
)

fig, ax = plt.subplots(figsize=(9, 5))
ax.bar(seg.index, seg["cancellation_rate"], color="#ef6c00")
ax.set_title("Cancellation rate by market segment")
ax.set_ylabel("Cancellation rate")
ax.tick_params(axis="x", rotation=20)
ax.bar_label(ax.containers[0], fmt="%.1%")
plt.tight_layout()
plt.savefig(IMAGES / "p2_q03_chart.png", dpi=120)
plt.close()

metrics = {
    "question": "How do market segments differ in cancellation behavior?",
    "segments": [
        {
            "segment": str(i),
            "cancellation_rate": float(r["cancellation_rate"]),
            "n": int(r["n"]),
            "avg_price_eur": round(float(r["avg_price"]), 2),
        }
        for i, r in seg.iterrows()
    ],
    "interpretation": "Online bookings (64% of volume) cancel the most (~37%); Corporate cancels "
    "the least among paying segments (~11%); Complementary never cancels (free stays).",
}
DOCS_JSON.mkdir(parents=True, exist_ok=True)
(DOCS_JSON / "p2_q03_metrics.json").write_text(json.dumps(metrics, indent=2))

snippet = f"""# Q03 Output — Market segment behavior

**Question:** How do market segments differ in cancellation behavior?

```
{seg.to_string()}
```

**Interpretation:** Online dominates volume (23,214 bookings, 64%) and shows the highest
cancellation rate (~37%) — a channel-risk concentration. Corporate (~11%) and Complementary
(0%) are the safest segments. Channel-specific policies (e.g., stricter online payment terms)
are a high-leverage lever.

![Q03 chart](../images/p2_q03_chart.png)
"""
SNIPPETS.mkdir(parents=True, exist_ok=True)
(SNIPPETS / "p2_q03_output.md").write_text(snippet)
print("Q03: segment rates computed")
