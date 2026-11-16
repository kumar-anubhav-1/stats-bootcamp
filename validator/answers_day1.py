"""Computed answers for Day 1 (data quality and descriptive statistics). Keys are prefixed d1_."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import measures as M


def _r(x, nd=4):
    return round(float(x), nd)


def _gini(x):
    x = np.sort(np.asarray(x, float))
    x = x[x >= 0]
    n = len(x)
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))


def _cramers_v(a, b):
    tab = pd.crosstab(a, b)
    chi2 = stats.chi2_contingency(tab, correction=False)[0]
    n = tab.values.sum()
    return float(np.sqrt(chi2 / (n * (min(tab.shape) - 1)))), float(stats.chi2_contingency(tab, correction=False)[1])


def compute_day1(data=str(M.DATA)) -> dict:
    a: dict = {}
    tx = M.load("retail", "transactions", data)
    cust = M.load("retail", "customers", data)
    acc = M.load("finance", "accounts", data)
    pm = M.load("finance", "performance_monthly", data)
    wsc = M.load("retail", "weekly_store_category", data)

    # ---------- L1.1 grain, tidy, joins ----------
    dd = tx.drop_duplicates("line_id")
    sales = dd[~dd.return_flag & (dd.quantity > 0)]
    a["d1_lines_per_basket"] = _r(len(sales) / sales.basket_id.nunique(), 2)
    a["d1_baskets_per_customer"] = _r(sales.basket_id.nunique() / sales.customer_id.nunique(), 2)
    a["d1_mean_line_rev"] = _r(sales.revenue.mean(), 2)
    clean = sales[sales.unit_price / sales.list_price < 20]
    basket = clean.groupby("basket_id").revenue.sum()
    a["d1_mean_basket_rev"] = _r(basket.mean(), 2)
    # join explosion: transactions joined to weekly_store_category on store+category (forgetting week)
    j = tx.merge(wsc[["store_id", "category", "week", "units"]], on=["store_id", "category"], how="left", suffixes=("", "_wk"))
    a["d1_join_rows_bad"] = len(j)
    j2 = tx.merge(wsc[["store_id", "category", "week", "units"]], on=["store_id", "category", "week"], how="left")
    a["d1_join_rows_good"] = len(j2)
    a["d1_join_factor"] = _r(len(j) / len(tx), 1)
    # finance grain: average balance at account vs account-month grain
    a["d1_bal_mean_account"] = _r(acc.balance_current.mean(), 0)
    a["d1_bal_mean_panel"] = _r(pm.balance.mean(), 0)
    a["d1_panel_key_unique"] = bool(not pm.duplicated(["account_id", "month_on_book"]).any())
    a["d1_months_per_account"] = _r(len(pm) / pm.account_id.nunique(), 1)

    # ---------- L1.2 data quality ----------
    a["d1_dup_rows_full"] = int(tx.duplicated().sum())
    a["d1_dup_ids"] = int(tx.line_id.duplicated().sum())
    a["d1_neg_nonreturn"] = int(((dd.quantity < 0) & ~dd.return_flag).sum())
    a["d1_price100"] = int((dd.unit_price / dd.list_price > 20).sum())
    a["d1_returns"] = int(dd.return_flag.sum())
    dup_rev = tx[~tx.return_flag].revenue.sum() - dd[~dd.return_flag].revenue.sum()
    a["d1_dup_revenue"] = _r(dup_rev, 2)
    a["d1_rev_mismatch"] = int((np.abs(dd.revenue - dd.quantity * dd.unit_price) > 0.011).sum())
    a["d1_rev_mismatch_s033"] = int((np.abs(dd.revenue - dd.quantity * dd.unit_price) > 0.011)[dd.store_id == "S033"].sum())
    on = dd[(dd.channel != "in-store") & dd.promo_flag]
    a["d1_disc_med_before"] = _r(on[on.week < 80].discount_pct.median(), 1)
    a["d1_disc_med_after"] = _r(on[on.week >= 80].discount_pct.median(), 3)
    a["d1_frac_disc_lines"] = int(((dd.discount_pct > 0) & (dd.discount_pct < 1)).sum())
    a["d1_bad_age"] = int(((acc.age >= 120) | (acc.age < 18)).sum())
    a["d1_neg_income"] = int((acc.income_annual < 0).sum())
    a["d1_util_over_1"] = int((acc.utilisation > 1).sum())
    ov = acc.utilisation > 1
    a["d1_def_over1_pct"] = _r(100 * acc[ov].default_12m.mean(), 1)
    a["d1_def_notover1_pct"] = _r(100 * acc[(acc.product_type == "credit_card") & ~ov].default_12m.mean(), 1)
    a["d1_rows_after_rules"] = int(len(dd) - a["d1_neg_nonreturn"] - a["d1_price100"])
    a["d1_rev_total_raw"] = _r(tx[~tx.return_flag].revenue.sum(), 0)
    a["d1_rev_total_clean"] = _r(dd[~dd.return_flag & (dd.quantity > 0) & (dd.unit_price / dd.list_price < 20)].revenue.sum(), 0)
    a["d1_rev_inflation_pct"] = _r(100 * (a["d1_rev_total_raw"] / a["d1_rev_total_clean"] - 1), 1)

    # ---------- L1.3 missing data ----------
    tm = dd.temperature_c.isna()
    a["d1_temp_miss_pct"] = _r(100 * tm.mean(), 1)
    a["d1_temp_miss_region_p_line"] = float(f"{stats.chi2_contingency(pd.crosstab(dd.region, tm))[1]:.2g}")
    rd = dd.groupby(["region", "date"]).temperature_c.apply(lambda s: s.isna().all()).reset_index()
    a["d1_temp_regiondays"] = int(len(rd))
    a["d1_temp_miss_rd_pct"] = _r(100 * rd.temperature_c.mean(), 1)
    a["d1_temp_miss_region_p"] = _r(stats.chi2_contingency(pd.crosstab(rd.region, rd.temperature_c))[1], 2)
    assert a["d1_temp_miss_region_p"] > 0.05, "L1.3 narrative assumes MCAR temperature passes at region-day level"
    a["d1_temp_miss_by_region"] = {k: _r(100 * v, 1) for k, v in tm.groupby(dd.region).mean().items()}
    am = cust.age_band.isna()
    a["d1_age_miss_member_pct"] = _r(100 * am[cust.loyalty_flag].mean(), 1)
    a["d1_age_miss_nonmember_pct"] = _r(100 * am[~cust.loyalty_flag].mean(), 1)
    a["d1_age_miss_p"] = float(f"{stats.chi2_contingency(pd.crosstab(cust.loyalty_flag, am))[1]:.3g}")
    r06 = M.R06(data)
    a["d1_hh_miss_pct"] = _r(100 * r06["missing_rate"], 1)
    a["d1_hh_lines_ratio"] = r06["measured"]
    a["d1_hh_rev_med_missing"], a["d1_hh_rev_med_known"] = r06["basket_rev_median_missing"], r06["basket_rev_median_known"]
    im = acc.income_annual.isna()
    a["d1_inc_miss_pct"] = _r(100 * im.mean(), 2)
    a["d1_def_inc_missing_pct"] = _r(100 * acc[im].default_12m.mean(), 2)
    a["d1_def_inc_known_pct"] = _r(100 * acc[~im].default_12m.mean(), 2)
    a["d1_bureau_inc_missing"] = _r(acc[im].bureau_score.mean(), 1)
    a["d1_bureau_inc_known"] = _r(acc[~im].bureau_score.mean(), 1)
    # listwise deletion impact on default rate of a modelling sample
    model_cols = ["income_annual", "utilisation"]
    lw = acc.dropna(subset=model_cols)
    a["d1_listwise_rows"] = len(lw)
    a["d1_listwise_drop_pct"] = _r(100 * (1 - len(lw) / len(acc)), 1)
    a["d1_listwise_default_pct"] = _r(100 * lw.default_12m.mean(), 2)
    cards = acc[acc.product_type == "credit_card"]
    lwc = cards.dropna(subset=["income_annual"])
    a["d1_cards_default_pct"] = _r(100 * cards.default_12m.mean(), 2)
    a["d1_cards_listwise_default_pct"] = _r(100 * lwc.default_12m.mean(), 2)
    inc_ok = acc.income_annual[acc.income_annual > 0]
    a["d1_income_mean_cc"] = _r(inc_ok.mean(), 0)
    a["d1_income_median_cc"] = _r(inc_ok.median(), 0)
    a["d1_util_na_loans_pct"] = _r(100 * acc[acc.product_type == "personal_loan"].utilisation.isna().mean(), 0)

    # ---------- L1.4 centre, spread, shape ----------
    b = basket
    q1, q3 = b.quantile([0.25, 0.75])
    a["d1_b_mean"], a["d1_b_median"] = _r(b.mean(), 2), _r(b.median(), 2)
    a["d1_b_sd"], a["d1_b_iqr"] = _r(b.std(), 2), _r(q3 - q1, 2)
    a["d1_b_q1"], a["d1_b_q3"] = _r(q1, 2), _r(q3, 2)
    a["d1_b_mad"] = _r(stats.median_abs_deviation(b), 2)
    a["d1_b_p90"], a["d1_b_p99"], a["d1_b_max"] = _r(b.quantile(0.9), 2), _r(b.quantile(0.99), 2), _r(b.max(), 2)
    a["d1_b_skew"], a["d1_b_kurt"] = _r(b.skew(), 2), _r(b.kurt(), 1)
    a["d1_b_cv"] = _r(b.std() / b.mean(), 2)
    a["d1_b_trim10"] = _r(stats.trim_mean(b, 0.1), 2)
    a["d1_b_geo"] = _r(stats.gmean(b[b > 0]), 2)
    a["d1_b_share_below_mean"] = _r(100 * (b < b.mean()).mean(), 1)
    a["d1_b_n"] = int(len(b))
    cr = clean.groupby("customer_id").revenue.sum().sort_values(ascending=False)
    a["d1_top25_share_pct"] = _r(100 * cr.head(25).sum() / cr.sum(), 1)
    a["d1_top10pct_share_pct"] = _r(100 * cr.head(int(0.1 * len(cr))).sum() / cr.sum(), 1)
    a["d1_cust_gini"] = _r(_gini(cr.values), 3)
    bal = acc.balance_current
    a["d1_bal_mean"], a["d1_bal_median"] = _r(bal.mean(), 0), _r(bal.median(), 0)
    a["d1_bal_skew"] = _r(bal.skew(), 2)
    a["d1_bal_top1_pct"] = _r(100 * bal.sort_values(ascending=False).head(int(0.01 * len(bal))).sum() / bal.sum(), 1)
    a["d1_bal_gini"] = _r(_gini(bal.values), 3)
    a["d1_bal_zero_pct"] = _r(100 * (bal == 0).mean(), 1)
    inc = acc[acc.income_annual > 0]
    cv = inc.groupby("employment_type").income_annual.agg(lambda s: s.std() / s.mean())
    med = inc.groupby("employment_type").income_annual.median()
    a["d1_inc_cv_by_emp"] = {k: _r(v, 2) for k, v in cv.items()}
    a["d1_inc_med_by_emp"] = {k: _r(v, 0) for k, v in med.items()}
    a["d1_bureau_mean"], a["d1_bureau_sd"] = _r(acc.bureau_score.mean(), 1), _r(acc.bureau_score.std(), 1)
    a["d1_bureau_skew"] = _r(acc.bureau_score.skew(), 2)

    # ---------- L1.5 visual ----------
    v = acc.assign(late=acc.vintage.isin(["2025Q2", "2025Q3"]))
    a["d1_bureau_p25_early"] = _r(v[~v.late].bureau_score.quantile(0.25), 0)
    a["d1_bureau_p25_late"] = _r(v[v.late].bureau_score.quantile(0.25), 0)
    a["d1_bureau_med_early"] = _r(v[~v.late].bureau_score.median(), 0)
    a["d1_bureau_med_late"] = _r(v[v.late].bureau_score.median(), 0)
    a["d1_share_below_650_early"] = _r(100 * (v[~v.late].bureau_score < 650).mean(), 1)
    a["d1_share_below_650_late"] = _r(100 * (v[v.late].bureau_score < 650).mean(), 1)
    a["d1_fd_bins"] = int(np.histogram_bin_edges(b, bins="fd").size - 1)
    a["d1_sturges_bins"] = int(np.histogram_bin_edges(b, bins="sturges").size - 1)
    lb = np.log(b[b > 0])
    a["d1_logb_skew"] = _r(pd.Series(lb).skew(), 2)

    # ---------- L1.6 outliers, transformations ----------
    iqr = q3 - q1
    a["d1_tukey_upper"] = _r(q3 + 1.5 * iqr, 2)
    a["d1_tukey_far_upper"] = _r(q3 + 3 * iqr, 2)
    a["d1_n_tukey"] = int((b > q3 + 1.5 * iqr).sum())
    a["d1_n_tukey_far"] = int((b > q3 + 3 * iqr).sum())
    z = (b - b.mean()) / b.std()
    a["d1_n_z3"] = int((z.abs() > 3).sum())
    mz = 0.6745 * (b - b.median()) / stats.median_abs_deviation(b)
    a["d1_n_mz35"] = int((mz.abs() > 3.5).sum())
    # with the 100x errors still in: does z-score catch them?
    braw = sales.groupby("basket_id").revenue.sum()
    zr = (braw - braw.mean()) / braw.std()
    mzr = 0.6745 * (braw - braw.median()) / stats.median_abs_deviation(braw)
    err_baskets = set(sales[sales.unit_price / sales.list_price > 20].basket_id)
    a["d1_err_baskets"] = len(err_baskets)
    a["d1_err_caught_z3"] = int(sum(1 for x in err_baskets if abs(zr[x]) > 3))
    a["d1_err_caught_mz"] = int(sum(1 for x in err_baskets if abs(mzr[x]) > 3.5))
    a["d1_sd_raw"], a["d1_sd_clean"] = _r(braw.std(), 2), _r(b.std(), 2)
    cap = b.clip(upper=b.quantile(0.99))
    a["d1_mean_capped99"] = _r(cap.mean(), 2)
    a["d1_mean_excl_outliers"] = _r(b[mz.abs() <= 3.5].mean(), 2)
    seg_path = M.ROOT / "instructor" / "truth" / "retail" / "customer_segments.parquet"
    if seg_path.exists():
        seg = pd.read_parquet(seg_path)
        bulk = set(seg[seg.bulk].customer_id)
        bc = clean.groupby("basket_id").customer_id.first()
        flagged = set(b[mz.abs() > 3.5].index)
        a["d1_flagged_bulk_share_pct"] = _r(100 * np.mean([bc[x] in bulk for x in flagged]), 0) if flagged else 0.0
    inc_pos = inc.income_annual.values
    a["d1_inc_skew"] = _r(pd.Series(inc_pos).skew(), 2)
    a["d1_loginc_skew"] = _r(pd.Series(np.log(inc_pos)).skew(), 2)
    bc_vals, lam = stats.boxcox(inc_pos)
    a["d1_boxcox_lambda"] = _r(lam, 3)
    a["d1_boxcox_skew"] = _r(pd.Series(bc_vals).skew(), 2)
    # target encoding leakage: branch target-encoded on full data vs out-of-fold
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import KFold
    rng = np.random.default_rng(3)
    noise_cat = pd.Series(rng.integers(0, 2000, len(acc)).astype(str))       # pure-noise high-cardinality code
    y = acc.default_12m.astype(int).values
    te_full = noise_cat.map(pd.Series(y).groupby(noise_cat).mean())
    oof = np.zeros(len(acc))
    for tr, te in KFold(5, shuffle=True, random_state=0).split(acc):
        m = pd.Series(y[tr]).groupby(noise_cat.iloc[tr].values).mean()
        oof[te] = noise_cat.iloc[te].map(m).fillna(y[tr].mean()).values
    a["d1_te_auc_leaky"] = _r(roc_auc_score(y, te_full), 3)
    a["d1_te_auc_oof"] = _r(roc_auc_score(y, oof), 3)

    # ---------- L1.7 relationships ----------
    s7 = clean[clean.customer_id.isin(cr.index[25:])]
    a["d1_pq_pearson"] = _r(stats.pearsonr(s7.unit_price, s7.quantity)[0], 3)
    a["d1_pq_spearman"] = _r(stats.spearmanr(s7.unit_price, s7.quantity)[0], 3)
    a["d1_pq_kendall"] = _r(stats.kendalltau(s7.unit_price, s7.quantity)[0], 3)
    xb = clean.groupby("basket_id").agg(promo=("promo_flag", "max"), seg=("loyalty_segment", "first"))
    vv, pv = _cramers_v(xb.seg, xb.promo)
    a["d1_promo_seg_v"], a["d1_promo_seg_p"] = _r(vv, 3), float(f"{pv:.3g}")
    a["d1_promo_by_seg_pct"] = {k: _r(100 * v_, 1) for k, v_ in xb.groupby("seg").promo.mean().items()}
    c = acc[acc.product_type == "credit_card"]
    a["d1_bu_pearson"] = _r(stats.pearsonr(c.bureau_score, c.utilisation)[0], 3)
    a["d1_bu_spearman"] = _r(stats.spearmanr(c.bureau_score, c.utilisation)[0], 3)
    il = acc[(acc.income_annual > 0)].dropna(subset=["income_annual"])
    a["d1_il_pearson"] = _r(stats.pearsonr(il.income_annual, il.limit_or_loan_amount)[0], 3)
    a["d1_il_spearman"] = _r(stats.spearmanr(il.income_annual, il.limit_or_loan_amount)[0], 3)
    # utilisation vs default: correlation small, but risk curve steep
    a["d1_util_def_pearson"] = _r(stats.pointbiserialr(c.default_12m.astype(int), c.utilisation)[0], 3)
    f04 = M.F04(data)
    a["d1_util_def_ratio"] = f04["measured"]
    # temperature vs beverages (region-week) — shared seasonality
    ws = M.load("retail", "weekly_store", data)
    rc = M.load("retail", "weekly_region_category", data)
    tw = ws.groupby(["region", "week"]).avg_temperature_c.mean().rename("temp").reset_index()
    bev = rc[rc.category == "Beverages"].merge(tw, on=["region", "week"])
    a["d1_temp_bev_r"] = _r(stats.pearsonr(bev.temp, bev.units)[0], 3)
    fr = rc[rc.category == "Frozen"].merge(tw, on=["region", "week"])
    a["d1_temp_frozen_r"] = _r(stats.pearsonr(fr.temp, fr.units)[0], 3)
    hc = rc[rc.category == "Hair Care"].merge(tw, on=["region", "week"])
    a["d1_temp_hair_r"] = _r(stats.pearsonr(hc.temp, hc.units)[0], 3)
    # guards: every narrative claim in the Day 1 lessons must remain true for the generated data
    checks = {
        "income-limit Pearson > Spearman": a["d1_il_pearson"] > a["d1_il_spearman"],
        "Hair Care weather r positive but below Beverages": 0.05 < a["d1_temp_hair_r"] < a["d1_temp_bev_r"],
        "utilisation r small, risk ratio large": a["d1_util_def_pearson"] < 0.2 and a["d1_util_def_ratio"] > 3,
        "promo x segment weak but significant": a["d1_promo_seg_v"] < 0.2 and a["d1_promo_seg_p"] < 0.05,
        "robust z catches more errors than plain z": a["d1_err_caught_mz"] > a["d1_err_caught_z3"],
        "basket SD exceeds mean (skewed)": a["d1_b_sd"] > a["d1_b_mean"] > a["d1_b_median"],
        "target encoding leak visible": a["d1_te_auc_leaky"] > 0.7 and a["d1_te_auc_oof"] < 0.56,
        "household-size MNAR signal": a["d1_hh_lines_ratio"] > 1.1,
        "age MAR by loyalty": a["d1_age_miss_nonmember_pct"] > 3 * a["d1_age_miss_member_pct"],
        "listwise drop large": a["d1_listwise_drop_pct"] > 30,
        "deletion lowers card default": a["d1_cards_listwise_default_pct"] < a["d1_cards_default_pct"],
        "late vintages weaker": a["d1_share_below_650_late"] > a["d1_share_below_650_early"],
        "price-quantity correlation weak": abs(a["d1_pq_pearson"]) < 0.2,
        "Box-Cox lambda near zero": abs(a["d1_boxcox_lambda"]) < 0.25,
        "revenue mismatches concentrated in one store": a["d1_rev_mismatch_s033"] >= 0.9 * a["d1_rev_mismatch"],
        "over-limit cards riskier": a["d1_def_over1_pct"] > a["d1_def_notover1_pct"],
    }
    bad = [k for k, ok in checks.items() if not ok]
    assert not bad, f"Day 1 narrative no longer supported by the data: {bad}"
    return a
