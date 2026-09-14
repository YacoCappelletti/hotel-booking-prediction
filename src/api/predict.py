"""Prediction service: loads artifacts once, transforms input, explains with SHAP,
maps probability to business recommendation using configs/business_rules.json."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

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

    def _to_frame(self, data: dict) -> pd.DataFrame:
        df = pd.DataFrame([data])
        df["total_nights"] = df["no_of_week_nights"] + df["no_of_weekend_nights"]
        df["type_of_meal_plan"] = df["type_of_meal_plan"].replace(
            {"Meal Plan 3": "Other"}
        )
        df["room_type_reserved"] = df["room_type_reserved"].replace(
            {"Room_Type 3": "Other"}
        )
        return df

    def _risk_band(self, probability: float) -> tuple[str, str]:
        for band in self.business_rules["risk_bands"]:
            if probability <= band["max_probability"]:
                return band["band"], band["recommendation"]
        last = self.business_rules["risk_bands"][-1]
        return last["band"], last["recommendation"]

    def _top_factors(self, X_t, k: int = 5) -> list[dict]:
        sv = self.explainer.shap_values(X_t, check_additivity=False)
        values = np.asarray(sv)
        if values.ndim == 3:  # (n_samples, n_features, n_outputs) layout
            values = values[:, :, 0]
        values = values[0]
        order = np.argsort(-np.abs(values))[:k]
        return [
            {
                "feature": self.feature_names[i],
                "contribution": round(float(values[i]), 4),
            }
            for i in order
        ]

    def predict(self, bookings: list[dict]) -> list[dict]:
        frames = [self._to_frame(b) for b in bookings]
        X = pd.concat(frames, ignore_index=True)
        feature_cols = self.metadata["feature_list"]
        X = X[feature_cols]
        X_t = self.preprocessor.transform(X)
        probs = self.model.predict_proba(X_t)[:, 1]
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
                    "contributing_factors": self._top_factors(X_t[i : i + 1]),
                    "model_version": self.version,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        return results

    def model_card(self) -> dict:
        return {
            "model_name": self.metadata["model_name"],
            "model_version": self.version,
            "approved_target": self.metadata["approved_target"],
            "problem_type": self.metadata["problem_type"],
            "features": self.metadata["feature_list"],
            "decision_threshold": self.threshold,
            "training_timestamp": self.metadata["training_timestamp"],
            "test_metrics": self.metadata["test_metrics"],
            "notes_and_limitations": self.metadata["notes_and_limitations"],
        }
