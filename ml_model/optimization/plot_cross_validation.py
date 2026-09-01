import os
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURATION
# ============================================================

RESULTS_FILE = "ml_model/results/cross_validation_fold_results.csv"

OUTPUT_DIR = "documentation/ai-ml"


# ============================================================
# LOAD RESULTS
# ============================================================

print("Loading cross-validation results...")

df = pd.read_csv(RESULTS_FILE)

print("\nResults loaded successfully.")
print(df)


# ============================================================
# PREPARE MODEL NAMES
# ============================================================

models = df["Model"].unique()

extra_trees = df[
    df["Model"] == "Baseline Extra Trees"
]

lightgbm = df[
    df["Model"] == "Tuned LightGBM"
]


# ============================================================
# GRAPH 1: MEAN METRIC COMPARISON
# ============================================================

metrics = [
    "Accuracy",
    "Precision",
    "Recall",
    "F1",
    "ROC-AUC"
]

extra_means = [
    extra_trees[metric].mean()
    for metric in metrics
]

lightgbm_means = [
    lightgbm[metric].mean()
    for metric in metrics
]


x = range(len(metrics))

width = 0.35

plt.figure(figsize=(10, 6))

plt.bar(
    [i - width / 2 for i in x],
    extra_means,
    width,
    label="Baseline Extra Trees"
)

plt.bar(
    [i + width / 2 for i in x],
    lightgbm_means,
    width,
    label="Tuned LightGBM"
)

plt.xticks(
    list(x),
    metrics
)

plt.ylabel("Score")

plt.title(
    "5-Fold Cross-Validation: Mean Metric Comparison"
)

plt.ylim(0.90, 1.00)

plt.legend()

plt.tight_layout()

graph1_path = os.path.join(
    OUTPUT_DIR,
    "mean_metrics_comparison.png"
)

plt.savefig(
    graph1_path,
    dpi=300
)

plt.close()

print(
    f"\nGraph 1 saved: {graph1_path}"
)


# ============================================================
# GRAPH 2: F1-SCORE ACROSS FOLDS
# ============================================================

plt.figure(figsize=(9, 6))

plt.plot(
    extra_trees["Fold"],
    extra_trees["F1"],
    marker="o",
    label="Baseline Extra Trees"
)

plt.plot(
    lightgbm["Fold"],
    lightgbm["F1"],
    marker="o",
    label="Tuned LightGBM"
)

plt.xlabel("Fold")

plt.ylabel("F1-Score")

plt.title(
    "F1-Score Across 5 Cross-Validation Folds"
)

plt.xticks(
    [1, 2, 3, 4, 5]
)

plt.ylim(0.93, 0.98)

plt.grid(
    True,
    alpha=0.3
)

plt.legend()

plt.tight_layout()

graph2_path = os.path.join(
    OUTPUT_DIR,
    "f1_fold_comparison.png"
)

plt.savefig(
    graph2_path,
    dpi=300
)

plt.close()

print(
    f"Graph 2 saved: {graph2_path}"
)


# ============================================================
# COMPLETION
# ============================================================

print("\n" + "=" * 60)
print("GRAPH GENERATION COMPLETED")
print("=" * 60)

print("\nGenerated files:")

print(
    f"1. {graph1_path}"
)

print(
    f"2. {graph2_path}"
)