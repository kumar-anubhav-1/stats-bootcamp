"""Anomaly & Phenomena Register: the single source of truth for the answer key.

`python -m validator.register` measures every item from the generated data and
writes instructor/anomaly_register.yaml and instructor/ANOMALY_REGISTER.md.
Tests in datagen/tests assert each measured value sits inside its band.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from . import measures

ROOT = Path(__file__).resolve().parents[1]

# id, title, where, planted, lesson(s), method, band (lo, hi) for `measured`, metric description, hint (Navigator node)
SPEC = [
    ("R01", "Negative-quantity entry errors (not returns)", "transactions: quantity<0 & return_flag=False", "40 lines", "L1.2",
     "validity rule", (40, 40), "count of lines", "N-DESC-QUALITY"),
    ("R02", "Unit price 100x list (decimal shift)", "transactions", "25 lines", "L1.2, L1.6",
     "price/list ratio rule; robust z", (25, 25), "count of lines with unit_price/list_price > 20", "N-DESC-OUTLIER"),
    ("R03", "Duplicate lines from re-ingestion", "transactions: repeated line_id", "150 lines", "L1.2",
     "duplicate key check", (150, 150), "count of duplicated line_id", "N-DESC-QUALITY"),
    ("R04", "MCAR missingness", "transactions.temperature_c", "3% of region-days", "L1.3",
     "missingness vs other fields (chi-square)", (0.02, 0.05), "share missing", "N-DESC-MISSING"),
    ("R05", "MAR missingness", "customers.age_band", "18% non-members vs 2% members", "L1.3",
     "missingness by loyalty_flag", (0.14, 0.24), "missing rate among non-members", "N-DESC-MISSING"),
    ("R06", "MNAR missingness", "customers.household_size", "50% missing if household 5+ vs 5%", "L1.3",
     "compare baskets of missing vs known", (1.2, 1.8), "lines per basket: missing / known", "N-DESC-MISSING"),
    ("R07", "Heavy-tailed spend: bulk buyers", "25 customers (truth)", "~12% of revenue, baskets 10-40x median", "L1.4, L1.6",
     "top-25 customer share; mean vs median", (0.12, 0.25), "revenue share of top 25 customers", "N-DESC-SKEW"),
    ("R08", "Store level shift", "weekly_store: S017", "-35% from week 61", "L7.5",
     "change-point on store share", (59, 63), "detected change week", "N-FCST-BREAK"),
    ("R09", "Store-level promo experiment, true lift", "weekly_store_category: Hair Care, test vs control, weeks 70-77", "+12% units", "L3.4, L4.5, L9.1",
     "store-level growth vs pre-period, Welch t", (0.02, 0.20), "lift estimate (95% CI must cover 0.12)", "N-TEST-2G-MEAN"),
    ("R10", "Cannibalisation", "weekly_sku_chain: Lustra Shampoo 200ml during 400ml promos", "-20% units", "L8.4",
     "share of category in promo vs neighbouring weeks", (-0.32, -0.12), "relative change in victim share", "N-OPT-PROMO"),
    ("R11", "Seasonality and holidays", "all", "Fri-Sat +30%, Q4 +25%, holiday weeks +40%", "L7.1",
     "day-of-week profile; STL; holiday regressor", (1.2, 1.45), "Fri-Sat / Mon-Thu basket ratio", "N-FCST-SEASON"),
    ("R12", "Stockouts censor demand", "4% of store-SKU-weeks", "sales = 30% of demand when out", "L7.5",
     "compare to true demand (instructor)", (0.02, 0.04), "share of demand lost", "N-FCST-CENSOR"),
    ("R13", "Known price elasticity", "price_elasticity_extract", "Snacks -1.8, Dairy -0.6", "L8.4",
     "Poisson/log-log with promo controls", (-2.05, -1.55), "Snacks elasticity (Poisson)", "N-REG-LOGLOG"),
    ("R14", "Simpson's paradox", "transactions: promo_flag x format", "promo concentrated in Express", "L2.4",
     "stratify by format", (-0.30, -0.03), "overall promo vs non-promo qty/line (negative) while each format positive", "N-DESC-STRATIFY"),
    ("R15", "Confounder: display paired with promo", "transactions", "display on 92% of promo vs 3% non-promo", "L4.4",
     "crosstab promo x display; DAG", (0.88, 0.96), "display rate on promo lines", "N-CAUSAL-DAG"),
    ("R16", "Survivorship trap: delisted SKUs", "products vs products_archive; weekly_sku_chain Snacks", "30 SKUs delisted week 52", "L2.4",
     "include archive SKUs", (0.08, 0.25), "current-range Snacks growth (true category growth is negative)", "N-DESC-BIAS"),
    ("R17", "Returns-abuse cluster", "30 customers, stores S005/S012", "return rate ~45% vs 3%", "L8.5",
     "customer return-rate outliers; Isolation Forest", (0.30, 0.55), "return rate of the cluster", "N-ANOM-MULTI"),
    ("R18", "Fabricated / rounded numbers", "transactions: store S033", "70% of revenues rounded, non-Benford", "L2.6",
     "Benford MAD vs peers; last-digit test", (0.05, 0.10), "S033 first-digit MAD (peers ~0.03)", "N-ANOM-BENFORD"),
    ("R19", "Data drift point", "online channel from week 80", "discount_pct logged as fraction; online share 12%->25%", "L1.2, L9.6",
     "PSI / distribution check by period", (0.25, 50), "PSI of discount_pct (online promo lines)", "N-MON-PSI"),
    ("R20", "Loyalty selection bias", "loyalty members", "naive +35-40%, true causal +5%", "L9.1",
     "matching / DiD on joiners", (0.25, 0.55), "naive member basket uplift", "N-CAUSAL-PSM"),
    ("R21", "Planted basket associations", "Pasta->Pasta Sauce, Beer->Chips", "lift ~3.5 and ~2.2", "L8.3",
     "association rules", (2.8, 4.2), "Pasta->Sauce lift", "N-SEG-BASKET"),
    ("R22", "Intermittent long tail", "weekly_sku_chain", "25% of SKUs", "L7.4",
     "ADI / CV2 classification", (0.22, 0.30), "share of SKUs with ADI > 1.32", "N-FCST-INTERMITTENT"),
    ("R23", "Latent customer segments", "customers (truth: 5 segments)", "5 segments", "L8.1, L8.2",
     "K-Means / GMM on customer features", (0.25, 0.65), "adjusted Rand index vs truth (partial recovery expected)", "N-CLUST-KMEANS"),
    ("R24", "A/B test with sample-ratio mismatch", "ecoupon_ab", "planned 50/50; control v3.2 logging loss; true +1.5pp", "L4.1",
     "SRM chi-square, then segment by app_version", (0.52, 0.535), "treatment share of users (should be 0.50)", "N-EXP-SRM"),
    ("F01", "Impossible values", "accounts: age, income_annual", "12 ages, 20 negative incomes", "L1.2",
     "validity rules", (12, 12), "count of impossible ages", "N-DESC-QUALITY"),
    ("F02", "Income missing not at random", "accounts.income_annual", "4% missing, more among risky", "L1.3, L8.7",
     "default rate by missingness", (3.0, 8.0), "default rate ratio missing / known", "N-DESC-MISSING"),
    ("F03", "Rare events and base-rate trap", "accounts", "default 4.0%, fraud 0.7%", "L2.1, L6.5",
     "base rates; PR-AUC", (0.040, 0.040), "default rate", "N-METRIC-RARE"),
    ("F04", "Non-linear utilisation risk", "credit cards", ">90% util ~4x default of <=50%", "L5.6, L8.7",
     "binned default rates; splines / WoE", (3.5, 9.0), "default ratio util>90% vs <=50%", "N-REG-NONLINEAR"),
    ("F05", "Interaction: young x high DTI", "age<25 & dti>0.45", "extra odds x2.5", "L5.6",
     "interaction term in logistic", (1.4, 3.5), "interaction odds ratio", "N-REG-INTERACT"),
    ("F06", "Multicollinearity", "income vs limit", "r ~0.95", "L5.2",
     "VIF", (5, 40), "VIF of income", "N-REG-VIF"),
    ("F07", "Fraud rings", "devices_addresses", "3 rings x 15 accounts, 60% fraud", "L8.6",
     "graph connected components", (3, 3), "rings (components >= 6 accounts)", "N-ANOM-GRAPH"),
    ("F08", "Structuring below reporting threshold", "performance_monthly.cash_deposit_max", "~120 accounts bunching 9,000-9,999", "L8.6",
     "histogram bunching", (3, 15), "deposits just below / just above 10,000", "N-ANOM-STRUCT"),
    ("F09", "Benford violation", "accounts.txn_amount_3m at BR07", "70% fabricated", "L2.6",
     "Benford MAD by branch", (0.05, 0.10), "BR07 MAD (peers ~0.01)", "N-ANOM-BENFORD"),
    ("F10", "Leakage trap", "collections_flag, recovery_amount", "post-default fields", "L6.4",
     "AUC with vs without post-outcome fields", (0.95, 1.0), "AUC with leaky fields (clean ~0.80)", "N-ML-LEAK"),
    ("F11", "Population drift", "vintages 2025Q2-Q3 (partner channel)", "score PSI ~0.28", "L9.6",
     "PSI vs 2023 baseline", (0.20, 0.40), "PSI of app_score", "N-MON-PSI"),
    ("F12", "Concept drift", "vintages 2025Q2-Q3", "AUC decay ~0.05-0.06", "L9.6",
     "AUC by vintage", (-0.09, -0.02), "AUC late minus early", "N-MON-CONCEPT"),
    ("F13", "Censoring for survival", "accounts.churn_flag/months_observed", "~70% censored", "L9.2",
     "Kaplan-Meier", (0.65, 0.78), "share censored", "N-TEST-SURV"),
    ("F14", "Heavy-tailed balances", "accounts.balance_current", "top 1% hold ~15%", "L1.4",
     "Lorenz / concentration", (0.10, 0.20), "share held by top 1%", "N-DESC-SKEW"),
    ("F15", "Proxy for protected attribute", "region R4 / protected_group", "disparate impact ~0.72-0.75", "L9.5",
     "approval rate by group incl. declined applications", (0.65, 0.80), "approval rate ratio B/A", "N-MON-FAIR"),
    ("F16", "Champion/challenger effect", "accounts entering 30+ DPD", "cure 35% -> 41%", "L4.5",
     "two-proportion test with 80/20 split", (0.03, 0.09), "cure-rate difference", "N-TEST-2G-PROP"),
    ("F17", "Insurance frequency-severity", "policies, claims", "NB frequency; Gamma severity + 3 catastrophic", "L9.4",
     "dispersion test; severity tail", (1.08, 1.5), "claim count variance / mean", "N-REG-GLM"),
    ("F18", "Reject-inference trap", "applications_declined", "declined have no performance", "L8.7, L9.6",
     "compare booked vs declined scores", (40, 100), "booked minus declined mean app_score", "N-MON-REJECT"),
]


def _tidy(o):
    if isinstance(o, float):
        return float(f"{o:.6g}")
    if isinstance(o, dict):
        return {k: _tidy(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_tidy(v) for v in o]
    return o


def build(data=str(measures.DATA)) -> list[dict]:
    res = measures.run_all(data)
    out = []
    for (i, title, where, planted, lesson, method, band, metric, node) in SPEC:
        m = res[i]
        detail = {k: v for k, v in m.items() if k != "measured"}
        out.append({"id": i, "title": title, "where": where, "planted": planted, "lessons": lesson,
                    "detection_method": method, "metric": metric, "measured": m["measured"],
                    "tolerance_band": list(band), "within_band": bool(band[0] <= m["measured"] <= band[1]),
                    "detail": _tidy(json.loads(json.dumps(detail, default=str))), "hint_node": node})
    return out


def write(items: list[dict]) -> None:
    inst = ROOT / "instructor"
    inst.mkdir(exist_ok=True)
    (inst / "anomaly_register.yaml").write_text(yaml.safe_dump(items, sort_keys=False, width=120))
    lines = ["# Anomaly & Phenomena Register (instructor only — answer key)", "",
             "Generated by `python -m validator.register` from seed 20261115. Do not edit by hand.", "",
             "| ID | Phenomenon | Where | Planted | Lesson | Method | Metric | Measured | Band | OK |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for it in items:
        lines.append(f"| {it['id']} | {it['title']} | {it['where']} | {it['planted']} | {it['lessons']} | "
                     f"{it['detection_method']} | {it['metric']} | {it['measured']} | {it['tolerance_band']} | "
                     f"{'yes' if it['within_band'] else 'NO'} |")
    (inst / "ANOMALY_REGISTER.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    items = build()
    write(items)
    bad = [i["id"] for i in items if not i["within_band"]]
    print(f"{len(items)} items, {len(items) - len(bad)} within band" + (f"; OUT: {bad}" if bad else ""))
