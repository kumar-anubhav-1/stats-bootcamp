# rcp_two_group_test — compare two groups the right way

**Navigator node:** `N-TEST-2G` (continuous: `N-TEST-2G-MEAN`, binary: `N-TEST-2G-PROP`) · **First used:** L3.4 · **Status:** working

## What it does (plain English)

Answers "is group A different from group B, by how much, and how sure are we?" It:

1. analyses at the **unit that was randomised** (store, branch, customer) — not at transaction level;
2. optionally turns the outcome into **growth versus each unit's own pre-period** (removes size differences);
3. detects whether the outcome is **binary** (rate) or **continuous** (amount);
4. **checks assumptions** (skew, normality, equal variances, expected cell counts, clustering);
5. picks the **primary test by Navigator rules** and runs robustness tests alongside;
6. reports **effect sizes with confidence intervals** and a plain-English verdict that never equates "significant" with "important".

| Outcome | Primary test | Robustness | Effect sizes |
| --- | --- | --- | --- |
| Continuous | Welch t-test (Mann-Whitney if heavy-tailed **and** < 30 units/group) | Student t, Mann-Whitney, permutation, bootstrap CI | difference + CI, % lift + bootstrap CI, Hedges' g, median difference, MDE |
| Binary | Two-proportion z-test (Fisher exact if any expected cell < 5) | chi-square, Fisher | risk difference + CI, relative risk + CI, odds ratio + CI, NNT, MDE |

## Roles

| Role | Required | Meaning |
| --- | --- | --- |
| `group` | yes | Column holding the two groups |
| `target` | yes | Outcome (numeric, or 0/1 / True/False) |
| `cluster` | no | Unit of randomisation if rows are nested in it (store_id, branch_id) |
| `id` | no | Row id (duplicate check) |

## Parameters

| Key | Default | Meaning |
| --- | --- | --- |
| `groups` | two most frequent | `[treatment, control]` order matters for lift |
| `aggregate_to` | `cluster` if mapped | `none` keeps row level (only if rows were randomised individually) |
| `aggregate_fn` | `mean` | How to aggregate rows to clusters |
| `baseline` | none | `{period_col, pre: [a, b], post: [c, d]}` → outcome = post mean ÷ pre mean per cluster |
| `alternative` | `two-sided` | `greater` / `less` only if pre-registered |
| `alpha` | 0.05 | Significance level |
| `practical_threshold` | none | Smallest % lift worth acting on; verdict compares the lower CI bound |
| `n_boot`, `n_perm`, `seed` | 5000, 5000, 42 | Resampling settings (seeded = reproducible) |

## Outputs

`narrative.md` · `tests.csv` · `effects.csv` · `analysis_units.csv` · `comparison.png` · `qq.png` · `metrics.json` · `schema_report.md` · `row_accounting.md`

## Where it breaks

- **Not a causal method for observational data.** If groups were not randomised, a difference may be confounding (→ `N-CAUSAL`).
- **One comparison.** Many segments or metrics → multiple-testing correction (→ `N-TEST-MULTI`).
- **Peeking.** Re-running daily and stopping when p < 0.05 inflates false positives (→ `N-EXP-SEQ`).
- **Check SRM first** for experiments (→ `rcp_ab_test`).

## Example configs

`retail_promo_lift.yaml` (store test, growth vs pre-period) · `retail_promo_lift_naive.yaml` · `retail_promo_lift_line_level.yaml` (wrong unit, for teaching) ·
`finance_default_by_verification.yaml` (binary) · `finance_challenger_cure.yaml` (binary, 80/20).
