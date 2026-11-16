# Navigator: all decision trees

Printable listing of every tree. The interactive version is on the [Navigator](index.md) page.

## Start: what is the business question?

- Describe / profile the data → **Which descriptive summary?**
- Which distribution describes this? → **Which distribution to assume?**
- Compare groups (is A different from B?) → **Which hypothesis test?**
- Design an experiment / how many units? → **Experiment design and sample size**
- Explain drivers of an outcome → **Which regression or GLM?**
- Predict an outcome for each customer/account → **Which ML model?**
- Forecast a quantity over time → **Which forecasting approach?**
- Segment customers or stores → **Which clustering method?**
- Detect anomalies or fraud → **Which anomaly-detection method?**
- Measure the causal impact of an action → **Which causal method?**
- Choose an evaluation metric or threshold → **Which evaluation metric and threshold?**
- Monitor a model or KPI over time → **Which drift or monitoring check?**
- Optimise a decision (price, stock, budget) → **Which optimisation approach?**

## Which descriptive summary?

**First — has the data been profiled and quality-checked?** <small>`N-DESC-Q1`</small>
- No, not yet → `N-DESC-PROFILE`
- Yes — summarise one categorical variable → `N-DESC-CAT`
- Yes — summarise one numeric variable → `N-DESC-Q2`
- Yes — relationship between two variables → `N-DESC-Q3`
- Yes — values are missing and I need to decide what to do → `N-DESC-MISSING`
- Profiling flagged duplicates, impossible values or unit errors → `N-DESC-QUALITY`
- I worry the data only contains survivors / approved cases → `N-DESC-BIAS`

**What does the distribution look like (histogram / ECDF)?** <small>`N-DESC-Q2`</small>
- Roughly symmetric, no extreme tail → `N-DESC-SYM`
- Skewed or heavy-tailed (spend, balances) → `N-DESC-SKEW`
- A few values look impossible or extreme → `N-DESC-OUTLIER`

**What types are the two variables?** <small>`N-DESC-Q3`</small>
- Both numeric → `N-DESC-CORR`
- Both categorical → `N-DESC-XTAB`
- The relationship flips when I split by a third variable → `N-DESC-STRATIFY`

???+ note "Profile + data-quality checklist — `N-DESC-PROFILE`"
    **Use when:** Always first. Types, nulls, uniques, ranges, duplicates, impossible values, grain.  
    **Check:** Declared grain matches keys; Control totals reconcile; Business rules (no negative prices; returns flagged)  
    **If a check fails:** Write a rule per issue and count rows affected before changing anything  
    **Alternatives:** Reconcile to finance totals; Compare with last month's profile  
    **Pitfalls:** Silently dropping rows; "Cleaning" valid returns as errors; Joining at the wrong grain  
    **Action:** Fix at source where possible; document every rule in the analysis log.  
    **Lessons:** L0.3, L1.2

???+ note "Data-quality rules (validity, duplicates, reconciliation) — `N-DESC-QUALITY`"
    **Use when:** Profiling flagged duplicates, impossible values or unit errors.  
    **Check:** Is the value impossible or merely unusual?; Duplicate key vs duplicate row  
    **If a check fails:** Quarantine doubtful rows into a separate file rather than deleting  
    **Alternatives:** Ask the data owner; Compare against source system  
    **Pitfalls:** Removing genuine extremes; Not reporting rows removed  
    **Action:** Correct, quarantine or keep with a flag — never silently drop.  
    **Lessons:** L1.2

???+ note "Counts, percentages, mode; bar chart — `N-DESC-CAT`"
    **Use when:** One categorical variable (region, product type).  
    **Check:** Categories consistent (spelling; case); Rare levels  
    **If a check fails:** Group rare levels into "Other"  
    **Alternatives:** Pareto chart for concentration  
    **Pitfalls:** Pie charts with many slices; Percentages without the base n  
    **Action:** Report shares with counts.  
    **Lessons:** L1.4

???+ note "Mean ± standard deviation; histogram — `N-DESC-SYM`"
    **Use when:** Symmetric numeric data without heavy tails.  
    **Check:** Histogram/Q-Q looks symmetric; No impossible values  
    **If a check fails:** Switch to median and IQR  
    **Alternatives:** Coefficient of variation to compare spread across scales  
    **Pitfalls:** Reporting mean of a skewed variable as "typical"  
    **Action:** Use the mean for planning totals; quote SD for variability.  
    **Lessons:** L1.4

???+ note "Median, IQR, percentiles (P90/P99), MAD; log-scale histogram, ECDF; Lorenz/Pareto — `N-DESC-SKEW`"
    **Use when:** Spend, income, balances, claim amounts — skewed or heavy-tailed.  
    **Check:** Skewness > 1; Mean ≫ median; Top 1% share  
    **If a check fails:** If decisions need totals; keep the mean but show the tail separately  
    **Alternatives:** Trimmed mean; Log transform; Separate model for extreme segment  
    **Pitfalls:** Averages driven by a few bulk buyers; Removing genuine high-value customers  
    **Action:** Describe the typical customer with the median; manage the tail as its own segment.  
    **Lessons:** L1.4, L1.6

???+ note "Outlier scan — IQR fences, robust (MAD) z-score; decide keep / cap / exclude / model separately — `N-DESC-OUTLIER`"
    **Use when:** Values far from the rest; suspected errors.  
    **Check:** Error or genuine extreme?; Effect on key results with and without  
    **If a check fails:** Use robust statistics instead of deleting  
    **Alternatives:** Isolation Forest for many variables  
    **Pitfalls:** Using a plain z-score on skewed data; Deleting fraud signals  
    **Action:** Correct errors; keep genuine extremes but report sensitivity.  
    **Lessons:** L1.6

???+ note "Missing-data diagnosis (MCAR / MAR / MNAR) and treatment — `N-DESC-MISSING`"
    **Use when:** Any variable with missing values that matters to the analysis.  
    **Check:** Missingness rate by segment (MAR?); Do rows with missing values differ in outcome (MNAR?)  
    **If a check fails:** MNAR → keep a "missing" category / flag and run a sensitivity analysis  
    **Alternatives:** Multiple imputation (MICE) for MAR; Simple imputation only for MCAR and small rates  
    **Pitfalls:** Listwise deletion that silently removes risky customers; Mean-imputing MNAR data  
    **Action:** Document mechanism, method and rows affected; never hide missingness.  
    **Lessons:** L1.3

???+ note "Scatter plot first, then Pearson (linear) / Spearman (monotone) / Kendall (small n, ties) — `N-DESC-CORR`"
    **Use when:** Two numeric variables.  
    **Check:** Linearity on the scatter; Outliers driving r  
    **If a check fails:** Non-linear → Spearman or binned means; outliers → robust or rank methods  
    **Alternatives:** LOESS smoother; Binned plot  
    **Pitfalls:** Reading correlation as causation; r on aggregated data (ecological fallacy)  
    **Action:** Use as a lead for further analysis, not a decision.  
    **Lessons:** L1.7

???+ note "Contingency table with row/column % and Cramér's V — `N-DESC-XTAB`"
    **Use when:** Two categorical variables.  
    **Check:** Cell counts; Which percentage answers the question  
    **If a check fails:** Collapse sparse categories  
    **Alternatives:** Chi-square test (→ T-TEST) if inference is needed  
    **Pitfalls:** Wrong denominator  
    **Action:** Show the comparison that matches the decision.  
    **Lessons:** L1.7

???+ note "Stratified analysis — check for Simpson's paradox and confounding — `N-DESC-STRATIFY`"
    **Use when:** An overall comparison may be distorted by a third variable (format, channel, vintage).  
    **Check:** Is the third variable related to both groups and outcome?  
    **If a check fails:** Report within-stratum results and a weighted overall  
    **Alternatives:** Regression with the confounder as a covariate (→ T-REG)  
    **Pitfalls:** Reporting only the aggregate  
    **Action:** Decide on the within-stratum result; explain the reversal.  
    **Lessons:** L2.4

???+ note "Sampling, selection and survivorship-bias check — `N-DESC-BIAS`"
    **Use when:** The data only contains "survivors" (current SKUs, approved applicants, active customers).  
    **Check:** What is missing from the population?; How was the sample selected?  
    **If a check fails:** Recover the missing history (archives; declined applications) or state the limitation  
    **Alternatives:** Reweighting; Reject inference  
    **Pitfalls:** Analysing the current range only  
    **Action:** Restate conclusions for the population actually analysed.  
    **Lessons:** L2.4

## Which distribution to assume?

**What kind of quantity is it?** <small>`N-DIST-Q1`</small>
- Yes/No per unit (default, conversion) → `N-DIST-BIN`
- Count of events in a period (units sold, claims) → `N-DIST-Q2`
- Positive skewed amount (spend, income, claim size) → `N-DIST-AMT`
- Time until an event (churn, default) → `N-DIST-TIME`
- A rate or probability itself → `N-DIST-BETA`
- Sample drawn without replacement from a small lot (audit) → `N-DIST-HYPER`

**Compare the variance with the mean.** <small>`N-DIST-Q2`</small>
- Variance ≈ mean → `N-DIST-POIS`
- Variance ≫ mean (over-dispersed) → `N-DIST-NB`
- Mostly zeros (intermittent) → `N-FCST-INTERMITTENT`

???+ note "Bernoulli / Binomial (Beta-Binomial if the rate varies across groups) — `N-DIST-BIN`"
    **Use when:** Defaults in a vintage, conversions in an A/B test.  
    **Check:** Independent trials; Same probability across units  
    **If a check fails:** Rate varies by store/branch → Beta-Binomial or hierarchical model  
    **Alternatives:** Logistic regression to model the rate  
    **Pitfalls:** Ignoring clustering → over-confident intervals  
    **Action:** Quote the rate with its interval.  
    **Lessons:** L2.2

???+ note "Poisson — `N-DIST-POIS`"
    **Use when:** Counts with variance ≈ mean (claims per policy, baskets per hour).  
    **Check:** Variance/mean ≈ 1; Constant exposure  
    **If a check fails:** Over-dispersion → Negative Binomial; varying exposure → rate with offset  
    **Alternatives:** Poisson GLM with covariates  
    **Pitfalls:** Assuming Poisson for retail SKU sales (usually over-dispersed)  
    **Action:** Use for capacity and frequency planning.  
    **Lessons:** L2.2, L5.5

???+ note "Negative Binomial — `N-DIST-NB`"
    **Use when:** Over-dispersed counts (weekly SKU units, claims with heterogeneous risk).  
    **Check:** Variance/mean > 1 clearly  
    **If a check fails:** Many structural zeros → zero-inflated / hurdle  
    **Alternatives:** Quasi-Poisson  
    **Pitfalls:** Under-stated uncertainty if Poisson is used  
    **Action:** Size safety stock with the wider spread.  
    **Lessons:** L2.2, L5.5

???+ note "Lognormal or Gamma (compare Q-Q plots and AIC) — `N-DIST-AMT`"
    **Use when:** Basket spend, income, claim severity.  
    **Check:** Positive only; Q-Q on log scale; Tail fit  
    **If a check fails:** Extreme tail → separate large-loss model / Pareto tail  
    **Alternatives:** Weibull; Empirical quantiles  
    **Pitfalls:** Assuming normality for amounts  
    **Action:** Use quantiles (P90, P99) for limits and reserves.  
    **Lessons:** L2.3

???+ note "Exponential (constant hazard) → Weibull (changing hazard); censoring-aware methods — `N-DIST-TIME`"
    **Use when:** Time to churn, time to default, time between purchases.  
    **Check:** Censoring present?; Hazard constant over time?  
    **If a check fails:** Non-constant hazard → Weibull or Kaplan-Meier  
    **Alternatives:** Survival analysis (→ N-TEST-SURV)  
    **Pitfalls:** Averaging only observed event times (ignores censoring)  
    **Action:** Use survival curves for retention planning.  
    **Lessons:** L2.3, L9.2

???+ note "Beta (uncertainty about a probability) — `N-DIST-BETA`"
    **Use when:** Prior/posterior for a conversion or default rate.  
    **Check:** Bounded 0-1  
    **If a check fails:** —  
    **Alternatives:** Bootstrap the rate  
    **Pitfalls:** Treating a small-sample rate as exact  
    **Action:** Report probability that rate exceeds a threshold.  
    **Lessons:** L2.3, L4.3

???+ note "Hypergeometric (acceptance sampling) — `N-DIST-HYPER`"
    **Use when:** Audit samples drawn without replacement from a finite file population.  
    **Check:** Sample is a large share of the lot  
    **If a check fails:** Small share → Binomial approximation is fine  
    **Alternatives:** Simulation  
    **Pitfalls:** Using Binomial when sampling 50 of 200 files  
    **Action:** Choose sample size for a target detection probability.  
    **Lessons:** L2.2

## Which hypothesis test?

**Is this an experiment that needs an SRM / design check first?** <small>`N-TEST-Q0`</small>
- Yes — randomised test, not yet checked → `N-EXP-SRM`
- No, or already checked → `N-TEST-Q1`

**What type is the outcome?** <small>`N-TEST-Q1`</small>
- Continuous (amount, units, score) → `N-TEST-Q2`
- Binary (rate: default, conversion, return) → `N-TEST-Q3`
- Count / rate with exposure → `N-TEST-COUNT`
- Time-to-event with censoring → `N-TEST-SURV`
- I am running many tests at once → `N-TEST-MULTI`

**How many groups, and are they independent?** <small>`N-TEST-Q2`</small>
- 2 independent groups → `N-TEST-2G-MEAN`
- 2 paired measurements (same store before/after) → `N-TEST-PAIRED`
- More than 2 groups → `N-TEST-KG`
- 2 groups and I have a strong pre-period measure per unit → `N-REG-ANCOVA`
- Very small samples; I want minimal assumptions → `N-TEST-PERM`
- I need to adjust for several covariates → `N-REG-OLS`

**How many groups / is it paired?** <small>`N-TEST-Q3`</small>
- 2 independent groups → `N-TEST-2G-PROP`
- Paired yes/no (same customer before/after) → `N-TEST-MCNEMAR`
- More than 2 groups or categories → `N-TEST-CHI`

???+ note "Welch two-sample t-test (+ effect size and CI) — `N-TEST-2G-MEAN`"
    **Use when:** Compare average outcome between two independent groups — at the unit that was randomised.  
    **Check:** Independent units (aggregate to store/branch if randomised there); ≥30 units/group or not heavy-tailed; Unequal variances are fine (Welch)  
    **If a check fails:** Heavy tails and small n → Mann-Whitney or bootstrap CI; Clustered rows → aggregate to cluster or mixed model; Size differences → growth vs own pre-period  
    **Alternatives:** Permutation test; Bayesian estimate of the difference; Regression with pre-period covariate (CUPED)  
    **Pitfalls:** Testing transaction lines when stores were randomised; Reading p < 0.05 as "large"; Ignoring a few bulk buyers  
    **Action:** Roll out / extend / stop — sized by the CI of the lift, not the p-value.  
    **Lessons:** L3.4

???+ note "Two-proportion z-test (Fisher's exact if any expected cell < 5) — `N-TEST-2G-PROP`"
    **Use when:** Compare a rate (default, conversion, cure) between two independent groups.  
    **Check:** Expected cell counts ≥ 5; Independent units; Same definition and observation window  
    **If a check fails:** Small counts → Fisher exact; Clustered → aggregate or GLMM  
    **Alternatives:** Logistic regression with covariates; Bayesian Beta-Binomial  
    **Pitfalls:** Base-rate blindness (0.5 pp may be huge at a 4% base); Confounding (channel; vintage)  
    **Action:** Quote risk difference in pp and relative risk; translate to accounts or units per 1,000.  
    **Lessons:** L3.4, L4.5

???+ note "Paired t-test (Wilcoxon signed-rank if differences are skewed) — `N-TEST-PAIRED`"
    **Use when:** Same units measured twice (store before/after, customer pre/post).  
    **Check:** Differences roughly symmetric; Pairs correctly matched  
    **If a check fails:** Skewed differences → Wilcoxon signed-rank  
    **Alternatives:** Difference-in-differences when a control group exists (→ T-CAUSAL)  
    **Pitfalls:** Before/after without control ignores seasonality  
    **Action:** Use only with a control group for causal claims.  
    **Lessons:** L3.4

???+ note "One-way ANOVA (+ Levene); Welch ANOVA + Games-Howell if variances differ; Kruskal-Wallis + Dunn if non-normal — `N-TEST-KG`"
    **Use when:** Compare means across 3+ groups (regions, formats).  
    **Check:** Equal variances (Levene); Normal residuals / large n  
    **If a check fails:** Welch ANOVA; Kruskal-Wallis  
    **Alternatives:** Regression with dummies  
    **Pitfalls:** Many pairwise t-tests without correction  
    **Action:** Act on the pairs that differ by a meaningful amount.  
    **Lessons:** L3.5

???+ note "Chi-square test of independence (Fisher exact for small tables) + Cramér's V — `N-TEST-CHI`"
    **Use when:** Association between two categorical variables.  
    **Check:** Expected counts ≥ 5  
    **If a check fails:** Fisher exact or collapse categories  
    **Alternatives:** Logistic / multinomial regression  
    **Pitfalls:** Huge n makes trivial associations significant  
    **Action:** Report the effect size, not just p.  
    **Lessons:** L3.5

???+ note "McNemar's test — `N-TEST-MCNEMAR`"
    **Use when:** Paired binary outcomes.  
    **Check:** Discordant pairs count  
    **If a check fails:** Exact binomial on discordant pairs  
    **Alternatives:** Conditional logistic regression  
    **Pitfalls:** Treating paired data as independent  
    **Action:** Report change in rate.  
    **Lessons:** L3.5

???+ note "Poisson / Negative Binomial rate comparison (GLM with exposure offset) — `N-TEST-COUNT`"
    **Use when:** Claims per policy-year, units per store-week.  
    **Check:** Over-dispersion  
    **If a check fails:** Negative Binomial  
    **Alternatives:** Bootstrap the rate ratio  
    **Pitfalls:** Ignoring different exposure  
    **Action:** Report rate ratio with CI.  
    **Lessons:** L5.5

???+ note "Kaplan-Meier curves + log-rank test (RMST if hazards cross) — `N-TEST-SURV`"
    **Use when:** Time to churn or default with censoring.  
    **Check:** Censoring non-informative; Proportional hazards for log-rank  
    **If a check fails:** Crossing curves → restricted mean survival time  
    **Alternatives:** Cox regression  
    **Pitfalls:** Comparing average time among churners only  
    **Action:** Target retention where curves diverge.  
    **Lessons:** L9.2

???+ note "Multiple-testing correction — Holm (family-wise) or Benjamini-Hochberg (false discovery rate) — `N-TEST-MULTI`"
    **Use when:** Many segments, metrics or features tested.  
    **Check:** How many tests were run (including ones not reported)?  
    **If a check fails:** Pre-register primary metric; treat the rest as exploratory  
    **Alternatives:** Hierarchical / Bayesian shrinkage  
    **Pitfalls:** p-hacking; reporting only "winners"  
    **Action:** Re-test winners on fresh data before acting.  
    **Lessons:** L3.7

???+ note "Permutation test — `N-TEST-PERM`"
    **Use when:** Small samples or unusual statistics; minimal assumptions.  
    **Check:** Exchangeability under the null (randomised design)  
    **If a check fails:** —  
    **Alternatives:** Bootstrap CI  
    **Pitfalls:** Permuting at the wrong level (lines vs stores)  
    **Action:** Use alongside the main test as a robustness check.  
    **Lessons:** L3.2

## Experiment design and sample size

**Can you randomise who/what gets the treatment?** <small>`N-EXP-Q1`</small>
- No → `N-CAUSAL-ROOT`
- Yes — I need a sample size → `N-EXP-POWER`
- Yes — the test is running/finished and I need to check it → `N-EXP-SRM`
- Yes — variance is high and the test would take too long → `N-EXP-CUPED`
- Yes — stakeholders want to look at results early → `N-EXP-SEQ`
- Yes — I want the probability B beats A → `N-BAYES-AB`

???+ note "Power and sample size (α, power, MDE, baseline variance; cluster design effect) — `N-EXP-POWER`"
    **Use when:** Before any test — how many customers/stores/weeks?  
    **Check:** Unit of randomisation; Historic SD or base rate; Smallest effect worth acting on  
    **If a check fails:** Too many units needed → CUPED; longer test; paired stores; larger MDE  
    **Alternatives:** Simulation-based power  
    **Pitfalls:** Forgetting the design effect for store-level tests; Post-hoc power  
    **Action:** Agree MDE and duration with the business before launch.  
    **Lessons:** L3.6

???+ note "Sample-ratio-mismatch check (chi-square on assignment counts) — `N-EXP-SRM`"
    **Use when:** Every experiment, before reading results.  
    **Check:** Observed split vs planned split; By platform/version/day  
    **If a check fails:** SRM detected → stop; find the assignment or logging bug; do not trust the results  
    **Alternatives:** Analyse the unaffected segment only; clearly labelled  
    **Pitfalls:** Analysing a broken test because "the lift looks good"  
    **Action:** Fix the pipeline and re-run.  
    **Lessons:** L4.1

???+ note "CUPED / pre-period covariate adjustment — `N-EXP-CUPED`"
    **Use when:** High-variance metrics with a correlated pre-period measure.  
    **Check:** Covariate measured before treatment  
    **If a check fails:** Post-treatment covariates bias the result  
    **Alternatives:** Stratified randomisation; paired design; growth vs own baseline  
    **Pitfalls:** Using covariates affected by the treatment  
    **Action:** Shorter tests with the same power.  
    **Lessons:** L4.2

???+ note "Sequential testing (alpha spending / always-valid p-values) — `N-EXP-SEQ`"
    **Use when:** Need to monitor results before the planned end.  
    **Check:** Planned looks and boundaries defined upfront  
    **If a check fails:** Ad-hoc peeking → treat results as exploratory  
    **Alternatives:** Bayesian monitoring with pre-agreed decision rule  
    **Pitfalls:** Stopping the first day p < 0.05  
    **Action:** Pre-register stopping rules.  
    **Lessons:** L4.2

???+ note "Bayesian A/B test (Beta-Binomial; P(B > A), expected loss) — `N-BAYES-AB`"
    **Use when:** Decision-makers want probability statements; prior knowledge exists.  
    **Check:** Prior is justified and disclosed; Same SRM hygiene  
    **If a check fails:** Sensitive to prior → report with a weak prior too  
    **Alternatives:** Frequentist CI  
    **Pitfalls:** Treating P(B > A) = 0.8 as certainty  
    **Action:** Ship when expected loss is below an agreed tolerance.  
    **Lessons:** L4.3

## Which regression or GLM?

**What type is the outcome?** <small>`N-REG-Q1`</small>
- Continuous, roughly symmetric residuals → `N-REG-OLS`
- Positive skewed amount → `N-REG-GLM`
- Binary → `N-REG-LOGIT`
- Count → `N-REG-GLM`
- Elasticity: % change in units for % change in price → `N-REG-LOGLOG`
- Many predictors / signs flip / VIF high → `N-REG-VIF`
- Effect depends on another variable → `N-REG-INTERACT`
- Risk jumps above a threshold (curved effect) → `N-REG-NONLINEAR`
- Insurance pricing: frequency × severity → `N-REG-GLM-INS`

???+ note "Linear regression (OLS) with diagnostics — `N-REG-OLS`"
    **Use when:** Explain a continuous outcome with several drivers.  
    **Check:** Linearity; Constant variance (Breusch-Pagan); Independence; Influential points (Cook's D); VIF  
    **If a check fails:** Heteroscedastic → robust SEs or log outcome; outliers → robust/quantile regression; collinear → Ridge  
    **Alternatives:** Quantile regression; GAM  
    **Pitfalls:** Reading coefficients causally; Extrapolating  
    **Action:** Use coefficients as "all else equal" associations; test causality separately.  
    **Lessons:** L5.1, L5.2

???+ note "Logistic regression (odds ratios) — `N-REG-LOGIT`"
    **Use when:** Binary outcomes — default, churn, response.  
    **Check:** Linearity in the logit; Enough events per variable (≥10); Separation  
    **If a check fails:** Non-linear → bins/WoE or splines; rare events → penalised (Firth)  
    **Alternatives:** Gradient boosting with SHAP (→ T-ML)  
    **Pitfalls:** Interpreting odds ratios as risk ratios when the outcome is common  
    **Action:** Score, rank, and set cut-offs with business costs.  
    **Lessons:** L5.3

???+ note "GLM — Poisson/Negative Binomial for counts (offset for exposure), Gamma for positive amounts, Tweedie for zero + positive — `N-REG-GLM`"
    **Use when:** Counts, claim severity, spend including non-buyers.  
    **Check:** Dispersion; Link function; Residual deviance  
    **If a check fails:** Over-dispersion → NB; many zeros → zero-inflated/hurdle or Tweedie  
    **Alternatives:** Log-OLS for amounts  
    **Pitfalls:** OLS on counts → negative predictions  
    **Action:** Price and plan on predicted means and quantiles.  
    **Lessons:** L5.5

???+ note "Log-log regression / Poisson GLM on log price (elasticity), with promo, display, SKU, store and week controls — `N-REG-LOGLOG`"
    **Use when:** Price elasticity, promotion response.  
    **Check:** Price variation not driven only by promotions; Controls for promo/display/seasonality; Stockouts excluded  
    **If a check fails:** No exogenous price variation → run a price test  
    **Alternatives:** Hierarchical elasticity by category  
    **Pitfalls:** Omitting promo controls → biased elasticity; Using chain-level averages that mix stores  
    **Action:** Feed elasticity into price/promo optimisation.  
    **Lessons:** L8.4

???+ note "Multicollinearity check (VIF) → drop/combine features or regularise (Ridge, Lasso, Elastic Net) — `N-REG-VIF`"
    **Use when:** Correlated predictors; unstable or flipping coefficient signs.  
    **Check:** VIF > 5–10 (rule of thumb); Correlation matrix  
    **If a check fails:** Combine (e.g. limit/income ratio); Ridge  
    **Alternatives:** PCA components  
    **Pitfalls:** Dropping the variable the business cares about without explanation  
    **Action:** Explain combined drivers, not individual unstable coefficients.  
    **Lessons:** L5.2, L5.4

???+ note "Interaction terms, splines/polynomials; mixed models for grouped data — `N-REG-INTERACT`"
    **Use when:** Effect depends on a second variable (young × high DTI) or is curved (utilisation).  
    **Check:** Partial-effect plots; Enough data in each combination  
    **If a check fails:** Too sparse → bins or regularisation  
    **Alternatives:** Tree-based models detect interactions automatically  
    **Pitfalls:** Interpreting main effects alone when interaction is present  
    **Action:** Target policies at the combination, not each factor alone.  
    **Lessons:** L5.6

???+ note "Non-linear effects — bins/WoE, splines — `N-REG-NONLINEAR`"
    **Use when:** Risk jumps above a threshold (utilisation > 80%).  
    **Check:** Binned outcome rates by decile  
    **If a check fails:** —  
    **Alternatives:** Gradient boosting  
    **Pitfalls:** A single linear term hides the threshold  
    **Action:** Set policy rules at the threshold.  
    **Lessons:** L5.6, L8.7

???+ note "Regression of outcome on group + pre-period covariate (ANCOVA / CUPED-style) — `N-REG-ANCOVA`"
    **Use when:** Two-group comparison with a strong baseline covariate.  
    **Check:** Covariate measured before treatment  
    **If a check fails:** —  
    **Alternatives:** Growth vs own baseline  
    **Pitfalls:** Adjusting for post-treatment variables  
    **Action:** Tighter CI for the same data.  
    **Lessons:** L4.2

???+ note "Frequency-severity GLMs (Poisson/NB × Gamma) or Tweedie pure premium — `N-REG-GLM-INS`"
    **Use when:** Insurance pricing.  
    **Check:** Exposure offset; Large-loss treatment  
    **If a check fails:** —  
    **Alternatives:** GBM with Tweedie loss  
    **Pitfalls:** Catastrophic claims distorting severity  
    **Action:** Price = expected frequency × severity × loadings.  
    **Lessons:** L9.4

## Which ML model?

**What matters most?** <small>`N-ML-Q1`</small>
- Regulator/customer needs reasons for each decision → `N-ML-SCORECARD`
- Best accuracy on tabular data → `N-ML-GBM`
- The target is rare (fraud ~1%) → `N-ML-IMBALANCE`
- Score looks too good to be true → `N-ML-LEAK`
- Images, text, sequences at scale → `N-ML-DL`

???+ note "Logistic scorecard with WoE binning (points to double the odds) — `N-ML-SCORECARD`"
    **Use when:** Credit decisions needing adverse-action reasons and stability.  
    **Check:** Monotonic WoE; IV per feature; Out-of-time validation; Calibration  
    **If a check fails:** Weak lift → GBM challenger with SHAP under model-risk governance  
    **Alternatives:** Explainable boosting machines  
    **Pitfalls:** Using post-outcome fields; Using protected attributes or proxies  
    **Action:** Set cut-offs on profit/loss by score band.  
    **Lessons:** L8.7

???+ note "Gradient boosting (LightGBM/XGBoost) vs logistic/linear baseline; random forest check — `N-ML-GBM`"
    **Use when:** Tabular prediction where accuracy matters.  
    **Check:** Leakage audit; Out-of-time or grouped CV; Calibration; Stability across segments  
    **If a check fails:** Overfitting → stronger regularisation; fewer features  
    **Alternatives:** Random forest; Stacking  
    **Pitfalls:** Tuning on the test set; Random split when time matters  
    **Action:** Deploy with monitoring and a champion/challenger test.  
    **Lessons:** L6.2, L6.4

???+ note "Class weights or threshold moving (SMOTE with care); evaluate with PR-AUC, precision@k — `N-ML-IMBALANCE`"
    **Use when:** Rare events — fraud, default in good books.  
    **Check:** Base rate; Cost of FP vs FN; Investigator capacity  
    **If a check fails:** —  
    **Alternatives:** Anomaly detection for unseen patterns (→ T-ANOM)  
    **Pitfalls:** 99% accuracy by predicting no fraud; Resampling before the train/test split  
    **Action:** Set the threshold by cost or capacity (→ T-METRIC).  
    **Lessons:** L6.5

???+ note "Leakage audit — target, temporal and preprocessing leakage — `N-ML-LEAK`"
    **Use when:** AUC suspiciously high (e.g. > 0.95 in credit), or a feature "too predictive".  
    **Check:** When is each field known?; Was preprocessing fit on all data?; Same customer in train and test?  
    **If a check fails:** Remove post-outcome fields; refit pipeline inside CV  
    **Alternatives:** Out-of-time validation  
    **Pitfalls:** Celebrating a 0.98 AUC  
    **Action:** Never ship until the leak is explained.  
    **Lessons:** L6.4

???+ note "Deep learning (awareness) — usually not better than GBM on tabular data — `N-ML-DL`"
    **Use when:** Unstructured data at scale.  
    **Check:** Data volume; Explainability needs; Baseline comparison  
    **If a check fails:** Use GBM  
    **Alternatives:** Embeddings + GBM  
    **Pitfalls:** Complexity without lift  
    **Action:** Benchmark against a simple baseline first.  
    **Lessons:** L9.3

## Which clustering method?

**What do the data and goal look like?** <small>`N-CLUST-Q1`</small>
- Business rules are enough (recency, frequency, value) → `N-SEG-RFM`
- Numeric features, compact groups → `N-CLUST-KMEANS`
- Odd shapes, noise points → `N-CLUST-DBSCAN`
- Overlapping groups, soft membership → `N-CLUST-GMM`
- Which products are bought together? → `N-SEG-BASKET`

???+ note "RFM segmentation — `N-SEG-RFM`"
    **Use when:** Simple, explainable CRM segments.  
    **Check:** Time window; Score cut-offs  
    **If a check fails:** —  
    **Alternatives:** K-Means on RFM features  
    **Pitfalls:** Static segments never refreshed  
    **Action:** Tailor CRM offers by segment.  
    **Lessons:** L8.2

???+ note "K-Means (scale features; choose k with elbow + silhouette; check stability) — `N-CLUST-KMEANS`"
    **Use when:** Customer/store segmentation on numeric features.  
    **Check:** Scaling; Outliers; Stability across seeds and samples  
    **If a check fails:** Unstable → fewer features; PCA first; GMM  
    **Alternatives:** Hierarchical (Ward); GMM  
    **Pitfalls:** Clusters that do not change any action; Including IDs as features  
    **Action:** Name each cluster and link it to a different action.  
    **Lessons:** L8.1

???+ note "DBSCAN / HDBSCAN — `N-CLUST-DBSCAN`"
    **Use when:** Irregular shapes; isolate noise.  
    **Check:** eps / min_samples sensitivity  
    **If a check fails:** —  
    **Alternatives:** Isolation Forest for anomalies  
    **Pitfalls:** Varying density  
    **Action:** Treat noise points as candidates for review.  
    **Lessons:** L8.1

???+ note "Gaussian mixture model (BIC for k) — `N-CLUST-GMM`"
    **Use when:** Soft, overlapping segments.  
    **Check:** BIC curve  
    **If a check fails:** —  
    **Alternatives:** K-Means  
    **Pitfalls:** Over-interpreting probabilities  
    **Action:** Use membership probabilities for targeting.  
    **Lessons:** L8.1

???+ note "Market-basket analysis (support, confidence, lift) — `N-SEG-BASKET`"
    **Use when:** Cross-sell, layout, bundles.  
    **Check:** Minimum support; Lift > 1 meaningful  
    **If a check fails:** —  
    **Alternatives:** Sequential patterns  
    **Pitfalls:** Trivial rules (bread → milk); High lift on tiny support  
    **Action:** Bundle or co-locate high-lift, decent-support pairs.  
    **Lessons:** L8.3

## Which anomaly-detection method?

**What does the suspicious pattern look like?** <small>`N-ANOM-Q1`</small>
- One variable, static → `N-DESC-OUTLIER`
- Many variables at once → `N-ANOM-MULTI`
- Entities linked by shared devices/addresses → `N-ANOM-GRAPH`
- Amounts bunched just below a threshold → `N-ANOM-STRUCT`
- Numbers look made up or rounded → `N-ANOM-BENFORD`
- A metric over time jumped → `N-FCST-BREAK`

???+ note "Isolation Forest (global) / LOF (local) / residual-based scores — `N-ANOM-MULTI`"
    **Use when:** Multivariate outliers without labels (returns abuse, unusual accounts).  
    **Check:** Feature scaling; Contamination = alert budget  
    **If a check fails:** Too many alerts → raise threshold; add rules  
    **Alternatives:** Supervised model once labels exist  
    **Pitfalls:** Treating every anomaly as fraud  
    **Action:** Route top alerts to investigators; measure precision.  
    **Lessons:** L8.5

???+ note "Graph / link analysis (connected components on shared devices and addresses) — `N-ANOM-GRAPH`"
    **Use when:** Fraud rings, mule networks.  
    **Check:** Benign sharing (households) vs suspicious  
    **If a check fails:** —  
    **Alternatives:** Community detection  
    **Pitfalls:** Flagging families  
    **Action:** Investigate components above a size threshold.  
    **Lessons:** L8.6

???+ note "Threshold-bunching (structuring) check — `N-ANOM-STRUCT`"
    **Use when:** Deposits just below a reporting limit.  
    **Check:** Compare just-below vs just-above frequencies  
    **If a check fails:** —  
    **Alternatives:** Rules on repeated near-threshold deposits  
    **Pitfalls:** Ignoring legitimate payroll patterns  
    **Action:** Escalate per AML policy.  
    **Lessons:** L8.6

???+ note "Benford first-digit test + last-digit/rounding test, compared with peers — `N-ANOM-BENFORD`"
    **Use when:** Suspected fabricated figures (a store, branch, expense claims).  
    **Check:** Data spans several orders of magnitude; Compare with peer units not only theory  
    **If a check fails:** Narrow-range data → use peer comparison and rounding tests  
    **Alternatives:** Duplicate-amount tests  
    **Pitfalls:** Treating a Benford deviation as proof  
    **Action:** Audit the flagged unit.  
    **Lessons:** L2.6

## Which forecasting approach?

**What does the series look like?** <small>`N-FCST-Q1`</small>
- Smooth with trend/seasonality → `N-FCST-SEASON`
- Known drivers (price, promo, holidays, weather) → `N-FCST-DRIVERS`
- Mostly zeros (intermittent) → `N-FCST-INTERMITTENT`
- Hierarchy (SKU → category → total) → `N-FCST-HIER`
- Sudden level change → `N-FCST-BREAK`
- Sales capped by stockouts → `N-FCST-CENSOR`

???+ note "Decompose (STL) → ETS / SARIMA vs seasonal-naive baseline — `N-FCST-SEASON`"
    **Use when:** Weekly category sales, monthly balances.  
    **Check:** Rolling-origin backtest vs seasonal-naive; Residual autocorrelation  
    **If a check fails:** Does not beat baseline → use baseline  
    **Alternatives:** Prophet-style models  
    **Pitfalls:** Evaluating on one split; MAPE near zero  
    **Action:** Plan with forecast + interval.  
    **Lessons:** L7.1, L7.2

???+ note "ARIMAX / regression with lags / GBM with calendar and driver features — `N-FCST-DRIVERS`"
    **Use when:** Promotions, prices, holidays drive demand.  
    **Check:** Driver values known at forecast time  
    **If a check fails:** —  
    **Alternatives:** Prophet with regressors  
    **Pitfalls:** Using actual future weather/promos that will not be known  
    **Action:** Scenario forecasts for promo plans.  
    **Lessons:** L7.2

???+ note "Croston / SBA; classify with ADI and CV²; evaluate with MASE — `N-FCST-INTERMITTENT`"
    **Use when:** Long-tail SKUs.  
    **Check:** ADI > 1.32  
    **If a check fails:** —  
    **Alternatives:** Aggregate to higher level  
    **Pitfalls:** MAPE undefined at zero  
    **Action:** Stock policy by service level, not point forecast.  
    **Lessons:** L7.4

???+ note "Hierarchical reconciliation (bottom-up, MinT) — `N-FCST-HIER`"
    **Use when:** Forecasts needed at several levels that must add up.  
    **Check:** Coherence  
    **If a check fails:** —  
    **Alternatives:** Top-down with proportions  
    **Pitfalls:** Inconsistent numbers across teams  
    **Action:** One reconciled number set.  
    **Lessons:** L7.4

???+ note "Change-point detection (CUSUM, PELT) then refit post-break — `N-FCST-BREAK`"
    **Use when:** Store refit, competitor opening, policy change.  
    **Check:** Break date confidence; Business explanation  
    **If a check fails:** —  
    **Alternatives:** Intervention dummy in the model  
    **Pitfalls:** Fitting through the break  
    **Action:** Investigate cause; adjust targets.  
    **Lessons:** L7.5

???+ note "Treat stockout periods as censored demand before modelling — `N-FCST-CENSOR`"
    **Use when:** Sales understate demand when out of stock.  
    **Check:** Stockout flags available  
    **If a check fails:** Exclude or uncensor stockout periods  
    **Alternatives:** Tobit-style models  
    **Pitfalls:** Forecasting sales instead of demand → chronic under-stocking  
    **Action:** Safety stock on uncensored demand.  
    **Lessons:** L7.5

## Which causal method?

**How was the treatment assigned?** <small>`N-CAUSAL-ROOT`</small>
- Randomly → `N-TEST-Q0`
- Not random — first draw the causal diagram → `N-CAUSAL-DAG`
- Treated vs control, before and after → `N-CAUSAL-DID`
- Chosen based on observed characteristics → `N-CAUSAL-PSM`
- By a score cut-off → `N-CAUSAL-RDD`
- Who should I target (heterogeneous effects)? → `N-CAUSAL-UPLIFT`

???+ note "Causal diagram (DAG) — adjust for confounders, not colliders or mediators — `N-CAUSAL-DAG`"
    **Use when:** Any observational causal question.  
    **Check:** All common causes listed; Colliders identified  
    **If a check fails:** Unmeasured confounders → sensitivity analysis or design an experiment  
    **Alternatives:** Run an experiment  
    **Pitfalls:** Adjusting for everything available  
    **Action:** Decide what can and cannot be claimed.  
    **Lessons:** L4.4

???+ note "Difference-in-differences (check parallel pre-trends) — `N-CAUSAL-DID`"
    **Use when:** Policy/promo applied to some stores or regions from a date.  
    **Check:** Parallel pre-trends; No spill-over  
    **If a check fails:** Synthetic control  
    **Alternatives:** Event-study plot  
    **Pitfalls:** Ignoring different pre-trends  
    **Action:** Estimate incremental impact.  
    **Lessons:** L9.1

???+ note "Propensity score matching / weighting (+ overlap and sensitivity checks) — `N-CAUSAL-PSM`"
    **Use when:** Loyalty membership, credit-limit increases chosen by the business.  
    **Check:** Overlap; Balance after matching  
    **If a check fails:** Poor overlap → restrict population  
    **Alternatives:** Doubly robust estimation  
    **Pitfalls:** Hidden confounding  
    **Action:** Present as best estimate with caveats.  
    **Lessons:** L9.1

???+ note "Regression discontinuity (awareness) — `N-CAUSAL-RDD`"
    **Use when:** Treatment assigned at a cut-off (score ≥ 650).  
    **Check:** No manipulation at the cut-off  
    **If a check fails:** —  
    **Alternatives:** —  
    **Pitfalls:** Extrapolating far from the cut-off  
    **Action:** Local effect at the threshold.  
    **Lessons:** L9.1

???+ note "Uplift modelling (T-learner, Qini curve) — `N-CAUSAL-UPLIFT`"
    **Use when:** Target customers who change behaviour because of the treatment.  
    **Check:** Randomised training data  
    **If a check fails:** —  
    **Alternatives:** Segment-level experiment results  
    **Pitfalls:** Targeting high-propensity "sure things"  
    **Action:** Spend on persuadables.  
    **Lessons:** L9.1

## Which evaluation metric and threshold?

**What will the model output be used for?** <small>`N-METRIC-Q1`</small>
- Ranking customers/accounts → `N-METRIC-CLASS`
- Rare-event detection → `N-METRIC-RARE`
- Probabilities used as numbers (pricing, provisions) → `N-METRIC-CALIB`
- Choosing a cut-off → `N-METRIC-COST`
- Forecast / regression accuracy → `N-METRIC-REG`

???+ note "ROC-AUC / Gini, KS, lift and gain by decile — `N-METRIC-CLASS`"
    **Use when:** Credit or response ranking.  
    **Check:** Out-of-time sample; Segment stability  
    **If a check fails:** —  
    **Alternatives:** PR-AUC for rare events  
    **Pitfalls:** AUC insensitive to calibration  
    **Action:** Rule of thumb: application scorecards often AUC 0.70–0.85 (varies by product and regulator).  
    **Lessons:** L6.6

???+ note "PR-AUC, precision@k, recall at investigator capacity — `N-METRIC-RARE`"
    **Use when:** Fraud, AML alerts.  
    **Check:** Base rate  
    **If a check fails:** —  
    **Alternatives:** Cost curves  
    **Pitfalls:** Accuracy  
    **Action:** Size the alert queue to capacity.  
    **Lessons:** L6.5, L6.6

???+ note "Calibration curve, Brier score; recalibrate (Platt/isotonic) — `N-METRIC-CALIB`"
    **Use when:** PD for provisioning, risk-based pricing.  
    **Check:** Predicted vs observed by decile  
    **If a check fails:** Recalibrate  
    **Alternatives:** —  
    **Pitfalls:** Good AUC but wrong levels  
    **Action:** Recalibrate before using probabilities in money calculations.  
    **Lessons:** L6.6

???+ note "Expected-cost threshold (cost FN × FN + cost FP × FP) or capacity-based cut-off — `N-METRIC-COST`"
    **Use when:** Any yes/no decision from a score.  
    **Check:** Agreed costs with the business  
    **If a check fails:** Unknown costs → show the trade-off curve  
    **Alternatives:** —  
    **Pitfalls:** Defaulting to 0.5  
    **Action:** Pick the threshold with the lowest expected cost.  
    **Lessons:** L6.6

???+ note "MAE, RMSE, WAPE, MASE, bias — `N-METRIC-REG`"
    **Use when:** Forecasts and regressions.  
    **Check:** Level at which decisions are made  
    **If a check fails:** Near-zero actuals → avoid MAPE; use WAPE/MASE  
    **Alternatives:** Quantile loss  
    **Pitfalls:** MAPE on intermittent demand  
    **Action:** Report accuracy and bias at the decision level.  
    **Lessons:** L7.3

## Which drift or monitoring check?

**What changed, or what are you worried about?** <small>`N-MON-Q1`</small>
- Score or input distributions → `N-MON-PSI`
- Model performance (AUC, calibration) → `N-MON-CONCEPT`
- Fairness across groups → `N-MON-FAIR`
- Only approved/booked cases have outcomes → `N-MON-REJECT`

???+ note "PSI (score) and CSI (each feature) — `N-MON-PSI`"
    **Use when:** Monthly model monitoring; data pipeline changes.  
    **Check:** Rule of thumb: < 0.10 stable · 0.10–0.25 investigate · > 0.25 significant shift  
    **If a check fails:** Find the driver: mix change (channel; product) or data error  
    **Alternatives:** KS test on distributions  
    **Pitfalls:** Treating PSI as a performance measure  
    **Action:** Monitor → investigate → recalibrate → rebuild.  
    **Lessons:** L9.6

???+ note "Performance decay by vintage (AUC/KS, calibration) — concept drift — `N-MON-CONCEPT`"
    **Use when:** Relationship between inputs and outcome changes.  
    **Check:** Mature outcome window; Segment breakdown  
    **If a check fails:** Recalibrate or rebuild  
    **Alternatives:** Challenger model  
    **Pitfalls:** Stable PSI ≠ stable performance  
    **Action:** Escalate under model-risk policy.  
    **Lessons:** L9.6

???+ note "Fairness metrics (approval rate ratio / 80% rule, equal opportunity) incl. proxy checks — `N-MON-FAIR`"
    **Use when:** Credit, pricing, hiring decisions.  
    **Check:** Outcomes by protected group; Proxies (region; postcode)  
    **If a check fails:** Remove/adjust proxy features; policy review  
    **Alternatives:** —  
    **Pitfalls:** Assuming removing the protected attribute removes bias  
    **Action:** Document and remediate.  
    **Lessons:** L9.5

???+ note "Reject-inference awareness — `N-MON-REJECT`"
    **Use when:** Models trained only on approved applicants.  
    **Check:** Score distribution of declined vs booked  
    **If a check fails:** Parcelling / augmentation; or a small randomised approval test  
    **Alternatives:** —  
    **Pitfalls:** Under-estimating risk at low scores  
    **Action:** Be cautious when lowering cut-offs.  
    **Lessons:** L8.7, L9.6

## Which optimisation approach?

**Which decision?** <small>`N-OPT-Q1`</small>
- Promotion depth / frequency → `N-OPT-PROMO`
- Stock level / safety stock → `N-OPT-INVENTORY`
- Price → `N-REG-LOGLOG`
- Decision under uncertainty → `N-OPT-MC`

???+ note "Promo uplift net of cannibalisation, halo and pull-forward → promo ROI — `N-OPT-PROMO`"
    **Use when:** Evaluating and planning promotions.  
    **Check:** Baseline estimate; Cannibalised SKUs; Post-promo dip  
    **If a check fails:** —  
    **Alternatives:** Store-level promo test  
    **Pitfalls:** Counting gross uplift as incremental  
    **Action:** Keep promotions with positive incremental margin.  
    **Lessons:** L8.4

???+ note "Safety stock = z(service level) × σ(demand over lead time); newsvendor for perishables; ABC/XYZ — `N-OPT-INVENTORY`"
    **Use when:** Replenishment policy.  
    **Check:** Forecast error distribution; Lead-time variability  
    **If a check fails:** —  
    **Alternatives:** Simulation  
    **Pitfalls:** Using sales (censored) instead of demand  
    **Action:** Set service levels by ABC/XYZ class.  
    **Lessons:** L7.6

???+ note "Monte Carlo simulation of the decision's P&L — `N-OPT-MC`"
    **Use when:** Uncertain inputs (demand, elasticity, default rates).  
    **Check:** Input distributions justified; Correlations between inputs  
    **If a check fails:** —  
    **Alternatives:** Scenario analysis  
    **Pitfalls:** Point estimates hiding risk  
    **Action:** Choose the option with acceptable downside.  
    **Lessons:** L2.5
