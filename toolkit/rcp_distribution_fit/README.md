# rcp_distribution_fit — which distribution describes this variable?

**Navigator tree:** `T-DIST` · **First used:** L2.2, L2.3 · **Status:** working

Fits candidate families and compares them on AIC, KS distance, Q-Q plot and tail quantiles. Continuous positive data: normal,
lognormal, gamma, Weibull, exponential. Counts: Poisson vs negative binomial, with a dispersion check (variance ÷ mean) and the
observed vs predicted share of zeros.

| Role | Required | Meaning |
| --- | --- | --- |
| `target` | yes | numeric variable |

| Param | Default | Meaning |
| --- | --- | --- |
| `kind` | `auto` | `continuous` or `count` |
| `unit`, `agg` | none | aggregate first (e.g. lines → baskets) |
| `candidates` | all suitable | restrict families |
| `exclude_above` | none | treat extreme values separately (e.g. catastrophic claims); reported in row accounting |
| `tail_quantiles` | `[0.9, 0.99]` | compare fitted vs empirical tails |

**Outputs:** `narrative.md`, `fit_table.csv`, `fit.png` (histogram + Q-Q vs best fit, or counts vs fitted pmf), `metrics.json`.

**Limits:** AIC compares the candidates you gave it — the "best" may still fit badly in the tail. Goodness-of-fit p-values reject
almost everything at large n; read them as distances.
