import pandas as pd
import time

from lightgbm import LGBMClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)


print("ThreatLens AI - LightGBM Training")



# ----------------------------------------------------------
# Load training data
# ----------------------------------------------------------

print("\nLoading training data...")

X_train = pd.read_parquet(
    "ml_model/dataset/train_test/X_train.parquet"
)

y_train = pd.read_parquet(
    "ml_model/dataset/train_test/y_train.parquet"
)["Label"]

print("Training data loaded.")
print("X_train:", X_train.shape)
print("y_train:", y_train.shape)


# ----------------------------------------------------------
# Load testing data
# ----------------------------------------------------------

print("\nLoading testing data...")

X_test = pd.read_parquet(
    "ml_model/dataset/train_test/X_test.parquet"
)

y_test = pd.read_parquet(
    "ml_model/dataset/train_test/y_test.parquet"
)["Label"]

print("Testing data loaded.")
print("X_test:", X_test.shape)
print("y_test:", y_test.shape)


# ----------------------------------------------------------
# Create LightGBM model
# ----------------------------------------------------------

print("\nCreating LightGBM model...")

model = LGBMClassifier(
    n_estimators=100,
    learning_rate=0.1,
    num_leaves=31,
    random_state=42,
    n_jobs=-1,
    verbosity=-1
)


# ----------------------------------------------------------
# Train model
# ----------------------------------------------------------

print("\nTraining LightGBM...")

start_time = time.time()

model.fit(X_train, y_train)

training_time = time.time() - start_time

print("\nTraining completed.")
print("Training Time:", round(training_time, 2), "seconds")


# ----------------------------------------------------------
# Prediction
# ----------------------------------------------------------

print("\nGenerating predictions...")

start_time = time.time()

y_pred = model.predict(X_test)
y_probability = model.predict_proba(X_test)[:, 1]

prediction_time = time.time() - start_time

print("Prediction completed.")
print("Prediction Time:", round(prediction_time, 2), "seconds")


# ----------------------------------------------------------
# Evaluation metrics
# ----------------------------------------------------------

accuracy = accuracy_score(y_test, y_pred)

precision = precision_score(
    y_test,
    y_pred,
    zero_division=0
)

recall = recall_score(
    y_test,
    y_pred,
    zero_division=0
)

f1 = f1_score(
    y_test,
    y_pred,
    zero_division=0
)

roc_auc = roc_auc_score(
    y_test,
    y_probability
)

cm = confusion_matrix(
    y_test,
    y_pred
)


# ----------------------------------------------------------
# Display results
# ----------------------------------------------------------


print("LightGBM Evaluation Results")


print("\nAccuracy  :", round(accuracy, 4))
print("Precision :", round(precision, 4))
print("Recall    :", round(recall, 4))
print("F1-Score  :", round(f1, 4))
print("ROC-AUC   :", round(roc_auc, 4))

print("\nTraining Time  :", round(training_time, 2), "seconds")
print("Prediction Time:", round(prediction_time, 2), "seconds")

print("\nConfusion Matrix:")
print(cm)


print("LightGBM Training Completed")
