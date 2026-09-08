 Model                   Accuracy |Precision |Recall |F1-Score| ROC-AUC |Train Time|Prediction Time |

 Random Forest             95.68% |   96.40% | 94.91% | 95.65% | 99.31% | 150.83s  |    2.11s |
 Extra Trees               96.31% |   97.18% | 95.39% | 96.28% | 99.44% | 42.23s   |    0.80s |
 XGBoost                   94.94% |   94.56% | 95.38% | 94.96% | 99.02% | 41.05s   |    0.21s |
 LightGBM                  95.37% |   95.42% | 95.33% | 95.37% | 99.17% | 49.96s   |    1.18s |
 HistGradientBoosting      95.33% |   95.28% | 95.37% | 95.33% | 99.13% | 142.58s  |    2.03s |



## Preliminary Conclusion

Extra Trees achieved the strongest overall baseline performance, with the highest Accuracy, Precision, F1-Score, and ROC-AUC.

LightGBM achieved competitive performance with efficient training and prediction time.

Therefore, Extra Trees and LightGBM have been selected for hyperparameter tuning and further evaluation before making the final model selection.