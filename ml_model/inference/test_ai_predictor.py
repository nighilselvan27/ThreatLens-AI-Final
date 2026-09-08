import pandas as pd

from ml_model.inference.ai_predictor import AIPredictor


# ============================================================
# LOAD TEST DATA
# ============================================================

print("=" * 60)
print("THREATLENS AI INFERENCE TEST")
print("=" * 60)

print("\nLoading test data...")

X_test = pd.read_parquet(
    "ml_model/dataset/train_test/X_test.parquet"
)

print(
    f"Test data loaded: {X_test.shape}"
)


# ============================================================
# TAKE ONE SAMPLE
# ============================================================

sample = X_test.iloc[0].tolist()

print(
    f"Sample feature count: {len(sample)}"
)


# ============================================================
# LOAD AI PREDICTOR
# ============================================================

print("\nInitializing AI Predictor...")

predictor = AIPredictor()


# ============================================================
# PREDICT
# ============================================================

print("\nRunning AI prediction...")

result = predictor.predict(sample)


# ============================================================
# DISPLAY RESULT
# ============================================================

print("\n" + "=" * 60)
print("AI PREDICTION RESULT")
print("=" * 60)

print(
    f"Verdict             : "
    f"{result['verdict']}"
)

print(
    f"Malware Probability : "
    f"{result['malware_probability']:.4f}"
)

print(
    f"Risk Score          : "
    f"{result['risk_score']}/100"
)

print(
    f"Risk Level          : "
    f"{result['risk_level']}"
)

print(
    f"Model               : "
    f"{result['model']}"
)

print("\nModel Probabilities:")

print(
    f"Extra Trees         : "
    f"{result['model_probabilities']['extra_trees']}"
)

print(
    f"LightGBM            : "
    f"{result['model_probabilities']['lightgbm']}"
)

print("\nEnsemble Weights:")

print(
    f"Extra Trees         : "
    f"{result['ensemble_weights']['extra_trees']}"
)

print(
    f"LightGBM            : "
    f"{result['ensemble_weights']['lightgbm']}"
)

print("\n" + "=" * 60)
print("AI INFERENCE TEST COMPLETED")
print("=" * 60)