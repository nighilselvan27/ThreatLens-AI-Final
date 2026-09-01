import os
import json
import gc
import time

import pandas as pd

from sklearn.ensemble import ExtraTreesClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score
)

from lightgbm import LGBMClassifier


# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_STATE = 42
N_SPLITS = 5

DATA_PATH = "ml_model/dataset/train_test"
RESULTS_PATH = "ml_model/results"

# Keep CPU usage controlled for an 8 GB RAM machine
EXTRA_TREES_JOBS = 2
LIGHTGBM_JOBS = 2


# ============================================================
# LOAD 160,000 TRAINING SAMPLES ONLY
# ============================================================

print("=" * 70)
print("ThreatLens AI - 5-Fold Cross-Validation")
print("=" * 70)

print("\nLoading training data...")

X_train = pd.read_parquet(
    os.path.join(DATA_PATH, "X_train.parquet")
)

y_train = pd.read_parquet(
    os.path.join(DATA_PATH, "y_train.parquet")
).squeeze()

print("\nTraining data loaded.")
print("X_train shape:", X_train.shape)
print("y_train shape:", y_train.shape)

print("\nUsing ALL 160,000 training samples.")

print("IMPORTANT:")
print("The 40,000 test samples are NOT loaded or used.")


# ============================================================
# LOAD ACTUAL TUNED LIGHTGBM PARAMETERS
# ============================================================

params_path = os.path.join(
    RESULTS_PATH,
    "lightgbm_best_params.json"
)

print("\nLoading tuned LightGBM parameters...")

with open(params_path, "r") as f:
    lightgbm_params = json.load(f)

print("Tuned LightGBM parameters:")
print(lightgbm_params)


# ============================================================
# BASELINE EXTRA TREES PARAMETERS
# MATCHES TEAMMATE'S train_extra_trees.py
# ============================================================

extra_trees_params = {
    "n_estimators": 100,
    "max_depth": 25,
    "min_samples_leaf": 2,
    "max_features": "sqrt",
    "class_weight": "balanced",
    "random_state": RANDOM_STATE,
    "n_jobs": EXTRA_TREES_JOBS
}


# ============================================================
# 5-FOLD STRATIFIED CROSS-VALIDATION
# ============================================================

cv = StratifiedKFold(
    n_splits=N_SPLITS,
    shuffle=True,
    random_state=RANDOM_STATE
)


# ============================================================
# FUNCTION FOR CROSS-VALIDATION
# ============================================================

def run_cross_validation(
    model_name,
    model_class,
    model_params
):

    print("\n")
    print("=" * 70)
    print(model_name)
    print("=" * 70)

    fold_results = []

    total_start_time = time.time()

    # --------------------------------------------------------
    # Run one fold at a time
    # --------------------------------------------------------

    for fold, (train_idx, val_idx) in enumerate(
        cv.split(X_train, y_train),
        start=1
    ):

        print("\n" + "-" * 60)
        print(f"FOLD {fold}/{N_SPLITS}")
        print("-" * 60)

        print(
            f"Training samples   : {len(train_idx):,}"
        )

        print(
            f"Validation samples : {len(val_idx):,}"
        )

        # ----------------------------------------------------
        # Select fold data
        # ----------------------------------------------------

        X_fold_train = X_train.iloc[train_idx]
        X_fold_val = X_train.iloc[val_idx]

        y_fold_train = y_train.iloc[train_idx]
        y_fold_val = y_train.iloc[val_idx]

        # ----------------------------------------------------
        # Create fresh model
        # ----------------------------------------------------

        model = model_class(
            **model_params
        )

        # ----------------------------------------------------
        # Train
        # ----------------------------------------------------

        print("\nTraining model...")

        start_time = time.time()

        model.fit(
            X_fold_train,
            y_fold_train
        )

        training_time = time.time() - start_time

        print(
            f"Training completed in "
            f"{training_time:.2f} seconds"
        )

        # ----------------------------------------------------
        # Predictions
        # ----------------------------------------------------

        print("Generating predictions...")

        y_pred = model.predict(
            X_fold_val
        )

        y_prob = model.predict_proba(
            X_fold_val
        )[:, 1]

        # ----------------------------------------------------
        # Metrics
        # ----------------------------------------------------

        accuracy = accuracy_score(
            y_fold_val,
            y_pred
        )

        precision = precision_score(
            y_fold_val,
            y_pred,
            zero_division=0
        )

        recall = recall_score(
            y_fold_val,
            y_pred,
            zero_division=0
        )

        f1 = f1_score(
            y_fold_val,
            y_pred,
            zero_division=0
        )

        roc_auc = roc_auc_score(
            y_fold_val,
            y_prob
        )

        # ----------------------------------------------------
        # Display fold results
        # ----------------------------------------------------

        print("\nFold Results:")

        print(f"Accuracy  : {accuracy:.4f}")
        print(f"Precision : {precision:.4f}")
        print(f"Recall    : {recall:.4f}")
        print(f"F1        : {f1:.4f}")
        print(f"ROC-AUC   : {roc_auc:.4f}")

        # ----------------------------------------------------
        # Store results
        # ----------------------------------------------------

        fold_results.append({
            "Model": model_name,
            "Fold": fold,
            "Accuracy": accuracy,
            "Precision": precision,
            "Recall": recall,
            "F1": f1,
            "ROC-AUC": roc_auc,
            "Training_Time_seconds": training_time
        })

        # ----------------------------------------------------
        # Release memory before next fold
        # ----------------------------------------------------

        del model
        del X_fold_train
        del X_fold_val
        del y_fold_train
        del y_fold_val
        del y_pred
        del y_prob

        gc.collect()

        print("\nMemory released.")

    total_time = time.time() - total_start_time

    print(
        f"\n{model_name} completed."
    )

    print(
        f"Total time: "
        f"{total_time / 60:.2f} minutes"
    )

    return pd.DataFrame(fold_results)


# ============================================================
# MODEL 1: BASELINE EXTRA TREES
# ============================================================

extra_trees_results = run_cross_validation(
    model_name="Baseline Extra Trees",
    model_class=ExtraTreesClassifier,
    model_params=extra_trees_params
)


# ============================================================
# MODEL 2: TUNED LIGHTGBM
# ============================================================

# Add controlled CPU usage for your machine
lightgbm_params["n_jobs"] = LIGHTGBM_JOBS

tuned_lightgbm_results = run_cross_validation(
    model_name="Tuned LightGBM",
    model_class=LGBMClassifier,
    model_params=lightgbm_params
)


# ============================================================
# COMBINE ALL FOLD RESULTS
# ============================================================

all_results = pd.concat(
    [
        extra_trees_results,
        tuned_lightgbm_results
    ],
    ignore_index=True
)


# ============================================================
# CALCULATE MEAN AND STANDARD DEVIATION
# ============================================================

metrics = [
    "Accuracy",
    "Precision",
    "Recall",
    "F1",
    "ROC-AUC"
]

summary_rows = []

for model_name in all_results["Model"].unique():

    model_results = all_results[
        all_results["Model"] == model_name
    ]

    row = {
        "Model": model_name
    }

    for metric in metrics:

        row[f"{metric}_Mean"] = (
            model_results[metric].mean()
        )

        row[f"{metric}_Std"] = (
            model_results[metric].std()
        )

    summary_rows.append(row)


summary_df = pd.DataFrame(
    summary_rows
)


# ============================================================
# SAVE CSV FILES
# ============================================================

os.makedirs(
    RESULTS_PATH,
    exist_ok=True
)

fold_results_path = os.path.join(
    RESULTS_PATH,
    "cross_validation_fold_results.csv"
)

summary_results_path = os.path.join(
    RESULTS_PATH,
    "cross_validation_summary.csv"
)


all_results.to_csv(
    fold_results_path,
    index=False
)

summary_df.to_csv(
    summary_results_path,
    index=False
)


# ============================================================
# DISPLAY FINAL RESULTS
# ============================================================

print("\n")
print("=" * 70)
print("FINAL 5-FOLD CROSS-VALIDATION RESULTS")
print("=" * 70)

print("\nFold-wise Results:\n")

print(
    all_results[
        [
            "Model",
            "Fold",
            "Accuracy",
            "Precision",
            "Recall",
            "F1",
            "ROC-AUC"
        ]
    ].to_string(index=False)
)


print("\n")
print("=" * 70)
print("MEAN ± STANDARD DEVIATION")
print("=" * 70)

for _, row in summary_df.iterrows():

    print(f"\n{row['Model']}")

    for metric in metrics:

        mean = row[f"{metric}_Mean"]
        std = row[f"{metric}_Std"]

        print(
            f"{metric:10s}: "
            f"{mean:.4f} ± {std:.4f}"
        )


# ============================================================
# FILE LOCATIONS
# ============================================================

print("\n")
print("=" * 70)
print("RESULTS SAVED")
print("=" * 70)

print("\nFold results:")
print(fold_results_path)

print("\nSummary results:")
print(summary_results_path)

print("\n")
print("=" * 70)
print("5-FOLD CROSS-VALIDATION COMPLETED SUCCESSFULLY")
print("=" * 70)