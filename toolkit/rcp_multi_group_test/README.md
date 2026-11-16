# rcp_multi_group_test — three or more groups, and categorical associations

**Navigator node:** `N-TEST-KG` · **First used:** L3.5 · **Status:** working

Compares an outcome across ≥ 3 groups. Numeric outcomes: classic ANOVA, **Welch ANOVA** (unequal variances), Kruskal-Wallis (skew),
Levene, η², pairwise Welch / Mann-Whitney with Holm correction. Binary or categorical outcomes: chi-square, Cramér's V, standardised
residuals, pairwise two-proportion tests (Fisher's exact where expected counts are small) with Holm correction. The primary test is
chosen by the Navigator rule (Kruskal-Wallis when any group is heavily skewed, otherwise Welch ANOVA).

| Role | Required | Meaning |
| --- | --- | --- |
| `group` | yes | grouping column (region, employment type, …) |
| `target` | yes | outcome (numeric, 0/1 or category) |
| `unit` | no | aggregate rows to this id first (e.g. `basket_id`) |

| Param | Default | Meaning |
| --- | --- | --- |
| `kind` | auto | numeric / binary / categorical |
| `aggregate_fn` | sum | how rows are combined per `unit` |
| `drop_duplicates` | — | key columns for de-duplication before aggregation |
| `alpha` | 0.05 | significance level |
| `min_expected` | 5 | chi-square validity threshold |

**Outputs:** `narrative.md`, `pairwise.csv`, `groups.png`, `metrics.json`, `row_accounting.md`.

**Limits:** significance with large n says little; read η² / Cramér's V and differences in business units. Observational group
differences are not causal (mix, confounding — Day 4).
