"""Step 3: evaluate the final model on the TEST set — exactly once.

This is the ONLY script that touches the test set for evaluation. It loads the
persisted artifacts, computes final test metrics at the validation-chosen
threshold, and updates models/model_metadata.json and
docs/json/model_performance.json. Re-training resets the test metrics in
scripts/p4_train_candidate_models.py, which re-enables this evaluation.
"""

import json
import sys
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.features.build_features import load_raw, temporal_split, xy  # noqa: E402

MODELS = ROOT / "models"
DOCS_JSON = ROOT / "docs" / "json"
IMAGES = ROOT / "docs" / "images"

metadata = json.loads((MODELS / "model_metadata.json").read_text())
assert metadata["test_metrics"] is None, (
    "Test set already evaluated once. Re-run scripts/p4_train_candidate_models.py "
    "to retrain before a new test evaluation."
)

model = joblib.load(MODELS / "final_model.joblib")
preprocessor = joblib.load(MODELS / "preprocessor.joblib")
threshold = metadata["chosen_decision_threshold"]

_, _, test = temporal_split(load_raw())
X_test, y_test = xy(test)
X_test_t = preprocessor.transform(X_test)
probs = model.predict_proba(X_test_t)[:, 1]
preds = (probs >= threshold).astype(int)

cm = confusion_matrix(y_test, preds)
test_metrics = {
    "n_test": int(len(y_test)),
    "test_positive_rate": round(float(y_test.mean()), 4),
    "threshold": threshold,
    "accuracy": round(float((preds == y_test).mean()), 4),
    "precision": round(float(precision_score(y_test, preds)), 4),
    "recall": round(float(recall_score(y_test, preds)), 4),
    "f1": round(float(f1_score(y_test, preds)), 4),
    "roc_auc": round(float(roc_auc_score(y_test, probs)), 4),
    "pr_auc": round(float(average_precision_score(y_test, probs)), 4),
    "brier": round(float(brier_score_loss(y_test, probs)), 4),
    "confusion_matrix": {
        "tn": int(cm[0, 0]),
        "fp": int(cm[0, 1]),
        "fn": int(cm[1, 0]),
        "tp": int(cm[1, 1]),
    },
}
print("Single test-set evaluation:")
for k, v in test_metrics.items():
    print(f"  {k}: {v}")

# ---- Persist ----
metadata["test_metrics"] = test_metrics
metadata["test_evaluated_at"] = pd.Timestamp.now(tz="UTC").isoformat()
(MODELS / "model_metadata.json").write_text(json.dumps(metadata, indent=2))

performance = json.loads((DOCS_JSON / "model_performance.json").read_text())
performance["test_metrics"] = test_metrics
(DOCS_JSON / "model_performance.json").write_text(json.dumps(performance, indent=2))

# Test-set charts (final, single evaluation)
IMAGES.mkdir(parents=True, exist_ok=True)
fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))
fpr, tpr, _ = roc_curve(y_test, probs)
axes[0].plot(fpr, tpr, color="#1565c0", label=f"ROC-AUC {test_metrics['roc_auc']:.3f}")
axes[0].plot([0, 1], [0, 1], "k--", alpha=0.4)
axes[0].set_title("ROC (test, single evaluation)")
axes[0].legend()
prec, rec, _ = precision_recall_curve(y_test, probs)
axes[1].plot(rec, prec, color="#c62828", label=f"PR-AUC {test_metrics['pr_auc']:.3f}")
axes[1].axhline(y_test.mean(), color="k", ls="--", alpha=0.4)
axes[1].set_title("Precision-Recall (test, single evaluation)")
axes[1].legend()
cm_arr = np.array([[cm[0, 0], cm[0, 1]], [cm[1, 0], cm[1, 1]]])
axes[2].imshow(cm_arr, cmap="Blues")
for (i, j), v in np.ndenumerate(cm_arr):
    axes[2].text(j, i, str(v), ha="center", va="center", fontsize=13)
axes[2].set_xticks([0, 1], ["Pred 0", "Pred 1"])
axes[2].set_yticks([0, 1], ["True 0", "True 1"])
axes[2].set_title(f"Confusion matrix (test, thr={threshold})")
plt.tight_layout()
plt.savefig(IMAGES / "test_evaluation_charts.png", dpi=120)
plt.close()
print(
    "Updated: models/model_metadata.json, docs/json/model_performance.json, docs/images/test_evaluation_charts.png"
)
