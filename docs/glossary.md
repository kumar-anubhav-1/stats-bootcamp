# Glossary

458 terms. Use the search box (top right) to find any term. Ranges are typical values and rules of thumb, not laws.

## 1

**1-SE rule** — Choose the simplest model whose CV score is within one standard error of the best.  
*Lessons:* L5.4

## A

**A/A test** — An experiment where both arms receive the same treatment; checks that the platform and analysis give ~5% false positives.  
*Lessons:* L3.3, L4.1

**ABC classification** — Ranking items by value contribution (A = top ~80% of value).  
*Lessons:* L7.6

**ACF** — Autocorrelation function: correlation of a series with its own lags.  
*Lessons:* L7.1

**Activation function** — Non-linear function (e.g. ReLU) applied inside a neural network.  
*Lessons:* L9.3

**Adam optimiser** — Gradient descent with momentum and per-parameter adaptive step sizes.  
*Lessons:* L9.8

**ADF test** — Augmented Dickey-Fuller test; null hypothesis = unit root (non-stationary).  
*Lessons:* L7.1

**ADI and CV²** — Average demand interval and squared coefficient of variation of non-zero demand; classify demand patterns.  
*Lessons:* L7.4

**Adjusted Rand index** — Agreement between two clusterings corrected for chance; 0 random, 1 identical.  
*Lessons:* L8.1

**Adjusted R²** — R² penalised for the number of predictors.  
*Lessons:* L5.1

**Adstock** — Carry-over of advertising effect into later weeks with geometric decay.  
*Lessons:* L8.4

**AIC** — Akaike information criterion: fit penalised by complexity; lower is better.  
*Typical range:* ΔAIC < 2 tie; > 10 decisive (rule of thumb)  *Lessons:* L2.3, L5.4

**Alert budget** — Number of cases the review team can handle per period.  
*Lessons:* L8.5

**Alpha** · `α` — The false-positive rate you accept when declaring a result significant.  
*Typical use:* Set before a test.  *Typical range:* 0.05 by convention; 0.01 or lower for high-stakes claims (rule of thumb)  *Watch out:* A convention, not a law.  *Lessons:* L3.3, L3.4

**Alpha spending** — Allocating the overall α across interim looks (Lan-DeMets), allowing unplanned look times.  
*Lessons:* L4.2

**Alternative hypothesis** · `H1` — The claim that there is a difference or effect.  
*Typical use:* Paired with the null hypothesis.  *Lessons:* L3.3, L3.4

**ANCOVA** — Regression of outcome on treatment plus a pre-period covariate.  
*Lessons:* L4.2, L5.1

**Anonymisation** — Transforming data so individuals cannot reasonably be re-identified.  
*Typical use:* Before sharing or analysing outside secure environments.  *Watch out:* Removing names is not enough.  *Lessons:* L0.5

**ANOVA** — Analysis of variance: tests whether means differ across three or more groups.  
*Watch out:* Assumes equal variances; use Welch ANOVA otherwise.  *Lessons:* L3.5

**ARIMA** — Model combining autoregression, differencing and moving-average error terms.  
*Lessons:* L7.2

**Assumption check** — A diagnostic confirming a method's conditions hold (e.g. independence, distribution shape).  
*Typical use:* Before interpreting any test or model.  *Lessons:* L0.2, L3.4

**AUC (ROC-AUC)** · `AUC` — Probability that a model ranks a random positive above a random negative.  
*Typical use:* Ranking quality of credit/fraud models.  *Typical range:* 0.5 random; application scorecards often 0.70–0.85 (rule of thumb)  *Watch out:* Insensitive to calibration and rare-event precision.  *Lessons:* L6.6

**Average precision (AP / mAP)** — Summary of the precision–recall curve for detections; mAP averages it over classes and IoU levels.  
*Lessons:* L11.3

## B

**Backdoor path** — A non-causal path from treatment to outcome through a common cause; block it by adjusting for confounders.  
*Lessons:* L4.4

**Backpropagation** — Using the chain rule to compute how much each weight contributed to the error, layer by layer backwards.  
*Lessons:* L9.8

**Bagging** — Bootstrap aggregating: averaging models trained on resampled data.  
*Lessons:* L6.2, L6.3

**Base rate** — How common an outcome is before any other information.  
*Typical use:* Interpreting alerts, accuracy, risk ratios.  *Typical range:* Default ~4% and fraud ~0.7% in the course bank data  *Watch out:* Ignoring it causes the base-rate fallacy.  *Lessons:* L2.1, L3.4

**Bayes' rule** — Turns P(evidence | cause) into P(cause | evidence) using the base rate.  
*Typical use:* Alert precision, diagnostic tests.  *Typical range:* P(A|B) = P(B|A)P(A) ÷ P(B)  *Lessons:* L2.1

**BCa bootstrap** — Bias-corrected and accelerated bootstrap interval; better for skewed statistics.  
*Lessons:* L3.2

**Behavioural score** — Risk score updated from recent account behaviour (arrears, utilisation, payments).  
*Lessons:* L6.1, L8.7

**Benford MAD** — Mean absolute deviation of first-digit shares from Benford's expected shares.  
*Typical range:* Nigrini first-digit: < 0.006 close; 0.006–0.012 acceptable; 0.012–0.015 marginal; > 0.015 nonconformity  *Watch out:* Expected MAD grows as sample size shrinks; compare with peers.  *Lessons:* L2.6

**Benford's law** — In many natural datasets, leading digit 1 appears ~30% of the time, 9 under 5%.  
*Typical use:* Screening for fabricated figures.  *Watch out:* Needs data spanning several orders of magnitude; compare with peers.  *Lessons:* L2.6

**Benjamini-Hochberg** · `BH` — Procedure controlling the false discovery rate.  
*Typical use:* Screens of features, segments, KPIs.  *Lessons:* L3.7

**Bernoulli distribution** — A single yes/no trial with success probability p.  
*Lessons:* L2.2

**Beta distribution** — Distribution on 0–1, used for rates and proportions.  
*Lessons:* L2.3

**Beta-binomial** — Binomial whose success rate itself varies between groups.  
*Typical use:* Store or branch rates with extra variation.  *Lessons:* L2.2

**Beta-Binomial update** — Beta(α, β) prior + k successes in n → Beta(α + k, β + n − k) posterior.  
*Lessons:* L4.3

**Bias-variance trade-off** — Simple models err systematically (bias); flexible models vary with the sample (variance).  
*Lessons:* L6.4

**BIC** — Bayesian information criterion: like AIC with a heavier penalty (log n per parameter).  
*Lessons:* L5.4

**Binary segmentation** — Recursively splitting a series at the point that most reduces within-segment variance.  
*Lessons:* L7.5

**Binomial distribution** — Number of successes in n independent trials with the same p.  
*Typical use:* Defaults in a pool, conversions.  *Typical range:* mean np, variance np(1 − p)  *Lessons:* L2.2

**Bonferroni correction** — Test each of m hypotheses at α/m (or multiply p by m).  
*Watch out:* Conservative; Holm is uniformly better.  *Lessons:* L3.7

**Bootstrap** — Estimating uncertainty by resampling your data with replacement many times.  
*Typical use:* CIs for medians, ratios, small or skewed samples.  *Watch out:* Resample the right unit (stores, not lines).  *Lessons:* L3.2, L3.4

**Box plot** — Median, IQR box, whiskers and points beyond them.  
*Typical use:* Comparing many groups.  *Watch out:* Hides bimodality.  *Lessons:* L1.5

**Box-Cox transform** · `λ` — Power transform that makes positive data more symmetric; λ = 0 is the log.  
*Typical use:* Preparing skewed amounts for models.  *Watch out:* Prefer the log when λ ≈ 0 — easier to explain.  *Lessons:* L1.6

**Breusch-Pagan test** — Test for heteroscedasticity in a regression.  
*Lessons:* L5.2

**Brier score** — Mean squared error of predicted probabilities.  
*Lessons:* L6.6

**Bunching** — Excess mass of a distribution just below a threshold.  
*Lessons:* L8.6

## C

**Calibration** — Agreement between predicted probabilities and observed frequencies.  
*Lessons:* L5.3, L6.6

**Cannibalisation** — Sales a promoted product takes from its own siblings.  
*Lessons:* L8.4

**Cauchy distribution** — Distribution with tails so heavy it has no mean.  
*Watch out:* The law of large numbers fails.  *Lessons:* L2.3

**Censored demand** — Observed sales below true demand because stock ran out.  
*Lessons:* L7.5, L7.6

**Censoring** — Knowing only that an event has not happened by the end of observation.  
*Lessons:* L9.2

**Central limit theorem** · `CLT` — Averages of many independent values are approximately normal.  
*Watch out:* n ≥ 30 is not enough for very skewed data.  *Lessons:* L2.5

**Challenge panel** — Reviewers who probe a readout's evidence, uncertainty and actions.  
*Lessons:* L10.2

**Change-point** — A time where a series' level (or other property) shifts persistently.  
*Lessons:* L7.5

**Characteristic stability index** — PSI applied to a model input.  
*Lessons:* L9.6

**Chi-square distribution** · `χ²` — Distribution of sums of squared standard normals; basis of count and variance tests.  
*Lessons:* L2.3, L3.5

**Chi-square test of independence** · `χ²` — Tests whether two categorical variables are associated.  
*Watch out:* Expected counts ≥ 5; else Fisher's exact.  *Lessons:* L3.5

**Class imbalance** — One outcome is much rarer than the other (fraud, default).  
*Lessons:* L6.5

**Class weights** — Training weights that up-weight the rare class.  
*Watch out:* Inflate predicted probabilities.  *Lessons:* L6.5

**Cluster (unit of randomisation)** — A group (store, branch) assigned to treatment as a whole.  
*Typical use:* Store-level tests.  *Watch out:* Analyse at cluster level or account for clustering.  *Lessons:* L3.4, L4.1

**Cluster bootstrap** — Resampling whole clusters (stores, customers) rather than rows.  
*Typical use:* Data with repeated rows per unit.  *Lessons:* L3.2

**Cluster sampling** — Sampling whole groups (stores, branches) rather than individuals.  
*Watch out:* Larger variance than SRS of the same size.  *Lessons:* L2.4

**Cluster-robust standard errors** — Standard errors allowing correlation within groups (stores, accounts).  
*Lessons:* L5.2, L9.1

**Code review** — Systematic critique of an analysis for data, method, inference and interpretation flaws.  
*Lessons:* L10.4

**Coefficient** · `β` — Expected change in the outcome per unit of a predictor, holding the other predictors fixed.  
*Watch out:* An adjusted association, not automatically causal.  *Lessons:* L5.1

**Coefficient of variation** · `CV` — Standard deviation divided by the mean.  
*Typical use:* Comparing variability across different scales.  *Typical range:* Spend often 0.8–1.5 (rule of thumb)  *Lessons:* L1.4

**Cohen's d** · `d` — Difference between means in standard-deviation units.  
*Typical use:* Comparable effect size across outcomes.  *Typical range:* 0.2 small, 0.5 medium, 0.8 large (Cohen's rough benchmarks)  *Watch out:* Benchmarks are context-free; judge in business units.  *Lessons:* L3.4, L3.6

**Cohen's h** · `h` — Effect size for a difference between two proportions (arcsine scale).  
*Lessons:* L3.6

**Cohen's kappa** — Agreement between two labellers corrected for agreement expected by chance.  
*Lessons:* L11.5

**Cohort analysis** — Tracking groups that started at the same time across their age.  
*Lessons:* L8.2, L8.7

**Collider** — A variable caused by two others; conditioning on it creates a spurious association.  
*Lessons:* L4.4

**Colour channel** — One of the red, green or blue layers of a colour image.  
*Lessons:* L11.1

**Concept drift** — Change in the relationship between inputs and outcome.  
*Lessons:* L9.6

**Conditional probability** · `P(A | B)` — Probability of A among only the cases where B is true.  
*Typical use:* Default rate given channel; fraud given alert.  *Watch out:* P(A | B) ≠ P(B | A).  *Lessons:* L2.1

**Confidence** — P(B | A): share of baskets with A that also contain B.  
*Lessons:* L8.3

**Confidence interval** · `CI` — Range of effect sizes compatible with the data at a chosen confidence level.  
*Typical use:* Report with every estimate.  *Watch out:* Not the range containing 95% of individuals.  *Lessons:* L3.1, L3.4

**Confidence routing** — Automating only predictions above a confidence threshold and sending the rest to people.  
*Lessons:* L11.4

**Config (toolkit)** — A YAML file mapping a recipe's roles to a dataset's columns, plus filters and parameters.  
*Typical use:* Reusing recipes without code changes.  *Lessons:* L0.4

**Conformal prediction** — Distribution-free prediction sets/intervals with guaranteed average coverage.  
*Lessons:* L9.5

**Confounder** — A variable that influences both the 'treatment' and the outcome, distorting their apparent relationship.  
*Typical use:* Observational comparisons.  *Watch out:* Stratify or adjust; better, randomise.  *Lessons:* L2.4, L3.4, L4.4

**Confusion matrix** — Table of true/false positives and negatives at a threshold.  
*Lessons:* L6.6

**Connected component** — Group of nodes linked by any path in a graph.  
*Lessons:* L8.6

**Contamination** — Control units receiving some of the treatment.  
*Lessons:* L4.1

**Contamination** — Assumed share of anomalies; in practice set by review capacity.  
*Lessons:* L8.5

**Convenience sample** — Units that were easy to get rather than randomly chosen.  
*Watch out:* Usually biased.  *Lessons:* L2.4

**Convolution** — Sliding a filter across an image and computing a weighted sum at each position.  
*Lessons:* L11.1

**Convolutional neural network** — Network using sliding filters (convolutions) and pooling; built for images.  
*Lessons:* L9.8

**Cook's distance** — How much the fitted model changes when a row is removed.  
*Typical range:* > 4/n flags rows to inspect  *Lessons:* L5.2

**Cosine similarity** — Cosine of the angle between two vectors; direction similarity ignoring length.  
*Typical use:* Product affinity, embeddings, RAG retrieval.  *Typical range:* −1 to 1  *Lessons:* L2.7

**Covariance** — Average joint deviation of two variables from their means, in original units.  
*Watch out:* Not comparable across scales — use correlation.  *Lessons:* L1.7

**Covariate adjustment** — Using pre-treatment variables to reduce noise in an experiment's effect estimate (CUPED, ANCOVA).  
*Lessons:* L4.2

**Coverage** — How often an interval method actually contains the true value.  
*Watch out:* Heavy tails and rare events make '95%' intervals cover less.  *Lessons:* L3.1

**Cox proportional hazards** — Regression of the hazard on drivers; coefficients exponentiate to hazard ratios.  
*Lessons:* L9.2

**Cramér's V** · `V` — Strength of association between two categorical variables (0–1).  
*Typical range:* 0.1 weak, 0.3 moderate, 0.5 strong (rough)  *Lessons:* L1.7

**Credible interval** — Range containing the parameter with a stated posterior probability.  
*Watch out:* Different interpretation from a confidence interval.  *Lessons:* L4.3

**Cross-entropy (log-loss)** — Classification loss −Σ y log ŷ: heavily penalises confident wrong probabilities.  
*Lessons:* L9.8

**Cross-validation** · `CV` — Estimating out-of-sample performance by repeatedly training on part of the data and testing on the rest.  
*Watch out:* Shuffle folds unless data are time-ordered.  *Lessons:* L5.4, L6.4

**Croston's method** — Forecasts intermittent demand by smoothing sizes and intervals separately.  
*Lessons:* L7.4

**CUPED** — Variance reduction using a pre-experiment covariate.  
*Typical use:* Shorter or more sensitive experiments.  *Watch out:* Covariate must be measured before treatment.  *Lessons:* L4.2

**Customer lifetime value** — Discounted future margin expected from a customer.  
*Lessons:* L8.2

**CUSUM** — Cumulative-sum control chart that accumulates deviations to detect shifts.  
*Lessons:* L7.5

**Cycle service level** — Probability of no stock-out during a replenishment cycle.  
*Lessons:* L7.6

## D

**DAG** — Directed acyclic graph: a diagram of assumed causal relationships.  
*Lessons:* L4.4

**Data augmentation** — Creating extra training images by changing things that should not change the label (brightness, small shifts).  
*Lessons:* L11.2

**Data card** — A short document describing a dataset's purpose, origin, contents and limitations.  
*Lessons:* L0.3

**Data dictionary** — Field-by-field description of a table: type, meaning, allowed values, nulls.  
*Lessons:* L0.3

**Data leakage** — Using information in a model or comparison that would not be available at decision time.  
*Typical use:* Model validation.  *Watch out:* Suspect when performance is too good to be true.  *Lessons:* L0.2, L6.4

**Data leakage (target)** — Using a feature recorded after, or because of, the outcome.  
*Lessons:* L6.4

**Data-quality dimensions** — Completeness, validity, accuracy, consistency, uniqueness, timeliness.  
*Lessons:* L1.2

**DBSCAN** — Density-based clustering that finds arbitrarily shaped clusters and labels sparse points as noise.  
*Lessons:* L8.1

**Decision memo** — One-page recommendation: decision, evidence with CI, hygiene, guardrails, value, plan.  
*Lessons:* L4.5, L9.7

**Decision tree** — Model that splits data by successive questions on features.  
*Watch out:* Overfits when deep.  *Lessons:* L6.2

**Design effect** · `DEFF` — Inflation of variance caused by clustering, relative to independent sampling.  
*Typical use:* Store/branch tests.  *Typical range:* 1 + (cluster size − 1) × ICC  *Lessons:* L3.4, L3.6

**Determinant** — Single number summarising a square matrix; zero means singular.  
*Lessons:* L2.7

**Deviance** — Measure of lack of fit for likelihood-based models; differences compare nested models.  
*Lessons:* L5.3, L5.5

**Difference-in-differences** — Effect = change in the treated group minus change in a control group over the same period.  
*Lessons:* L9.1

**Differencing** — Replacing a series by its period-to-period changes to remove trend.  
*Lessons:* L7.1

**Diffusion model** — Generative model trained to remove noise step by step; generates by denoising random noise.  
*Lessons:* L9.8, L6.8

**Direct effect** — Effect of a treatment not passing through a specified mediator.  
*Lessons:* L4.4

**Disparate impact** — Ratio of favourable-outcome rates between groups; below 0.8 is a common flag.  
*Lessons:* L9.5

**Dispersion (count data)** — Variance divided by mean of a count.  
*Typical range:* ≈ 1 Poisson; > 1 over-dispersed  *Lessons:* L2.2

**Dropout** — Randomly switching off neurons during training so the network does not rely on any one of them.  
*Lessons:* L9.8

**Dummy variable** — 0/1 indicator for a category level; coefficients compare with a reference level.  
*Lessons:* L5.1

**Duplicate** — The same record appearing more than once.  
*Typical use:* Data quality checks.  *Watch out:* Distinguish duplicate keys from legitimate repeats.  *Lessons:* L0.3, L1.2

**Durbin-Watson statistic** — Test statistic for first-order autocorrelation in residuals (≈ 2 none).  
*Lessons:* L5.2

## E

**Early stopping** — Stopping training when validation loss stops improving.  
*Lessons:* L9.8

**ECDF** — Empirical cumulative distribution: share of values at or below each x.  
*Typical use:* Comparing distributions; reading percentiles.  *Lessons:* L1.5

**Economic capital** — Capital held for unexpected loss: VaR minus expected loss.  
*Lessons:* L9.4

**Effect size** — How big a difference or relationship is, in business or standardised units.  
*Typical use:* Always alongside p-values.  *Lessons:* L3.4, L3.6

**Eigenvalue** · `λ` — Variance along a principal direction of a correlation matrix.  
*Watch out:* Near-zero eigenvalue → collinear predictors.  *Lessons:* L2.7, L5.2

**Elastic net** — Mix of ridge and lasso penalties.  
*Lessons:* L5.4

**Embedding** — Dense vector representation where distance reflects similarity.  
*Lessons:* L9.3

**Epoch** — One full pass over the training data.  
*Lessons:* L9.8

**Equal opportunity** — Fairness criterion: equal true positive rates across groups.  
*Lessons:* L9.5

**Estimator properties** — Unbiased (right on average), consistent (closer as n grows), efficient (small spread), robust (insensitive to outliers).  
*Lessons:* L3.1

**Eta-squared** · `η²` — Share of outcome variation explained by group membership.  
*Typical range:* 0.01 small, 0.06 medium, 0.14 large (rough benchmarks)  *Lessons:* L3.5, L3.6

**Event study** — Plot of the treated–control gap by period relative to treatment, used to check pre-trends.  
*Lessons:* L9.1

**Expected cell count** — Count a 2×2 table cell would have if there were no association.  
*Typical use:* Checking validity of chi-square / z-tests.  *Typical range:* ≥ 5 rule of thumb; else Fisher's exact  *Lessons:* L3.4, L3.5

**Expected loss** — Average shortfall of a decision if it turns out wrong, weighted by posterior probability.  
*Typical use:* Bayesian ship/no-ship rules.  *Lessons:* L4.3

**Expected loss** — PD × LGD × EAD.  
*Lessons:* L8.7

**Expected shortfall** — Average loss in the worst (1 − α) of outcomes; at least as large as VaR.  
*Lessons:* L9.4

**Expected value** · `E[X]` — Probability-weighted average outcome.  
*Typical use:* Expected loss, expected P&L.  *Watch out:* Says nothing about downside risk.  *Lessons:* L2.1, L2.5

**Exponential distribution** — Waiting time with a constant hazard.  
*Lessons:* L2.3

**Exponential smoothing** · `ETS` — Forecasts as weighted averages of past values with exponentially decaying weights (level, trend, season).  
*Lessons:* L7.2

**Exposure offset** — log(exposure) added to a count model so it describes a rate per unit of exposure.  
*Lessons:* L5.5

**Exposure offset** — log(exposure) added to a count GLM so it models a rate.  
*Lessons:* L9.4

## F

**F distribution** — Ratio of two variance estimates; basis of ANOVA.  
*Lessons:* L2.3, L3.6

**F1 score** — Harmonic mean of precision and recall.  
*Lessons:* L6.6

**False discovery rate** · `FDR` — Expected share of false positives among results declared significant.  
*Lessons:* L3.7

**Family-wise error rate** · `FWER` — Probability of at least one false positive among a family of tests.  
*Lessons:* L3.7

**Feature engineering** — Creating model inputs from raw data: aggregates, ratios, recency, lags, flags.  
*Lessons:* L6.1

**Field accuracy** — Share of whole fields (e.g. a 6-digit amount) read completely correctly.  
*Lessons:* L11.4

**Fill rate** — Share of demand served directly from stock.  
*Lessons:* L7.6

**Filter (kernel)** — Small grid of weights slid across an image; its weighted sums highlight a pattern such as an edge.  
*Lessons:* L11.1

**Fine-tuning** — Continuing to train a pretrained model on your own labelled data.  
*Lessons:* L11.2

**Fisher's exact test** — Exact test of association in a 2×2 table.  
*Typical use:* Small counts.  *Lessons:* L3.4, L3.5

**Fixed effects** — One indicator per unit (store, branch) so each unit is compared with itself.  
*Lessons:* L5.1, L9.1

**Forecast bias** — Σ(forecast − actual) ÷ Σ actual — systematic over- or under-forecasting.  
*Lessons:* L7.3

**Forecast reconciliation** — Adjusting forecasts so lower levels add up to higher levels.  
*Lessons:* L7.4

**Fourier terms** — Sine/cosine pairs that model smooth seasonality in a regression.  
*Lessons:* L7.2

## G

**Gains chart** — Cumulative share of positives captured as more of the population is targeted.  
*Lessons:* L6.6

**Gamma distribution** — Flexible positive, right-skewed distribution.  
*Typical use:* Claim severity, durations.  *Lessons:* L2.3

**Garden of forking paths** — Many reasonable analysis choices (outcome, subgroup, window, exclusions) that inflate false positives even without intent.  
*Lessons:* L3.7

**Geometric distribution** — Number of trials until the first success.  
*Typical range:* mean 1/p  *Lessons:* L2.2

**Geometric mean** — exp(mean of logs); the typical value of multiplicative or log-normal data.  
*Lessons:* L1.4

**Gini (model)** — 2 × AUC − 1; credit-industry ranking metric.  
*Typical range:* 0.4–0.7 typical for application scorecards  *Lessons:* L6.6, L8.7

**Gini coefficient** — Concentration measure from the Lorenz curve: 0 equal, 1 maximal concentration.  
*Typical use:* Revenue or exposure concentration.  *Lessons:* L1.4

**Gini coefficient** — 2 × AUC − 1; ranking power of a credit score.  
*Lessons:* L8.7

**GLM** — Generalised linear model: a family (Poisson, binomial, Gamma…), a link function and a linear predictor.  
*Lessons:* L5.5

**Gradient boosting** · `GBM` — Ensemble that adds small trees sequentially to correct remaining errors (LightGBM, XGBoost).  
*Lessons:* L6.2

**Gradient descent** — Repeatedly stepping the parameters against the gradient of the loss: θ ← θ − η∇L.  
*Lessons:* L9.8

**Grain** — What one row of a table represents.  
*Typical use:* Before any aggregation or join.  *Watch out:* Wrong grain → wrong averages and join explosions.  *Lessons:* L0.3, L1.1

**Grouped cross-validation** — CV where all rows of the same entity (customer) stay in the same fold.  
*Lessons:* L6.4

**Growth index** — A unit's outcome in a test window divided by its own baseline-period average.  
*Typical use:* Removing size differences between stores.  *Lessons:* L3.4

**Guardrail metric** — A metric that must not get worse (complaints, margin, delinquency); can veto a launch.  
*Lessons:* L4.1, L4.5

## H

**Hallucination** — Fluent but false output from a generative model.  
*Lessons:* L9.3

**HARKing** — Hypothesising After the Results are Known — presenting exploratory findings as if predicted.  
*Lessons:* L3.7

**Hazard ratio** — Multiplicative change in the instantaneous event rate.  
*Lessons:* L9.2

**Heavy tail** — More extreme values than a normal distribution would produce.  
*Typical use:* Spend, balances, claims.  *Watch out:* Means unstable; use medians and robust methods.  *Lessons:* L1.4, L3.4

**Hedges' g** · `g` — Cohen's d with a small-sample bias correction.  
*Typical use:* Effect size with small groups.  *Lessons:* L3.4

**Held-out data** — Data not seen during learning, used to test transfer (exam seeds 7001/7002).  
*Lessons:* L10.4

**Heteroscedasticity** — Residual variance that changes with the fitted value or a predictor.  
*Watch out:* Wrong SEs; use robust SEs or transform.  *Lessons:* L5.2

**Hierarchical forecasting** — Forecasting at several aggregation levels and reconciling them (bottom-up, top-down, MinT).  
*Lessons:* L7.4

**Histogram** — Counts of values in bins.  
*Watch out:* Bin width changes the story; use a log scale for skewed data.  *Lessons:* L1.5

**Holdout** — Units kept on the old treatment after a rollout to keep measuring the effect.  
*Lessons:* L4.5

**Holm correction** — Step-down version of Bonferroni: same FWER control, more power.  
*Lessons:* L3.5, L3.7

**Holt-Winters** — Exponential smoothing with trend and seasonality.  
*Watch out:* Needs at least two seasonal cycles.  *Lessons:* L7.2

**Human-in-the-loop** — A process where people review the cases a model is unsure about.  
*Lessons:* L11.4, L11.5

**Hypergeometric distribution** — Successes when sampling without replacement from a finite population.  
*Typical use:* Audit sample sizing.  *Lessons:* L2.2

**Hyperparameter** — A model setting chosen before training (depth, learning rate, penalty).  
*Lessons:* L6.4

**Hypothesis test** — Procedure to judge whether data are compatible with 'no effect'.  
*Lessons:* L3.3, L3.4

## I

**ICC (intra-class correlation)** · `ρ` — Share of variation that lies between clusters rather than within them.  
*Typical use:* Planning and analysing cluster tests.  *Lessons:* L3.4, L3.6

**ICE plot** — Individual conditional expectation: one prediction curve per case.  
*Lessons:* L6.7

**Imputation** — Filling in missing values with estimates.  
*Watch out:* Can mislead when data are MNAR.  *Lessons:* L1.3

**Independence** — Two events are independent when knowing one does not change the probability of the other: P(A and B) = P(A) × P(B).  
*Typical use:* Checking whether drivers can be separated.  *Watch out:* Promotions and displays in the course data are strongly dependent.  *Lessons:* L2.1

**Information value** — Sum over bins of (% goods − % bads) × WoE; above 0.3 is strong, above 0.5 suspicious.  
*Lessons:* L8.7

**Interaction term** — Product of two predictors, letting one's effect depend on the other.  
*Lessons:* L5.6

**Interference** — Treatment of one unit affecting another unit's outcome (shared stock, social effects, agents).  
*Watch out:* Use cluster randomisation.  *Lessons:* L4.1

**Intermittent demand** — Demand with many zero periods (ADI > 1.32).  
*Lessons:* L7.4

**Interquartile range** · `IQR` — Q3 minus Q1: the spread of the middle 50%.  
*Typical use:* Robust spread for skewed data.  *Lessons:* L1.4

**Intersection over union (IoU)** — Overlap of a predicted and a true box divided by the area they cover together; 1 = perfect.  
*Lessons:* L11.3

**Isolation Forest** — Anomaly score from how few random splits isolate a point.  
*Lessons:* L8.5

**Isotonic regression (calibration)** — Non-parametric monotone recalibration of scores.  
*Lessons:* L6.6

## J

**Join explosion** — Row multiplication caused by joining on a key that is not unique.  
*Watch out:* Check row counts before and after every join.  *Lessons:* L1.1

## K

**k-anonymity** — Every combination of quasi-identifiers is shared by at least k records.  
*Typical use:* Re-identification risk check.  *Lessons:* L0.5

**K-Means** — Clustering that assigns points to the nearest of k centres and updates the centres until stable.  
*Lessons:* L8.1

**K-nearest neighbours** — Predicts from the k most similar past cases.  
*Lessons:* L6.3, L6.8

**Kaplan–Meier estimator** — Survival curve multiplying period-by-period survival among those still at risk.  
*Lessons:* L9.2

**Kendall's tau** · `τ` — Rank correlation based on concordant and discordant pairs.  
*Typical use:* Small samples, many ties.  *Lessons:* L1.7

**KNN** — k-nearest neighbours: predicts from the most similar training cases.  
*Lessons:* L6.3

**KPSS test** — Test whose null hypothesis is stationarity (complements ADF).  
*Lessons:* L7.1

**Kruskal-Wallis test** — Rank-based comparison of three or more groups; robust to skew.  
*Lessons:* L3.5

**KS distance** — Largest gap between a fitted and empirical cumulative distribution.  
*Watch out:* Insensitive in the far tail; also compare P99.  *Lessons:* L2.3

**KS statistic** — Maximum gap between cumulative distributions of scores for positives and negatives.  
*Lessons:* L6.6, L8.7

**KS statistic** — Maximum gap between cumulative good and bad distributions over the score.  
*Lessons:* L8.7

**Kurtosis** — Heaviness of a distribution's tails (excess kurtosis: relative to normal).  
*Watch out:* High kurtosis → unstable means and SDs.  *Lessons:* L1.4

## L

**Label noise** — Errors in training labels; random noise averages out, systematic noise misleads the model.  
*Lessons:* L11.5

**Laplace distribution** — Sharp-peaked, fat-tailed symmetric distribution.  
*Typical use:* Price changes, returns.  *Lessons:* L2.3

**Large-loss loading** — Separate premium charge for rare very large claims excluded from attritional models.  
*Lessons:* L5.5, L9.4

**Large-loss loading** — Premium add-on covering rare catastrophic claims excluded from attritional pricing.  
*Lessons:* L9.4

**Lasso** · `L1` — Regression with a penalty on absolute coefficients; can set some exactly to zero.  
*Lessons:* L5.4

**Law of large numbers** · `LLN` — Sample averages approach the true mean as n grows.  
*Watch out:* Slow for heavy tails; fails with no mean.  *Lessons:* L2.5

**Law of total probability** — An overall rate is the share-weighted average of group rates.  
*Typical use:* Combining segments; checking mix effects.  *Lessons:* L2.1

**Learning rate** — Step size η in gradient descent; too large diverges, too small crawls.  
*Lessons:* L9.8

**Levene's test** — Test of equal variances across groups.  
*Typical use:* Informative check; Welch's t does not need equal variances.  *Lessons:* L3.4, L3.5

**Leverage** — How unusual a row's predictor values are.  
*Lessons:* L5.2

**Lift** — Confidence ÷ base rate of B; above 1 means bought together more than chance.  
*Lessons:* L8.3

**Lift (promotion)** — Relative increase in an outcome caused by a promotion versus a baseline/control.  
*Lessons:* L3.4, L8.4

**Lift chart** — Event rate by score decile relative to the average.  
*Lessons:* L6.6

**Likelihood** — How probable the observed data are for each possible parameter value.  
*Lessons:* L4.3

**Link function** — Transformation connecting the mean outcome to the linear predictor (log, logit).  
*Lessons:* L5.5

**Listwise deletion** — Dropping every row with any missing value in the variables used.  
*Watch out:* Silent row loss and bias unless data are MCAR.  *Lessons:* L1.3

**Log transform** — Taking logarithms to compress a right tail.  
*Typical use:* Spend, income, balances; coefficients become % effects.  *Watch out:* Cannot handle zeros — report them separately.  *Lessons:* L1.5, L1.6

**Log-odds** · `logit` — Natural log of the odds; the scale logistic regression is linear on.  
*Lessons:* L2.1, L6.1

**Log-rank test** — Test of whether survival curves differ between groups.  
*Lessons:* L9.2

**Logistic regression** — Model of the log-odds of a yes/no outcome as a linear function of predictors.  
*Lessons:* L5.3

**Lognormal distribution** — A variable whose logarithm is normal: positive and right-skewed.  
*Typical use:* Spend, basket value, income.  *Lessons:* L2.3

**Lorenz curve** — Cumulative share of a total against cumulative share of units, sorted from smallest.  
*Lessons:* L1.4

**Loss ratio** — Claims paid ÷ premiums earned.  
*Typical range:* > 1 means claims exceed premiums  *Lessons:* L5.5, L9.4

## M

**MAD (median absolute deviation)** · `MAD` — Median of absolute deviations from the median; robust spread.  
*Typical use:* Robust z-scores (× 1.4826 ≈ SD for normal data).  *Lessons:* L1.4, L1.6

**Mann-Whitney U test** — Rank-based comparison of two independent groups.  
*Typical use:* Skewed outcomes, small samples.  *Watch out:* Tests 'tends to be larger', not equality of means.  *Lessons:* L3.4

**MAPE** — Mean absolute percentage error.  
*Watch out:* Undefined at zero; favours under-forecasts.  *Lessons:* L7.3

**MAR (missing at random)** — Missingness depends on observed data but not on the missing value itself.  
*Lessons:* L1.3

**Marginal effect** — Change in predicted probability for a change in a predictor, averaged over observations.  
*Typical use:* Translating odds ratios into percentage points.  *Lessons:* L5.3

**MASE** — Mean absolute scaled error: MAE divided by in-sample naive MAE (< 1 beats naive).  
*Lessons:* L7.3

**Masking** — Extreme values inflating the mean and SD so that a z-score fails to flag them.  
*Lessons:* L1.6

**Matrix rank** — Number of linearly independent columns.  
*Watch out:* Rank-deficient design → coefficients not identifiable.  *Lessons:* L2.7

**Maximum likelihood** · `MLE` — Choosing parameter values that make the observed data most probable.  
*Typical use:* Distribution fits, logistic regression.  *Lessons:* L3.1, L5.3

**MCAR (missing completely at random)** — Missingness unrelated to any data.  
*Lessons:* L1.3

**MCMC** — Markov chain Monte Carlo: simulation methods that draw from posterior distributions (PyMC, Stan).  
*Watch out:* Check R-hat and effective sample size.  *Lessons:* L4.3

**McNemar's test** — Test for paired binary outcomes using only the units that changed.  
*Typical use:* Same accounts measured twice.  *Lessons:* L3.5

**MDE (minimum detectable effect)** · `MDE` — Smallest true effect a design detects with the chosen power and α.  
*Typical use:* Planning tests; interpreting null results.  *Typical range:* Power 80%, α 0.05 by convention  *Lessons:* L3.4, L3.6

**Mean** · `x̄` — Sum divided by count.  
*Typical use:* Totals and symmetric data.  *Watch out:* Pulled by extremes.  *Lessons:* L1.4

**Measurement scale** — Nominal, ordinal, interval or ratio — decides which summaries are meaningful.  
*Lessons:* L1.1

**Median** — Middle value when data are sorted.  
*Typical use:* Typical value for skewed data.  *Lessons:* L1.4

**Mediator** — A variable on the causal path from treatment to outcome.  
*Watch out:* Adjust only for a direct effect.  *Lessons:* L4.4

**Mental map** — A diagram that shows which family of techniques fits which business question.  
*Lessons:* L0.2

**Minor currency units** — Amounts stored in cents/pence (×100); a common unit trap.  
*Lessons:* L10.1

**Mix vs rate decomposition** — Splitting a change in an overall rate into changes in segment composition (mix) and within-segment rates (rate).  
*Lessons:* L5.7

**Mixed model** — Regression with random effects (e.g. a random intercept per store) as well as fixed effects.  
*Lessons:* L5.6

**Mix–rate decomposition** — Splitting a change in an average into the part due to segment mix and the part due to within-segment rates.  
*Lessons:* L10.2

**ML ladder** — The progression of algorithms from simple and explainable to complex and opaque; climb only when a fair test justifies it.  
*Lessons:* L6.8

**MNAR (missing not at random)** — Missingness depends on the unobserved value itself.  
*Watch out:* Simple imputation biases results; flag and run sensitivity analysis.  *Lessons:* L1.3

**Mode** — Most frequent value.  
*Typical use:* Categories.  *Lessons:* L1.4

**Model risk management** — Governance of models: inventory, validation, monitoring, change control, ownership.  
*Lessons:* L9.5

**Mondrian conformal** — Conformal prediction calibrated separately within classes or groups.  
*Lessons:* L9.5

**Monte Carlo simulation** — Repeatedly sampling uncertain inputs to get a distribution of outcomes.  
*Typical use:* P(loss), risk ranges, capital.  *Watch out:* Fix the seed; model correlations between inputs.  *Lessons:* L2.5

**mSPRT** — Mixture sequential probability ratio test giving always-valid p-values for continuous monitoring.  
*Lessons:* L4.2

**Multilayer perceptron** — Neural network of fully connected layers with non-linear activations.  
*Lessons:* L9.3

## N

**Naive Bayes** — Classifier combining per-feature likelihoods under an independence assumption.  
*Watch out:* Poorly calibrated probabilities.  *Lessons:* L6.3

**Naive Bayes** — Classifier that multiplies per-feature likelihoods assuming independence.  
*Lessons:* L6.3, L6.8

**Natural frequencies** — Stating probabilities as counts out of a round number (e.g. per 10,000 accounts).  
*Typical use:* Explaining alerts and tests to non-specialists.  *Lessons:* L2.1

**Negative binomial distribution** — Count model allowing variance larger than the mean.  
*Typical use:* Retail demand, claim counts with heterogeneous risk.  *Lessons:* L2.2, L6.3

**Newsvendor model** — Single-period order quantity at the critical ratio (p − c) ÷ (p − s) of the demand distribution.  
*Lessons:* L7.6

**Non-maximum suppression** — Removing overlapping duplicate detections, keeping the highest-scoring one.  
*Lessons:* L11.3

**Normal distribution** — Symmetric bell curve described by mean and SD.  
*Typical range:* ~68% within 1 SD, ~95% within 2  *Watch out:* Understates extreme events in most business data.  *Lessons:* L2.3

**Novelty effect** — Temporary response to something new that fades with exposure.  
*Watch out:* Run tests ≥ 2 weeks; plot effect by exposure week.  *Lessons:* L4.1

**Null hypothesis** · `H0` — The claim of no difference or no effect that a test tries to reject.  
*Lessons:* L3.3, L3.4

**Number needed to treat** · `NNT` — Units that must receive a treatment for one extra success: 1 ÷ risk difference.  
*Lessons:* L3.6

## O

**O'Brien-Fleming boundary** — Interim-analysis boundary that is very strict early and close to 1.96 at the end.  
*Lessons:* L4.2

**Object detection** — Finding objects in an image and drawing a box around each.  
*Lessons:* L11.3

**Observation point** — The moment a prediction would be made; features may only use data up to it.  
*Lessons:* L6.1, L6.4

**OCR** — Optical character recognition: reading text from images.  
*Lessons:* L11.4

**Odds** — p ÷ (1 − p): chance of an event relative to its absence.  
*Typical use:* Logistic regression, credit scoring.  *Watch out:* Close to p only when p is small.  *Lessons:* L2.1, L6.1

**Odds ratio** · `OR` — Ratio of the odds of an outcome between two groups.  
*Typical use:* Logistic regression, case-control data.  *Watch out:* Approximates relative risk only when outcomes are rare.  *Lessons:* L3.4, L5.3

**OLS (ordinary least squares)** — Fits a linear model by minimising the sum of squared residuals.  
*Lessons:* L5.1

**On-shelf availability (OSA)** — Share of shelf space where product is present; the key retail KPI for gaps.  
*Lessons:* L11.3

**One-hot encoding** — One 0/1 column per category.  
*Typical use:* Few categories.  *Lessons:* L1.6

**One-sided test** — Test of a difference in one pre-specified direction.  
*Watch out:* Choose before seeing data; otherwise it halves the p-value dishonestly.  *Lessons:* L3.3

**Optional stopping** — Stopping a test when results look significant.  
*Watch out:* Inflates false positives; use a fixed horizon or alpha spending.  *Lessons:* L3.7, L4.2

**Out-of-time validation** — Testing a model on a later period than it was trained on.  
*Lessons:* L6.4

**Output anatomy** — A table explaining every number in an analysis output: meaning, range, good/bad/suspicious values.  
*Lessons:* L3.4

**Over-dispersion** — Variance larger than a model (usually Poisson) assumes.  
*Watch out:* Use negative binomial or robust SEs.  *Lessons:* L5.5

**Overfitting** — A model that fits noise in the training data and performs worse on new data.  
*Lessons:* L5.4, L6.4

## P

**p-hacking** — Trying analyses until something is significant.  
*Lessons:* L3.7

**p-value** · `p` — Probability of data at least this extreme if the null hypothesis were true.  
*Watch out:* Not the probability H0 is true; not an effect size.  *Lessons:* L3.3, L3.4

**PACF** — Partial autocorrelation: correlation at a lag after removing shorter lags.  
*Lessons:* L7.1

**Paired test** — Comparison of two measurements on the same units.  
*Typical use:* Before/after on the same stores or customers.  *Lessons:* L3.4

**Parallel trends** — DiD assumption that treated and control would have moved together without treatment.  
*Lessons:* L9.1

**Partial dependence plot** · `PDP` — Average model prediction as one feature varies.  
*Lessons:* L6.7

**PCA** — Principal component analysis: rotating features into uncorrelated directions ordered by variance explained.  
*Lessons:* L8.1

**Pearson correlation** · `r` — Strength of linear association (−1 to 1).  
*Watch out:* Sensitive to outliers; misses curves.  *Lessons:* L1.7

**Percentile** — Value below which a given percentage of observations fall (P90, P99).  
*Lessons:* L1.4

**Percentile bootstrap** — Bootstrap CI from the 2.5th and 97.5th percentiles of resampled statistics.  
*Lessons:* L3.2

**Permutation importance** — Drop in model performance when a feature's values are shuffled.  
*Lessons:* L6.7

**Permutation test** — Builds the null distribution by shuffling group labels.  
*Typical use:* Minimal-assumption check, small samples.  *Lessons:* L3.2, L3.4

**Pipeline** — Chained preprocessing and model steps fitted together so no information leaks across folds.  
*Lessons:* L6.4

**Pixel** — One point of an image; in colour it holds three numbers (red, green, blue), each 0–255.  
*Lessons:* L11.1

**Placebo test** — Applying the method where no effect should exist to check it finds none.  
*Lessons:* L9.1

**Platt scaling** — Recalibrating scores with a logistic fit on a validation set.  
*Lessons:* L6.6

**Pocock boundary** — Interim-analysis boundary that is constant across looks.  
*Lessons:* L4.2

**Point estimate** — A single best guess of a population value from a sample (e.g. the sample mean).  
*Watch out:* Always pair with an interval.  *Lessons:* L3.1

**Point-biserial correlation** — Pearson correlation between a numeric and a binary variable.  
*Watch out:* Small for rare outcomes even when risk gradients are steep.  *Lessons:* L1.7

**Points to double the odds** — Scorecard scaling: score points that double the good:bad odds (PDO).  
*Lessons:* L8.7

**Poisson distribution** — Count of events in a fixed window at a constant rate.  
*Typical use:* Claims, arrivals.  *Watch out:* Variance = mean; real counts are often over-dispersed.  *Lessons:* L2.2

**Population stability index** — Σ (actual% − expected%) × ln(actual% ÷ expected%) across bins; drift measure.  
*Lessons:* L9.6

**Positional encoding** — Information added to tokens so a transformer knows word order.  
*Lessons:* L9.8

**Post-hoc power** — 'Observed power' computed from the observed effect after a test.  
*Watch out:* Uninformative — a restatement of the p-value. Report the MDE instead.  *Lessons:* L3.6

**Post-hoc test** — Pairwise comparisons after a significant omnibus test, corrected for multiplicity (Tukey HSD, Games-Howell, Dunn).  
*Lessons:* L3.5

**Posterior** — Updated belief about a parameter after combining prior and data.  
*Lessons:* L4.3

**Power** · `1 − β` — Probability a test detects a true effect of a given size.  
*Typical range:* 80% conventional target  *Lessons:* L3.6

**PR-AUC** — Area under the precision-recall curve; baseline equals the event rate.  
*Lessons:* L6.5, L6.6

**Practical significance** — Whether an effect is big enough to matter for the decision.  
*Typical use:* Compare the CI with the minimum worthwhile effect.  *Lessons:* L3.4

**Pre-registration** — Writing hypothesis, outcome, unit, test, sample size and stopping rule before seeing data.  
*Lessons:* L3.7, L4.1

**Precision (PPV)** · `PPV` — Share of flagged cases that are truly positive.  
*Typical use:* Alert queues, fraud rules.  *Watch out:* Falls sharply when the base rate is low.  *Lessons:* L2.1, L6.6

**Precision at k** — Share of positives among the k highest-scored cases.  
*Typical use:* Alert queues with fixed capacity.  *Lessons:* L6.5

**Prediction interval** — Range likely to contain a new individual observation — much wider than a CI for the mean.  
*Lessons:* L3.1, L7.3

**Preprocessing leakage** — Fitting scalers, imputers or encoders on data that includes the test set.  
*Lessons:* L6.4

**Price elasticity** — Percentage change in units for a 1% change in price; the slope of a log–log model.  
*Lessons:* L8.4

**Primacy effect** — Initial resistance to change that fades as users adapt.  
*Lessons:* L4.1

**Primary metric** — The single pre-registered outcome that decides a test.  
*Lessons:* L4.1

**Prior** — Probability distribution expressing belief about a parameter before seeing the data.  
*Watch out:* State and justify in advance; show sensitivity.  *Lessons:* L4.3

**Projection** — Closest point in a subspace; least squares projects y onto the predictors' columns.  
*Watch out:* Residuals are orthogonal to every predictor.  *Lessons:* L2.7, L5.1

**Promotion ROI** — Incremental margin ÷ promotion cost (discount given away).  
*Lessons:* L8.4

**Prompt card** — Weak, better and expert versions of a request to Claude Code, with what to verify.  
*Lessons:* L0.2

**Propensity score** — Probability of treatment given covariates; used to match or weight comparable units.  
*Lessons:* L9.1

**Proxy variable** — A feature that carries information about a protected attribute.  
*Lessons:* L9.5

**Pseudo-replication** — Treating repeated, correlated rows (lines in baskets, months in accounts) as independent observations.  
*Watch out:* Gives falsely small p-values and narrow intervals.  *Lessons:* L3.2, L3.3

**Pseudo-R²** — Fit measure for logistic models (e.g. McFadden); not comparable with OLS R².  
*Typical range:* 0.2–0.4 considered good  *Lessons:* L5.3

**Pseudonymisation** — Replacing identifiers with codes (e.g. salted hashes); reversible with a key.  
*Watch out:* Still personal data in most laws.  *Lessons:* L0.5

**PSI (population stability index)** · `PSI` — Measure of shift between two distributions (e.g. score at build vs now).  
*Typical range:* < 0.10 stable · 0.10–0.25 investigate · > 0.25 significant (rule of thumb)  *Lessons:* L9.6

**Pure premium** — Expected claims cost per unit of exposure: frequency × severity.  
*Lessons:* L5.5, L9.4

**Pyramid principle** — Structure that leads with the answer, then supporting points, then evidence.  
*Lessons:* L9.7

## Q

**Q-Q plot** — Plot of data quantiles against a reference distribution's quantiles.  
*Typical use:* Checking normality or a fitted distribution.  *Lessons:* L1.5

**Quantile regression** — Regression for a chosen percentile of the outcome rather than its mean.  
*Lessons:* L5.5

## R

**Random forest** — Average of many trees trained on bootstrap samples with random feature subsets.  
*Lessons:* L6.2

**Random intercept** — A group-specific baseline drawn from a common distribution, estimated with shrinkage.  
*Lessons:* L5.6

**Randomisation** — Assigning units to groups by chance so groups are comparable on average.  
*Lessons:* L3.4, L4.1

**Range** — Maximum minus minimum.  
*Watch out:* Determined by two extreme values.  *Lessons:* L1.4

**Rate ratio** — Multiplicative change in an event rate per unit of a predictor (exp of a log-link coefficient).  
*Lessons:* L5.5

**Reason codes** — Top factors behind an individual credit decision (adverse-action reasons).  
*Lessons:* L6.7, L8.7

**Recalibration** — Adjusting a model's intercept/slope so predicted rates match observed rates.  
*Lessons:* L9.6

**Recall** — Share of actual positives the model flags: TP ÷ (TP + FN).  
*Lessons:* L6.6

**Recipe (toolkit)** — A tested, documented, configuration-driven analysis that asks for roles, not column names.  
*Lessons:* L0.4

**Recurrent neural network** — Network that processes sequences step by step with a memory (LSTM, GRU).  
*Lessons:* L9.8

**Regression check** — Re-running an analysis after a change to confirm original results are unchanged.  
*Lessons:* L0.4

**Regression discontinuity** — Comparing units just above and below an eligibility cut-off.  
*Lessons:* L9.1

**Reject inference** — Methods for the unobserved outcomes of declined applicants.  
*Lessons:* L8.7

**Relative risk** · `RR` — Ratio of event rates between two groups.  
*Watch out:* Always quote with the base rate.  *Lessons:* L3.4

**Reorder point** — Stock level that triggers an order: mean lead-time demand + safety stock.  
*Lessons:* L7.6

**Reproducibility** — Getting identical results from the same data, code, config and seed.  
*Lessons:* L0.1, L0.4

**Residual** — Observed minus fitted value.  
*Lessons:* L5.2

**Restricted mean survival time** — Area under the survival curve up to a horizon; average time survived within it.  
*Lessons:* L9.2

**Retrieval-augmented generation** — Giving an LLM retrieved documents so answers are grounded and citable.  
*Lessons:* L9.3

**RFM** — Recency, frequency, monetary scoring of customers.  
*Lessons:* L8.2

**Ridge regression** · `L2` — Regression with a penalty on squared coefficients; shrinks all toward zero.  
*Lessons:* L5.4

**Risk difference** — Difference in event rates, usually in percentage points.  
*Typical use:* Extra events per 100 or 1,000.  *Lessons:* L3.4

**RLHF** — Reinforcement learning from human feedback: optimising a model toward answers people prefer.  
*Lessons:* L9.8

**RMSE** — Root mean squared error: typical prediction error in outcome units.  
*Lessons:* L5.1, L7.3

**Robust standard errors** · `HC3` — Standard errors valid under unequal variance (heteroscedasticity-consistent).  
*Lessons:* L5.2

**Robust z-score** — 0.6745 × (x − median) ÷ MAD.  
*Typical use:* Outlier flagging in skewed data.  *Typical range:* |z| > 3.5 common threshold  *Lessons:* L1.6

**Robust z-score** — (x − median) ÷ (1.4826 × MAD); not masked by the outliers it hunts.  
*Lessons:* L8.5

**Roll rate** — Share of balances moving from one delinquency bucket to the next.  
*Lessons:* L8.7

**Rolling-origin backtest** — Re-fitting and forecasting from several successive origins to evaluate a method.  
*Lessons:* L7.3

**Row accounting** — Record of rows in, removed at each step and why, and rows analysed.  
*Lessons:* L0.2, L0.4

## S

**Safety stock** — Extra stock held to cover demand variability over the lead time: z × σ × √L.  
*Lessons:* L7.6

**Sample ratio mismatch** · `SRM` — Observed group sizes differ from the planned split by more than chance.  
*Watch out:* Signals broken assignment or logging; do not trust the results.  *Lessons:* L4.1

**Sampling distribution** — Distribution of a statistic across repeated samples.  
*Typical use:* Basis of standard errors and intervals.  *Lessons:* L2.5, L3.1

**SARIMAX** — Seasonal ARIMA with external regressors.  
*Lessons:* L7.2

**SBA** — Syntetos-Boylan approximation: bias-corrected Croston.  
*Lessons:* L7.4

**Schema check** — Verifying that a dataset has the columns, types and grain a recipe needs.  
*Lessons:* L0.4

**Seasonal naive forecast** — Forecast equal to the value in the same period last season.  
*Lessons:* L7.2, L7.3

**Seasonality** — Regular repeating pattern tied to the calendar (week, year, holidays).  
*Lessons:* L7.1

**Selection bias** — Systematic difference between the units observed and the population of interest.  
*Typical use:* Booked-only credit data, loyalty members.  *Lessons:* L2.4

**Selection bias (collider)** — Bias from analysing only units selected on variables related to the outcome (approved, retained).  
*Lessons:* L4.4, L8.7

**Self-selection** — Units choosing their treatment for reasons related to the outcome.  
*Lessons:* L9.1

**Sequential testing** — Planned interim analyses with boundaries that keep the overall false-positive rate at α.  
*Lessons:* L4.2

**SHAP values** — Additive per-feature contributions to an individual prediction (Shapley values).  
*Lessons:* L6.7

**Shapiro-Wilk test** — Test of normality.  
*Watch out:* Rejects trivially at large n; look at Q-Q plots.  *Lessons:* L3.4

**Shrinkage** — Pulling noisy small-group estimates toward a broader average.  
*Typical use:* New segments, small branches.  *Lessons:* L4.3, L5.6

**Silhouette score** — How much closer a point is to its own cluster than the next one; −1 to 1, above 0.5 is strong.  
*Lessons:* L8.1

**Simple random sample** · `SRS` — Every unit has the same chance of selection.  
*Lessons:* L2.4

**Simpson's paradox** — A trend in aggregated data reverses within subgroups.  
*Lessons:* L2.4

**Skewness** — Asymmetry of a distribution; positive = long right tail.  
*Typical range:* |skew| > 1 notably skewed (rule of thumb)  *Lessons:* L1.4

**SMOTE** — Synthetic minority over-sampling: creates synthetic rare-class points between neighbours.  
*Watch out:* Only inside training folds.  *Lessons:* L6.5

**Spearman correlation** · `ρ` — Correlation of ranks; captures monotone relationships.  
*Lessons:* L1.7

**Specificity** — Share of actual negatives correctly not flagged: TN ÷ (TN + FP).  
*Lessons:* L6.6

**Spline** — Flexible smooth curve built from pieces joined at knots.  
*Lessons:* L5.6

**Stacking** — Combining models with a meta-model trained on their out-of-fold predictions.  
*Lessons:* L6.3

**Standard deviation** · `SD, s` — Typical distance from the mean (square root of the variance, n − 1 denominator).  
*Watch out:* Misleading for skewed amounts.  *Lessons:* L1.4

**Standard error** · `SE` — Standard deviation of an estimate across repeated samples.  
*Typical use:* Builds CIs and test statistics.  *Lessons:* L2.5, L3.4

**Standardisation** — Rescaling to mean 0 and SD 1 (z-scores).  
*Typical use:* Distance-based and penalised methods.  *Lessons:* L1.6

**Standardised mean difference** · `SMD` — Difference in group means divided by the pooled SD; used to check balance.  
*Typical range:* < 0.1 good balance (rule of thumb)  *Lessons:* L4.5, L9.1

**Standardised residual** — (observed − expected) ÷ √expected for a table cell.  
*Typical range:* |r| > 2 marks cells that drive an association  *Lessons:* L3.5

**Stationarity** — Constant mean, variance and autocorrelation over time.  
*Lessons:* L7.1

**Statistical significance** — p below the chosen α.  
*Watch out:* Says nothing about size or importance.  *Lessons:* L3.3

**STL decomposition** — Seasonal-Trend decomposition using Loess: splits a series into trend, seasonal and remainder.  
*Lessons:* L7.1

**Stratified randomisation** — Randomising within strata (format, risk band) so arms are balanced on them.  
*Lessons:* L4.1

**Stratified sampling** — Sampling separately within groups (strata).  
*Typical use:* Guaranteeing small subgroups; reducing variance when strata differ.  *Lessons:* L2.4

**Stress test** — Estimating outcomes under a specified severe scenario.  
*Lessons:* L9.4

**Structural missingness** — A field that does not apply to some rows (utilisation for loans).  
*Watch out:* Treat as not applicable, not as missing.  *Lessons:* L1.3

**Structuring** — Keeping transactions just under a reporting threshold to avoid reporting.  
*Lessons:* L8.6

**Supervised fine-tuning** — Training a pre-trained model on example prompts and ideal answers.  
*Lessons:* L9.8

**Support** — Share of baskets containing an itemset.  
*Lessons:* L8.3

**Support vector machine** — Finds the boundary with the widest margin; kernels allow curved boundaries.  
*Lessons:* L6.3, L6.8

**Survivorship bias** — Drawing conclusions only from units that 'survived' a selection process.  
*Lessons:* L2.4

**SVD** — Singular value decomposition: factorising a matrix into directions ordered by importance.  
*Typical use:* PCA, recommendations, compression.  *Lessons:* L2.7, L8.1

**SVM** — Support vector machine: classifier that maximises the margin between classes, optionally with kernels.  
*Lessons:* L6.3

**Synthetic control** — A weighted combination of untreated units built to track one treated unit before treatment.  
*Lessons:* L9.1

**Systematic sampling** — Selecting every k-th unit from an ordered list.  
*Watch out:* Biased if the list has a cycle of length k.  *Lessons:* L2.4

## T

**t distribution** — Like the normal but heavier-tailed; used when the SD is estimated.  
*Typical range:* 95% critical 2.57 at df 5 vs 1.96 normal  *Lessons:* L2.3, L3.1

**Target encoding** — Replacing each category with the average outcome for that category.  
*Watch out:* Leaks the label unless fitted out-of-fold.  *Lessons:* L1.6

**Test statistic** — Number measuring how far the data are from H0, usually in standard-error units.  
*Lessons:* L3.3

**Threshold moving** — Choosing a decision cut-off other than 0.5, from costs or capacity.  
*Lessons:* L6.5, L6.6

**Tidy data** — One row per observation, one column per variable, one table per unit type.  
*Lessons:* L1.1

**Total effect** — Effect of a treatment including all paths (direct and via mediators).  
*Lessons:* L4.4

**Transfer learning** — Starting from a model pretrained on millions of images and fine-tuning it for your task.  
*Lessons:* L11.2

**Transfer test** — Applying the toolkit to an unseen dataset in a new domain using configuration only.  
*Lessons:* L10.1

**Transformer** — Neural architecture using attention; the basis of modern LLMs.  
*Lessons:* L9.3

**Trimmed mean** — Mean after removing a fixed share of the smallest and largest values.  
*Lessons:* L1.4

**Tukey fences** — Q1 − k·IQR and Q3 + k·IQR (k = 1.5 or 3).  
*Watch out:* k = 1.5 over-flags skewed data.  *Lessons:* L1.6

**Tweedie regression** — GLM for outcomes with many zeros plus positive continuous values.  
*Lessons:* L5.5

**Two-proportion z-test** — Test comparing two rates.  
*Typical use:* Default rate, conversion rate.  *Watch out:* Use Fisher if expected cells < 5.  *Lessons:* L3.4

**Two-way fixed effects** — Regression with unit and time effects, removing fixed differences between units and common shocks.  
*Lessons:* L9.1

**Type I error** — Declaring an effect that is not there (false positive).  
*Lessons:* L3.3

**Type II error** — Missing an effect that is there (false negative).  
*Lessons:* L3.3

## U

**Unit of analysis** — The entity each observation in a test represents.  
*Watch out:* Must match the unit of randomisation.  *Lessons:* L3.4

**Unit of randomisation** — The entity assigned to treatment or control (user, customer, store, agent team).  
*Watch out:* Analyse at this unit.  *Lessons:* L4.1

**Uplift model** — Model predicting the change in outcome caused by treatment for each customer.  
*Lessons:* L9.1

## V

**Validation report** — Row count, schema, grain, coverage, completeness, validity and reconciliation checks for a dataset.  
*Lessons:* L0.3

**Value at Risk** — Loss not exceeded with a given probability over a horizon (e.g. 99.5%, one year).  
*Lessons:* L9.4

**Vasicek model** — One-factor credit model where defaults correlate through a common economic factor.  
*Lessons:* L9.4

**Vibe coding** — Doing analysis by instructing an AI assistant in plain English, then verifying its work.  
*Lessons:* L0.2

**VIF (variance inflation factor)** · `VIF` — How much a coefficient's variance is inflated by correlation with other predictors.  
*Typical range:* > 5 (or 10) signals problematic collinearity  *Lessons:* L5.2

**Vintage curve** — Cumulative bad rate of a cohort by months on book.  
*Lessons:* L8.7

**Violin plot** — Box plot combined with a density shape.  
*Lessons:* L1.5

## W

**Wald interval** — Proportion ± 1.96 × √(p(1 − p)/n).  
*Watch out:* Fails for rare events and small n (can give 0–0).  *Lessons:* L3.1

**WAPE** — Weighted absolute percentage error: Σ|error| ÷ Σ actual.  
*Lessons:* L7.3

**Weibull distribution** — Time-to-event distribution whose hazard can rise, fall or stay constant (shape k).  
*Typical range:* k < 1 falling risk; k = 1 exponential; k > 1 rising  *Lessons:* L2.3, L7.4

**Weight of evidence** — ln(% of goods ÷ % of bads) in a bin.  
*Lessons:* L8.7

**Welch ANOVA** — ANOVA that does not assume equal variances.  
*Typical use:* Default for comparing means across groups.  *Lessons:* L3.5

**Welch's t-test** — Two-sample test of means that does not assume equal variances.  
*Typical use:* Default two-group test for continuous outcomes.  *Lessons:* L3.4

**Wilson interval** — A confidence interval for a proportion with good coverage even for rare events.  
*Typical use:* Default for rates.  *Lessons:* L3.1

**Winner's curse** — Effects that were selected for being large (or stopped early) tend to be overestimates.  
*Lessons:* L4.2, L4.3

**Winsorising** — Replacing values beyond chosen percentiles with those percentiles.  
*Lessons:* L1.6

## X

**XYZ classification** — Ranking items by demand variability (X stable, Z erratic).  
*Lessons:* L7.6
