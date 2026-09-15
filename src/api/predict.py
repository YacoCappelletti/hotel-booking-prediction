"""Prediction service: loads artifacts once, transforms input, explains with SHAP,
maps probability to business recommendation using configs/business_rules.json."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.features.build_features import add_engineered_features

ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT / "models"
CONFIGS = ROOT / "configs"

logger = logging.getLogger("api.predict")


class PredictionService:
    """Loads model artifacts once at startup and serves predictions."""

    def __init__(self):
        self.model = joblib.load(MODELS / "final_model.joblib")
        self.preprocessor = joblib.load(MODELS / "preprocessor.joblib")
        bundle = joblib.load(MODELS / "explainer.joblib")
        self.explainer = bundle["explainer"]
        self.feature_names = bundle["feature_names"]
        self.metadata = json.loads((MODELS / "model_metadata.json").read_text())
        self.business_rules = json.loads((CONFIGS / "business_rules.json").read_text())
        self.threshold = self.metadata["chosen_decision_threshold"]
        self.version = self.metadata["model_version"]
        logger.info(
            "Model %s v%s loaded (threshold=%.3f)",
            self.metadata["model_name"],
            self.version,
            self.threshold,
        )

    def _risk_band(self, probability: float) -> tuple[str, str]:
        for band in self.business_rules["risk_bands"]:
            # null max_probability = the model's cost-optimal decision threshold
            limit = (
                self.threshold
                if band["max_probability"] is None
                else band["max_probability"]
            )
            if probability <= limit:
                return band["band"], band["recommendation"]
        last = self.business_rules["risk_bands"][-1]
        return last["band"], last["recommendation"]

    def _top_factors(self, shap_values: np.ndarray, k: int = 5) -> list[dict]:
        order = np.argsort(-np.abs(shap_values))[:k]
        return [
            {
                "feature": self._display_name(self.feature_names[i]),
                "contribution": round(float(shap_values[i]), 4),
            }
            for i in order
        ]

    @staticmethod
    def _display_name(raw: str) -> str:
        """Preprocessor prefixes (num__/cat__) removed; one-hot levels readable."""
        name = raw.split("__", 1)[-1]
        return name.replace("_", " ").strip() if raw.startswith("cat__") else name

    def predict(self, bookings: list[dict]) -> list[dict]:
        X = add_engineered_features(pd.DataFrame(bookings))
        X = X[self.metadata["feature_list"]]
        X_t = self.preprocessor.transform(X)
        probs = self.model.predict_proba(X_t)[:, 1]

        # One SHAP call for the whole batch
        sv = self.explainer.shap_values(X_t, check_additivity=False)
        values = np.asarray(sv)
        if values.ndim == 3:  # (n_samples, n_features, n_outputs) layout
            values = values[:, :, 0]

        results = []
        for i, p in enumerate(probs):
            band, recommendation = self._risk_band(float(p))
            results.append(
                {
                    "predicted_probability": round(float(p), 4),
                    "predicted_label": "Canceled"
                    if p >= self.threshold
                    else "Not_Canceled",
                    "risk_band": band,
                    "recommendation": recommendation,
                    "contributing_factors": self._top_factors(values[i]),
                    "model_version": self.version,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
        return results

    def model_card(self) -> dict:
        return {
            "model_name": self.metadata["model_name"],
            "model_version": self.version,
            "target": self.metadata["target"],
            "problem_type": self.metadata["problem_type"],
            "features": self.metadata["feature_list"],
            "decision_threshold": self.threshold,
            "training_timestamp": self.metadata["training_timestamp"],
            "test_metrics": self.metadata["test_metrics"],
            "notes_and_limitations": self.metadata["notes_and_limitations"],
        }
