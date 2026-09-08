import pandas as pd

# Load processed dataset
df = pd.read_parquet("ml_model/dataset/processed/processed_train.parquet")


print("Processed Dataset Verification")


print("\nShape:")
print(df.shape)

print("\nFirst 5 Rows:")
print(df.head())

print("\nLabel Distribution:")
print(df["Label"].value_counts())

print("\nMissing Values:")
print(df.isnull().sum().sum())

print("\nData Types:")
print(df.dtypes.head())