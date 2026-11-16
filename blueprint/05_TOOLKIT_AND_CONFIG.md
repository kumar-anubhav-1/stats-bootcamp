# 05. Reusable Toolkit and Configuration Design

Learners never write code. Claude Code runs, adapts and extends these recipes on instruction. The recipes are what make vibe-coded work reusable instead of throw-away.

## 1. Recipe catalogue (20)

| Recipe | Purpose | First used | Key outputs |
| --- | --- | --- | --- |
| `rcp_profile` ★ | Profile any table: types, nulls, uniques, ranges, distributions | L0.4 | profile table, null heatmap, narrative |
| `rcp_quality` | Rule-based validity, duplicates, reconciliation, missingness mechanism checks | L1.2 | rule log with rows affected, cleaned file |
| `rcp_outliers` | IQR, robust z, Isolation Forest scan with treatment comparison | L1.6 | flagged rows, before/after stats |
| `rcp_distribution_fit` | Fit candidate distributions, Q-Q, AIC | L2.3 | fit table, plots |
| `rcp_benford` | First/last-digit tests by group | L2.6 | MAD by group, chart |
| `rcp_two_group_test` ★ | Assumption checks → right test → effect size + CI → plain-English verdict | L3.4 | test table, effect, plots, narrative |
| `rcp_multi_group_test` | ANOVA / Welch / Kruskal / chi-square with post-hoc and corrections | L3.5 | test + post-hoc table |
| `rcp_power` | Sample size, MDE, power curves (means, proportions, clusters) | L3.6 | power table, curve |
| `rcp_ab_test` | SRM check, primary + guardrails, CUPED, frequentist + Bayesian readout | L4.1 | experiment readout |
| `rcp_regression` | OLS/GLM family with diagnostics panel and business coefficient table | L5.1 | coefficients, diagnostics, narrative |
| `rcp_classifier` | Pipeline: split (random/out-of-time), baseline + GBM, imbalance handling, metrics, calibration, SHAP | L6.2 | metrics table, ROC/PR, calibration, SHAP |
| `rcp_forecast` | Baselines + ETS/SARIMA(X), rolling backtest, WAPE/MASE/bias | L7.2 | forecast, backtest table |
| `rcp_changepoint` | CUSUM/PELT on a series, by group | L7.5 | break dates, plot |
| `rcp_inventory` | ABC/XYZ, safety stock at service levels | L7.6 | policy table |
| `rcp_cluster` | Scaling, PCA, K-Means/GMM, silhouette, profiles | L8.1 | cluster profiles, plots |
| `rcp_basket` | Association rules with support/confidence/lift filters | L8.3 | rules table |
| `rcp_elasticity` | Log-log own/cross elasticity, promo uplift net of cannibalisation | L8.4 | elasticity table |
| `rcp_anomaly_scan` | Multi-method anomaly scan + graph ring detection + threshold bunching | L8.5 | alerts, network summary |
| `rcp_scorecard` | WoE/IV binning, logistic scorecard, points, vintage & roll-rate tables | L8.7 | IV table, scorecard, vintage curves |
| `rcp_drift` | PSI/CSI, performance decay, fairness monitor | L9.6 | monitoring report |

★ = built and working in Step 2. Others are scaffolded in Step 2 and completed in the day they are taught.

## 2. Configuration contract

Every recipe reads one YAML file. Same keys everywhere; recipe-specific parameters under `params`.

```yaml
# toolkit/configs/retail_promo_lift.yaml
recipe: rcp_two_group_test
dataset:
  name: northstar_transactions
  path: data/retail/transactions.parquet
  grain: line            # declared grain; recipe can aggregate
columns:                 # map dataset columns -> recipe roles
  id: line_id
  date: date
  group: experiment_group
  target: quantity
  cluster: store_id      # unit of randomisation
filters:
  - "category == 'Hair Care'"
  - "week >= 70 and week <= 77"
  - "experiment_group in ['test', 'control']"
params:
  aggregate_to: cluster  # analyse at store level, not line level
  alternative: two-sided
  alpha: 0.05
  effect_size: [diff, pct_lift, cohens_d]
  robustness: [mann_whitney, bootstrap_ci, permutation]
output:
  folder: outputs/{recipe}/{date}_{dataset}
  narrative: true
```

## 3. Schema check (runs before every recipe)

1. Required roles present? Missing → stop with a plain message ("recipe needs `target`; your file has `units_sold` and `qty_net`: which one?").
2. Types and units: numeric where expected; flags currency/unit suspicion (e.g. median price 100× historic).
3. Grain: duplicates on declared id; aggregation needed vs declared grain.
4. Row accounting: rows in → after each filter → after cleaning → analysed. **Any row drop is reported**, never silent.
5. Null rates per role vs thresholds.
6. Writes `schema_report.md` to the output folder.

## 4. Claude Code project guidance

- `CLAUDE.md` (repo root, learner-facing): describes datasets and toolkit; rules: state assumptions and explain the statistics before running; never claim a number you did not compute; always report rows dropped; prefer recipes over ad-hoc code; never edit recipe logic when adapting to new data, change config only; ask before committing.
- `.claude/commands/` slash commands, one per recipe, e.g. `/run-recipe two_group_test config=...`, `/map-columns <file> <recipe>`, `/regression-check <recipe>`, `/review-analysis <path>`, `/new-recipe-from <notebook>`.
- `toolkit/<recipe>/README.md`: plain-English purpose, inputs, roles, outputs, assumptions, limits, example prompt.

## 5. Reuse skills taught (prompt cards in every lesson)

| # | Skill | Example expert prompt (abridged) |
| --- | --- | --- |
| 1 | Read before touching | "Read `rcp_two_group_test` and explain in plain English what it does, its assumptions, and which config keys control it. Don't change anything." |
| 2 | Adapt by config only | "Copy the retail promo config to a finance one for default rate by branch. Change only config; keep the logic." |
| 3 | Map unfamiliar columns | "Map columns in `bank_b.csv` to the recipe roles. Flag type, unit, grain, null and renamed-field mismatches before running." |
| 4 | Regression check | "Re-run the original retail config and confirm every output number is unchanged versus the saved baseline." |
| 5 | Controlled modification | "Add a region filter as a new config option. Show me the diff and the before/after results." |
| 6 | Save and version | "Commit this change with a clear message describing what and why." |
| 7 | Review others' work | "Summarise this analysis, list its assumptions and risks, and challenge its conclusion." |
| 8 | One-off → recipe | "Turn this successful analysis into a new parameterised recipe with README, config and schema check." |

**Reuse drill** (end of every lesson): run the same recipe on the other industry's data or a variant (`renamed`, `weekly`, `period2`, `units`), change configuration only, compare and explain differences.

**Leader approval checklist for reused analyses:** schema report clean · grain matches the question · units checked · row accounting shown · parameters (dates, filters, thresholds) not stale · assumptions re-checked on the new data · regression check passed on original data · conclusion phrased with effect size and uncertainty.

## 6. Transfer test (Day 10)

Unseen quick-commerce orders dataset (seed 9001, ≈ 20K rows), columns deliberately different (`order_ts`, `dark_store`, `basket_amt_minor`, `rider_id`, `promo_code_used`…). Two planted issues: amounts in minor currency units, i.e. 100× (unit trap) and a duplicated day of orders. Task: map into ≥ 4 recipes via config, pass schema checks, find both issues, deliver a one-page readout. Scored by rubric.
