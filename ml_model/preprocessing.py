import os
import duckdb

# ==========================================================
# ThreatLens AI - Dataset Preprocessing
# ==========================================================

# Get project directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Input dataset
input_file = os.path.join(
    base_dir,
    "dataset",
    "raw",
    "train_ember_2018_v2_features.parquet"
)

# Output folder
output_folder = os.path.join(
    base_dir,
    "dataset",
    "processed"
)

os.makedirs(output_folder, exist_ok=True)

# Output file
output_file = os.path.join(
    output_folder,
    "processed_train.parquet"
)

print("=" * 60)
print("ThreatLens AI - Dataset Preprocessing")
print("=" * 60)

try:

    print("\nReading dataset and removing unlabeled samples (Label = -1)...")

    duckdb.sql(f"""
    COPY (
        SELECT *
        REPLACE (CAST(Label AS INTEGER) AS Label)
        FROM read_parquet('{input_file}')
        WHERE Label IN (0,1)
    )
    TO '{output_file}'
    (FORMAT PARQUET);
    """)

    print("\nProcessed dataset created successfully.")

    # Verify label distribution
    result = duckdb.sql(f"""
    SELECT Label,
           COUNT(*) AS Samples
    FROM read_parquet('{output_file}')
    GROUP BY Label
    ORDER BY Label;
    """).df()

    print("\nLabel Distribution")
    print("------------------")
    print(result)

    # Dataset shape
    rows = duckdb.sql(f"""
    SELECT COUNT(*)
    FROM read_parquet('{output_file}');
    """).fetchone()[0]

    cols = duckdb.sql(f"""
    SELECT *
    FROM read_parquet('{output_file}')
    LIMIT 1;
    """).df().shape[1]

    print("\nProcessed Dataset")
    print("------------------")
    print("Rows    :", rows)
    print("Columns :", cols)

    print("\nDuplicate Removal")
    print("------------------")
    print("Skipped because duplicate removal on the full dataset")
    print("may cause memory issues, as instructed.")

    print("\nSaved to:")
    print(output_file)

except Exception as e:

    print("\nPreprocessing could not be completed.")
    print("Reason:", e)
    print("\nThis is likely due to insufficient system memory while")
    print("processing the complete EMBER dataset.")