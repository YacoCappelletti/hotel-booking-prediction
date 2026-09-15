"""Baseline model: majority-class predictor.

Uses ONLY train data for fitting and validation for reporting.
The test set is never touched here; it is evaluated exactly once by
scripts/p4_evaluate_final_model.py.
"""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.features.build_features import load_raw, temporal_split, xy  # noqa: E402

DOCS_JSON = ROOT / "docs" / "json"

train, val, _ = temporal_split(load_raw())
_, y_train = xy(train)
_, y_val = xy(val)

majority_class = int(y_train.value_counts().idxmax())
val_pred = np.full(len(y_val), majority_class)

tp = int(((y_val == 1) & (val_pred == 1)).sum())
fp = int(((y_val == 0) & (val_pred == 1)).sum())
fn = int(((y_val == 1) & (val_pred == 0)).sum())
tn = int(((y_val == 0) & (val_pred == 0)).sum())

baseline = {
    "model": "majority_class_baseline",
    "majority_class": "Not_Canceled" if majority_class == 0 else "Canceled",
    "train_positive_rate": round(float(y_train.mean()), 4),
    "validation_metrics": {
        "accuracy": round(float((y_val == majority_class).mean()), 4),
        "precision": round(tp / (tp + fp), 4) if (tp + fp) else 0.0,
        "recall": round(tp / (tp + fn), 4) if (tp + fn) else 0.0,
        "f1": round(2 * tp / (2 * tp + fp + fn), 4) if (2 * tp + fp + fn) else 0.0,
        "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "note": "Majority-class baseline: ROC-AUC/PR-AUC undefined (constant scores).",
    },
}
DOCS_JSON.mkdir(parents=True, exist_ok=True)
(DOCS_JSON / "baseline_metrics.json").write_text(json.dumps(baseline, indent=2))
print(f"Baseline: majority class = {baseline['majority_class']}")
print(
    f"Validation accuracy = {baseline['validation_metrics']['accuracy']}, F1 = {baseline['validation_metrics']['f1']}"
)
