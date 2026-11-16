# 01. Concept Inventory (master list)

Every concept is placed in at least one lesson. Depth tags:

- **Foundation (F):** `D` deep (built step by step, worked examples, graded lab) · `W` working (use, read, interpret) · `A` awareness (what it is, when to call a specialist)
- **Leader (L):** `J` judgement (refresh, then output anatomy, scenarios, actions, norms, coaching card) · `R` refresh only (minutes) · `A` awareness

Lesson IDs refer to `04_MODULE_MAP.md`. Where a concept recurs, the first lesson teaches it and later ones apply it.

## Part A: Descriptive

### A1. Data foundations and EDA

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C001 | Data types: categorical, numeric, discrete, continuous | D | R | L1.1 |
| C002 | Measurement scales: nominal, ordinal, interval, ratio | D | R | L1.1 |
| C003 | Grain (unit of analysis) and keys | D | J | L1.1 |
| C004 | Tidy data (one row per observation, one column per variable) | D | R | L1.1 |
| C005 | Fact and dimension tables, joins, join explosion | W | J | L1.1 |
| C006 | EDA workflow (question → profile → visualise → hypothesise) | D | J | L1.1 |
| C007 | Data profiling (counts, uniques, ranges, nulls) | D | R | L1.2 |
| C008 | Data quality dimensions: completeness, validity, accuracy, consistency, timeliness, uniqueness | D | J | L1.2 |
| C009 | Duplicate detection (exact and fuzzy) | D | R | L1.2 |
| C010 | Impossible and implausible values; business rules | D | J | L1.2 |
| C011 | Unit and scale errors (100× price) | D | J | L1.2 |
| C012 | Reconciliation to control totals | W | J | L1.2 |
| C013 | Missing data mechanisms: MCAR | D | J | L1.3 |
| C014 | MAR | D | J | L1.3 |
| C015 | MNAR | D | J | L1.3 |
| C016 | Little's MCAR test and missingness-indicator comparison | W | R | L1.3 |
| C017 | Deletion: listwise, pairwise; silent row loss | D | J | L1.3 |
| C018 | Simple imputation (mean, median, mode, constant, flag) | D | R | L1.3 |
| C019 | Model-based imputation (KNN, regression, MICE) | W | J | L1.3 |

### A2. Summaries and visuals

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C020 | Mean (arithmetic, weighted) | D | R | L1.4 |
| C021 | Geometric and harmonic mean | W | R | L1.4 |
| C022 | Median | D | R | L1.4 |
| C023 | Mode | D | R | L1.4 |
| C024 | Trimmed and winsorised mean | W | R | L1.4 |
| C025 | Range | D | R | L1.4 |
| C026 | Variance (population vs sample, n−1) | D | R | L1.4 |
| C027 | Standard deviation | D | R | L1.4 |
| C028 | Percentiles, quantiles, deciles | D | R | L1.4 |
| C029 | Interquartile range (IQR) | D | R | L1.4 |
| C030 | Median absolute deviation (MAD) | W | R | L1.4 |
| C031 | Coefficient of variation | D | J | L1.4 |
| C032 | Skewness | D | R | L1.4 |
| C033 | Kurtosis and heavy tails | D | J | L1.4 |
| C034 | Concentration: Pareto/80-20, Lorenz curve, Gini of spend | W | J | L1.4 |
| C035 | Histogram and bin choice | D | R | L1.5 |
| C036 | Density plot (KDE) | W | R | L1.5 |
| C037 | Box plot | D | R | L1.5 |
| C038 | Violin plot | W | R | L1.5 |
| C039 | ECDF | D | R | L1.5 |
| C040 | Q-Q plot | D | J | L1.5 |
| C041 | Bar, line, scatter, heatmap; chart choice | D | R | L1.5 |
| C042 | Misleading charts (truncated axes, dual axes) | W | J | L1.5 |

### A3. Outliers and transformations

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C043 | Outlier vs anomaly vs error vs genuine extreme | D | J | L1.6 |
| C044 | IQR (Tukey) fences | D | R | L1.6 |
| C045 | Z-score rule | D | R | L1.6 |
| C046 | Robust (modified) z-score using MAD | D | R | L1.6 |
| C047 | Outlier treatment: keep, cap, transform, exclude, model separately | D | J | L1.6 |
| C048 | Log transform | D | R | L1.6 |
| C049 | Box-Cox and Yeo-Johnson | W | R | L1.6 |
| C050 | Standardisation and min-max scaling | D | R | L1.6 |
| C051 | Encoding: one-hot, ordinal, target encoding (and its leakage risk) | D | J | L1.6 |
| C052 | Binning and discretisation | D | R | L1.6 |

### A4. Relationships

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C053 | Covariance | D | R | L1.7 |
| C054 | Pearson correlation | D | J | L1.7 |
| C055 | Spearman rank correlation | D | R | L1.7 |
| C056 | Kendall's tau | W | R | L1.7 |
| C057 | Correlation matrix and heatmap | D | R | L1.7 |
| C058 | Non-linear relationships that correlation misses (Anscombe) | D | J | L1.7 |
| C059 | Contingency tables (crosstabs), row/column percentages | D | R | L1.7 |
| C060 | Cramér's V | W | R | L1.7 |
| C061 | Grouped summaries and pivoting | D | R | L1.7 |
| C062 | Correlation vs causation | D | J | L1.7 |

### A5. Sampling and bias

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C063 | Population, sample, parameter, statistic | D | R | L2.4 |
| C064 | Simple random sampling | D | R | L2.4 |
| C065 | Stratified sampling | D | R | L2.4 |
| C066 | Cluster and systematic sampling | W | R | L2.4 |
| C067 | Selection bias | D | J | L2.4 |
| C068 | Survivorship bias | D | J | L2.4 |
| C069 | Non-response and self-selection bias | W | J | L2.4 |
| C070 | Simpson's paradox | D | J | L2.4 |
| C071 | Confounding | D | J | L2.4 |
| C072 | Sampling weights and representativeness | W | R | L2.4 |

### A6. Probability

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C073 | Sample space, events, axioms | D | R | L2.1 |
| C074 | Addition and multiplication rules | D | R | L2.1 |
| C075 | Independence | D | R | L2.1 |
| C076 | Conditional probability | D | J | L2.1 |
| C077 | Law of total probability | D | R | L2.1 |
| C078 | Bayes' rule | D | J | L2.1 |
| C079 | Base rates and the base-rate fallacy | D | J | L2.1 |
| C080 | Random variables, expected value, variance of sums | D | R | L2.1 |
| C081 | Odds and log-odds | D | J | L2.1 |

### A7. Distributions (each mapped to a retail or finance use)

| ID | Concept | Use in course | F | L | Lesson |
| --- | --- | --- | --- | --- | --- |
| C082 | Bernoulli | Did this customer default? | D | R | L2.2 |
| C083 | Binomial | Number of defaults in a vintage | D | R | L2.2 |
| C084 | Geometric | Visits until first purchase | D | R | L2.2 |
| C085 | Negative binomial | Over-dispersed weekly SKU unit sales | D | J | L2.2 |
| C086 | Poisson | Basket counts per hour; claims per policy | D | J | L2.2 |
| C087 | Hypergeometric | Audit sampling without replacement | W | R | L2.2 |
| C088 | Discrete uniform | Random store allocation | W | R | L2.2 |
| C089 | Beta-binomial | Conversion rates that vary by store | W | J | L2.2 |
| C090 | Normal | Measurement error, averages | D | R | L2.3 |
| C091 | Standard normal and z-scores | Standardised scores | D | R | L2.3 |
| C092 | Lognormal | Basket spend, income | D | J | L2.3 |
| C093 | Exponential | Time between transactions | D | R | L2.3 |
| C094 | Gamma | Claim severity | D | R | L2.3 |
| C095 | Weibull | Time to churn or default | W | R | L2.3 |
| C096 | Beta | Uncertainty about a conversion rate | D | J | L2.3 |
| C097 | Continuous uniform | Simulation inputs | D | R | L2.3 |
| C098 | Cauchy | Why averages can fail (no mean) | W | A | L2.3 |
| C099 | Laplace | Sharp-peaked price changes; robust loss | W | A | L2.3 |
| C100 | Chi-square | Sampling distribution of variance; tests | D | R | L2.3 |
| C101 | Student's t | Small-sample means | D | R | L2.3 |
| C102 | F | Ratio of variances; ANOVA | D | R | L2.3 |
| C103 | Distribution family map (limits and relationships) | Choosing a distribution | D | J | L2.3 |
| C104 | Distribution fitting and goodness of fit (KS, AD, AIC) | Fitting spend and claims | W | R | L2.3 |

### A8. Simulation, laws and special patterns

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C105 | Law of large numbers | D | R | L2.5 |
| C106 | Central limit theorem (by simulation) | D | J | L2.5 |
| C107 | Sampling distribution and standard error | D | J | L2.5 |
| C108 | Monte Carlo simulation | D | J | L2.5 |
| C109 | Benford's law and first-digit tests | D | J | L2.6 |
| C110 | Digit preference and rounding detection | W | J | L2.6 |

### A9. Linear algebra essentials (intuitive)

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C111 | Vectors, length, dot product, angle (cosine similarity) | W | R | L2.7 |
| C112 | Matrices, matrix multiplication, transpose | W | R | L2.7 |
| C113 | Identity, inverse, determinant, singular matrices | W | R | L2.7 |
| C114 | Rank and linear dependence (link to multicollinearity) | W | J | L2.7 |
| C115 | Eigenvalues and eigenvectors | W | R | L2.7 |
| C116 | Singular value decomposition | W | A | L2.7 |
| C117 | Least squares as projection | W | R | L2.7 |

## Part B: Analytical

### B1. Estimation and inference

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C118 | Point estimation, bias, consistency, efficiency | D | R | L3.1 |
| C119 | Maximum likelihood (intuition) | W | R | L3.1 |
| C120 | Confidence interval: meaning and misreadings | D | J | L3.1 |
| C121 | CI for a mean, proportion, difference | D | J | L3.1 |
| C122 | Bootstrap (percentile, BCa) | D | J | L3.2 |
| C123 | Permutation test | D | J | L3.2 |
| C124 | Null and alternative hypotheses; one vs two-sided | D | J | L3.3 |
| C125 | Test statistic and p-value | D | J | L3.3 |
| C126 | Limits of p-values (ASA statement); significance ≠ importance | D | J | L3.3 |
| C127 | Type I error (α) and Type II error (β) | D | J | L3.3 |
| C128 | One-sample and two-sample z-tests (incl. proportions) | D | J | L3.4 |
| C129 | One-sample and Welch two-sample t-test | D | J | L3.4 |
| C130 | Paired t-test | D | J | L3.4 |
| C131 | Mann-Whitney U / Wilcoxon rank-sum | D | J | L3.4 |
| C132 | Wilcoxon signed-rank | W | R | L3.4 |
| C133 | Normality tests (Shapiro-Wilk, Anderson-Darling) and their limits at large n | D | J | L3.4 |
| C134 | Levene and Brown-Forsythe tests | D | R | L3.5 |
| C135 | One-way ANOVA | D | J | L3.5 |
| C136 | Post-hoc tests (Tukey HSD, Games-Howell) | W | R | L3.5 |
| C137 | Kruskal-Wallis and Dunn's test | D | R | L3.5 |
| C138 | Chi-square test of independence and goodness of fit | D | J | L3.5 |
| C139 | Fisher's exact test | D | R | L3.5 |
| C140 | McNemar's test | W | R | L3.5 |
| C141 | Effect size: Cohen's d, Hedges' g | D | J | L3.6 |
| C142 | Effect size: odds ratio, relative risk, risk difference, NNT | D | J | L3.6 |
| C143 | Effect size: eta-squared, Cramér's V | W | R | L3.6 |
| C144 | Statistical power | D | J | L3.6 |
| C145 | Minimum detectable effect and sample size | D | J | L3.6 |
| C146 | Multiple comparisons and family-wise error | D | J | L3.7 |
| C147 | Bonferroni and Holm | D | R | L3.7 |
| C148 | Benjamini-Hochberg (FDR) | D | J | L3.7 |
| C149 | p-hacking, HARKing, garden of forking paths | D | J | L3.7 |

### B2. Experiments and Bayesian thinking

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C150 | Randomisation and unit of randomisation | D | J | L4.1 |
| C151 | Primary, secondary and guardrail metrics | D | J | L4.1 |
| C152 | Sample ratio mismatch (SRM) check | D | J | L4.1 |
| C153 | Novelty and primacy effects; test duration | D | J | L4.1 |
| C154 | Interference and cluster-randomised (store-level) tests | W | J | L4.1 |
| C155 | Peeking and sequential testing (alpha spending, mSPRT awareness) | W | J | L4.2 |
| C156 | CUPED variance reduction | W | J | L4.2 |
| C157 | Champion/challenger tests | D | J | L4.5 |
| C158 | Prior, likelihood, posterior | D | J | L4.3 |
| C159 | Beta-binomial conjugate update | D | J | L4.3 |
| C160 | Credible interval vs confidence interval | D | J | L4.3 |
| C161 | Bayesian A/B: P(B>A), expected loss | D | J | L4.3 |
| C162 | Probabilistic programming (PyMC) intro | A | A | L4.3 |
| C163 | DAG intuition | D | J | L4.4 |
| C164 | Confounders, mediators, colliders; backdoor path | D | J | L4.4 |

### B3. Regression and GLMs

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C165 | Simple linear regression; OLS | D | J | L5.1 |
| C166 | Multiple regression; holding other things constant | D | J | L5.1 |
| C167 | Coefficient interpretation for business (units, log-log as elasticity) | D | J | L5.1 |
| C168 | R², adjusted R², RMSE; F-test | D | J | L5.1 |
| C169 | Dummy variables and reference categories | D | R | L5.1 |
| C170 | Residual analysis; linearity and normality of errors | D | J | L5.2 |
| C171 | Heteroscedasticity (Breusch-Pagan) and robust standard errors | D | J | L5.2 |
| C172 | Multicollinearity and VIF | D | J | L5.2 |
| C173 | Influence: leverage, Cook's distance | D | J | L5.2 |
| C174 | Autocorrelated errors (Durbin-Watson) | W | R | L5.2 |
| C175 | Logistic regression; odds ratios | D | J | L5.3 |
| C176 | Goodness of fit for logistic (deviance, Hosmer-Lemeshow awareness) | W | R | L5.3 |
| C177 | Ridge (L2) | D | J | L5.4 |
| C178 | Lasso (L1) and Elastic Net | D | J | L5.4 |
| C179 | Model selection: AIC, BIC, cross-validated error | D | J | L5.4 |
| C180 | GLM framework: link function, family, deviance | D | J | L5.5 |
| C181 | Poisson regression, exposure offset | D | J | L5.5 |
| C182 | Over-dispersion; negative binomial regression | D | J | L5.5 |
| C183 | Gamma regression | W | R | L5.5 |
| C184 | Tweedie regression | W | J | L5.5 |
| C185 | Quantile regression | W | J | L5.5 |
| C186 | Polynomial terms and splines | D | R | L5.6 |
| C187 | Interaction terms | D | J | L5.6 |
| C188 | Mixed/hierarchical models intro (random intercepts by store) | W | J | L5.6 |

### B4. Machine learning

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C189 | Feature engineering (ratios, lags, aggregates, dates) | D | J | L6.1 |
| C190 | Feature selection (filter, wrapper, embedded) | D | R | L6.1 |
| C191 | Decision tree | D | J | L6.2 |
| C192 | Random forest | D | J | L6.2 |
| C193 | Gradient boosting (XGBoost/LightGBM) | D | J | L6.2 |
| C194 | SVM | W | R | L6.3 |
| C195 | KNN | W | R | L6.3 |
| C196 | Naive Bayes | W | R | L6.3 |
| C197 | Ensembling, bagging, stacking | W | R | L6.3 |
| C198 | Train/validation/test split; out-of-time validation | D | J | L6.4 |
| C199 | Cross-validation (k-fold, stratified, grouped, time-series) | D | J | L6.4 |
| C200 | Hyperparameter tuning (grid, random, Bayesian) | W | R | L6.4 |
| C201 | Overfitting, underfitting, bias-variance trade-off | D | J | L6.4 |
| C202 | Data leakage (target, temporal, preprocessing) | D | J | L6.4 |
| C203 | Pipelines | W | R | L6.4 |
| C204 | Class imbalance: class weights, resampling (SMOTE), threshold moving | D | J | L6.5 |

### B5. Evaluation

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C205 | Confusion matrix; precision, recall, specificity, F1 | D | J | L6.6 |
| C206 | ROC curve and AUC; Gini = 2·AUC − 1 | D | J | L6.6 |
| C207 | PR curve and PR-AUC (rare events) | D | J | L6.6 |
| C208 | KS statistic | D | J | L6.6 |
| C209 | Lift and gain charts; deciles | D | J | L6.6 |
| C210 | Calibration (reliability curve, Brier score) | D | J | L6.6 |
| C211 | Cost-based threshold selection; expected value | D | J | L6.6 |
| C212 | Regression/forecast metrics: MAE, RMSE, MAPE, sMAPE, WAPE, MASE, bias | D | J | L7.3 |

### B6. Explainability, responsible AI and monitoring

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C213 | Feature importance (impurity vs permutation) | D | J | L6.7 |
| C214 | SHAP values (global and local) | W | J | L6.7 |
| C215 | Partial dependence and ICE plots | W | R | L6.7 |
| C216 | Fairness metrics (demographic parity, equal opportunity, disparate impact 80% rule) and proxy variables | W | J | L9.5 |
| C217 | Model risk management (SR 11-7 style: validation, documentation, challenge) | A | J | L9.5 |
| C218 | Conformal prediction intervals | W | R | L9.5 |
| C219 | PSI and CSI | D | J | L9.6 |
| C220 | Data drift vs concept drift; performance monitoring | D | J | L9.6 |
| C221 | Reject inference (awareness) | A | J | L9.6 |

### B7. Time series and forecasting

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C222 | Trend, seasonality, cycle; additive vs multiplicative decomposition (STL) | D | J | L7.1 |
| C223 | Stationarity, differencing, ADF/KPSS | D | R | L7.1 |
| C224 | ACF and PACF | D | R | L7.1 |
| C225 | Naive and seasonal-naive baselines | D | J | L7.2 |
| C226 | Exponential smoothing (ETS, Holt-Winters) | D | J | L7.2 |
| C227 | ARIMA, SARIMA, ARIMAX with regressors | D | J | L7.2 |
| C228 | Prophet-style models (trend + seasonality + holidays) | W | R | L7.2 |
| C229 | Backtesting (rolling origin), horizon, forecast bias | D | J | L7.3 |
| C230 | Intermittent demand (Croston, SBA, ADI/CV²) | W | J | L7.4 |
| C231 | Hierarchical forecasting and reconciliation | W | J | L7.4 |
| C232 | Change-point detection (CUSUM, PELT) | W | J | L7.5 |
| C233 | Demand censoring by stockouts | D | J | L7.5 |

### B8. Retail and FMCG analytics

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C234 | Safety stock and service level (cycle vs fill rate) | D | J | L7.6 |
| C235 | ABC/XYZ classification | D | J | L7.6 |
| C236 | Clustering: K-Means, elbow and silhouette | D | J | L8.1 |
| C237 | Hierarchical clustering and dendrograms | W | R | L8.1 |
| C238 | DBSCAN | W | R | L8.1 |
| C239 | Gaussian mixture models | W | R | L8.1 |
| C240 | PCA, explained variance, loadings | D | J | L8.1 |
| C241 | t-SNE/UMAP (awareness; not for clustering decisions) | A | A | L8.1 |
| C242 | RFM segmentation | D | J | L8.2 |
| C243 | Customer lifetime value (historic, cohort, BG/NBD awareness) | W | J | L8.2 |
| C244 | Cohort retention analysis | D | J | L8.2 |
| C245 | Market basket: support, confidence, lift; Apriori | D | J | L8.3 |
| C246 | Price elasticity (log-log, own and cross) | D | J | L8.4 |
| C247 | Promotion uplift, baseline, cannibalisation, halo, pull-forward | D | J | L8.4 |
| C248 | Marketing mix modelling: adstock and saturation | W | J | L8.4 |
| C249 | Price and promo optimisation | W | J | L8.4 |
| C250 | Assortment and delisting analysis (incrementality, transfer demand) | W | J | L8.4 |
| C251 | Inventory optimisation (newsvendor, reorder point) | W | J | L7.6 |

### B9. Anomaly, fraud, credit, insurance and risk

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C252 | Statistical anomaly detection (control charts, z/MAD, residual-based) | D | J | L8.5 |
| C253 | Isolation Forest | D | J | L8.5 |
| C254 | Local Outlier Factor | W | R | L8.5 |
| C255 | Contamination rate and alert budgets | D | J | L8.5 |
| C256 | Network/link analysis for fraud rings (shared devices, addresses) | W | J | L8.6 |
| C257 | Structuring detection (threshold bunching) | W | J | L8.6 |
| C258 | Weight of evidence (WoE) and information value (IV) | D | J | L8.7 |
| C259 | Credit scorecard: coarse classing, points to double odds | D | J | L8.7 |
| C260 | PD, LGD, EAD and expected loss = PD × LGD × EAD | D | J | L8.7 |
| C261 | Vintage analysis | D | J | L8.7 |
| C262 | Roll-rate / transition matrices | D | J | L8.7 |
| C263 | Churn modelling | D | J | L8.7 |
| C264 | Frequency-severity modelling, pure premium | W | J | L9.4 |
| C265 | Loss ratio, combined ratio | W | J | L9.4 |
| C266 | Value at Risk and expected shortfall | W | J | L9.4 |
| C267 | Stress testing and scenario analysis | W | J | L9.4 |

### B10. Causal inference

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C268 | Potential outcomes; ATE, ATT | W | J | L9.1 |
| C269 | Difference-in-differences; parallel trends | D | J | L9.1 |
| C270 | Propensity score matching and weighting; overlap | W | J | L9.1 |
| C271 | Uplift modelling (T-learner, Qini) | W | J | L9.1 |
| C272 | Regression discontinuity (awareness) | A | J | L9.1 |
| C273 | Synthetic control (awareness) | A | J | L9.1 |
| C274 | Survival analysis: censoring, Kaplan-Meier, log-rank | D | J | L9.2 |
| C275 | Cox proportional hazards; hazard ratio; PH assumption | W | J | L9.2 |

### B11. Deep learning and modern AI

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C276 | Neuron, weights, bias, activation functions (ReLU, sigmoid, softmax) | W | A | L9.3 |
| C277 | Forward pass and loss functions (MSE, cross-entropy) | W | A | L9.3 |
| C278 | Backpropagation and gradient descent | W | A | L9.3 |
| C279 | Optimisers: SGD, momentum, Adam; learning rate | W | A | L9.3 |
| C280 | Regularisation: L1/L2, dropout, early stopping | W | R | L9.3 |
| C281 | Hyperparameters (epochs, batch size, width, depth) | W | A | L9.3 |
| C282 | When NOT to use deep learning on tabular data | D | J | L9.3 |
| C283 | CNN, RNN/LSTM, Transformer and self-attention (awareness) | A | A | L9.3 |
| C284 | Embeddings and vector similarity | W | R | L9.3 |
| C285 | RAG, fine-tuning, RLHF (awareness) | A | A | L9.3 |
| C286 | Using LLMs safely in analytics (hallucination, data privacy, verification) | D | J | L0.2, L9.3 |

### B12. Delivery, vibe coding and governance

| ID | Concept | F | L | Lesson |
| --- | --- | --- | --- | --- |
| C287 | Vibe-coding loop: intent → assumptions → run → diagnose → verify → save | D | J | L0.2 |
| C288 | Prompt cards: weak, better, expert | D | R | L0.2 |
| C289 | Typical AI statistical errors (wrong test, leakage, silent drops, hallucinated numbers) | D | J | L0.2 |
| C290 | Reproducibility: seeds, versions, config files, Git commits | D | J | L0.4 |
| C291 | Reusable recipes, column mapping, schema checks, regression checks | D | J | L0.4 |
| C292 | Code and analysis review | W | J | L0.4, L10.4 |
| C293 | Data safety, anonymisation and pseudonymisation | D | J | L0.5 |
| C294 | Data storytelling: pyramid principle, so-what, one-page readout | D | J | L9.7 |
| C295 | Executive summaries and stakeholder challenge | D | J | L9.7 |
| C296 | Ethics and privacy in analytics | W | J | L9.5 |

**Total: 296 concepts** (Part A: 117, Part B: 179).

## Glossary design (built in Step 2, completed in Step 3)

Stored as `glossary/glossary.yaml`, one entry per concept plus extra terms (≈400 entries). Fields:

```yaml
- id: C206
  term: ROC-AUC
  plain_meaning: Chance the model ranks a random defaulter above a random non-defaulter.
  symbol: AUC
  typical_use: Ranking quality of a credit or fraud model.
  typical_range: "0.5 = random; credit application scorecards often 0.70-0.85 (rule of thumb)"
  watch_out: Insensitive to calibration and to rare-event precision; check PR-AUC.
  lessons: [L6.6, L8.7]
  navigator_nodes: [N-METRIC-CLASS]
```

The site renders it as a searchable page; every lesson auto-links glossary terms on first use.
