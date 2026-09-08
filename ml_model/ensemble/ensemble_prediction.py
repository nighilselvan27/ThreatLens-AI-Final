import os
import time
import joblib
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)

from ml_model.risk_scoring.risk_scorer import RiskScorer


# ============================================================
# CONFIGURATION
# ============================================================

DATA_PATH = "ml_model/dataset/train_test"

EXTRA_TREES_PATH = (
    "ml_model/saved_model/extra_trees_baseline.pkl"
)

LIGHTGBM_PATH = (
    "ml_model/saved_model/lightgbm_tuned.pkl"
)

RESULT_PATH = (
    "ml_model/results/ensemble_results.csv"
)

PREDICTION_RESULT_PATH = (
    "ml_model/results/ensemble_predictions.csv"
)


# Ensemble weights
EXTRA_TREES_WEIGHT = 0.5
LIGHTGBM_WEIGHT = 0.5

THRESHOLD = 0.5


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("ThreatLens AI - Ensemble Prediction")
print("=" * 70)


# ============================================================
# LOAD TEST DATA
# ============================================================

print("\nLoading test data...")

X_test = pd.read_parquet(
    os.path.join(DATA_PATH, "X_test.parquet")
)

y_test = pd.read_parquet(
    os.path.join(DATA_PATH, "y_test.parquet")
).squeeze()


print("Test data loaded.")

print("X_test:", X_test.shape)
print("y_test:", y_test.shape)


# ============================================================
# LOAD EXTRA TREES
# ============================================================

print("\nLoading Baseline Extra Trees...")

extra_trees = joblib.load(
    EXTRA_TREES_PATH
)

print("Extra Trees loaded.")


# ============================================================
# LOAD LIGHTGBM
# ============================================================

print("\nLoading Tuned LightGBM...")

lightgbm = joblib.load(
    LIGHTGBM_PATH
)

print("LightGBM loaded.")


# ============================================================
# EXTRA TREES PREDICTION
# ============================================================

print("\nRunning Extra Trees predictions...")

start_time = time.time()

extra_trees_prob = extra_trees.predict_proba(
    X_test
)[:, 1]

extra_trees_prediction_time = (
    time.time() - start_time
)


print(
    f"Extra Trees Prediction Time: "
    f"{extra_trees_prediction_time:.2f} seconds"
)


# ============================================================
# LIGHTGBM PREDICTION
# ============================================================

print("\nRunning LightGBM predictions...")

start_time = time.time()

lightgbm_prob = lightgbm.predict_proba(
    X_test
)[:, 1]

lightgbm_prediction_time = (
    time.time() - start_time
)


print(
    f"LightGBM Prediction Time: "
    f"{lightgbm_prediction_time:.2f} seconds"
)


# ============================================================
# ENSEMBLE
# ============================================================

print("\nCombining model probabilities...")

ensemble_probability = (
    EXTRA_TREES_WEIGHT * extra_trees_prob
    +
    LIGHTGBM_WEIGHT * lightgbm_prob
)


# Convert probability into class prediction
ensemble_prediction = (
    ensemble_probability >= THRESHOLD
).astype(int)


# ============================================================
# RISK SCORING
# ============================================================

print("\nCalculating AI risk scores...")

risk_scores = []
risk_levels = []
verdicts = []

for probability in ensemble_probability:

    risk_analysis = RiskScorer.analyze(
        probability,
        threshold=THRESHOLD
    )

    verdicts.append(
        risk_analysis["verdict"]
    )

    risk_scores.append(
        risk_analysis["risk_score"]
    )

    risk_levels.append(
        risk_analysis["risk_level"]
    )


print("Risk scoring completed.")


# ============================================================
# EVALUATION
# ============================================================

accuracy = accuracy_score(
    y_test,
    ensemble_prediction
)

precision = precision_score(
    y_test,
    ensemble_prediction,
    zero_division=0
)

recall = recall_score(
    y_test,
    ensemble_prediction,
    zero_division=0
)

f1 = f1_score(
    y_test,
    ensemble_prediction,
    zero_division=0
)

roc_auc = roc_auc_score(
    y_test,
    ensemble_probability
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    y_test,
    ensemble_prediction
)


# ============================================================
# RESULTS
# ============================================================

print("\n" + "=" * 70)
print("ENSEMBLE EVALUATION RESULTS")
print("=" * 70)

print(f"Extra Trees Weight : {EXTRA_TREES_WEIGHT}")
print(f"LightGBM Weight    : {LIGHTGBM_WEIGHT}")
print(f"Decision Threshold : {THRESHOLD}")

print("\nAccuracy  :", round(accuracy, 4))
print("Precision :", round(precision, 4))
print("Recall    :", round(recall, 4))
print("F1-Score  :", round(f1, 4))
print("ROC-AUC   :", round(roc_auc, 4))

print("\nConfusion Matrix:")
print(cm)


# ============================================================
# SAMPLE AI RESULTS
# ============================================================

print("\n" + "=" * 70)
print("SAMPLE AI RISK RESULTS")
print("=" * 70)

for i in range(min(10, len(ensemble_probability))):

    print(
        f"\nSample {i + 1}"
    )

    print(
        f"Malware Probability : "
        f"{ensemble_probability[i]:.4f}"
    )

    print(
        f"Risk Score          : "
        f"{risk_scores[i]}/100"
    )

    print(
        f"Risk Level          : "
        f"{risk_levels[i]}"
    )

    print(
        f"Verdict             : "
        f"{verdicts[i]}"
    )


# ============================================================
# SAVE OVERALL RESULTS
# ============================================================

os.makedirs(
    "ml_model/results",
    exist_ok=True
)

results = pd.DataFrame([
    {
        "Model": "Extra Trees + Tuned LightGBM Ensemble",
        "Extra Trees Weight": EXTRA_TREES_WEIGHT,
        "LightGBM Weight": LIGHTGBM_WEIGHT,
        "Threshold": THRESHOLD,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
        "ROC-AUC": roc_auc,
        "Extra Trees Prediction Time": extra_trees_prediction_time,
        "LightGBM Prediction Time": lightgbm_prediction_time
    }
])


results.to_csv(
    RESULT_PATH,
    index=False
)


# ============================================================
# SAVE PER-SAMPLE PREDICTIONS
# ============================================================

prediction_results = pd.DataFrame({
    "Actual_Label": y_test.values,
    "Extra_Trees_Probability": extra_trees_prob,
    "LightGBM_Probability": lightgbm_prob,
    "Ensemble_Malware_Probability": ensemble_probability,
    "Prediction": ensemble_prediction,
    "Verdict": verdicts,
    "Risk_Score": risk_scores,
    "Risk_Level": risk_levels
})


prediction_results.to_csv(
    PREDICTION_RESULT_PATH,
    index=False
)


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\nOverall results saved to:")
print(RESULT_PATH)

print("\nPer-sample AI predictions saved to:")
print(PREDICTION_RESULT_PATH)

print("\n" + "=" * 70)
print("ENSEMBLE + RISK SCORING COMPLETED")
print("=" * 70)