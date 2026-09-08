import pandas as pd
from sklearn.model_selection import train_test_split
import os

print("ThreatLens AI - Train Test Split")

# Load balanced dataset
df = pd.read_parquet(
    "ml_model/dataset/balanced/balanced_dataset.parquet"
)

print("\nDataset Shape:", df.shape)

print("\nLabel Distribution:")
print(df["Label"].value_counts())

# Features and Target
X = df.drop("Label", axis=1)
y = df["Label"]

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining Set")
print("X_train :", X_train.shape)
print("y_train :", y_train.shape)

print("\nTesting Set")
print("X_test :", X_test.shape)
print("y_test :", y_test.shape)

# Create output folder
os.makedirs("ml_model/dataset/train_test", exist_ok=True)

# Save datasets
X_train.to_parquet(
    "ml_model/dataset/train_test/X_train.parquet",
    index=False
)

X_test.to_parquet(
    "ml_model/dataset/train_test/X_test.parquet",
    index=False
)

y_train.to_frame().to_parquet(
    "ml_model/dataset/train_test/y_train.parquet",
    index=False
)

y_test.to_frame().to_parquet(
    "ml_model/dataset/train_test/y_test.parquet",
    index=False
)

print("\nTrain-Test split completed successfully.")