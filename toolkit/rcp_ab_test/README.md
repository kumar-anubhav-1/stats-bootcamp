# rcp_ab_test — experiment readout with hygiene, CUPED, Bayesian view, guardrails and a decision

**Navigator nodes:** `N-EXP-SRM`, `N-EXP-CUPED`, `N-BAYES-AB` · **First used:** L4.1 · **Status:** working

Reads an A/B or champion/challenger test in the order a reviewer should: (1) sample-ratio mismatch against the planned split, overall and
by segment, with a note on where it is localised; (2) the primary metric at the unit of randomisation; (3) CUPED adjustment with a
pre-treatment covariate; (4) frequentist and Bayesian readouts; (5) guardrails; (6) a decision line (STOP on SRM; SHIP / SHIP WITH CAUTION
/ DON'T SHIP / INCONCLUSIVE against a practical threshold). Optional cumulative daily looks show why peeking misleads.

| Role | Required | Meaning |
| --- | --- | --- |
| `arm` | yes | assignment column |
| `outcome` | yes | primary metric (0/1 or numeric) |
| `unit` | no | unit of randomisation to aggregate to (store, branch) |
| `covariate` | no | pre-treatment covariate for CUPED |
| `date` | no | assignment date for cumulative looks |

| Param | Default | Meaning |
| --- | --- | --- |
| `arms` | two most frequent | `[treatment, control]` |
| `planned_split` | 50/50 | expected shares by arm |
| `srm_alpha` | 0.001 | SRM threshold |
| `segments` | — | columns used to localise an SRM |
| `baseline` | — | `{period_col, pre, post}` for cluster tests: post mean outcome, pre mean covariate |
| `log_covariate` | false | log-transform a skewed covariate |
| `guardrails` | — | list of `{metric, direction, tolerance}` |
| `practical_threshold` | — | smallest effect worth shipping (absolute units) |

**Outputs:** `narrative.md` (readout with decision), `metrics.json`, `cumulative_looks.csv`, `looks.png`, `row_accounting.md`.

**Limits:** cumulative looks are descriptive — use a pre-planned sequential design to stop early. CUPED requires a covariate measured
before assignment. Excluding a broken segment is a sensitivity analysis; the fix is to repair logging and re-run.
