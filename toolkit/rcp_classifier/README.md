# rcp_classifier — baseline vs boosting, honest validation, rare-event metrics, thresholds and explanations

**Navigator nodes:** `N-ML-GBM`, `N-ML-LEAK`, `N-ML-IMBALANCE`, `N-METRIC-CLASS`, `N-METRIC-RARE`, `N-METRIC-COST` · **First used:** L6.2 · **Status:** working

Trains a logistic baseline and gradient boosting (optionally a random forest) on a random or out-of-time split; reports ROC-AUC,
Gini, PR-AUC, KS, Brier, precision/recall at capacity, train-vs-test gaps, lift by decile, calibration, permutation importance and a
threshold table with expected cost; raises a **leakage alert** when AUC exceeds domain norms and names the dominant feature.

| Role | Required | Meaning |
| --- | --- | --- |
| `target` | yes | 0/1 outcome |
| `features` | yes | predictors (categoricals one-hot encoded; missing values median-filled with an indicator) |
| `time` | no | column for out-of-time splits |

| Param | Default | Meaning |
| --- | --- | --- |
| `split` / `cutoff` | random | `time` with `cutoff` trains on ≤ cutoff |
| `models` | [logistic, gbm] | also `random_forest` |
| `class_weight` | none | `balanced` for rare events (changes probability scale) |
| `capacity_k` | [100, 500] | alert-queue sizes for precision@k |
| `cost_fn`, `cost_fp` | — | expected-cost threshold |
| `leakage_auc` | 0.95 | alert threshold |

**Outputs:** `narrative.md`, `lift_by_decile.csv`, `calibration.csv`, `permutation_importance.csv`, `thresholds.csv`, `roc_pr.png`, `metrics.json`.

**Regression check:** fitted models differ slightly across scikit-learn versions, so this recipe declares a tolerance
(`_tolerance` in `metrics.json`: rtol 5%, atol 0.03).

**Limits:** SHAP is not bundled (permutation importance and partial dependence are); install `shap` for local tree explanations.
