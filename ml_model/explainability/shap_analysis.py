import os
import time
import joblib
import numpy as np
import pandas as pd
import shap


# ============================================================
# Paths
# ============================================================

TEST_DATA_PATH = "ml_model/dataset/train_test/X_test.parquet"

LIGHTGBM_MODEL_PATH = "ml_model/saved_model/lightgbm_tuned.pkl"
EXTRA_TREES_MODEL_PATH = "ml_model/saved_model/extra_trees_baseline.pkl"

RESULTS_DIR = "ml_model/explainability/results"


# ============================================================
# Configuration
# ============================================================

# LightGBM is very fast, so we can use more samples.
LIGHTGBM_SAMPLE_SIZE = 100

# Extra Trees is much slower.
# Start with only 10 samples.
EXTRA_TREES_SAMPLE_SIZE = 10

RANDOM_STATE = 42


# ============================================================
# Create results directory
# ============================================================

os.makedirs(RESULTS_DIR, exist_ok=True)


# ============================================================
# Load test data
# ============================================================

print("=" * 60)
print("SHAP EXPLAINABILITY ANALYSIS")
print("=" * 60)

print("\nLoading test data...")

X_test = pd.read_parquet(TEST_DATA_PATH)

print(f"Test data shape: {X_test.shape}")


# ============================================================
# Feature names
# ============================================================

feature_names = list(X_test.columns)

print(f"Number of features: {len(feature_names)}")


# ============================================================
# LIGHTGBM SHAP
# ============================================================

print("\n" + "=" * 60)
print("LIGHTGBM SHAP ANALYSIS")
print("=" * 60)

X_lgb = X_test.sample(
    n=LIGHTGBM_SAMPLE_SIZE,
    random_state=RANDOM_STATE
)

print(f"LightGBM sample shape: {X_lgb.shape}")

print("\nLoading LightGBM model...")

lgb_model = joblib.load(LIGHTGBM_MODEL_PATH)

print("LightGBM model loaded.")

print("\nCreating LightGBM SHAP explainer...")

start_time = time.time()

lgb_explainer = shap.TreeExplainer(lgb_model)

print("Explainer created.")

print("\nCalculating LightGBM SHAP values...")

lgb_shap_values = lgb_explainer.shap_values(
    X_lgb,
    check_additivity=False
)

lgb_time = time.time() - start_time

print(f"SHAP completed in {lgb_time:.2f} seconds")

print(f"SHAP shape: {lgb_shap_values.shape}")


# ============================================================
# Save LightGBM SHAP values
# ============================================================

lgb_shap_path = os.path.join(
    RESULTS_DIR,
    "lightgbm_shap_values.npy"
)

np.save(
    lgb_shap_path,
    lgb_shap_values
)

print(f"Saved: {lgb_shap_path}")


# ============================================================
# LightGBM Feature Importance
# ============================================================

print("\nCalculating LightGBM feature importance...")

lgb_mean_abs_shap = np.mean(
    np.abs(lgb_shap_values),
    axis=0
)

lgb_importance = pd.DataFrame({
    "Feature": feature_names,
    "Mean_Absolute_SHAP": lgb_mean_abs_shap
})

lgb_importance = lgb_importance.sort_values(
    by="Mean_Absolute_SHAP",
    ascending=False
).reset_index(drop=True)

lgb_importance_path = os.path.join(
    RESULTS_DIR,
    "lightgbm_feature_importance.csv"
)

lgb_importance.to_csv(
    lgb_importance_path,
    index=False
)

print(f"Saved: {lgb_importance_path}")

print("\nTop 20 LightGBM features:")

print(
    lgb_importance.head(20).to_string(index=False)
)


# ============================================================
# EXTRA TREES SHAP
# ============================================================

print("\n" + "=" * 60)
print("EXTRA TREES SHAP ANALYSIS")
print("=" * 60)

X_et = X_test.sample(
    n=EXTRA_TREES_SAMPLE_SIZE,
    random_state=RANDOM_STATE
)

print(f"Extra Trees sample shape: {X_et.shape}")

print("\nLoading Extra Trees model...")

et_model = joblib.load(EXTRA_TREES_MODEL_PATH)

print("Extra Trees model loaded.")

print("\nCreating Extra Trees SHAP explainer...")

start_time = time.time()

et_explainer = shap.TreeExplainer(
    et_model,
    feature_perturbation="tree_path_dependent",
    model_output="raw"
)

print("Explainer created.")

print("\nCalculating Extra Trees SHAP values...")

et_shap_values = et_explainer.shap_values(
    X_et,
    check_additivity=False
)

et_time = time.time() - start_time

print(f"SHAP completed in {et_time:.2f} seconds")

print(f"Original SHAP shape: {et_shap_values.shape}")


# ============================================================
# Handle Extra Trees multiclass SHAP output
# ============================================================

if isinstance(et_shap_values, list):

    print("SHAP returned a list of class arrays.")

    # Binary classification:
    # use class 1 (malware) explanation.
    if len(et_shap_values) == 2:
        et_shap_class1 = et_shap_values[1]
    else:
        et_shap_class1 = et_shap_values[0]

else:

    # Newer SHAP versions may return:
    # (samples, features, classes)
    if et_shap_values.ndim == 3:

        print("SHAP returned a 3D array.")

        # Class 1 = malware
        et_shap_class1 = et_shap_values[:, :, 1]

    else:

        et_shap_class1 = et_shap_values


print(
    f"Extra Trees class-1 SHAP shape: "
    f"{et_shap_class1.shape}"
)


# ============================================================
# Save Extra Trees SHAP values
# ============================================================

et_shap_path = os.path.join(
    RESULTS_DIR,
    "extra_trees_shap_values.npy"
)

np.save(
    et_shap_path,
    et_shap_class1
)

print(f"Saved: {et_shap_path}")


# ============================================================
# Extra Trees Feature Importance
# ============================================================

print("\nCalculating Extra Trees feature importance...")

et_mean_abs_shap = np.mean(
    np.abs(et_shap_class1),
    axis=0
)

et_importance = pd.DataFrame({
    "Feature": feature_names,
    "Mean_Absolute_SHAP": et_mean_abs_shap
})

et_importance = et_importance.sort_values(
    by="Mean_Absolute_SHAP",
    ascending=False
).reset_index(drop=True)

et_importance_path = os.path.join(
    RESULTS_DIR,
    "extra_trees_feature_importance.csv"
)

et_importance.to_csv(
    et_importance_path,
    index=False
)

print(f"Saved: {et_importance_path}")

print("\nTop 20 Extra Trees features:")

print(
    et_importance.head(20).to_string(index=False)
)


# ============================================================
# Summary
# ============================================================

print("\n" + "=" * 60)
print("SHAP ANALYSIS COMPLETE")
print("=" * 60)

print("\nGenerated files:")

print(f"1. {lgb_shap_path}")
print(f"2. {lgb_importance_path}")
print(f"3. {et_shap_path}")
print(f"4. {et_importance_path}")

print("\nSHAP timing:")
print(f"LightGBM : {lgb_time:.2f} seconds")
print(f"Extra Trees: {et_time:.2f} seconds")

print("\nDONE!")