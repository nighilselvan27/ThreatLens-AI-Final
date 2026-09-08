import os
import time
import json
import joblib
import pandas as pd

from sklearn.ensemble import ExtraTreesClassifier
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)


print("=" * 70)
print("ThreatLens AI - Extra Trees Hyperparameter Tuning")
print("=" * 70)


# ============================================================
# 1. LOAD DATA
# ============================================================

DATA_PATH = "ml_model/dataset/train_test"

print("\nLoading training data...")

X_train = pd.read_parquet(
    os.path.join(DATA_PATH, "X_train.parquet")
)

y_train = pd.read_parquet(
    os.path.join(DATA_PATH, "y_train.parquet")
).squeeze()

print("Training data loaded.")
print("X_train:", X_train.shape)
print("y_train:", y_train.shape)


print("\nLoading testing data...")

X_test = pd.read_parquet(
    os.path.join(DATA_PATH, "X_test.parquet")
)

y_test = pd.read_parquet(
    os.path.join(DATA_PATH, "y_test.parquet")
).squeeze()

print("Testing data loaded.")
print("X_test:", X_test.shape)
print("y_test:", y_test.shape)


# ============================================================
# 2. BASELINE EXTRA TREES
# ============================================================

print("\n" + "=" * 70)
print("BASELINE EXTRA TREES")
print("=" * 70)

baseline_model = ExtraTreesClassifier(
    n_estimators=100,
    random_state=42,
    n_jobs=2
)

print("\nTraining baseline model...")

start_time = time.time()

baseline_model.fit(X_train, y_train)

baseline_train_time = time.time() - start_time

print(
    f"Baseline Training Time: "
    f"{baseline_train_time:.2f}s"
)


print("\nGenerating baseline predictions...")

start_time = time.time()

baseline_pred = baseline_model.predict(X_test)
baseline_prob = baseline_model.predict_proba(X_test)[:, 1]

baseline_prediction_time = time.time() - start_time


baseline_accuracy = accuracy_score(
    y_test,
    baseline_pred
)

baseline_precision = precision_score(
    y_test,
    baseline_pred,
    zero_division=0
)

baseline_recall = recall_score(
    y_test,
    baseline_pred,
    zero_division=0
)

baseline_f1 = f1_score(
    y_test,
    baseline_pred,
    zero_division=0
)

baseline_auc = roc_auc_score(
    y_test,
    baseline_prob
)

baseline_cm = confusion_matrix(
    y_test,
    baseline_pred
)


print("\nBaseline Results")

print(f"Accuracy       : {baseline_accuracy:.4f}")
print(f"Precision      : {baseline_precision:.4f}")
print(f"Recall         : {baseline_recall:.4f}")
print(f"F1-Score       : {baseline_f1:.4f}")
print(f"ROC-AUC        : {baseline_auc:.4f}")
print(f"Training Time  : {baseline_train_time:.2f}s")
print(f"Prediction Time: {baseline_prediction_time:.2f}s")

print("\nConfusion Matrix:")
print(baseline_cm)


# ============================================================
# 3. HYPERPARAMETER SEARCH
# ============================================================

print("\n" + "=" * 70)
print("EXTRA TREES HYPERPARAMETER TUNING")
print("=" * 70)


param_distributions = {
    "n_estimators": [100, 150, 200],
    "max_depth": [None, 20, 30],
    "min_samples_split": [2, 5, 10],
    "min_samples_leaf": [1, 2, 4],
    "max_features": ["sqrt", 0.5, 1.0]
}


tuning_model = ExtraTreesClassifier(
    random_state=42,
    n_jobs=2
)


search = RandomizedSearchCV(
    estimator=tuning_model,
    param_distributions=param_distributions,
    n_iter=2,
    scoring="f1",
    cv=2,
    random_state=42,
    n_jobs=2,
    verbose=2
)


print("\nStarting RandomizedSearchCV...")

print(
    f"Parameter combinations: "
    f"{search.n_iter}"
)

print(
    f"Cross-validation folds: "
    f"{search.cv}"
)

print(
    f"Total model fits: "
    f"{search.n_iter * search.cv}"
)


tuning_start = time.time()

# IMPORTANT: only ONE search.fit()
search.fit(X_train, y_train)

tuning_time = time.time() - tuning_start


print("\nTuning completed.")

print("\nBest Parameters:")
print(search.best_params_)

print(
    f"\nBest Cross-Validation F1-Score: "
    f"{search.best_score_:.4f}"
)

print(
    f"Tuning Time: "
    f"{tuning_time:.2f}s"
)


# ============================================================
# 4. EVALUATE TUNED MODEL
# ============================================================

best_model = search.best_estimator_

print("\n" + "=" * 70)
print("TUNED EXTRA TREES EVALUATION")
print("=" * 70)


print("\nGenerating tuned predictions...")

start_time = time.time()

tuned_pred = best_model.predict(X_test)
tuned_prob = best_model.predict_proba(X_test)[:, 1]

tuned_prediction_time = time.time() - start_time


tuned_accuracy = accuracy_score(
    y_test,
    tuned_pred
)

tuned_precision = precision_score(
    y_test,
    tuned_pred,
    zero_division=0
)

tuned_recall = recall_score(
    y_test,
    tuned_pred,
    zero_division=0
)

tuned_f1 = f1_score(
    y_test,
    tuned_pred,
    zero_division=0
)

tuned_auc = roc_auc_score(
    y_test,
    tuned_prob
)

tuned_cm = confusion_matrix(
    y_test,
    tuned_pred
)


print("\nTuned Results")

print(f"Accuracy       : {tuned_accuracy:.4f}")
print(f"Precision      : {tuned_precision:.4f}")
print(f"Recall         : {tuned_recall:.4f}")
print(f"F1-Score       : {tuned_f1:.4f}")
print(f"ROC-AUC        : {tuned_auc:.4f}")
print(f"Prediction Time: {tuned_prediction_time:.2f}s")

print("\nConfusion Matrix:")
print(tuned_cm)


# ============================================================
# 5. BASELINE VS TUNED
# ============================================================

print("\n" + "=" * 70)
print("BASELINE VS TUNED EXTRA TREES")
print("=" * 70)


comparison = pd.DataFrame([
    {
        "Model": "Baseline Extra Trees",
        "Accuracy": baseline_accuracy,
        "Precision": baseline_precision,
        "Recall": baseline_recall,
        "F1": baseline_f1,
        "ROC-AUC": baseline_auc,
        "Training Time": baseline_train_time,
        "Prediction Time": baseline_prediction_time
    },
    {
        "Model": "Tuned Extra Trees",
        "Accuracy": tuned_accuracy,
        "Precision": tuned_precision,
        "Recall": tuned_recall,
        "F1": tuned_f1,
        "ROC-AUC": tuned_auc,
        "Training Time": tuning_time,
        "Prediction Time": tuned_prediction_time
    }
])


print("\n")
print(comparison.to_string(index=False))


# ============================================================
# 6. SAVE RESULTS
# ============================================================

os.makedirs(
    "ml_model/results",
    exist_ok=True
)

os.makedirs(
    "ml_model/saved_model",
    exist_ok=True
)


comparison.to_csv(
    "ml_model/results/"
    "extra_trees_baseline_vs_tuned.csv",
    index=False
)


with open(
    "ml_model/results/"
    "extra_trees_best_params.json",
    "w"
) as f:

    json.dump(
        search.best_params_,
        f,
        indent=4
    )


joblib.dump(
    best_model,
    "ml_model/saved_model/"
    "extra_trees_tuned.pkl"
)


print("\nResults saved:")

print(
    "ml_model/results/"
    "extra_trees_baseline_vs_tuned.csv"
)

print(
    "ml_model/results/"
    "extra_trees_best_params.json"
)

print(
    "ml_model/saved_model/"
    "extra_trees_tuned.pkl"
)


print("\n" + "=" * 70)
print("Extra Trees Hyperparameter Tuning Completed")
print("=" * 70)