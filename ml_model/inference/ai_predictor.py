import joblib
import pandas as pd

from ml_model.risk_scoring.risk_scorer import RiskScorer


class AIPredictor:
    """
    ThreatLens AI inference pipeline.

    Takes a 2,381-feature vector and returns:
    - Extra Trees probability
    - LightGBM probability
    - Ensemble malware probability
    - Verdict
    - Risk score
    - Risk level
    """

    EXTRA_TREES_PATH = (
        "ml_model/saved_model/extra_trees_baseline.pkl"
    )

    LIGHTGBM_PATH = (
        "ml_model/saved_model/lightgbm_tuned.pkl"
    )

    EXTRA_TREES_WEIGHT = 0.5
    LIGHTGBM_WEIGHT = 0.5

    THRESHOLD = 0.5

    EXPECTED_FEATURE_COUNT = 2381

    def __init__(self):

        print("Loading ThreatLens AI models...")

        self.extra_trees = joblib.load(
            self.EXTRA_TREES_PATH
        )

        self.lightgbm = joblib.load(
            self.LIGHTGBM_PATH
        )

        print("Extra Trees loaded.")
        print("LightGBM loaded.")
        print("AI models ready.")

    def predict(self, features):
        """
        Generate an AI prediction for one sample.

        Parameters
        ----------
        features:
            A 2,381-feature vector.

        Returns
        -------
        dict:
            Complete AI analysis.
        """

        # ----------------------------------------------------
        # Validate feature count
        # ----------------------------------------------------

        if len(features) != self.EXPECTED_FEATURE_COUNT:

            raise ValueError(
                f"Expected "
                f"{self.EXPECTED_FEATURE_COUNT} features, "
                f"but received {len(features)}."
            )

        # ----------------------------------------------------
        # Convert to DataFrame
        # ----------------------------------------------------

        if isinstance(features, pd.DataFrame):

            X = features.copy()

        else:

            X = pd.DataFrame(
                [features],
                columns=[
                    f"F{i}"
                    for i in range(
                        1,
                        self.EXPECTED_FEATURE_COUNT + 1
                    )
                ]
            )

        # ----------------------------------------------------
        # Model predictions
        # ----------------------------------------------------

        extra_trees_probability = (
            self.extra_trees.predict_proba(X)[0][1]
        )

        lightgbm_probability = (
            self.lightgbm.predict_proba(X)[0][1]
        )

        # ----------------------------------------------------
        # Ensemble probability
        # ----------------------------------------------------

        ensemble_probability = (
            self.EXTRA_TREES_WEIGHT
            * extra_trees_probability
            +
            self.LIGHTGBM_WEIGHT
            * lightgbm_probability
        )

        # ----------------------------------------------------
        # Risk analysis
        # ----------------------------------------------------

        risk_analysis = RiskScorer.analyze(
            ensemble_probability,
            threshold=self.THRESHOLD
        )

        # ----------------------------------------------------
        # Final result
        # ----------------------------------------------------

        result = {
            "verdict": risk_analysis["verdict"],
            "malware_probability": risk_analysis[
                "malware_probability"
            ],
            "risk_score": risk_analysis[
                "risk_score"
            ],
            "risk_level": risk_analysis[
                "risk_level"
            ],
            "model": (
                "Extra Trees + Tuned LightGBM"
            ),
            "ensemble_weights": {
                "extra_trees": self.EXTRA_TREES_WEIGHT,
                "lightgbm": self.LIGHTGBM_WEIGHT
            },
            "model_probabilities": {
                "extra_trees": round(
                    float(extra_trees_probability),
                    4
                ),
                "lightgbm": round(
                    float(lightgbm_probability),
                    4
                )
            }
        }

        return result