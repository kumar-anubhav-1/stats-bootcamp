# 03. Datasets and Anomaly Register

All data is synthetic and seeded (seed `20261115`). Magnitudes below are **planted design parameters**. In Step 2 the generator is run, the observed values are measured, and the register is updated with the measured value and tolerance band; CI fails if any measured value leaves its band.

## 1. Generator design (instructor area)

- **Latent-process simulation, not random columns.** Customers, stores and SKUs get latent traits (price sensitivity, segment, risk). Demand is simulated weekly per store × SKU from baseline × seasonality × price effect × promo/display effects × noise; transaction lines are then sampled from that demand. Credit outcomes come from a latent PD built from a known logistic formula (incl. the planted non-linearity and interaction). This is what makes elasticities, lifts and odds ratios recoverable with known true values.
- **Two outputs per dataset:** the learner files (`data/retail/*.parquet` + `.csv`) and an instructor truth pack (`instructor/truth/*.parquet`: true demand under stockouts, true lift, true segment labels, true PD, anomaly row ids).
- **Variants for reuse drills:** `--variant renamed` (all columns renamed, e.g. `qty`→`units_sold`), `--variant weekly` (store-SKU-week grain), `--variant period2` (a later 52 weeks), `--variant units` (prices in cents). Same truths, different shape.
- **Held-out exam data:** seeds `7001` (retail) and `7002` (finance), same schema, 10 new planted issues with shifted magnitudes and locations.
- **Transfer-test data (Day 10):** seed `9001`, a third domain: **quick-commerce delivery orders** (≈20K rows), different column names, two planted issues.
- Runtime target: < 60 s on a laptop; files < 30 MB total.

## 2. Dataset 1: CPG/Retail (fictional grocery/FMCG chain "NorthStar Markets")

### Tables and row counts

| Table | Grain | Rows |
| --- | --- | --- |
| `transactions` (fact) | one transaction line | **25,000** (± 0; generator trims to exactly 25,000 after planting duplicates) |
| `products` | SKU | 420 (incl. 30 delisted) |
| `stores` | store | 40 |
| `customers` | customer | ≈ 6,000 (≈ 65% loyalty members; non-members carry an anonymous id per basket) |
| `calendar` | day | 728 (104 weeks) |
| `weekly_region_category` (derived, for forecasting) | region × category × week | 4 × 12 × 104 = 4,992 |
| `ecoupon_ab` (online A/B test) | customer assignment | ≈ 4,000 |

### `transactions` fields

| Field | Type | Notes |
| --- | --- | --- |
| `line_id`, `basket_id`, `transaction_id` | string | line_id unique except planted duplicates |
| `date`, `week` | date, int | week 1–104 |
| `store_id` | string | S001–S040 |
| `channel` | cat | in-store, click-and-collect, delivery |
| `customer_id` | string | blank for non-members' anonymous baskets is *not* used; anonymous ids `A…` |
| `sku`, `category`, `brand`, `pack_size`, `pack_unit` | string/num | 12 categories, ≈ 60 brands |
| `list_price`, `unit_price`, `discount_pct` | num | unit_price = list × (1 − discount) except planted errors |
| `promo_flag`, `promo_type` | bool, cat | none, TPR, multibuy, BOGO, coupon |
| `display_flag` | bool | end-cap or gondola display |
| `quantity` | int | returns are separate lines with `return_flag` = 1 |
| `revenue`, `unit_cost`, `margin` | num | margin = revenue − cost × qty |
| `stockout_flag` | bool | SKU out of stock in that store-week at time of basket |
| `return_flag` | bool | |
| `payment_method` | cat | card, cash, wallet, voucher |
| `temperature_c` | num | daily, by region |
| `holiday_flag` | bool | 9 holiday periods / year |
| `competitor_price_index` | num | 100 = parity |
| `experiment_group` | cat | test / control / none (store-level Hair Care promo test) |

### Dimension fields

- `stores`: store_id, format (hyper, super, express), region (N/S/E/W), city_tier (1–3), size_sqm, open_date, latitude band.
- `customers`: customer_id, loyalty_flag, loyalty_segment (bronze/silver/gold), age_band, household_size, tenure_months, home_store_id, signup_date.
- `products`: sku, category, subcategory, brand, pack_size, pack_unit, list_price, unit_cost, launch_week, delist_week, private_label_flag.
- `calendar`: date, week, month, quarter, year, day_of_week, holiday_flag, holiday_name, payday_flag.

## 3. Dataset 2: Financial (fictional retail bank "Meridian Bank")

### Tables and row counts

| Table | Grain | Rows |
| --- | --- | --- |
| `accounts` (fact) | one booked customer-account | **25,000** |
| `performance_monthly` | account × month on book (≤ 24) | ≈ 400,000 |
| `applications_declined` | declined application (no performance) | ≈ 4,000 |
| `devices_addresses` | account × device / address link | ≈ 31,000 |
| `policies` (optional insurance) | policy-year | 8,000 |
| `claims` (optional insurance) | claim | ≈ 1,100 |

### `accounts` fields

| Field | Type | Notes |
| --- | --- | --- |
| `customer_id`, `account_id` | string | |
| `age`, `income_annual`, `employment_type`, `region`, `tenure_months_with_bank` | mixed | employment: salaried, self-employed, contract, retired, student |
| `product_type` | cat | personal_loan, credit_card |
| `limit_or_loan_amount`, `interest_rate`, `term_months` | num | term blank for cards |
| `utilisation` | num 0–1.2 | cards; loans use balance/original |
| `dti` | num | debt-to-income |
| `bureau_score` | int 300–900 | |
| `inquiries_6m`, `delinq_2y`, `balance_current` | num | |
| `txn_count_3m`, `txn_amount_3m` | num | |
| `digital_share`, `branch_visits_6m` | num | channel usage |
| `complaints_12m` | int | |
| `origination_date`, `vintage` | date, string | vintages 2023Q1–2025Q4 |
| `income_verified_flag` | bool | |
| `default_12m` | bool | 90+ DPD within 12 months |
| `max_dpd_12m` | int | |
| `churn_flag`, `churn_month` | bool, int | for survival; censored if no churn by panel end |
| `fraud_flag` | bool | confirmed fraud |
| `protected_group` | cat A/B | for fairness checks only; never a model input |
| `strategy_group` | cat | champion / challenger (collections) |
| `collections_flag`, `recovery_amount` | | **leakage trap**: populated after default |
| `branch_id` | string | |

### `performance_monthly` fields

account_id, month_on_book, calendar_month, balance, payment, minimum_due, dpd, delinquency_bucket (current, 1–29, 30–59, 60–89, 90+), utilisation, txn_count, txn_amount, cash_deposit_count, cash_deposit_max, status (open, closed, charged-off).

### Insurance (optional)

`policies`: policy_id, customer_id, product (motor, home), exposure_years, sum_insured, driver_age_band, vehicle_group / property_type, region, premium. `claims`: claim_id, policy_id, claim_date, claim_amount, claim_type.

## 4. Anomaly & Phenomena Register (instructor-only answer key)

Columns in the live register (`instructor/anomaly_register.yaml`): id, description, location (table, filter, row ids file), planted magnitude, measured magnitude, tolerance, lesson that finds it, detection method, expected finding, Anomaly Hunt hint.

### Retail (24)

| ID | Phenomenon | Where | Planted magnitude | Found in | Expected finding |
| --- | --- | --- | --- | --- | --- |
| R01 | Negative quantity entry errors (not returns) | transactions, `return_flag`=0 | 40 lines | L1.2 | Flag and exclude; not returns |
| R02 | Price off by 100× (decimal shift) | transactions | 25 lines, unit_price = 100 × list | L1.2, L1.6 | Robust z flags; correct or drop; mean basket drops materially |
| R03 | Duplicate lines from re-ingestion | transactions | 150 duplicated line_ids (0.6%) | L1.2 | De-duplicate; revenue overstated by ≈ 0.6% |
| R04 | MCAR missingness | `temperature_c` | 3% random | L1.3 | Missingness unrelated to anything; simple imputation OK |
| R05 | MAR missingness | `age_band` | 18% non-members vs 2% members | L1.3 | Missingness predicted by loyalty_flag; condition on it |
| R06 | MNAR missingness | `household_size` | 35% missing for 5+ households vs 5% | L1.3 | Missing group has larger baskets; flag + sensitivity analysis |
| R07 | Heavy-tailed spend (bulk buyers) | 25 customers | ≈ 12% of revenue; baskets 10–40× median | L1.4, L1.6 | Mean ≫ median; use robust stats; model separately |
| R08 | Store level shift | S017 | −35% revenue from week 61 | L7.5 | Change-point at week 61 ± 1 |
| R09 | Promo experiment true lift | Hair Care, 20 test vs 20 control stores, weeks 70–77 | +12% units | L3.4, L4.5, L9.1 | Lift CI covers 12%; DiD agrees |
| R10 | Cannibalisation | Brand X 400 ml promo → Brand X 200 ml | −20% units of 200 ml during promo | L8.4 | Net uplift ≈ gross − cannibalised units |
| R11 | Seasonality and holidays | all | Fri–Sat +30%; Q4 +25%; holiday weeks +40% | L7.1 | STL shows weekly + annual; holiday regressors significant |
| R12 | Stockouts censoring demand | 4% of SKU-store-weeks | sales capped at stock | L7.5 | Naive forecast biased low ≈ 3–5%; uncensoring fixes |
| R13 | Known price elasticity | Snacks, Dairy | −1.8 and −0.6 | L8.4 | log-log estimate within ± 0.25 |
| R14 | Simpson's paradox | promo lines × store format | Overall promo qty/line lower; within each format +15% | L2.4 | Stratify by format; promo helps |
| R15 | Confounder: display paired with promo | promo lines | display on 92% of promo vs 3% non-promo; true promo +15%, display +10% | L4.4 | Naive promo effect ≈ +26%; cannot separate without design |
| R16 | Survivorship trap: delisted SKUs | 30 SKUs delisted week 52 | omitted from "current" master | L2.4 | Category growth overstated if delisted history dropped |
| R17 | Returns-abuse cluster | 30 customers, 2 stores | return rate ≈ 45% vs 4% base | L8.5 | Isolation Forest/robust z flags cluster |
| R18 | Fabricated/rounded numbers | store S033 | 70% revenues end in .00/.50; first digit non-Benford | L2.6 | Benford MAD > 0.015 (nonconformity) for S033 only |
| R19 | Data drift point | online channel, week 80+ | `discount_pct` logged as fraction (0.2) not percent (20); online share 12%→25% | L1.2, L9.6 | PSI on discount_pct > 0.25; unit fix |
| R20 | Loyalty selection bias | loyalty members | naive spend uplift +35%, true causal +5% | L9.1 | Matching/DiD on pre-period shrinks effect |
| R21 | Basket associations | Pasta↔Sauce, Beer↔Chips | lift ≈ 3.5 and ≈ 2.2 | L8.3 | Rules recovered with stated lift |
| R22 | Intermittent long tail | ≈ 25% of SKUs | ADI > 1.32 | L7.4 | Croston/SBA beats ETS on MASE |
| R23 | Latent customer segments | members | 5 segments | L8.1, L8.2 | K-Means/GMM recovers 4–6 clusters; ARI vs truth ≥ 0.6 |
| R24 | e-coupon A/B with SRM | `ecoupon_ab` | planned 50/50, observed ≈ 52.6/47.4; true conversion 10.0% → 11.5% | L4.1 | SRM χ² p < 0.001 → fix logging; then lift ≈ +1.5 pp |

### Financial (18)

| ID | Phenomenon | Where | Planted magnitude | Found in | Expected finding |
| --- | --- | --- | --- | --- | --- |
| F01 | Impossible values | accounts | 12 ages ≥ 120 or < 18; 20 negative incomes | L1.2 | Rule-based validity checks |
| F02 | Income missing not at random | `income_annual` | 4% overall, ≈ 3× more among high latent risk | L1.3, L8.7 | Missing-income bin has higher default; keep as WoE bin |
| F03 | Rare events & base-rate trap | default, fraud | default ≈ 4.0%; fraud ≈ 0.7% | L2.1, L6.5 | "99% accuracy" is trivial; use PR-AUC |
| F04 | Non-linear utilisation risk | cards | flat < 50%, steep > 80%; > 90% ≈ 4× default of < 50% | L5.6, L8.7 | Splines/WoE bins capture it; linear term misses |
| F05 | Interaction: young × high DTI | age < 25 & DTI > 0.45 | extra odds × 2.5 | L5.6 | Interaction term significant |
| F06 | Multicollinearity | income vs limit | r ≈ 0.85, VIF > 5 | L5.2 | Coefficient signs unstable; combine or regularise |
| F07 | Fraud ring | 45 accounts, 6 devices, 4 addresses | fraud rate ≈ 60% in ring | L8.6 | Graph components recover 3 rings |
| F08 | Structuring | ≈ 120 accounts, perf. panel | cash deposits bunched 9,000–9,999 under 10,000 limit | L8.6 | Histogram bunching; accounts flagged |
| F09 | Benford violation | branch BR07, txn amounts | first-digit MAD > 0.015 | L2.6 | BR07 only fails |
| F10 | Leakage trap | `collections_flag`, `recovery_amount` | AUC ≈ 0.99 when included | L6.4 | Drop post-outcome fields; AUC ≈ 0.75–0.80 |
| F11 | Population drift | vintage 2025Q3–Q4 (digital partner) | score PSI ≈ 0.28 vs 2023 baseline | L9.6 | PSI > 0.25 → investigate mix |
| F12 | Concept drift | latest vintages | utilisation→default slope steeper; AUC −0.06 | L9.6 | Performance decay despite stable CSI on most features |
| F13 | Censoring for survival | churn | ≈ 70% censored at panel end | L9.2 | KM handles censoring; naive mean time-to-churn biased |
| F14 | Heavy-tailed balances | `balance_current` | top 1% hold ≈ 15% of balances | L1.4 | Log scale, quantiles; Lorenz |
| F15 | Proxy for protected attribute | region R4 | 85% group B; disparate impact ≈ 0.72 | L9.5 | Fails 80% rule via proxy |
| F16 | Champion/challenger effect | 30+ DPD accounts, 80/20 split | cure rate 35% → 38% | L4.5 | Lift ≈ +3 pp, CI excludes 0 (power check) |
| F17 | Insurance frequency-severity | policies/claims | frequency over-dispersed (NB); severity Gamma + 3 catastrophic claims | L9.4 | NB beats Poisson; cap/large-loss loading |
| F18 | Reject-inference trap | `applications_declined` | declined have no performance; lower scores | L8.7, L9.6 | Booked-only model under-states risk at low scores |

**Total: 42 planted items.** Anomaly Hunt scoreboard counts these.

## 5. Data dictionaries, data cards, tests

- `data/<domain>/DATA_DICTIONARY.md`: every field with type, unit, allowed values, null policy, description.
- `data/<domain>/DATA_CARD.md`: purpose, synthetic-generation method, intended use, known limitations, seed, version, row counts.
- `datagen/tests/test_anomalies.py`: one test per register id; asserts the planted pattern is detectable by the stated method and that its measured magnitude sits inside the tolerance band. Also schema, row-count and reproducibility tests (same seed ⇒ identical file hashes).
