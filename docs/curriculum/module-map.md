# 04. Ten-Day Module Map

69 lessons: Day 0 (5) + Days 1–10 (64). Average lesson ≈ 60–75 min including lab; Day-end gate ≈ 45 min.

## Daily rhythm (Days 1–9, ~8 hours)

| Time | Foundation track | Leader track |
| --- | --- | --- |
| 09:00–09:30 | Joint: Navigator walkthrough of the day ("where we are on the map") | Joint |
| 09:30–12:30 | Concept + lab blocks (3 lessons) | Fast refresh (15 min/lesson) then output-anatomy and decision drills |
| 12:30–13:15 | Lunch | Lunch |
| 13:15–16:15 | Concept + lab blocks (3–4 lessons) | Scenario matrices, coaching cards, review of Foundation outputs |
| 16:15–16:45 | Joint junior-leader review huddle: leaders review juniors' analyses using the approval checklist | Joint |
| 16:45–17:30 | Mastery gate (quiz + data task) | Mastery gate (scenario quiz + "read and decide" task) |
| 19:00–20:30 (Days 2, 3, 5, 6, 8, 9) | Evening lab: extra exercise set + Anomaly Hunt | Optional: decision cases |

## Lessons

**Part** A = Descriptive, B = Analytical. Retail = NorthStar Markets, Finance = Meridian Bank.

### Day 0: Build the data and the playbook (half day, can be pre-work)

| Lesson | Title | Part | Retail topic | Finance topic | Technique | Vibe-coding skill | Leader focus |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L0.1 | Your workbench: VS Code, Claude Code, Codespaces, Git | — | — | — | Environment | Open repo, ask Claude Code to explain the project | Setting team standards |
| L0.2 | The vibe-coding playbook for analytics | — | — | — | Intent → assumptions → run → verify loop; AI error catalogue | Weak/better/expert prompts; "state assumptions first" | Reviewing AI-generated work |
| L0.3 | Build and validate both datasets | A | Generate 25K lines, profile | Generate 25K accounts + panel | Row counts, schema checks | Run the generator; ask for a validation report | What "validated data" means |
| L0.4 | The toolkit: recipes, configs, reuse, Git | — | Run `rcp_profile` | Re-run on finance via config only | Reproducibility | Read a recipe, change config, regression check, commit | Approval checklist for reuse |
| L0.5 | Data safety and anonymisation | — | Hash customer ids | Mask income, bucket age | Pseudonymisation, k-anonymity intuition | Ask Claude Code to anonymise before analysis | Policy and accountability |

Then: pre-bootcamp diagnostic (40 questions, recommends track, flags weak topics).

### Day 1: Data quality and descriptive statistics (Part A)

| Lesson | Title | Part | Retail topic | Finance topic | Technique | Vibe-coding skill | Leader focus |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L1.1 | Data types, grain, tidy data, EDA workflow | A | Line vs basket vs customer grain | Account vs month grain | EDA plan | Ask for a grain and key check | Wrong-grain analyses |
| L1.2 | Data quality checks | A | R01, R02, R03, R19 | F01 | Validity rules, dedupe, reconciliation | "List every rule you applied and rows affected" | Silent row loss |
| L1.3 | Missing data: MCAR, MAR, MNAR | A | R04, R05, R06 | F02 | Missingness tests, imputation, flags | Ask for missingness-by-segment table | When imputation misleads |
| L1.4 | Centre, spread, shape | A | Basket value, R07 | Balances, F14 | Mean/median, SD/IQR/MAD, skew, kurtosis, CV, Lorenz | Request robust summaries side by side | Which number to put on a slide |
| L1.5 | Visualising distributions | A | Spend histogram (log) | Score ECDF by vintage | Histogram, box, violin, ECDF, Q-Q | Ask for the right chart and why | Spotting misleading charts |
| L1.6 | Outliers and transformations | A | Bulk buyers, 100× prices | Income outliers | IQR, robust z, log, Box-Cox, encoding | "Show me what changes if we cap" | Error vs genuine extreme |
| L1.7 | Relationships | A | Price vs quantity; promo × loyalty crosstab | Score vs utilisation | Pearson, Spearman, Kendall, Cramér's V | Ask for scatter before correlation | Correlation ≠ causation |

Gate D1: 12-question quiz + data-quality report on a fresh 2K-row slice.

### Day 2: Probability, distributions, sampling, simulation (Part A)

| Lesson | Title | Part | Retail topic | Finance topic | Technique | Vibe-coding skill | Leader focus |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L2.1 | Probability, conditional probability, Bayes, base rates | A | P(return \| electronics) | Fraud alert base-rate trap, F03 | Bayes' rule | Ask Claude Code for a natural-frequency table | Base-rate fallacy in alerts |
| L2.2 | Discrete distributions | A | Weekly SKU units (Poisson vs NB) | Defaults per vintage (Binomial); audit sampling (Hypergeometric) | Fit, dispersion check | Ask for variance-to-mean ratio | Over-dispersion consequences |
| L2.3 | Continuous distributions and the family map | A | Basket spend (lognormal) | Claim severity (Gamma), time to churn (Weibull) | Q-Q, AIC fit comparison | Ask to compare 3 candidate fits | Why tails matter for risk |
| L2.4 | Sampling, bias, Simpson's paradox, confounding | A | R14, R16 | Booked-only bias (F18 preview) | Stratification | Ask "what would reverse this conclusion?" | Challenging aggregate results |
| L2.5 | LLN, CLT, Monte Carlo | A | Simulate promo P&L | Simulate portfolio losses | Simulation | Ask for a seeded simulation with convergence plot | Uncertainty ranges vs point forecasts |
| L2.6 | Benford's law and digit tests | A | R18 | F09 | First-digit, last-digit tests | Ask for Benford MAD by store/branch | Fraud red flags vs false alarms |
| L2.7 | Linear algebra essentials | A | Product-feature matrix | Correlated risk features | Vectors, matrices, eigen, SVD, least squares | Ask for a visual explanation | Why collinearity breaks models |

### Day 3: Estimation and hypothesis testing (Part B)

| Lesson | Title | Part | Retail topic | Finance topic | Technique | Vibe-coding skill | Leader focus |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L3.1 | Estimation and confidence intervals | B | CI for mean basket | CI for default rate | Point/interval estimates | Ask for CI and its plain-English meaning | Misreadings of CIs |
| L3.2 | Bootstrap and permutation | B | Bootstrap median spend | Permutation test of branch default rates | Resampling | Ask for bootstrap distribution plot | When resampling beats formulas |
| L3.3 | Hypothesis testing logic, p-values, errors | B | "Is weekend basket bigger?" | "Did default change?" | NHST, α, β | Ask Claude Code to state H0/H1 before testing | p-value abuse |
| **L3.4** | **Two-group comparison: promo lift and default-rate difference** (Step 2 reference lesson) | B | R09 Hair Care test, R07 tails | Default rate branch A vs B; F03 | Welch t, Mann-Whitney, two-proportion z, Fisher, normality tests, effect size | Prompt cards: choose test, check assumptions, effect + CI | Statistical vs practical significance; rollout decision |
| L3.5 | More than two groups and categorical tests | B | Basket by region | Default by employment type | ANOVA, Welch ANOVA, Kruskal, chi-square, Fisher, McNemar, post-hoc | Ask for assumption checks and post-hoc | Which differences matter |
| L3.6 | Effect sizes, power, sample size | B | Stores needed for next test | Accounts needed for challenger | Cohen's d, OR, RR, power, MDE | Ask for power curve | Under-powered "no effect" claims |
| L3.7 | Multiple testing and p-hacking | B | 40 segment tests | 30 feature tests | Bonferroni, Holm, BH | Ask for adjusted p-values table | Spotting forking paths (S43) |

### Day 4: Experiments, Bayesian thinking, causal basics (Part B)

| Lesson | Title | Part | Retail topic | Finance topic | Technique | Vibe-coding skill | Leader focus |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L4.1 | A/B test design and hygiene | B | R24 e-coupon SRM | Card-offer test design | Randomisation, SRM, guardrails, novelty | Ask for SRM check before results | Stop/ship decisions |
| L4.2 | CUPED and sequential testing | B | Pre-period spend as covariate | Early stopping risk | CUPED, alpha spending | Ask for variance reduction achieved | Peeking culture |
| L4.3 | Bayesian thinking and Bayesian A/B | B | P(coupon B > A) | Prior for new-segment default | Beta-Binomial, credible intervals, expected loss | Ask for posterior plot + decision rule | Communicating probability of being better |
| L4.4 | Causal basics: DAGs, confounders, colliders | B | R15 display/promo | Collider bias in approved-only data | DAGs, backdoor | Ask Claude Code to draw the DAG | "What else could explain this?" |
| L4.5 | Store-level and champion/challenger tests end to end | B | R09 store test | F16 collections challenger | Cluster-level analysis, guardrails | Full A/B recipe run | Writing the decision memo |

### Day 5: Regression and GLMs + checkpoint (Part B)

| Lesson | Title | Part | Retail topic | Finance topic | Technique | Vibe-coding skill | Leader focus |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L5.1 | Linear regression and coefficient interpretation | B | Sales drivers (price, promo, temp) | Balance drivers | OLS, R², dummies | Ask for business reading of each coefficient | Over-reading coefficients |
| L5.2 | Regression diagnostics | B | Heteroscedastic sales | F06 income vs limit | Residuals, BP test, VIF, Cook's | Ask for the diagnostic panel | Red flags in a junior's model |
| L5.3 | Logistic regression | B | Return probability | Default probability | Logit, odds ratios | Ask for odds ratios with CIs | Explaining odds to executives |
| L5.4 | Regularisation and model selection | B | 60-feature sales model | Default with many features | Ridge, Lasso, Elastic Net, AIC/BIC, CV | Ask for coefficient path plot | Parsimony vs accuracy |
| L5.5 | GLMs: Poisson, NB, Gamma, Tweedie, quantile | B | Units sold (NB) | Claims count/severity preview | GLM families, offset, dispersion | Ask to compare families by deviance/AIC | Choosing the family |
| L5.6 | Non-linearity, interactions, mixed models | B | Store random effects | F04, F05 | Splines, interactions, random intercepts | Ask for partial-effect plots | Hidden interactions |
| L5.7 | **Part A/B checkpoint capstone** | A+B | "Why did Q4 margin fall?" | "Why are approvals down?" | Integrated | End-to-end vibe-coded analysis, saved as recipe | Leader reviews junior output live |

### Day 6: Core ML and evaluation (Part B)

| Lesson | Title | Part | Retail topic | Finance topic | Technique | Vibe-coding skill | Leader focus |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L6.1 | Feature engineering and selection | B | Customer-level features from lines | Behavioural features from panel | Aggregates, lags, ratios, selection | Ask for a feature-leakage audit | Feature provenance |
| L6.2 | Trees, random forests, gradient boosting | B | Return prediction | Default prediction | Tree ensembles | Ask for baseline vs GBM comparison | Complexity vs explainability |
| L6.3 | SVM, KNN, Naive Bayes, ensembling | B | Category affinity | Complaint classification | Alternative learners, stacking | Ask for a model bake-off table | Diminishing returns |
| L6.4 | Validation, tuning, bias-variance, leakage | B | Time-based split | F10 leakage trap; out-of-time | CV variants, tuning | "Explain why this score is suspicious" | AUC too good to be true (S26) |
| L6.5 | Class imbalance | B | Returns abuse | Fraud 0.7% | Weights, SMOTE, threshold moving | Ask for PR curve not accuracy | S27 base-rate trap |
| L6.6 | Evaluation and thresholds | B | Promo response model lift | Scorecard AUC, KS, calibration | Confusion matrix, ROC/PR, KS, lift, calibration, cost threshold | Ask for cost-based threshold | Industry norms; S28 |
| L6.7 | Explainability | B | Drivers of return risk | SHAP for credit decisions | Permutation importance, SHAP, PDP | Ask for global + local explanations | Adverse-action reasons |

### Day 7: Time series and forecasting (Part B)

| Lesson | Title | Part | Retail topic | Finance topic | Technique | Vibe-coding skill | Leader focus |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L7.1 | Decomposition, stationarity, ACF/PACF | B | R11 seasonality | Monthly delinquency series | STL, ADF/KPSS | Ask for decomposition plot | Reading seasonality |
| L7.2 | ETS, ARIMA/SARIMA, Prophet-style | B | Category weekly sales | Monthly balances | Models + baselines | Ask for model vs seasonal-naive | Over-engineered forecasts |
| L7.3 | Backtesting and forecast metrics | B | WAPE by level | Balance forecast bias | Rolling origin, WAPE, MASE, bias | Ask for backtest table | Forecast accuracy norms |
| L7.4 | Intermittent and hierarchical forecasting | B | R22 long tail; region→total | Branch→region | Croston/SBA, reconciliation | Ask for ADI/CV² classification | Where to forecast |
| L7.5 | Change-points and censored demand | B | R08, R12 | Delinquency regime shift | CUSUM, PELT, uncensoring | Ask for change-point dates with confidence | Explaining breaks |
| L7.6 | Inventory: safety stock, service level, ABC/XYZ | B | Safety stock for top SKUs | Cash-at-branch buffer | Service level, newsvendor, ABC/XYZ | Ask for service-level vs stock curve | Cost of service level |

### Day 8: Segmentation, anomaly & fraud, retail and finance specialisations (Part B)

| Lesson | Title | Part | Retail topic | Finance topic | Technique | Vibe-coding skill | Leader focus |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L8.1 | Clustering and PCA | B | R23 segments | Customer behaviour clusters | K-Means, hierarchical, DBSCAN, GMM, PCA | Ask for silhouette + cluster profiles | Are segments actionable? |
| L8.2 | RFM, CLV, cohorts | B | Loyalty RFM, CLV | Card cohort retention | RFM, CLV, cohorts | Ask for cohort heatmap | Investing by CLV |
| L8.3 | Market basket analysis | B | R21 | Cross-sell product holdings | Apriori, lift | Ask for top rules with support filter | Trivial vs useful rules |
| L8.4 | Pricing, promotions, MMM, optimisation | B | R10, R13, promo ROI, MMM | Rate elasticity for loans | Log-log, uplift, adstock, optimisation | Ask for elasticity with CI and optimal price | Promo ROI decisions |
| L8.5 | Anomaly detection | B | R17 returns abuse | Transaction anomalies | Robust z, Isolation Forest, LOF, residual | Ask for contamination sensitivity | Alert budgets |
| L8.6 | Fraud analytics: rings and structuring | B | Coupon abuse rings | F07, F08 | Graph components, bunching | Ask for network summary | Escalation thresholds |
| L8.7 | Credit risk: scorecards, PD/LGD/EAD, vintages, roll rates, churn | B | — | F02, F04, F18; churn model | WoE/IV, scorecard, vintage, roll rate | Ask for IV table and scorecard points | Credit norms (AUC, KS, IV) |

### Day 9: Advanced methods (Part B)

| Lesson | Title | Part | Retail topic | Finance topic | Technique | Vibe-coding skill | Leader focus |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L9.1 | Causal methods | B | R09 DiD, R20 loyalty | Credit-limit increase effect | DiD, propensity, uplift, RDD, synthetic control | Ask for parallel-trends plot | Causal claims you can defend |
| L9.2 | Survival analysis | B | Time to repeat purchase | F13 churn | KM, log-rank, Cox | Ask for KM curves + PH test | Retention actions |
| L9.3 | Deep learning essentials and modern AI | B | Demand with a small MLP vs GBM | Embeddings for complaint text | NN basics, optimisers, regularisation, Transformers, RAG | Ask Claude Code to compare MLP vs GBM honestly | When not to use DL; LLM governance |
| L9.4 | Insurance and market-risk basics | B | — | F17; VaR, ES, stress tests | Frequency-severity, loss ratio, VaR/ES | Ask for Monte Carlo VaR | Risk appetite conversations |
| L9.5 | Fairness, responsible AI, model risk | B | Personalised pricing fairness | F15 proxy | Fairness metrics, MRM, conformal | Ask for fairness table by group | Regulatory exposure |
| L9.6 | Monitoring and drift | B | R19 | F11, F12, F18 | PSI/CSI, concept drift, reject inference | Ask for a monitoring report | Monitor → recalibrate → rebuild |
| L9.7 | Data storytelling and executive readouts | B | Promo review deck | Default-rise readout | Pyramid principle | Ask Claude Code to draft, then you edit | Stakeholder challenge |

### Day 10: Transfer, capstone, assessment

| Lesson | Title | Part | Retail topic | Finance topic | Technique | Vibe-coding skill | Leader focus |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L10.1 | Transfer test (unseen quick-commerce dataset) | A+B | — | — | Toolkit via config | Map columns, schema check, adapt configs | Review a reused analysis |
| L10.2 | Final capstone business readout | A+B | "Did the Q4 promo plan work?" | "Why did default rise in the latest vintage?" | Integrated | Full workflow | Board-level challenge panel |
| L10.3 | Navigator consolidation | A+B | Scenario sprint | Scenario sprint | All trees | — | Coaching juniors through the map |
| L10.4 | Final exam + code-review exam | A+B | Held-out seed 7001 | Held-out seed 7002 | — | — | Critique a flawed junior analysis |

Completion record issued per learner.

## Rebalancing vs the suggested arc

1. Monte Carlo and Benford sit in Day 2 (they need distributions, not tests).
2. Insurance frequency-severity and VaR/ES move from Day 8 to Day 9 (L9.4) to relieve Day 8.
3. Inventory/safety stock sits in Day 7 next to forecasting, since it consumes forecast error.

All other placements follow your suggested arc.
