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

    print("\nReading dataset...")
    print("Removing unlabeled samples (Label = -1)...")
    print("Removing duplicate rows...")

    # Count rows before preprocessing
    before_rows = duckdb.sql(f"""
        SELECT COUNT(*)
        FROM read_parquet('{input_file}')
        WHERE Label IN (0,1);
    """).fetchone()[0]

    # Remove unlabeled samples and duplicate rows
    duckdb.sql(f"""
        COPY (
            SELECT DISTINCT *
            REPLACE (CAST(Label AS INTEGER) AS Label)
            FROM read_parquet('{input_file}')
            WHERE Label IN (0,1)
        )
        TO '{output_file}'
        (FORMAT PARQUET);
    """)

    print("\nProcessed dataset created successfully.")

    # Count rows after preprocessing
    after_rows = duckdb.sql(f"""
        SELECT COUNT(*)
        FROM read_parquet('{output_file}');
    """).fetchone()[0]

    duplicates_removed = before_rows - after_rows

    # Display label distribution
    print("\nLabel Distribution")
    print("------------------")

    label_result = duckdb.sql(f"""
        SELECT Label,
               COUNT(*) AS Samples
        FROM read_parquet('{output_file}')
        GROUP BY Label
        ORDER BY Label;
    """).fetchall()

    for label, samples in label_result:
        print(f"Label {label}: {samples} samples")

    # Dataset dimensions
    rows = after_rows

    cols = len(
        duckdb.sql(f"""
            SELECT *
            FROM read_parquet('{output_file}')
            LIMIT 1;
        """).fetchone()
    )

    print("\nProcessed Dataset")
    print("------------------")
    print(f"Rows    : {rows}")
    print(f"Columns : {cols}")

    print("\nDuplicate Removal")
    print("------------------")
    print(f"Rows before preprocessing : {before_rows}")
    print(f"Rows after preprocessing  : {after_rows}")
    print(f"Duplicate rows removed    : {duplicates_removed}")

    print("\nProcessed dataset saved successfully.")
    print(f"Location: {output_file}")

except Exception as e:

    print("\nPreprocessing could not be completed.")
    print(f"Reason: {e}")

    print("\nPossible causes:")
    print("- Insufficient system memory.")
    print("- Missing or corrupted dataset.")
    print("- Insufficient disk space.")
    print("- Dataset file is open in another application.")