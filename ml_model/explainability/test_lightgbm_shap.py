import time
import joblib
import pandas as pd
import shap

TEST_DATA_PATH = "ml_model/dataset/train_test/X_test.parquet"
MODEL_PATH = "ml_model/saved_model/lightgbm_tuned.pkl"

print("Loading test data...")

X_test = pd.read_parquet(TEST_DATA_PATH)

X_sample = X_test.sample(
    n=100,
    random_state=42
)

print("Sample:", X_sample.shape)

print("Loading LightGBM...")

model = joblib.load(MODEL_PATH)

print("Model loaded.")

print("Creating SHAP explainer...")

explainer = shap.TreeExplainer(model)

print("Explainer created.")

print("Calculating SHAP values for 10 samples...")

start = time.time()

shap_values = explainer.shap_values(
    X_sample,
    check_additivity=False
)

elapsed = time.time() - start

print("\nSHAP completed!")
print("Time:", round(elapsed, 2), "seconds")

if isinstance(shap_values, list):

    print("Number of SHAP outputs:", len(shap_values))

    for i, values in enumerate(shap_values):
        print(
            f"Class {i} SHAP shape:",
            values.shape
        )

else:

    print(
        "SHAP type:",
        type(shap_values)
    )

    print(
        "SHAP shape:",
        shap_values.shape
    )

print("DONE!")