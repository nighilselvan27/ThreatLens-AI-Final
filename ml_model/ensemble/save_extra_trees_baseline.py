import os
import time
import joblib
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier


print("=" * 70)
print("ThreatLens AI - Save Baseline Extra Trees")
print("=" * 70)


# ============================================================
# CONFIGURATION
# ============================================================

DATA_PATH = "ml_model/dataset/train_test"

MODEL_PATH = "ml_model/saved_model/extra_trees_baseline.pkl"


# ============================================================
# CREATE MODEL DIRECTORY
# ============================================================

os.makedirs("ml_model/saved_model", exist_ok=True)


# ============================================================
# LOAD TRAINING DATA
# ============================================================

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


# ============================================================
# CREATE BASELINE EXTRA TREES
# ============================================================

print("\nCreating baseline Extra Trees model...")

model = ExtraTreesClassifier(
    n_estimators=100,
    random_state=42,
    n_jobs=2
)


# ============================================================
# TRAIN MODEL
# ============================================================

print("\nTraining Extra Trees...")

start_time = time.time()

model.fit(
    X_train,
    y_train
)

training_time = time.time() - start_time


print("\nTraining completed.")

print(
    f"Training Time: {training_time:.2f} seconds"
)


# ============================================================
# SAVE MODEL
# ============================================================

print("\nSaving model...")

joblib.dump(
    model,
    MODEL_PATH,
    compress=3
)


print("\nModel saved successfully.")

print(
    "Location:",
    MODEL_PATH
)

print("\nDONE!")