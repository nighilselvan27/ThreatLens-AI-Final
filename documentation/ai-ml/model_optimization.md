# Model Optimization

## Objective

The objective of model optimization is to improve the performance of the selected machine learning models by tuning their hyperparameters.

The two models selected for optimization were:

- Extra Trees
- LightGBM

Both models were evaluated using the same dataset and train-test split to ensure a fair comparison.

## Dataset

- Total samples: 200,000
- Training samples: 160,000
- Testing samples: 40,000
- Features: 2,381
- Classes: Benign and Malware
- Dataset format: Parquet

## Baseline Models

Five machine learning models were evaluated during the baseline stage:

- Random Forest
- Extra Trees
- XGBoost
- LightGBM
- HistGradientBoosting

Based on the baseline evaluation, Extra Trees and LightGBM were selected for further optimization.

## Hyperparameter Tuning

RandomizedSearchCV was used for controlled hyperparameter tuning.

The tuning objective was to maximize F1-Score using 2-fold cross-validation.

Two parameter combinations were evaluated for each model, resulting in a total of four model fits per optimization process.

The same training and testing datasets were used for both models to ensure a fair comparison.

## Extra Trees Optimization

The following parameters were considered for tuning:

- Number of estimators
- Maximum depth
- Minimum samples split
- Minimum samples leaf
- Maximum features

### Best Parameters

```text
n_estimators: 200
max_depth: 30
min_samples_split: 10
min_samples_leaf: 2
max_features: sqrt
```

**Best Cross-Validation F1-Score:** 0.9473

### Baseline Results

| Metric | Value |
|---|---:|
| Accuracy | 0.9654 |
| Precision | 0.9728 |
| Recall | 0.9575 |
| F1-Score | 0.9651 |
| ROC-AUC | 0.9950 |
| Training Time | 387.89s |
| Prediction Time | 9.01s |

### Tuned Results

| Metric | Value |
|---|---:|
| Accuracy | 0.9556 |
| Precision | 0.9613 |
| Recall | 0.9494 |
| F1-Score | 0.9553 |
| ROC-AUC | 0.9928 |
| Tuning Time | 8776.13s |
| Prediction Time | 16.50s |

### Extra Trees Comparison

The tuned Extra Trees model did not improve upon the baseline model.

| Metric | Baseline | Tuned | Change |
|---|---:|---:|---:|
| Accuracy | 0.9654 | 0.9556 | -0.0098 |
| Precision | 0.9728 | 0.9613 | -0.0115 |
| Recall | 0.9575 | 0.9494 | -0.0081 |
| F1-Score | 0.9651 | 0.9553 | -0.0098 |
| ROC-AUC | 0.9950 | 0.9928 | -0.0022 |

The tuned model showed lower performance across all evaluated classification metrics. Therefore, the tuned Extra Trees model was not selected as the final model.

### Extra Trees Confusion Matrices

**Baseline:**

```text
[[19464   536]
 [  850 19150]]
```

**Tuned:**

```text
[[19236   764]
 [ 1013 18987]]
```

### Extra Trees Saved Files

- `ml_model/results/extra_trees_baseline_vs_tuned.csv`
- `ml_model/results/extra_trees_best_params.json`
- `ml_model/saved_model/extra_trees_tuned.pkl`

## LightGBM Optimization

The following parameters were considered for tuning:

- Number of estimators
- Learning rate
- Maximum depth
- Number of leaves
- Minimum child samples

### Best Parameters

```text
n_estimators: 200
learning_rate: 0.1
max_depth: -1
num_leaves: 63
min_child_samples: 20
```

**Best Cross-Validation F1-Score:** 0.9663

### Baseline Results

| Metric | Value |
|---|---:|
| Accuracy | 0.9537 |
| Precision | 0.9542 |
| Recall | 0.9533 |
| F1-Score | 0.9537 |
| ROC-AUC | 0.9917 |
| Training Time | 145.90s |
| Prediction Time | 3.12s |

### Tuned Results

| Metric | Value |
|---|---:|
| Accuracy | 0.9712 |
| Precision | 0.9724 |
| Recall | 0.9700 |
| F1-Score | 0.9712 |
| ROC-AUC | 0.9962 |
| Tuning Time | 711.75s |
| Prediction Time | 5.35s |

### LightGBM Performance Improvement

The tuned LightGBM model improved all major classification metrics compared with the baseline LightGBM model.

| Metric | Baseline | Tuned | Improvement |
|---|---:|---:|---:|
| Accuracy | 0.9537 | 0.9712 | +0.0175 |
| Precision | 0.9542 | 0.9724 | +0.0182 |
| Recall | 0.9533 | 0.9700 | +0.0167 |
| F1-Score | 0.9537 | 0.9712 | +0.0175 |
| ROC-AUC | 0.9917 | 0.9962 | +0.0045 |

### LightGBM Confusion Matrices

**Baseline:**

```text
[[19084   916]
 [  935 19065]]
```

**Tuned:**

```text
[[19450   550]
 [  600 19400]]
```

The tuned LightGBM model produced fewer false positives and false negatives than the baseline model, resulting in improved classification performance.

### LightGBM Saved Files

- `ml_model/results/lightgbm_baseline_vs_tuned.csv`
- `ml_model/results/lightgbm_best_params.json`
- `ml_model/saved_model/lightgbm_tuned.pkl`

## Final Comparison

The baseline and tuned models were compared using Accuracy, Precision, Recall, F1-Score, and ROC-AUC.

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Baseline Extra Trees | 0.9654 | 0.9728 | 0.9575 | 0.9651 | 0.9950 |
| Tuned Extra Trees | 0.9556 | 0.9613 | 0.9494 | 0.9553 | 0.9928 |
| Baseline LightGBM | 0.9537 | 0.9542 | 0.9533 | 0.9537 | 0.9917 |
| **Tuned LightGBM** | **0.9712** | **0.9724** | **0.9700** | **0.9712** | **0.9962** |

Tuned LightGBM achieved the highest Accuracy, Recall, F1-Score, and ROC-AUC among the evaluated models.

## Computational Performance

| Model | Training Time | Tuning Time | Prediction Time |
|---|---:|---:|---:|
| Baseline Extra Trees | 387.89s | - | 9.01s |
| Tuned Extra Trees | - | 8776.13s | 16.50s |
| Baseline LightGBM | 145.90s | - | 3.12s |
| Tuned LightGBM | - | 711.75s | 5.35s |

Hyperparameter tuning increased the computational time for both models.

Extra Trees required substantially more tuning time than LightGBM. Although tuned LightGBM also required additional tuning time compared with its baseline model, it provided a significant improvement in classification performance.

## Model Selection

The final model was selected based on overall classification performance and computational efficiency, with priority given to:

1. F1-Score
2. Recall
3. ROC-AUC
4. Precision
5. Accuracy
6. Training Time
7. Prediction Time

Based on the final evaluation, **Tuned LightGBM was selected as the final optimized model**.

Tuned LightGBM achieved:

- Accuracy: **0.9712**
- Precision: **0.9724**
- Recall: **0.9700**
- F1-Score: **0.9712**
- ROC-AUC: **0.9962**

The final tuned LightGBM model was saved at:

`ml_model/saved_model/lightgbm_tuned.pkl`

## Conclusion

The hyperparameter optimization process was completed for both Extra Trees and LightGBM.

The Extra Trees optimization did not improve the baseline performance. The tuned Extra Trees model showed lower Accuracy, Precision, Recall, F1-Score, and ROC-AUC compared with its baseline model.

In contrast, the tuned LightGBM model showed significant improvement across all major classification metrics. Its F1-Score increased from 0.9537 to 0.9712, while ROC-AUC increased from 0.9917 to 0.9962.

Based on the final comparison, **Tuned LightGBM was selected as the preferred optimized model for the next stage of the ThreatLens AI system.**