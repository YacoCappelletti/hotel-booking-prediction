"""Step 2: candidate model training, selection, threshold optimization,
explainer, and artifact persistence.

- Time-based split: train 70% / validation 15% / test 15% by arrival date.
- Preprocessing is re-fit inside every cross-validation fold (no leakage).
- Candidates are cross-validated on train (StratifiedKFold, seed from
  model_config.json); the best configuration per family is refit on the full
  train set and compared on VALIDATION by PR-AUC.
- The decision threshold is optimized on VALIDATION with the cost matrix from
  configs/business_rules.json. The test set is never used for selection or
  tuning; it is evaluated exactly once by scripts/p4_evaluate_final_model.py.
- A SHAP explainer is persisted for per-prediction contributing factors.
"""

import itertools
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import sklearn
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
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
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.features.build_features import (  # noqa: E402
    CATEGORICAL_FEATURES,
    FEATURES,
    NUMERIC_FEATURES,
    POSITIVE_LABEL,
    TARGET,
    arrival_datetime,
    class_sample_weights,
    load_raw,
    temporal_split,
    xy,
)

MODEL_CONFIG = json.loads((ROOT / "configs" / "model_config.json").read_text())
BUSINESS_RULES = json.loads((ROOT / "configs" / "business_rules.json").read_text())
DOCS_JSON = ROOT / "docs" / "json"
IMAGES = ROOT / "docs" / "images"
MODELS = ROOT / "models"

SEED = MODEL_CONFIG["random_seed"]
FOLDS = MODEL_CONFIG["cv"]["folds"]
np.random.seed(SEED)


def make_preprocessor() -> ColumnTransformer:
    """Fresh, unfitted preprocessing transformer (one per pipeline/fold)."""
    return ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                NUMERIC_FEATURES,
            ),
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )


# ---- Data ----
df = load_raw()
train, val, _test = temporal_split(df)  # _test deliberately unused here
X_train, y_train = xy(train)
X_val, y_val = xy(val)

# ---- Candidate model specifications ----
SPECS = {
    "LogisticRegression": (
        lambda p: LogisticRegression(class_weight="balanced", random_state=SEED, **p),
        [
            {"C": c, "max_iter": 1000}
            for c in MODEL_CONFIG["hyperparameter_grids"]["LogisticRegression"]["C"]
        ],
    ),
    "DecisionTreeClassifier": (
        lambda p: DecisionTreeClassifier(
            class_weight="balanced", random_state=SEED, **p
        ),
        [
            dict(zip(("max_depth", "min_samples_leaf"), combo, strict=True))
            for combo in itertools.product(
                MODEL_CONFIG["hyperparameter_grids"]["DecisionTreeClassifier"][
                    "max_depth"
                ],
                MODEL_CONFIG["hyperparameter_grids"]["DecisionTreeClassifier"][
                    "min_samples_leaf"
                ],
            )
        ],
    ),
    "RandomForestClassifier": (
        lambda p: RandomForestClassifier(
            class_weight="balanced", random_state=SEED, n_jobs=-1, **p
        ),
        [
            dict(zip(("n_estimators", "max_depth", "min_samples_leaf"), combo, strict=True))
            for combo in itertools.product(
                MODEL_CONFIG["hyperparameter_grids"]["RandomForestClassifier"][
                    "n_estimators"
                ],
                MODEL_CONFIG["hyperparameter_grids"]["RandomForestClassifier"][
                    "max_depth"
                ],
                MODEL_CONFIG["hyperparameter_grids"]["RandomForestClassifier"][
                    "min_samples_leaf"
                ],
            )
        ],
    ),
    "GradientBoostingClassifier": (
        lambda p: GradientBoostingClassifier(random_state=SEED, **p),
        [
            dict(zip(("n_estimators", "learning_rate", "max_depth"), combo, strict=True))
            for combo in itertools.product(
                MODEL_CONFIG["hyperparameter_grids"]["GradientBoostingClassifier"][
                    "n_estimators"
                ],
                MODEL_CONFIG["hyperparameter_grids"]["GradientBoostingClassifier"][
                    "learning_rate"
                ],
                MODEL_CONFIG["hyperparameter_grids"]["GradientBoostingClassifier"][
                    "max_depth"
                ],
            )
        ],
    ),
}
GB_FAMILY = {"GradientBoostingClassifier"}
sample_weights_train = class_sample_weights(y_train)


def cv_evaluate(name: str, params: dict) -> dict:
    """5-fold StratifiedKFold CV on train; preprocessing fit per fold."""
    skf = StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=SEED)
    factory, _ = SPECS[name]
    scores = []
    for tr_idx, hold_idx in skf.split(np.zeros(len(y_train)), y_train):
        pipe = Pipeline([("pre", make_preprocessor()), ("model", factory(params))])
        Xh_tr, Xh_hold = X_train.iloc[tr_idx], X_train.iloc[hold_idx]
        yh_tr, yh_hold = y_train.iloc[tr_idx], y_train.iloc[hold_idx]
        if name in GB_FAMILY:
            pipe.fit(
                Xh_tr,
                yh_tr,
                model__sample_weight=class_sample_weights(yh_tr),
            )
        else:
            pipe.fit(Xh_tr, yh_tr)
        probs = pipe.predict_proba(Xh_hold)[:, 1]
        scores.append(average_precision_score(yh_hold, probs))
    return {
        "mean": float(np.mean(scores)),
        "std": float(np.std(scores)),
        "scores": [round(s, 4) for s in scores],
    }


# ---- Train + CV all candidates ----
results = []
for name, (_factory, grid) in SPECS.items():
    best_for_model: dict | None = None
    for params in grid:
        cv = cv_evaluate(name, params)
        rec = {
            "model": name,
            "params": params,
            "cv_pr_auc_mean": round(cv["mean"], 4),
            "cv_pr_auc_std": round(cv["std"], 4),
        }
        if best_for_model is None or cv["mean"] > best_for_model["cv_mean"]:
            best_for_model = {**rec, "cv_mean": cv["mean"]}
        results.append(rec)
    print(
        f"{name}: best CV PR-AUC = {best_for_model['cv_mean']:.4f} with {best_for_model['params']}"
    )

# ---- Final preprocessing fitted on full train ----
preprocessor = make_preprocessor()
preprocessor.fit(X_train)
X_train_t = preprocessor.transform(X_train)
X_val_t = preprocessor.transform(X_val)
feature_names = list(preprocessor.get_feature_names_out())


def get_feature_label(name: str) -> str:
    return name.split("__", 1)[-1]


# Refit best config per model on the full transformed train, evaluate on validation
validation_table = []
fitted = {}
for name, (factory, _grid) in SPECS.items():
    best = max(
        [r for r in results if r["model"] == name], key=lambda r: r["cv_pr_auc_mean"]
    )
    model = factory(best["params"])
    if name in GB_FAMILY:
        model.fit(X_train_t, y_train, sample_weight=sample_weights_train)
    else:
        model.fit(X_train_t, y_train)
    probs = model.predict_proba(X_val_t)[:, 1]
    metrics = {
        "cv_pr_auc_mean": best["cv_pr_auc_mean"],
        "cv_pr_auc_std": best["cv_pr_auc_std"],
        "params": best["params"],
        "val_pr_auc": round(float(average_precision_score(y_val, probs)), 4),
        "val_roc_auc": round(float(roc_auc_score(y_val, probs)), 4),
        "val_f1_at_0.5": round(float(f1_score(y_val, (probs >= 0.5).astype(int))), 4),
    }
    validation_table.append({"model": name, **metrics})
    fitted[name] = model
    print(
        f"{name}: val PR-AUC = {metrics['val_pr_auc']:.4f}, ROC-AUC = {metrics['val_roc_auc']:.4f}"
    )

# ---- Select best model on VALIDATION by PR-AUC ----
best_name = max(validation_table, key=lambda r: r["val_pr_auc"])["model"]
best_model = fitted[best_name]
best_params = next(r["params"] for r in validation_table if r["model"] == best_name)
val_probs = best_model.predict_proba(X_val_t)[:, 1]
print(
    f"\nSelected model: {best_name} (validation PR-AUC = {max(r['val_pr_auc'] for r in validation_table):.4f})"
)

# ---- Threshold optimization on VALIDATION with the business cost matrix ----
fn_cost = BUSINESS_RULES["cost_matrix"]["false_negative_cost"]
fp_cost = BUSINESS_RULES["cost_matrix"]["false_positive_cost"]
thresholds = np.linspace(0.01, 0.99, 197)
costs = [
    (
        fn_cost * ((y_val == 1) & (val_probs < t)).sum()
        + fp_cost * ((y_val == 0) & (val_probs >= t)).sum()
    )
    for t in thresholds
]
best_threshold = float(thresholds[int(np.argmin(costs))])
print(
    f"Cost-optimal threshold on validation: {best_threshold:.3f} "
    f"(cost {min(costs):.0f} vs default 0.5 cost "
    f"{fn_cost * ((y_val == 1) & (val_probs < 0.5)).sum() + fp_cost * ((y_val == 0) & (val_probs >= 0.5)).sum():.0f})"
)

val_pred_t = (val_probs >= best_threshold).astype(int)
cm_val = confusion_matrix(y_val, val_pred_t)
final_val_metrics = {
    "threshold": round(best_threshold, 3),
    "accuracy": round(float((val_pred_t == y_val).mean()), 4),
    "precision": round(float(precision_score(y_val, val_pred_t)), 4),
    "recall": round(float(recall_score(y_val, val_pred_t)), 4),
    "f1": round(float(f1_score(y_val, val_pred_t)), 4),
    "roc_auc": round(float(roc_auc_score(y_val, val_probs)), 4),
    "pr_auc": round(float(average_precision_score(y_val, val_probs)), 4),
    "brier": round(float(brier_score_loss(y_val, val_probs)), 4),
    "confusion_matrix": {
        "tn": int(cm_val[0, 0]),
        "fp": int(cm_val[0, 1]),
        "fn": int(cm_val[1, 0]),
        "tp": int(cm_val[1, 1]),
    },
    "expected_cost": int(min(costs)),
}
print(f"Validation metrics at threshold: {final_val_metrics}")

# ---- Global feature importance: permutation importance on validation ----
from sklearn.inspection import permutation_importance  # noqa: E402

perm = permutation_importance(
    best_model,
    X_val_t,
    y_val,
    n_repeats=5,
    random_state=SEED,
    scoring="average_precision",
    n_jobs=-1,
)
importance = sorted(
    [
        {
            "feature": get_feature_label(f),
            "importance_mean": round(float(m), 5),
            "importance_std": round(float(s), 5),
        }
        for f, m, s in zip(feature_names, perm.importances_mean, perm.importances_std, strict=True)
    ],
    key=lambda x: x["importance_mean"],
    reverse=True,
)

# ---- SHAP explainer (persisted for per-prediction contributing factors) ----
background = shap.utils.sample(X_train_t, 500, random_state=SEED)
masker = shap.maskers.Independent(background, max_samples=500)
if best_name == "LogisticRegression":
    explainer = shap.LinearExplainer(
        best_model, background, feature_names=feature_names
    )
else:
    explainer = shap.TreeExplainer(best_model, data=masker, feature_names=feature_names)

# ---- Charts (validation only) ----
IMAGES.mkdir(parents=True, exist_ok=True)
fig, axes = plt.subplots(2, 2, figsize=(14, 11))
for name, model in fitted.items():
    p = model.predict_proba(X_val_t)[:, 1]
    fpr, tpr, _ = roc_curve(y_val, p)
    axes[0, 0].plot(fpr, tpr, label=f"{name} (AUC {roc_auc_score(y_val, p):.3f})")
axes[0, 0].plot([0, 1], [0, 1], "k--", alpha=0.4)
axes[0, 0].set_title("ROC curves (validation)")
axes[0, 0].set_xlabel("FPR")
axes[0, 0].set_ylabel("TPR")
axes[0, 0].legend(fontsize=8)
for name, model in fitted.items():
    p = model.predict_proba(X_val_t)[:, 1]
    prec, rec, _ = precision_recall_curve(y_val, p)
    axes[0, 1].plot(
        rec, prec, label=f"{name} (AP {average_precision_score(y_val, p):.3f})"
    )
axes[0, 1].axhline(y_val.mean(), color="k", ls="--", alpha=0.4, label="base rate")
axes[0, 1].set_title("Precision-Recall curves (validation)")
axes[0, 1].set_xlabel("Recall")
axes[0, 1].set_ylabel("Precision")
axes[0, 1].legend(fontsize=8)
cm_arr = np.array(
    [
        [
            final_val_metrics["confusion_matrix"]["tn"],
            final_val_metrics["confusion_matrix"]["fp"],
        ],
        [
            final_val_metrics["confusion_matrix"]["fn"],
            final_val_metrics["confusion_matrix"]["tp"],
        ],
    ]
)
axes[1, 0].imshow(cm_arr, cmap="Blues")
for (i, j), v in np.ndenumerate(cm_arr):
    axes[1, 0].text(j, i, str(v), ha="center", va="center", fontsize=14)
axes[1, 0].set_xticks([0, 1], ["Pred 0", "Pred 1"])
axes[1, 0].set_yticks([0, 1], ["True 0", "True 1"])
axes[1, 0].set_title(f"Confusion matrix (validation, threshold={best_threshold:.2f})")
frac_pos, mean_pred = calibration_curve(
    y_val, val_probs, n_bins=10, strategy="quantile"
)
axes[1, 1].plot(mean_pred, frac_pos, marker="o", label=best_name)
axes[1, 1].plot([0, 1], [0, 1], "k--", alpha=0.4)
axes[1, 1].set_title("Calibration (validation)")
axes[1, 1].set_xlabel("Mean predicted probability")
axes[1, 1].set_ylabel("Observed positive rate")
axes[1, 1].legend()
plt.tight_layout()
plt.savefig(IMAGES / "model_performance_charts.png", dpi=120)
plt.close()

# Top-15 importance chart
top15 = importance[:15]
fig, ax = plt.subplots(figsize=(9, 6))
ax.barh(
    [d["feature"] for d in top15][::-1],
    [d["importance_mean"] for d in top15][::-1],
    color="#1565c0",
)
ax.set_title(f"Permutation importance, top 15 ({best_name}, validation, PR-AUC drop)")
plt.tight_layout()
plt.savefig(IMAGES / "feature_importance_top15.png", dpi=120)
plt.close()

# ---- Persist artifacts ----
MODELS.mkdir(parents=True, exist_ok=True)
joblib.dump(best_model, MODELS / "final_model.joblib")
joblib.dump(preprocessor, MODELS / "preprocessor.joblib")
joblib.dump(
    {"explainer": explainer, "feature_names": feature_names, "model_name": best_name},
    MODELS / "explainer.joblib",
)


def period_label(part: pd.DataFrame) -> str:
    dates = arrival_datetime(part)
    return f"{dates.min():%b %Y} - {dates.max():%b %Y}"


metadata = {
    "model_name": best_name,
    "model_version": "1.1.0",
    "target": TARGET,
    "positive_class": POSITIVE_LABEL,
    "problem_type": "binary classification",
    "training_timestamp": datetime.now(UTC).isoformat(),
    "random_seed": SEED,
    "feature_list": FEATURES,
    "engineered_features": [
        "total_nights = no_of_week_nights + no_of_weekend_nights",
        "arrival_month_sin / arrival_month_cos = cyclic encoding of arrival_month",
        "rare categories grouped: Meal Plan 3 -> Other; Room_Type 3 -> Other",
    ],
    "excluded_columns": {
        "Booking_ID": "identifier",
        "booking_status": "target label",
        "arrival_year": "split-only (year drift)",
        "arrival_date": "split-only (noise)",
    },
    "preprocessing_summary": {
        "numeric": "median imputer + standard scaler",
        "categorical": "most-frequent imputer + one-hot (handle_unknown=ignore)",
        "fit_on": "train split only (re-fit inside every CV fold)",
    },
    "split_strategy": {
        "type": "time_based",
        "order_by": "arrival date (year-month-day)",
        "ratios": MODEL_CONFIG["split_ratios"],
        "train_period": period_label(train),
        "val_period": period_label(val),
        "test_period": period_label(_test),
        "note": "No booking-creation timestamp exists; arrival date is the best available "
        "temporal proxy. Validation and test periods may show seasonal drift vs train; "
        "the positive rates per split are recorded in the metrics files.",
    },
    "candidate_models": validation_table,
    "selected_params": best_params,
    "selection_metric": "pr_auc (validation)",
    "chosen_decision_threshold": round(best_threshold, 3),
    "threshold_rationale": (
        f"Cost-optimal threshold on validation with FN:FP = {fn_cost}:{fp_cost} from "
        f"configs/business_rules.json. Lower than 0.5 because a missed cancellation (FN) costs ~10x "
        f"an unnecessary retention action (FP); the model trades precision for recall accordingly."
    ),
    "validation_metrics": final_val_metrics,
    "test_metrics": None,  # filled by scripts/p4_evaluate_final_model.py (single evaluation)
    "library_versions": {
        "python": sys.version.split()[0],
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "scikit-learn": sklearn.__version__,
        "shap": shap.__version__,
    },
    "notes_and_limitations": [
        "Temporal drift: validation/test periods may have materially different cancellation rates than train.",
        "Guest-history features require production lookups (conditional availability).",
        "Single anonymized hotel chain; external validity unverified.",
    ],
}
(MODELS / "model_metadata.json").write_text(json.dumps(metadata, indent=2))

# ---- JSON deliverables ----
(DOCS_JSON / "model_performance.json").write_text(
    json.dumps(
        {
            "baseline": json.loads((DOCS_JSON / "baseline_metrics.json").read_text()),
            "candidate_models": validation_table,
            "selected_model": best_name,
            "validation_metrics": final_val_metrics,
            "chosen_threshold": round(best_threshold, 3),
            "test_metrics": None,
        },
        indent=2,
    )
)
(DOCS_JSON / "feature_importance.json").write_text(
    json.dumps(
        {
            "method": "permutation importance (validation, average_precision scoring)",
            "model": best_name,
            "importance": importance,
        },
        indent=2,
    )
)
(DOCS_JSON / "candidate_cv_results.json").write_text(json.dumps(results, indent=2))

print(
    "\nArtifacts saved: models/final_model.joblib, preprocessor.joblib, explainer.joblib, model_metadata.json"
)
print(
    "Top-5 importance:", [(d["feature"], d["importance_mean"]) for d in importance[:5]]
)
