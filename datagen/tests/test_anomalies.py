"""Proof that every planted anomaly is present at its stated size, plus schema and reproducibility.

Run:  python -m pytest datagen/tests -q
Requires data generated with --with-truth (CI does this).
"""
import hashlib

import pandas as pd
import pytest

from datagen import finance, retail
from validator import measures
from validator.register import SPEC

ROW_COUNTS = {("retail", "transactions"): 25_000, ("finance", "accounts"): 25_000,
              ("retail", "stores"): 40, ("retail", "weekly_store"): 4_160}


@pytest.mark.parametrize("item", SPEC, ids=[s[0] for s in SPEC])
def test_anomaly_within_band(item):
    aid, band = item[0], item[6]
    m = measures.ALL[aid]()
    assert band[0] <= m["measured"] <= band[1], f"{aid} measured {m['measured']} outside {band}: {m}"


def test_r09_ci_covers_truth():
    m = measures.R09()
    assert m["ci_low"] <= 0.12 <= m["ci_high"]


def test_f16_ci_excludes_zero():
    m = measures.F16()
    assert m["ci_low"] > 0


def test_r14_reverses_within_each_format():
    m = measures.R14()
    assert m["measured"] < 0 and all(v > 0 for v in m["within_format_lift"].values())


def test_r13_dairy_elasticity():
    assert -0.85 <= measures.R13()["measured_dairy"] <= -0.35


@pytest.mark.parametrize("key,n", ROW_COUNTS.items())
def test_row_counts(key, n):
    assert len(measures.load(*key)) == n


def test_schema_core_columns():
    tx = measures.load("retail", "transactions")
    need = {"line_id", "basket_id", "transaction_id", "date", "week", "store_id", "format", "region", "city_tier",
            "channel", "customer_id", "loyalty_flag", "loyalty_segment", "age_band", "household_size", "tenure_months",
            "sku", "category", "brand", "pack_size", "list_price", "unit_price", "discount_pct", "promo_flag",
            "promo_type", "display_flag", "quantity", "revenue", "unit_cost", "margin", "stockout_flag", "return_flag",
            "payment_method", "temperature_c", "holiday_flag", "competitor_price_index", "experiment_group"}
    assert need <= set(tx.columns)
    acc = measures.load("finance", "accounts")
    need_f = {"customer_id", "account_id", "age", "income_annual", "employment_type", "region", "tenure_months_with_bank",
              "product_type", "limit_or_loan_amount", "interest_rate", "term_months", "utilisation", "dti", "bureau_score",
              "inquiries_6m", "delinq_2y", "balance_current", "txn_count_3m", "txn_amount_3m", "digital_share",
              "complaints_12m", "origination_date", "vintage", "income_verified_flag", "default_12m", "max_dpd_12m",
              "churn_flag", "fraud_flag", "protected_group", "strategy_group"}
    assert need_f <= set(acc.columns)


def _h(df):
    return hashlib.sha256(pd.util.hash_pandas_object(df.astype(str), index=False).values.tobytes()).hexdigest()


def test_reproducible_same_seed():
    a = retail.generate(retail.RetailParams(seed=123))["tables"]["transactions"]
    b = retail.generate(retail.RetailParams(seed=123))["tables"]["transactions"]
    assert _h(a) == _h(b)
    fa = finance.generate(finance.FinanceParams(seed=123))["tables"]["accounts"]
    fb = finance.generate(finance.FinanceParams(seed=123))["tables"]["accounts"]
    assert _h(fa) == _h(fb)


def test_identical_data_across_platforms():
    """Every cohort, on any machine, must get byte-identical data (canonical CSV fingerprints)."""
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    expected = json.loads((root / "datagen" / "expected_hashes.json").read_text())
    for dom, tables in expected.items():
        got = {t["table"]: t["hash"] for t in json.loads((root / "data" / dom / "MANIFEST.json").read_text())["tables"]}
        assert got == tables, f"{dom} data differs from the reference fingerprints: " + str({k: (got.get(k), v) for k, v in tables.items() if got.get(k) != v})
