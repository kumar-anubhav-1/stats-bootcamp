# Data card: NorthStar Markets (synthetic CPG/retail)

**Purpose:** teaching data for the Statistics for Data Science bootcamp. **Fully synthetic**; no real customer, store or product.

**How it was made:** a seeded simulation (`python -m datagen.generate`, seed 20261115). A latent store x SKU x week demand model
(seasonality, holidays, price elasticity, promotions, displays, stockouts, a store-level experiment, delisting) drives both the
full-chain weekly tables and a customer panel of exactly 25,000 transaction lines sampled basket by basket.

**Tables:** transactions (25,000) · products (390) + products_archive (30) · stores (40) · customers (1,500) · calendar (728 days) ·
weekly_store · weekly_store_category · weekly_region_category · weekly_sku_chain · price_elasticity_extract · ecoupon_ab.

**Period:** 104 weeks from 2024-11-04. **Currency:** neutral "units".

**Intended use:** descriptive statistics, data quality, testing, experiments, regression, ML, forecasting, segmentation, anomaly
detection, pricing and promotion analytics. **Not for:** benchmarking real retailers.

**Known issues:** the data deliberately contains realistic data-quality problems and analytical traps. Finding them is part of
the course (Anomaly Hunt). Do not "clean" silently: document every rule and the rows it affects.

**Variants (reuse drills):** `variants/transactions_renamed`, `transactions_weekly`, `transactions_cents`, `transactions_period2`.
