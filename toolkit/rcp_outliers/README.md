# rcp_outliers — compare outlier rules and treatments

**Navigator node:** `N-DESC-OUTLIER` · **First used:** L1.6 · **Status:** working

## What it does

Flags extreme values with several rules side by side (Tukey fences, plain z-score, robust median/MAD z-score, optional Isolation
Forest), explains why they disagree, and shows how each treatment (keep, cap, winsorise, exclude, trim, log) changes the mean, median,
SD and skew. Optionally aggregates rows to a unit first (e.g. lines → baskets).

## Roles

| Role | Required | Meaning |
| --- | --- | --- |
| `target` | yes | Numeric variable to scan |
| `id` | no | Row key |

## Parameters

| Key | Default | Meaning |
| --- | --- | --- |
| `unit`, `agg` | none, `sum` | aggregate to this unit before scanning |
| `iqr_k` | `[1.5, 3]` | Tukey fence multipliers |
| `z` | 3 | plain z threshold |
| `robust_z` | 3.5 | modified z threshold |
| `isolation_forest` | none | `{columns: [...], contamination: 0.01}` |
| `log_scale` | `auto` | log axis for skewed positive data |

## Outputs

`narrative.md` · `flagged.csv` (every flagged unit with each rule's verdict and robust z) · `treatment_comparison.csv` · `outliers.png` ·
`metrics.json` · `row_accounting.md`

## Limits

A flag is a question: error, genuine extreme, or signal. The recipe never deletes; the treatment is your decision — report it and its
effect.
