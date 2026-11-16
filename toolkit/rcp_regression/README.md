# rcp_regression — OLS, logistic and GLMs with diagnostics and a business reading

**Navigator nodes:** `N-REG-OLS`, `N-REG-LOGIT`, `N-REG-GLM`, `N-REG-VIF` · **First used:** L5.1 · **Status:** working

Fits a linear, logistic, Poisson, negative-binomial or Gamma model from a config (feature list or a statsmodels formula), reports each
coefficient in business terms (units, % change for log outcomes and log links, odds ratios for logistic), fit statistics (R², AIC/BIC,
AUC, dispersion) and diagnostics (Breusch-Pagan, residual skew, Cook's distance, VIF) with plain-English warnings.

| Role | Required | Meaning |
| --- | --- | --- |
| `target` | yes | outcome |
| `features` | unless `formula` | predictor columns |
| `cluster` | no | cluster-robust standard errors by this column |
| `exposure` | no | log offset for count models (policy-years, store-weeks) |

| Param | Default | Meaning |
| --- | --- | --- |
| `family` | ols (logit if 0/1) | ols / logit / poisson / negbin / gamma |
| `formula` | — | e.g. `np.log(units) ~ promo_sku_share + C(store_id)` |
| `log_target` | false | model log(target) (OLS) |
| `robust` | HC3 (OLS) | HC3 / cluster / none |
| `negbin_alpha` | estimated | NB dispersion |
| `hide` | — | term prefixes hidden from the narrative table (fixed effects) |

The dataset block accepts `joins` (`{path, keys, columns}` or `{path, keys, count_as}`) to bring in drivers from another table or
count events per key (claims per policy).

**Outputs:** `narrative.md`, `coefficients.csv`, `diagnostics.png`, `metrics.json`, `row_accounting.md`.

**Limits:** associations, not causal effects, unless the design supports it. Regularised and non-linear models: L5.4, L5.6 and Day 6.
