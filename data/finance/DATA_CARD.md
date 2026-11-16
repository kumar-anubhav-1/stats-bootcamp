# Data card: Meridian Bank (synthetic retail lending and cards)

**Purpose:** teaching data for the Statistics for Data Science bootcamp. **Fully synthetic.**

**How it was made:** seeded simulation (seed 20261115). Applications are scored by the bank's (old) application scorecard and
decided; booked accounts get a latent risk that drives collections entry, cure, default, churn and fraud. The monthly panel is
built from the same event timeline, so vintage curves, roll rates and survival analysis reconcile with account labels.

**Tables:** accounts (25,000) · performance_monthly (~450,000, parquet only) · applications_declined (~5,200) ·
devices_addresses · policies (8,000) · claims.

**Period:** originations 2023-01 to 2025-09; snapshot 2026-10-31. **Currency:** neutral "units".

**Labels:** default_12m = 90+ DPD within 12 months (base rate 4.0%); fraud_flag (0.7%); churn with censoring.

**Fairness:** `protected_group` exists only so learners can measure disparate impact. It must never be used as a model input.

**Leakage warning:** some fields are only known after the outcome. Identifying them is an exercise.

**Variants:** `variants/accounts_renamed`.
