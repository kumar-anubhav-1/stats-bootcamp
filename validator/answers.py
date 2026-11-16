"""Named, computed answers for lessons, quizzes and exercises.

Lesson pages and question banks contain placeholders like {{ a.l34_hc_lift_pct }}.
`python -m tools.build_site` renders them with the values computed here, so every number
in the course comes from the generated data and changes automatically if the seed changes.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from . import measures as M

ROOT = Path(__file__).resolve().parents[1]


def _r(x, nd=4):
    return round(float(x), nd)


def _prop_test(x1, n1, x0, n0):
    p1, p0 = x1 / n1, x0 / n0
    pp = (x1 + x0) / (n1 + n0)
    z = (p1 - p0) / np.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n0))
    se = np.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
    return p1, p0, z, 2 * stats.norm.sf(abs(z)), (p1 - p0 - 1.96 * se, p1 - p0 + 1.96 * se)


def compute(data=str(M.DATA)) -> dict:
    a: dict = {}
    tx = M.load("retail", "transactions", data)
    acc = M.load("finance", "accounts", data)
    pm = M.load("finance", "performance_monthly", data)

    # ---------------- Day 0: data facts ----------------
    a["rt_rows"] = len(tx)
    a["rt_cols"] = tx.shape[1]
    a["rt_stores"] = tx.store_id.nunique()
    a["rt_skus_active"] = len(M.load("retail", "products", data))
    a["rt_customers"] = tx.customer_id.nunique()
    a["rt_baskets"] = tx.basket_id.nunique()
    a["rt_first_date"], a["rt_last_date"] = tx.date.min(), tx.date.max()
    a["rt_return_lines"] = int(tx.return_flag.sum())
    a["rt_dup_lines"] = int(tx.line_id.duplicated().sum())
    a["rt_hh_null_pct"] = _r(100 * tx.household_size.isna().mean(), 1)
    a["rt_age_null_pct"] = _r(100 * tx.age_band.isna().mean(), 1)
    a["rt_neg_qty_nonreturn"] = M.R01(data)["measured"]
    a["rt_revenue_total"] = _r(tx.revenue.sum(), 0)
    a["fi_rows"] = len(acc)
    a["fi_cols"] = acc.shape[1]
    a["fi_panel_rows"] = len(pm)
    a["fi_declined"] = len(M.load("finance", "applications_declined", data))
    a["fi_default_pct"] = _r(100 * acc.default_12m.mean(), 2)
    a["fi_fraud_pct"] = _r(100 * acc.fraud_flag.mean(), 2)
    a["fi_vintages"] = acc.vintage.nunique()
    a["fi_first_vintage"], a["fi_last_vintage"] = acc.vintage.min(), acc.vintage.max()
    a["fi_income_null_pct"] = _r(100 * acc.income_annual.isna().mean(), 2)
    a["fi_bad_age"] = M.F01(data)["measured"]

    # ---------------- L3.4 retail ----------------
    r09 = M.R09(data)
    a["l34_hc_lift_pct"] = _r(100 * r09["measured"], 1)
    a["l34_hc_ci_lo"], a["l34_hc_ci_hi"] = _r(100 * r09["ci_low"], 1), _r(100 * r09["ci_high"], 1)
    a["l34_hc_p"] = _r(r09["p_value"], 4)
    a["l34_threshold_pct"] = 10
    assert a["l34_hc_ci_lo"] < a["l34_threshold_pct"] < a["l34_hc_ci_hi"], \
        "L3.4 narrative assumes the rollout threshold lies inside the lift CI — revisit the lesson text"
    assert r09["ci_low"] > 0, "L3.4 narrative assumes the store-level lift is significant"
    a["l34_hc_naive_lift_pct"] = _r(100 * r09["naive_post_lift"], 1)
    a["l34_hc_naive_p"] = _r(r09["naive_p_value"], 3)
    sc = M.load("retail", "weekly_store_category", data)
    h = sc[sc.category == "Hair Care"]
    st = M.load("retail", "stores", data)
    a["l34_arm_by_format"] = pd.crosstab(st.format, st.experiment_group).to_dict()
    pre = h[h.week.between(54, 69)].groupby("store_id").units.mean()
    post = h[h.week.between(70, 77)].groupby("store_id").units.mean()
    grp = h.groupby("store_id").experiment_group.first()
    g = post / pre
    tt = stats.ttest_ind(pre[grp == "test"], pre[grp == "control"], equal_var=False)
    a["l34_pre_test_mean"], a["l34_pre_ctrl_mean"] = _r(pre[grp == "test"].mean(), 1), _r(pre[grp == "control"].mean(), 1)
    a["l34_pre_balance_p"] = _r(tt.pvalue, 3)
    a["l34_pre_sd_stores"] = _r(pre.std(), 1)
    a["l34_pre_min"], a["l34_pre_max"] = _r(pre.min(), 1), _r(pre.max(), 1)
    gi = g / g[grp == "control"].mean()
    a["l34_growth_test"], a["l34_growth_ctrl"] = _r(g[grp == "test"].mean(), 3), _r(g[grp == "control"].mean(), 3)
    a["l34_growth_sd"] = _r(np.sqrt((gi[grp == "test"].var() + gi[grp == "control"].var()) / 2), 3)
    sd = a["l34_growth_sd"]
    a["l34_mde_pct"] = _r(100 * (stats.norm.ppf(0.975) + stats.norm.ppf(0.8)) * sd * np.sqrt(2 / 20), 1)
    a["l34_stores_needed_thr"] = int(np.ceil(2 * ((stats.norm.ppf(0.975) + stats.norm.ppf(0.8)) * sd / (a["l34_threshold_pct"] / 100)) ** 2))
    tr_g, ct_g = gi[grp == "test"].values, gi[grp == "control"].values
    a["l34_mw_p"] = _r(stats.mannwhitneyu(tr_g, ct_g).pvalue, 4)
    sk = (pd.Series(tr_g).skew(), pd.Series(ct_g).skew())
    a["l34_growth_skew_max"] = _r(max(abs(sk[0]), abs(sk[1])), 2)
    a["l34_shapiro_min_p"] = _r(min(stats.shapiro(tr_g).pvalue, stats.shapiro(ct_g).pvalue), 3)
    a["l34_levene_p"] = _r(stats.levene(tr_g, ct_g, center="median").pvalue, 3)
    sp = np.sqrt((tr_g.var(ddof=1) + ct_g.var(ddof=1)) / 2)
    a["l34_hedges_g"] = _r((tr_g.mean() - ct_g.mean()) / sp * (1 - 3 / (4 * 40 - 9)), 2)
    by_f = {}
    for f in ("Hyper", "Super", "Express"):
        ids = st[st.format == f].store_id
        gg = g[g.index.isin(ids)]
        gr_ = grp[grp.index.isin(ids)]
        by_f[f] = {"lift_pct": _r(100 * (gg[gr_ == "test"].mean() / gg[gr_ == "control"].mean() - 1), 1),
                   "n_test": int((gr_ == "test").sum()), "n_control": int((gr_ == "control").sum())}
    a["l34_lift_by_format"] = by_f
    rng = np.random.default_rng(7)
    pool = np.concatenate([tr_g, ct_g])
    obs = tr_g.mean() - ct_g.mean()
    cnt = 0
    for _ in range(10000):
        rng.shuffle(pool)
        cnt += abs(pool[:20].mean() - pool[20:].mean()) >= abs(obs)
    a["l34_perm_p"] = _r((cnt + 1) / 10001, 4)
    # line level (panel)
    hl = tx[(tx.category == "Hair Care") & tx.week.between(70, 77) & ~tx.return_flag & (tx.quantity > 0)].drop_duplicates("line_id")
    a["l34_panel_lines_test"] = int((hl.experiment_group == "test").sum())
    a["l34_panel_lines_ctrl"] = int((hl.experiment_group == "control").sum())
    # basket value weekend vs weekday; loyalty; bulk buyers
    s = tx[~tx.return_flag & (tx.quantity > 0)].drop_duplicates("line_id")
    s_clean = s[s.unit_price / s.list_price < 20]
    b = s_clean.groupby("basket_id").agg(rev=("revenue", "sum"), date=("date", "first"), loyal=("loyalty_flag", "first"),
                                         cust=("customer_id", "first"), promo=("promo_flag", "max"))
    b["dow"] = pd.to_datetime(b.date).dt.dayofweek
    wk = b[b.dow.isin([4, 5])].rev.values
    wd = b[b.dow.isin([0, 1, 2, 3])].rev.values
    d, lo, hi, p = M.welch_ci(wk, wd)
    a["l34_wkend_mean"], a["l34_wkday_mean"] = _r(wk.mean(), 2), _r(wd.mean(), 2)
    a["l34_wkend_median"], a["l34_wkday_median"] = _r(np.median(wk), 2), _r(np.median(wd), 2)
    a["l34_wkend_diff"], a["l34_wkend_ci_lo"], a["l34_wkend_ci_hi"], a["l34_wkend_p"] = _r(d, 2), _r(lo, 2), _r(hi, 2), _r(p, 4)
    a["l34_wkend_mw_p"] = _r(stats.mannwhitneyu(wk, wd).pvalue, 4)
    a["l34_wkend_n"], a["l34_wkday_n"] = len(wk), len(wd)
    a["l34_basket_skew"] = _r(pd.Series(b.rev).skew(), 1)
    rng = np.random.default_rng(11)
    bs = [np.median(rng.choice(wk, len(wk))) - np.median(rng.choice(wd, len(wd))) for _ in range(4000)]
    a["l34_wkend_median_diff"] = _r(np.median(wk) - np.median(wd), 2)
    a["l34_wkend_median_ci"] = [_r(np.percentile(bs, 2.5), 2), _r(np.percentile(bs, 97.5), 2)]
    seg = pd.read_parquet(ROOT / "instructor" / "truth" / "retail" / "customer_segments.parquet") if (ROOT / "instructor" / "truth" / "retail" / "customer_segments.parquet").exists() else None
    lo_ = b[b.loyal].rev.values
    nl_ = b[~b.loyal].rev.values
    a["l34_loyal_mean"], a["l34_nonloyal_mean"] = _r(lo_.mean(), 2), _r(nl_.mean(), 2)
    a["l34_loyal_welch_p"] = _r(stats.ttest_ind(lo_, nl_, equal_var=False).pvalue, 6)
    a["l34_loyal_mw_p"] = _r(stats.mannwhitneyu(lo_, nl_).pvalue, 6)
    top = s_clean.groupby("customer_id").revenue.sum().nlargest(25).index
    bb = b[~b.cust.isin(top)]
    a["l34_loyal_mean_excl_top25"] = _r(bb[bb.loyal].rev.mean(), 2)
    a["l34_nonloyal_mean_excl_top25"] = _r(bb[~bb.loyal].rev.mean(), 2)
    a["l34_mean_basket_with_errors"] = _r(s.groupby("basket_id").revenue.sum().mean(), 2)
    a["l34_mean_basket_clean"] = _r(b.rev.mean(), 2)
    # promo share of baskets, loyal vs non-loyal (binary per basket)
    x1, n1 = int(b[b.loyal].promo.sum()), int(b.loyal.sum())
    x0, n0 = int(b[~b.loyal].promo.sum()), int((~b.loyal).sum())
    p1, p0, z, pz, ci = _prop_test(x1, n1, x0, n0)
    a["l34_promo_basket_loyal_pct"], a["l34_promo_basket_nonloyal_pct"] = _r(100 * p1, 1), _r(100 * p0, 1)
    a["l34_promo_basket_p"] = _r(pz, 4)
    a["l34_promo_basket_ci_pp"] = [_r(100 * ci[0], 1), _r(100 * ci[1], 1)]
    # e-coupon naive
    ab = M.load("retail", "ecoupon_ab", data)
    c1 = ab[ab.assigned_arm == "treatment"].converted_14d
    c0 = ab[ab.assigned_arm == "control"].converted_14d
    p1, p0, z, pz, ci = _prop_test(c1.sum(), len(c1), c0.sum(), len(c0))
    a["l34_ab_conv_t"], a["l34_ab_conv_c"] = _r(100 * p1, 2), _r(100 * p0, 2)
    a["l34_ab_p"] = _r(pz, 3)
    a["l34_ab_n_t"], a["l34_ab_n_c"] = len(c1), len(c0)
    a["l34_ab_srm_p"] = float(M.R24(data)["srm_p"])

    # ---------------- L3.4 finance ----------------
    v = acc.groupby("income_verified_flag").default_12m.agg(["sum", "size", "mean"])
    p1, p0, z, pz, ci = _prop_test(v.loc[False, "sum"], v.loc[False, "size"], v.loc[True, "sum"], v.loc[True, "size"])
    a["l34_unver_rate"], a["l34_ver_rate"] = _r(100 * p1, 2), _r(100 * p0, 2)
    a["l34_unver_n"], a["l34_ver_n"] = int(v.loc[False, "size"]), int(v.loc[True, "size"])
    a["l34_unver_defaults"], a["l34_ver_defaults"] = int(v.loc[False, "sum"]), int(v.loc[True, "sum"])
    a["l34_ver_rd_pp"] = _r(100 * (p1 - p0), 2)
    assert a["l34_wkend_p"] > 0.05 if "l34_wkend_p" in a else True
    a["l34_ver_ci_pp"] = [_r(100 * ci[0], 2), _r(100 * ci[1], 2)]
    a["l34_ver_z"] = _r(z, 2)
    a["l34_ver_p"] = float(f"{pz:.3g}")
    a["l34_ver_rr"] = _r(p1 / p0, 2)
    a["l34_ver_or"] = _r((p1 / (1 - p1)) / (p0 / (1 - p0)), 2)
    a["l34_ver_per100"] = _r(100 * (p1 - p0), 1)
    se = np.sqrt(0.04 * 0.96 * 2)
    a["l34_n_per_group_05pp"] = int(np.ceil(((stats.norm.ppf(0.975) + stats.norm.ppf(0.8)) * se / 0.005) ** 2))
    # channel and stratification
    ch = acc.groupby("acquisition_channel").default_12m.agg(["mean", "size"])
    a["l34_def_by_channel_pct"] = {k: _r(100 * v_, 2) for k, v_ in ch["mean"].items()}
    a["l34_n_by_channel"] = {k: int(v_) for k, v_ in ch["size"].items()}
    strat = {}
    for chn in ("branch", "online", "partner"):
        x = acc[acc.acquisition_channel == chn].groupby("income_verified_flag").default_12m.mean()
        strat[chn] = {"unverified_pct": _r(100 * x[False], 2), "verified_pct": _r(100 * x[True], 2)}
    a["l34_ver_by_channel"] = strat
    a["l34_unver_share_partner_pct"] = _r(100 * (~acc[acc.acquisition_channel == "partner"].income_verified_flag).mean(), 1)
    a["l34_unver_share_other_pct"] = _r(100 * (~acc[acc.acquisition_channel != "partner"].income_verified_flag).mean(), 1)
    # bureau score defaulters vs not
    d1, d0 = acc[acc.default_12m].bureau_score.values, acc[~acc.default_12m].bureau_score.values
    d, lo, hi, p = M.welch_ci(d1, d0)
    sp = np.sqrt(((len(d1) - 1) * d1.var(ddof=1) + (len(d0) - 1) * d0.var(ddof=1)) / (len(d1) + len(d0) - 2))
    a["l34_bureau_def_mean"], a["l34_bureau_good_mean"] = _r(d1.mean(), 1), _r(d0.mean(), 1)
    a["l34_bureau_diff"], a["l34_bureau_ci"] = _r(d, 1), [_r(lo, 1), _r(hi, 1)]
    a["l34_bureau_d"] = _r(d / sp, 2)
    a["l34_bureau_overlap_auc"] = _r(stats.mannwhitneyu(d0, d1).statistic / (len(d0) * len(d1)), 3)
    c = acc[acc.product_type == "credit_card"]
    u1, u0 = c[c.default_12m].utilisation.values, c[~c.default_12m].utilisation.values
    a["l34_util_def_median"], a["l34_util_good_median"] = _r(np.median(u1), 3), _r(np.median(u0), 3)
    a["l34_util_mw_p"] = float(f"{stats.mannwhitneyu(u1, u0).pvalue:.3g}")
    a["l34_util_welch_p"] = float(f"{stats.ttest_ind(u1, u0, equal_var=False).pvalue:.3g}")
    # Fisher: top-1% income
    inc = acc[acc.income_annual > 0]
    hi_inc = inc.income_annual >= inc.income_annual.quantile(0.99)
    tab = pd.crosstab(hi_inc, inc.default_12m).reindex(index=[True, False], columns=[True, False], fill_value=0)
    a["l34_hni_n"], a["l34_hni_defaults"] = int(hi_inc.sum()), int(tab.loc[True, True])
    a["l34_hni_rate_pct"] = _r(100 * tab.loc[True, True] / hi_inc.sum(), 2)
    a["l34_hni_fisher_p"] = _r(stats.fisher_exact(tab.values)[1], 4)
    assert a["l34_hni_fisher_p"] > 0.05, "L3.4 F-A5 narrative assumes no evidence of a difference"
    exp = tab.values.sum(0)[0] * hi_inc.sum() / len(inc)
    a["l34_hni_expected_defaults"] = _r(exp, 1)
    f16 = M.F16(data)
    a["l34_cure_diff_pp"] = _r(100 * f16["measured"], 1)
    a["l34_cure_ci_pp"] = [_r(100 * f16["ci_low"], 1), _r(100 * f16["ci_high"], 1)]
    a["l34_cure_n_ch"], a["l34_cure_n_cp"] = f16["n_challenger"], f16["n_champion"]
    a["l34_acc_no_default_model_pct"] = _r(100 * (1 - acc.default_12m.mean()), 1)
    # median balance bootstrap
    rng = np.random.default_rng(5)
    b1, b0 = acc[acc.default_12m].balance_current.values, acc[~acc.default_12m].balance_current.values
    a["l34_bal_def_median"], a["l34_bal_good_median"] = _r(np.median(b1), 0), _r(np.median(b0), 0)
    bs = [np.median(rng.choice(b1, len(b1))) - np.median(rng.choice(b0, len(b0))) for _ in range(3000)]
    a["l34_bal_median_ci"] = [_r(np.percentile(bs, 2.5), 0), _r(np.percentile(bs, 97.5), 0)]
    # vintage-year stratification of verification effect
    acc2 = acc.assign(year=acc.vintage.str[:4])
    a["l34_ver_by_year"] = {y: {"unverified_pct": _r(100 * x[x.income_verified_flag == False].default_12m.mean(), 2),
                                "verified_pct": _r(100 * x[x.income_verified_flag].default_12m.mean(), 2)}
                            for y, x in acc2.groupby("year")}
    from .answers_day1 import compute_day1
    a.update(compute_day1(data))
    from .answers_day2 import compute_day2
    a.update(compute_day2(data))
    from .answers_day3 import compute_day3
    a.update(compute_day3(data))
    from .answers_day4 import compute_day4
    a.update(compute_day4(data))
    from .answers_day5 import compute_day5
    a.update(compute_day5(data))
    from .answers_day6 import compute_day6
    a.update(compute_day6(data))
    from .answers_day7 import compute_day7
    a.update(compute_day7(data))
    from .answers_day8 import compute_day8
    a.update(compute_day8(data))
    from .answers_day9 import compute_day9
    a.update(compute_day9(data))
    from .answers_day10 import compute_day10
    a.update(compute_day10(data))
    from .answers_ladder import compute_ladder
    a.update(compute_ladder(data))
    from .answers_vision import compute_vision
    a.update(compute_vision(data))
    return a


def save(path=ROOT / "validator" / "answers.json"):
    a = compute()
    Path(path).write_text(json.dumps(a, indent=2, default=str))
    return a


if __name__ == "__main__":
    a = save()
    print(f"{len(a)} answers computed")
    for k in list(a)[:200]:
        print(f"{k}: {a[k]}")
