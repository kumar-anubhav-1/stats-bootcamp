# More mental maps

## Causal inference

```mermaid
flowchart LR
  Q{Can you assign the treatment?} -->|yes| RCT[Randomised test: A/B, store test<br/>check SRM, CUPED, power]
  Q -->|no| D[Draw the DAG: confounders, mediators, colliders]
  D --> P{Data available?}
  P -->|treated & control, before & after| DID[Difference-in-differences<br/>check parallel pre-trends]
  P -->|eligibility by a score cut-off| RDD[Regression discontinuity]
  P -->|one treated unit, many donors| SC[Synthetic control]
  P -->|rich pre-treatment covariates| PSM[Matching / propensity weighting<br/>assumes no hidden confounders]
  P -->|units observed before and after opting in| FE[Within-unit fixed effects]
  RCT --> UP[Uplift model: whom to target]
```

| Design | Retail example | Finance example |
| --- | --- | --- |
| Randomised test | e-coupon A/B; Hair Care store test | champion/challenger collections strategy |
| DiD | promotion in 20 test stores vs 20 controls | new branch process in one region |
| Fixed effects | loyalty joiners before vs after joining | customers before/after a limit increase |
| RDD | free delivery above a basket threshold | limit increase above score 650 |
| Synthetic control | one city's new pricing | one country's regulation change |
| Uplift | whom to send a retention coupon | whom to offer a hardship plan |

## Forecasting

```mermaid
flowchart LR
  F{What are you forecasting?} --> CL{Demand pattern?}
  CL -->|smooth, seasonal| SE[Seasonal naive baseline → ETS / SARIMA]
  CL -->|driven by price, promo, weather| DR[Regression with lags · ARIMAX · GBM with calendar features]
  CL -->|many zeros, lumpy| IN[Croston / SBA · judge with MASE]
  F --> H{Many related series?}
  H -->|SKU → category → chain| HI[Hierarchical reconciliation]
  F --> BR{Sudden level change?}
  BR -->|yes| CP[Change-point detection, refit after the break]
  F --> ST{Stock-outs?}
  ST -->|yes| CE[Treat sales as censored demand]
  SE & DR & IN --> BT[Rolling-origin backtest vs baseline] --> INV[Safety stock, reorder point, newsvendor]
```

## Segment and detect

```mermaid
flowchart LR
  S{Goal?} -->|group similar customers| K[K-means / GMM / DBSCAN → profile and size segments]
  S -->|score customer value| R[RFM · CLV · cohorts]
  S -->|what sells together| B[Market basket: support, confidence, lift]
  S -->|find the unusual| A{Labels available?}
  A -->|no| UN[Robust z · Isolation Forest · LOF]
  A -->|yes| SUP[Supervised fraud model + PR-AUC]
  A -->|linked entities| GR[Graph components: fraud rings]
  A -->|amounts near a threshold| BU[Bunching: structuring]
  A -->|digits of reported numbers| BF[Benford + peer comparison]
  S -->|credit risk| CR[WoE/IV scorecard · PD × LGD × EAD · vintages · roll rates]
```

## Which metric?

```mermaid
flowchart LR
  M{Model output} -->|probability, ranking| AUC[AUC / Gini, KS, lift by decile]
  M -->|rare positives, fixed review team| PR[Precision@k, PR-AUC, recall at capacity]
  M -->|probabilities used as numbers| CAL[Calibration curve, Brier score]
  M -->|decision with costs| COST[Expected-cost threshold]
  M -->|a number| REG[MAE, RMSE, WAPE]
  M -->|a forecast| FC[MASE vs seasonal naive, bias]
```

## Monitoring and governance

```mermaid
flowchart LR
  D[Monthly monitoring] --> I[Inputs: PSI / CSI, missingness, units]
  D --> P[Performance: AUC, calibration on matured cohorts]
  D --> F[Fairness: approval ratio, error rates by group]
  I -->|median ×100, new codes| BUG[Data incident → fix pipeline]
  I -->|PSI high, AUC stable| RECAL[Recalibrate]
  P -->|AUC falling| REB[Rebuild with recent data]
  F -->|ratio below 0.8 or proxy found| REV[Review features with legal]
```

## Linear algebra under the hood

```mermaid
flowchart LR
  V[Vectors: one customer's features] --> MX[Matrices: the dataset, a transformation]
  MX --> MM[Multiplication: every model's forward pass]
  MX --> TI[Transpose, inverse, determinant: solving equations]
  TI --> LS[Least squares: x̂ = AᵀA⁻¹Aᵀb — linear regression]
  MX --> EV[Eigenvalues: collinearity, PCA directions]
  EV --> SVD[SVD: PCA, recommender systems, compression]
  MM --> NN[Neural networks and transformers]
```

Rotate and stretch matrices yourself: [matrix transformation explorer](../day-02/L2-7.md).
