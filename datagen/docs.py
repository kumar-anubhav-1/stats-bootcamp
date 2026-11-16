"""Write DATA_DICTIONARY.md and DATA_CARD.md for each domain from the generated files.

python -m datagen.docs
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

DESC = {
    "retail": {
        "transactions": {
            "_": "One row per transaction line from the NorthStar customer panel (~1,500 identified shoppers). Returns are separate lines with negative quantity and return_flag = True.",
            "line_id": "Line identifier (should be unique)", "basket_id": "Shopping basket (one visit)",
            "transaction_id": "Payment transaction; returns carry an 'R' suffix and reference the original basket",
            "date": "Transaction date (ISO)", "week": "Week number 1-104 (week 1 starts 2024-11-04)",
            "store_id": "Store code", "format": "Store format: Hyper, Super, Express", "region": "North/South/East/West",
            "city_tier": "1 = metro, 3 = small town", "channel": "in-store, click-and-collect, delivery",
            "customer_id": "Shopper id", "loyalty_flag": "Shopper was a loyalty member at the time of the basket",
            "loyalty_segment": "bronze/silver/gold for members, none otherwise", "age_band": "Shopper age band",
            "household_size": "People in household (self-reported)", "tenure_months": "Months since first relationship",
            "sku": "Product code", "category": "One of 12 categories", "brand": "Brand", "pack_size": "Pack size",
            "pack_unit": "g, ml or unit", "list_price": "Regular shelf price before any discount",
            "unit_price": "Price paid per unit", "discount_pct": "Discount depth in percent (0-100)",
            "promo_flag": "Line was on a price promotion", "promo_type": "none, TPR, multibuy, BOGO, coupon",
            "display_flag": "Product was on secondary display", "quantity": "Units (negative for returns)",
            "revenue": "Line revenue = quantity x unit_price", "unit_cost": "Cost per unit",
            "margin": "revenue - unit_cost x quantity", "stockout_flag": "SKU was out of stock in that store-week (partial availability)",
            "return_flag": "Line is a return", "payment_method": "card, cash, wallet, voucher",
            "temperature_c": "Daily mean temperature in the store's region", "holiday_flag": "Date falls in a holiday week",
            "competitor_price_index": "Competitor price level in region-week (100 = parity)",
            "experiment_group": "For Hair Care lines: the store's arm in the store-level feature-promotion test (test/control); 'none' otherwise",
        },
        "products": {"_": "Current SKU master (active range as of today). Delisted SKUs are in products_archive.",
                     "product_name": "Readable product name", "subcategory": "Subcategory", "private_label_flag": "NorthStar own brand",
                     "long_tail_flag": "Low-volume specialty SKU", "launch_week": "First week on sale", "delist_week": "Week the SKU was delisted (blank if active)"},
        "products_archive": {"_": "SKUs delisted during the period (same columns as products)."},
        "stores": {"_": "Store master.", "size_sqm": "Selling area (m2)", "open_date": "Store opening date",
                   "experiment_group": "Arm in the Hair Care feature-promotion test (weeks 70-77), randomised within format"},
        "customers": {"_": "Shopper master for the panel.", "home_store_id": "Most-visited store", "signup_date": "Loyalty sign-up date (blank for non-members)"},
        "calendar": {"_": "Daily calendar.", "payday_flag": "Day 25-28 of month"},
        "weekly_store": {"_": "Full-chain weekly sales by store (all customers, not just the panel).", "avg_temperature_c": "Weekly mean temperature"},
        "weekly_store_category": {"_": "Full-chain weekly sales by store and category.", "promo_sku_share": "Share of the category's SKUs on promotion",
                                  "stockout_sku_share": "Share of the category's SKUs out of stock"},
        "weekly_region_category": {"_": "Full-chain weekly sales by region and category (forecasting)."},
        "weekly_sku_chain": {"_": "Full-chain weekly sales by SKU (all 40 stores).", "promo_store_count": "Stores running a promotion on the SKU",
                             "display_store_count": "Stores with the SKU on display", "stockout_store_count": "Stores out of stock",
                             "avg_shelf_price": "Simple average shelf price across stores", "avg_unit_price": "Revenue / units"},
        "price_elasticity_extract": {"_": "Store x SKU x week extract for the top-20 Snacks and Dairy SKUs in the North region (pricing work).",
                                     "shelf_price": "Price charged that week"},
        "ecoupon_ab": {"_": "Online e-coupon A/B test: one row per app user logged in the experiment.",
                       "assigned_arm": "control or treatment (planned 50/50)", "app_version": "App version at assignment",
                       "pre_period_spend_30d": "Spend in the 30 days before assignment", "converted_14d": "Purchased within 14 days",
                       "revenue_14d": "Revenue within 14 days"},
    },
    "finance": {
        "accounts": {
            "_": "One row per booked account at Meridian Bank (personal loans and credit cards), originated 2023-01 to 2025-09, observed to 2026-10-31.",
            "income_annual": "Stated annual income", "employment_type": "salaried, self-employed, contract, retired, student",
            "region": "R1-R4", "branch_id": "Booking branch", "acquisition_channel": "branch, online, partner",
            "tenure_months_with_bank": "Months as a bank customer before this account", "product_type": "credit_card or personal_loan",
            "limit_or_loan_amount": "Card limit or loan principal", "interest_rate": "Annual rate (decimal)",
            "term_months": "Loan term (blank for cards)", "utilisation": "Card balance / limit at origination (cards only)",
            "dti": "Debt-to-income ratio", "bureau_score": "Credit bureau score (300-900)", "app_score": "Bank's application score (higher = safer)",
            "inquiries_6m": "Credit inquiries in last 6 months", "delinq_2y": "Delinquencies in last 2 years",
            "balance_current": "Balance at snapshot", "txn_count_3m": "Transactions, last 3 observed months",
            "txn_amount_3m": "Transaction value, last 3 observed months", "digital_share": "Share of interactions via app/web",
            "branch_visits_6m": "Branch visits, last 6 months", "complaints_12m": "Complaints, last 12 months",
            "origination_date": "Account open date", "vintage": "Origination quarter", "income_verified_flag": "Income was documented",
            "default_12m": "Reached 90+ days past due within 12 months of origination", "max_dpd_12m": "Worst days past due in first 12 months",
            "churn_flag": "Account closed by customer before snapshot", "churn_month": "Month on book of closure",
            "months_observed": "Months observed until churn, charge-off or snapshot (survival time)", "fraud_flag": "Confirmed fraud",
            "protected_group": "Protected characteristic (A/B) — for fairness monitoring only, never a model input",
            "strategy_group": "Collections strategy for accounts that reached 30 DPD: champion / challenger (80/20); none otherwise",
            "cured_within_3m": "Collections account returned to current within 3 months",
            "collections_flag": "Account entered collections (recorded after the event)", "recovery_amount": "Amount recovered after charge-off",
        },
        "performance_monthly": {"_": "Monthly performance panel: one row per account per month on book (max 24). Parquet only.",
                                "dpd": "Days past due", "delinquency_bucket": "current, 1-29, 30-59, 60-89, 90+",
                                "cash_deposit_count": "Cash deposits in month", "cash_deposit_max": "Largest single cash deposit",
                                "status": "open, closed, charged-off"},
        "applications_declined": {"_": "Applications declined in the same period (no performance data).",
                                  "requested_amount": "Requested limit/principal", "decline_reason": "Primary decline reason"},
        "devices_addresses": {"_": "Links between accounts and device ids / address ids (anonymised).",
                              "link_type": "device or address", "link_id": "Anonymised device or address id"},
        "policies": {"_": "Optional insurance book: one row per policy-year.", "exposure_years": "Fraction of year insured",
                     "sum_insured": "Sum insured", "vehicle_group": "Motor risk group 1-5"},
        "claims": {"_": "Claims on the policies.", "claim_amount": "Incurred amount"},
    },
}


def dictionary(domain: str) -> str:
    folder = ROOT / "data" / domain
    man = json.loads((folder / "MANIFEST.json").read_text())
    out = [f"# Data dictionary: {domain}", "",
           "Generated from the data by `python -m datagen.docs`. Null % and examples are measured, not typed.", ""]
    for t in man["tables"]:
        name = t["table"]
        df = pd.read_parquet(folder / f"{name}.parquet")
        d = DESC[domain].get(name, {})
        out += [f"## {name}", "", d.get("_", ""), "", f"Rows: {len(df):,} · Columns: {df.shape[1]}", "",
                "| Field | Type | Null % | Example | Description |", "| --- | --- | --- | --- | --- |"]
        for c in df.columns:
            ex = df[c].dropna()
            ex = str(ex.iloc[len(ex) // 2]) if len(ex) else ""
            desc = d.get(c) or DESC[domain].get(list(DESC[domain])[0], {}).get(c, "")
            dt = str(df[c].dtype)
            dt = "datetime" if dt.startswith("datetime64") else {"object": "text", "str": "text", "string": "text"}.get(dt, dt)
            out.append(f"| `{c}` | {dt} | {100 * df[c].isna().mean():.1f} | {ex[:28]} | {desc} |")
        out.append("")
    return "\n".join(out)


CARD = {
    "retail": """# Data card: NorthStar Markets (synthetic CPG/retail)

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
""",
    "finance": """# Data card: Meridian Bank (synthetic retail lending and cards)

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
""",
}


def main():
    for dom in ("retail", "finance"):
        folder = ROOT / "data" / dom
        (folder / "DATA_DICTIONARY.md").write_text(dictionary(dom))
        (folder / "DATA_CARD.md").write_text(CARD[dom])
        print("wrote", folder / "DATA_DICTIONARY.md")


if __name__ == "__main__":
    main()
