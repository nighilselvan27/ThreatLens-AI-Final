import duckdb
import os


print("ThreatLens AI - Balanced Dataset Creation")


input_file = "ml_model/dataset/processed/processed_train.parquet"

output_folder = "ml_model/dataset/balanced"
os.makedirs(output_folder, exist_ok=True)

output_file = os.path.join(output_folder, "balanced_dataset.parquet")

duckdb.sql(f"""
COPY (
    SELECT *
    FROM (
        SELECT *
        FROM read_parquet('{input_file}')
        WHERE Label = 0
        ORDER BY random()
        LIMIT 100000
    )

    UNION ALL

    SELECT *
    FROM (
        SELECT *
        FROM read_parquet('{input_file}')
        WHERE Label = 1
        ORDER BY random()
        LIMIT 100000
    )
)
TO '{output_file}'
(FORMAT PARQUET);
""")

print("Balanced dataset created successfully.")

result = duckdb.sql(f"""
SELECT Label, COUNT(*)
FROM read_parquet('{output_file}')
GROUP BY Label
ORDER BY Label;
""").df()

print(result)