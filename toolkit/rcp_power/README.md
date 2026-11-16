# rcp_power — sample size, MDE and power curves from your own data

**Navigator node:** `N-EXP-POWER` · **First used:** L3.6 · **Status:** working

Estimates the variability (or baseline rate) from data, then reports units needed per arm for a list of effects, achieved power and the
minimum detectable effect (MDE) for the sample you have, and power curves. Supports means, proportions, cluster designs (design effect
from ICC and cluster size), unequal allocation and growth-index outcomes measured against a pre-period.

| Role | Required | Meaning |
| --- | --- | --- |
| `target` | yes | outcome (numeric or 0/1) |
| `cluster` | no | unit of randomisation (store, branch) |
| `group` | no | arm column, used with `control_label` |

| Param | Default | Meaning |
| --- | --- | --- |
| `design` | auto | means / proportions / cluster_means |
| `baseline` | — | `{period_col, pre, post}`: outcome = post ÷ pre per cluster |
| `control_label` | — | estimate SD or rate from this arm |
| `sd_method` | — | `pooled_within`: scale to control mean and pool SD within arms |
| `effects` | — | relative lifts (means) or absolute rate differences (proportions) |
| `ratio` | 1.0 | n_treatment ÷ n_control |
| `alpha`, `power`, `sides` | 0.05, 0.8, 2 | |
| `icc`, `cluster_size` | — | design effect = 1 + (m − 1) × ICC |
| `n_available` | — | control units you have: achieved power and MDE |

**Outputs:** `narrative.md`, `sample_size.csv`, `power_curve.png`, `metrics.json`.

**Limits:** normal approximations (with a small-sample t correction for means). Plan with a conservative SD; power is about the design,
never computed after the fact from the observed effect.
