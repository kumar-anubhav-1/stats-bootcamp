# Scenario atlas

44 realistic situations mapped to the Navigator. Click a node to open it in the interactive map.

| # | Industry | Situation | Navigator path | Lesson |
| --- | --- | --- | --- | --- |
| S01 | Retail | Did the store-level Hair Care feature promotion lift sales? | [`N-EXP-SRM`](index.md#N-EXP-SRM) → [`N-TEST-2G-MEAN`](index.md#N-TEST-2G-MEAN) | L3.4 |
| S02 | Retail | Promotion looks harmful overall but helpful in every store format | [`N-DESC-STRATIFY`](index.md#N-DESC-STRATIFY) | L2.4 |
| S03 | Retail | Average basket jumped because of a few bulk buyers | [`N-DESC-SKEW`](index.md#N-DESC-SKEW) → [`N-DESC-OUTLIER`](index.md#N-DESC-OUTLIER) | L1.4 |
| S04 | Retail | Which of four regions has a different basket value? | [`N-TEST-KG`](index.md#N-TEST-KG) | L3.5 |
| S05 | Retail | Is promo uptake independent of loyalty tier? | [`N-TEST-CHI`](index.md#N-TEST-CHI) | L3.5 |
| S06 | Retail | Display and promotion always run together — what drove sales? | [`N-CAUSAL-DAG`](index.md#N-CAUSAL-DAG) | L4.4 |
| S07 | Retail | How price-sensitive is the Snacks category? | [`N-REG-LOGLOG`](index.md#N-REG-LOGLOG) | L8.4 |
| S08 | Retail | Promo on the 400 ml shampoo; the 200 ml fell | [`N-OPT-PROMO`](index.md#N-OPT-PROMO) | L8.4 |
| S09 | Retail | Forecast weekly category sales for the next 13 weeks | [`N-FCST-SEASON`](index.md#N-FCST-SEASON) → [`N-METRIC-REG`](index.md#N-METRIC-REG) | L7.2 |
| S10 | Retail | Long-tail SKUs sell zero most weeks | [`N-FCST-INTERMITTENT`](index.md#N-FCST-INTERMITTENT) | L7.4 |
| S11 | Retail | One store's sales stepped down mid-year | [`N-FCST-BREAK`](index.md#N-FCST-BREAK) | L7.5 |
| S12 | Retail | Lost sales during stockouts | [`N-FCST-CENSOR`](index.md#N-FCST-CENSOR) → [`N-OPT-INVENTORY`](index.md#N-OPT-INVENTORY) | L7.5 |
| S13 | Retail | Which SKUs deserve deeper stock? | [`N-OPT-INVENTORY`](index.md#N-OPT-INVENTORY) | L7.6 |
| S14 | Retail | Segment loyalty customers for CRM | [`N-SEG-RFM`](index.md#N-SEG-RFM) → [`N-CLUST-KMEANS`](index.md#N-CLUST-KMEANS) | L8.1 |
| S15 | Retail | What sells with what? | [`N-SEG-BASKET`](index.md#N-SEG-BASKET) | L8.3 |
| S16 | Retail | A group of customers returns 40% of what they buy | [`N-ANOM-MULTI`](index.md#N-ANOM-MULTI) | L8.5 |
| S17 | Retail | One store's numbers look too neat | [`N-ANOM-BENFORD`](index.md#N-ANOM-BENFORD) | L2.6 |
| S18 | Retail | Loyalty members spend more — is the programme causing it? | [`N-CAUSAL-DAG`](index.md#N-CAUSAL-DAG) → [`N-CAUSAL-PSM`](index.md#N-CAUSAL-PSM) | L9.1 |
| S19 | Retail | 'Delisted SKUs never mattered' analysis | [`N-DESC-BIAS`](index.md#N-DESC-BIAS) | L2.4 |
| S20 | Retail | How to split marketing budget across media | [`N-OPT-MC`](index.md#N-OPT-MC) | L8.4 |
| S21 | Retail | How many stores for the next promo test? | [`N-EXP-POWER`](index.md#N-EXP-POWER) → [`N-EXP-CUPED`](index.md#N-EXP-CUPED) | L3.6 |
| S22 | Retail | Daily dashboard: did this week's dip matter? | [`N-FCST-BREAK`](index.md#N-FCST-BREAK) → [`N-EXP-SEQ`](index.md#N-EXP-SEQ) | L7.5 |
| S23 | Finance | Is the default rate different for unverified-income customers? | [`N-TEST-2G-PROP`](index.md#N-TEST-2G-PROP) → [`N-DESC-STRATIFY`](index.md#N-DESC-STRATIFY) | L3.4 |
| S24 | Finance | Build an application scorecard | [`N-ML-SCORECARD`](index.md#N-ML-SCORECARD) → [`N-METRIC-CLASS`](index.md#N-METRIC-CLASS) → [`N-METRIC-CALIB`](index.md#N-METRIC-CALIB) | L8.7 |
| S25 | Finance | Gradient boosting beats the scorecard by 3 Gini points | [`N-ML-GBM`](index.md#N-ML-GBM) → [`N-MON-FAIR`](index.md#N-MON-FAIR) | L6.7 |
| S26 | Finance | Model AUC is 0.98 on day one | [`N-ML-LEAK`](index.md#N-ML-LEAK) | L6.4 |
| S27 | Finance | Fraud is 0.7% and the model is '99% accurate' | [`N-ML-IMBALANCE`](index.md#N-ML-IMBALANCE) → [`N-METRIC-RARE`](index.md#N-METRIC-RARE) | L6.5 |
| S28 | Finance | Where to set the fraud alert threshold? | [`N-METRIC-COST`](index.md#N-METRIC-COST) | L6.6 |
| S29 | Finance | Accounts share devices and addresses | [`N-ANOM-GRAPH`](index.md#N-ANOM-GRAPH) | L8.6 |
| S30 | Finance | Cash deposits cluster just under the reporting limit | [`N-ANOM-STRUCT`](index.md#N-ANOM-STRUCT) | L8.6 |
| S31 | Finance | The latest vintage defaults more | [`N-MON-PSI`](index.md#N-MON-PSI) → [`N-MON-CONCEPT`](index.md#N-MON-CONCEPT) | L9.6 |
| S32 | Finance | PSI is stable but AUC dropped | [`N-MON-CONCEPT`](index.md#N-MON-CONCEPT) | L9.6 |
| S33 | Finance | Income is missing more often for risky applicants | [`N-DESC-MISSING`](index.md#N-DESC-MISSING) | L1.3 |
| S34 | Finance | Risk jumps above 80% utilisation; young customers with high DTI look worse | [`N-REG-NONLINEAR`](index.md#N-REG-NONLINEAR) → [`N-REG-INTERACT`](index.md#N-REG-INTERACT) | L5.6 |
| S35 | Finance | Income and limit both in the model; signs flip | [`N-REG-VIF`](index.md#N-REG-VIF) | L5.2 |
| S36 | Finance | Approval rates differ by group; region looks innocent | [`N-MON-FAIR`](index.md#N-MON-FAIR) | L9.5 |
| S37 | Finance | When do customers churn? | [`N-TEST-SURV`](index.md#N-TEST-SURV) → [`N-DIST-TIME`](index.md#N-DIST-TIME) | L9.2 |
| S38 | Finance | Champion vs challenger collections strategy | [`N-EXP-SRM`](index.md#N-EXP-SRM) → [`N-TEST-2G-PROP`](index.md#N-TEST-2G-PROP) | L4.5 |
| S39 | Finance | Expected loss for a portfolio | [`N-OPT-MC`](index.md#N-OPT-MC) | L8.7 |
| S40 | Finance | Claims frequency and severity pricing | [`N-REG-GLM-INS`](index.md#N-REG-GLM-INS) | L9.4 |
| S41 | Finance | 1-day 99% VaR for a card book | [`N-OPT-MC`](index.md#N-OPT-MC) | L9.4 |
| S42 | Finance | Is an audit sample of 50 files enough? | [`N-DIST-HYPER`](index.md#N-DIST-HYPER) | L2.2 |
| S43 | Both | A junior ran 40 segment tests and found 3 'wins' | [`N-TEST-MULTI`](index.md#N-TEST-MULTI) | L3.7 |
| S44 | Both | Claude Code reports a number you cannot reproduce | [`N-DESC-PROFILE`](index.md#N-DESC-PROFILE) | L0.2 |
