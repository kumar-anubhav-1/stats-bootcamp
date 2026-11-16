"""Computed answers for Day 4 (experiments, CUPED, sequential, Bayesian A/B, DAGs, end-to-end tests). Keys d4_."""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

from . import measures as M


def _r(x, nd=4):
    return round(float(x), nd)


def _sig(x, n=3):
    return float(f"{float(x):.{n}g}")


def two_prop(k1, n1, k0, n0):
    p1, p0 = k1 / n1, k0 / n0
    se = np.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
    pp = (k1 + k0) / (n1 + n0)
    z = (p1 - p0) / np.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n0))
    return p1 - p0, p1 - p0 - 1.96 * se, p1 - p0 + 1.96 * se, 2 * stats.norm.sf(abs(z)), z


def obf_bounds(info, alpha=0.05, sims=200_000, seed=1):
    """Classical O'Brien-Fleming boundaries z_k = c / sqrt(t_k) for looks at information fractions t_k, with c calibrated by
    simulation so the overall two-sided false-positive rate equals alpha."""
    info = np.asarray(info, float)
    rng = np.random.default_rng(seed)
    inc = np.diff(np.concatenate([[0.0], info]))
    w = np.cumsum(rng.normal(size=(sims, len(info))) * np.sqrt(inc), axis=1) / np.sqrt(info)
    lo, hi = 1.5, 5.0
    for _ in range(40):
        c = (lo + hi) / 2
        fwer = (np.abs(w) >= c / np.sqrt(info)).any(axis=1).mean()
        lo, hi = (c, hi) if fwer > alpha else (lo, c)
    c = (lo + hi) / 2
    return list(c / np.sqrt(info)), c


def compute_day4(data=str(M.DATA)) -> dict:
    a: dict = {}
    ab = M.load("retail", "ecoupon_ab", data).copy()
    ab["c"] = ab.converted_14d.astype(float)
    acc = M.load("finance", "accounts", data)
    rng = np.random.default_rng(404)

    # ================= L4.1 A/B hygiene: SRM =================
    cnt = ab.assigned_arm.value_counts()
    a["d4_ab_n"], a["d4_ab_nt"], a["d4_ab_nc"] = len(ab), int(cnt["treatment"]), int(cnt["control"])
    a["d4_ab_share_t"] = _r(100 * cnt["treatment"] / len(ab), 1)
    a["d4_srm_chi2"] = _r(stats.chisquare(cnt.values).statistic, 1)
    a["d4_srm_p"] = _sig(stats.chisquare(cnt.values).pvalue, 2)
    seg = {}
    for v, g in ab.groupby("app_version"):
        c_ = g.assigned_arm.value_counts()
        seg[v] = {"t": int(c_.get("treatment", 0)), "c": int(c_.get("control", 0)), "p": _sig(stats.chisquare(c_.values).pvalue, 2)}
    a["d4_srm_by_version"] = seg
    plat = {}
    for v, g in ab.groupby("platform"):
        c_ = g.assigned_arm.value_counts()
        plat[v] = _sig(stats.chisquare(c_.values).pvalue, 2)
    a["d4_srm_by_platform"] = plat
    conv = ab.groupby("assigned_arm").c.agg(["sum", "size", "mean"])
    d, lo, hi, p, _ = two_prop(conv.loc["treatment", "sum"], conv.loc["treatment", "size"], conv.loc["control", "sum"], conv.loc["control", "size"])
    a["d4_naive_t"], a["d4_naive_c"] = _r(100 * conv.loc["treatment", "mean"], 2), _r(100 * conv.loc["control", "mean"], 2)
    a["d4_naive_lift_pp"], a["d4_naive_ci"], a["d4_naive_p"] = _r(100 * d, 2), [_r(100 * lo, 2), _r(100 * hi, 2)], _r(p, 3)
    v32 = ab[ab.app_version == "3.2"].groupby("assigned_arm").c.mean()
    a["d4_v32_conv_c"], a["d4_v32_conv_t"] = _r(100 * v32["control"], 1), _r(100 * v32["treatment"], 1)
    cl = ab[ab.app_version != "3.2"]
    cc = cl.groupby("assigned_arm").c.agg(["sum", "size", "mean"])
    a["d4_clean_srm_p"] = _r(stats.chisquare(cl.assigned_arm.value_counts().values).pvalue, 3)
    d, lo, hi, p, z = two_prop(cc.loc["treatment", "sum"], cc.loc["treatment", "size"], cc.loc["control", "sum"], cc.loc["control", "size"])
    a["d4_clean_n"] = len(cl)
    a["d4_clean_t"], a["d4_clean_c"] = _r(100 * cc.loc["treatment", "mean"], 2), _r(100 * cc.loc["control", "mean"], 2)
    a["d4_clean_lift_pp"], a["d4_clean_ci"], a["d4_clean_p"] = _r(100 * d, 2), [_r(100 * lo, 2), _r(100 * hi, 2)], _r(p, 4)
    a["d4_true_lift_pp"] = 1.5
    # guardrail: revenue per user in clean data (Welch)
    rt = cl[cl.assigned_arm == "treatment"].revenue_14d
    rc = cl[cl.assigned_arm == "control"].revenue_14d
    dd, l_, h_, pp_ = M.welch_ci(rt, rc)
    a["d4_rev_t"], a["d4_rev_c"] = _r(rt.mean(), 2), _r(rc.mean(), 2)
    a["d4_rev_diff"], a["d4_rev_ci"], a["d4_rev_p"] = _r(dd, 2), [_r(l_, 2), _r(h_, 2)], _r(pp_, 3)
    # pre-period balance (randomisation check on a pre-treatment covariate)
    a["d4_pre_balance_p"] = _r(stats.ttest_ind(cl[cl.assigned_arm == "treatment"].pre_period_spend_30d,
                                               cl[cl.assigned_arm == "control"].pre_period_spend_30d, equal_var=False).pvalue, 3)
    # card-offer design (finance): customers to randomise for +1 pp take-up from 6% base, stratified
    from toolkit.rcp_power.recipe import n_props
    a["d4_card_n_per_arm"] = int(np.ceil(n_props(0.06, 0.07, 0.05, 0.8)))

    # ================= L4.2 CUPED and sequential =================
    sc = M.load("retail", "weekly_store_category", data)
    h = sc[sc.category == "Hair Care"]
    pre = h[h.week.between(54, 69)].groupby("store_id").units.mean()
    post = h[h.week.between(70, 77)].groupby("store_id").units.mean()
    grp = h.groupby("store_id").experiment_group.first()
    df = pd.DataFrame({"pre": pre, "post": post, "t": (grp == "test").astype(int)})
    a["d4_store_corr"] = _r(np.corrcoef(df.pre, df.post)[0, 1], 3)
    m0 = smf.ols("post ~ t", df).fit()
    th = np.cov(df.post, df.pre)[0, 1] / df.pre.var()
    df["cuped"] = df.post - th * (df.pre - df.pre.mean())
    m1 = smf.ols("cuped ~ t", df).fit()
    m2 = smf.ols("post ~ t + pre", df).fit()
    cm = df.post[df.t == 0].mean()
    a["d4_store_theta"] = _r(th, 3)
    a["d4_store_varred_pct"] = _r(100 * (1 - df.cuped.var() / df.post.var()), 1)
    a["d4_store_raw_diff"], a["d4_store_raw_se"], a["d4_store_raw_p"] = _r(m0.params.t, 2), _r(m0.bse.t, 2), _r(m0.pvalues.t, 3)
    a["d4_store_cuped_diff"], a["d4_store_cuped_se"], a["d4_store_cuped_p"] = _r(m1.params.t, 2), _r(m1.bse.t, 2), _sig(m1.pvalues.t, 2)
    a["d4_store_cuped_lift_pct"] = _r(100 * m1.params.t / cm, 1)
    ci1 = m1.conf_int().loc["t"]
    a["d4_store_cuped_ci_pct"] = [_r(100 * ci1[0] / cm, 1), _r(100 * ci1[1] / cm, 1)]
    a["d4_store_ancova_p"] = _sig(m2.pvalues.t, 2)
    a["d4_store_se_ratio"] = _r(m0.bse.t / m1.bse.t, 1)
    # CUPED on e-coupon conversion (weak covariate)
    x = np.log(cl.pre_period_spend_30d)
    a["d4_ec_corr"] = _r(np.corrcoef(x, cl.c)[0, 1], 3)
    the = np.cov(cl.c, x)[0, 1] / x.var()
    cy = cl.c - the * (x - x.mean())
    a["d4_ec_varred_pct"] = _r(100 * (1 - cy.var() / cl.c.var()), 1)
    mt = cl.assigned_arm == "treatment"
    se_raw = np.sqrt(cl.c[mt].var() / mt.sum() + cl.c[~mt].var() / (~mt).sum())
    se_cup = np.sqrt(cy[mt].var() / mt.sum() + cy[~mt].var() / (~mt).sum())
    a["d4_ec_cuped_lift_pp"] = _r(100 * (cy[mt].mean() - cy[~mt].mean()), 2)
    a["d4_ec_cuped_p"] = _r(2 * stats.norm.sf(abs((cy[mt].mean() - cy[~mt].mean()) / se_cup)), 4)
    a["d4_ec_se_raw_pp"], a["d4_ec_se_cup_pp"] = _r(100 * se_raw, 3), _r(100 * se_cup, 3)
    a["d4_ec_n_saving_pct"] = _r(100 * (1 - (se_cup / se_raw) ** 2), 1)
    # sequential: daily cumulative looks over 14 assignment days (clean data)
    days = sorted(cl.assignment_date.unique())
    looks = []
    for i, dday in enumerate(days):
        sub = cl[cl.assignment_date <= dday]
        g_ = sub.groupby("assigned_arm").c.agg(["sum", "size"])
        _, _, _, p_, z_ = two_prop(g_.loc["treatment", "sum"], g_.loc["treatment", "size"], g_.loc["control", "sum"], g_.loc["control", "size"])
        looks.append({"day": i + 1, "n": len(sub), "z": float(z_), "p": float(p_)})
    info = np.array([l["n"] for l in looks], float) / looks[-1]["n"]
    bnd, c_obf = obf_bounds(info)
    a["d4_obf_c"] = _r(c_obf, 2)
    a["d4_seq_days"] = len(days)
    a["d4_seq_z"] = [_r(l["z"], 2) for l in looks]
    a["d4_seq_bounds"] = [_r(b, 2) for b in bnd]
    a["d4_seq_first_naive"] = next((l["day"] for l in looks if l["p"] < 0.05), None)
    a["d4_seq_first_obf"] = next((l["day"] for l, b in zip(looks, bnd) if abs(l["z"]) >= b), None)
    a["d4_seq_final_z"], a["d4_seq_final_bound"] = _r(looks[-1]["z"], 2), _r(bnd[-1], 2)
    a["d4_seq_naive_days_sig"] = int(sum(l["p"] < 0.05 for l in looks))
    a["d4_seq_bound_day1"], a["d4_seq_bound_day7"] = _r(bnd[0], 2), _r(bnd[min(6, len(bnd) - 1)], 2)

    # ================= L4.3 Bayesian A/B =================
    kt, nt = cc.loc["treatment", "sum"], cc.loc["treatment", "size"]
    kc, nc = cc.loc["control", "sum"], cc.loc["control", "size"]
    S = 200_000
    pt = rng.beta(1 + kt, 1 + nt - kt, S)
    pc = rng.beta(1 + kc, 1 + nc - kc, S)
    a["d4_bayes_p_better"] = _r(100 * (pt > pc).mean(), 1)
    diff = pt - pc
    a["d4_bayes_ci_pp"] = [_r(100 * np.percentile(diff, 2.5), 2), _r(100 * np.percentile(diff, 97.5), 2)]
    a["d4_bayes_mean_pp"] = _r(100 * diff.mean(), 2)
    a["d4_bayes_p_gt1pp"] = _r(100 * (diff > 0.01).mean(), 1)
    a["d4_bayes_loss_t_pp"] = _r(100 * np.maximum(pc - pt, 0).mean(), 3)
    a["d4_bayes_loss_c_pp"] = _r(100 * np.maximum(pt - pc, 0).mean(), 3)
    # informative prior from previous coupon tests: lift ~ N(0.5 pp, 0.5 pp) — expressed through control-rate prior Beta
    # (sceptical prior on the difference, normal approximation)
    se_d = np.sqrt(kt / nt * (1 - kt / nt) / nt + kc / nc * (1 - kc / nc) / nc)
    dhat = kt / nt - kc / nc
    pm, ps = 0.002, 0.004
    post_var = 1 / (1 / ps ** 2 + 1 / se_d ** 2)
    post_mean = post_var * (pm / ps ** 2 + dhat / se_d ** 2)
    a["d4_bayes_skept_mean_pp"] = _r(100 * post_mean, 2)
    a["d4_bayes_skept_ci_pp"] = [_r(100 * (post_mean - 1.96 * np.sqrt(post_var)), 2), _r(100 * (post_mean + 1.96 * np.sqrt(post_var)), 2)]
    a["d4_bayes_skept_p_better"] = _r(100 * stats.norm.sf(0, post_mean, np.sqrt(post_var)), 1)
    # finance: prior for a new segment's default rate (students via partner, latest vintage)
    stu_hist = acc[(acc.employment_type == "student") & (acc.vintage < "2025Q1")].default_12m
    new = acc[(acc.employment_type == "student") & (acc.acquisition_channel == "partner") & (acc.vintage == "2025Q3")].default_12m
    p0 = stu_hist.mean()
    m_eff = 100
    a0, b0 = p0 * m_eff, (1 - p0) * m_eff
    k, n = int(new.sum()), len(new)
    a1, b1 = a0 + k, b0 + n - k
    a["d4_prior_rate_pct"] = _r(100 * p0, 2)
    a["d4_prior_eff_n"] = m_eff
    a["d4_new_k"], a["d4_new_n"] = k, n
    a["d4_new_raw_pct"] = _r(100 * k / n, 2)
    a["d4_post_mean_pct"] = _r(100 * a1 / (a1 + b1), 2)
    a["d4_post_ci_pct"] = [_r(100 * stats.beta.ppf(0.025, a1, b1), 2), _r(100 * stats.beta.ppf(0.975, a1, b1), 2)]
    a["d4_post_p_gt10"] = _r(100 * stats.beta.sf(0.10, a1, b1), 1)
    from statsmodels.stats.proportion import proportion_confint
    lo_, hi_ = proportion_confint(k, n, method="wilson")
    a["d4_new_wilson"] = [_r(100 * lo_, 2), _r(100 * hi_, 2)]

    # ================= L4.4 DAGs: confounding (R15/R14) and collider/selection =================
    tx = M.load("retail", "transactions", data)
    s = tx[~tx.return_flag & (tx.quantity > 0)].drop_duplicates("line_id")
    s = s[s.unit_price / s.list_price < 20].copy()
    s["lq"] = np.log(s.quantity)
    fits = {
        "naive": smf.ols("lq ~ promo_flag", s).fit(),
        "format": smf.ols("lq ~ promo_flag + C(format)", s).fit(),
        "format_display": smf.ols("lq ~ promo_flag + display_flag + C(format)", s).fit(),
    }
    for k_, m_ in fits.items():
        b_ = m_.params["promo_flag[T.True]"]
        ci_ = m_.conf_int().loc["promo_flag[T.True]"]
        a[f"d4_promo_{k_}_pct"] = _r(100 * (np.exp(b_) - 1), 1)
        a[f"d4_promo_{k_}_ci"] = [_r(100 * (np.exp(ci_[0]) - 1), 1), _r(100 * (np.exp(ci_[1]) - 1), 1)]
    md = fits["format_display"]
    a["d4_display_pct"] = _r(100 * (np.exp(md.params["display_flag[T.True]"]) - 1), 1)
    cid = md.conf_int().loc["display_flag[T.True]"]
    a["d4_display_ci"] = [_r(100 * (np.exp(cid[0]) - 1), 1), _r(100 * (np.exp(cid[1]) - 1), 1)]
    r15 = M.R15(data)
    a["d4_disp_given_promo"], a["d4_disp_given_nonpromo"] = _r(100 * r15["measured"], 1), _r(100 * r15["display_rate_non_promo"], 1)
    a["d4_promo_no_display_n"] = int((s.promo_flag & ~s.display_flag).sum())
    a["d4_nonpromo_display_n"] = int((~s.promo_flag & s.display_flag).sum())
    a["d4_true_promo_pct"], a["d4_true_display_pct"] = 15, 10
    a["d4_express_promo_share"] = _r(100 * s[s.format == "Express"].promo_flag.mean(), 1)
    # mediator mistake: adjusting for basket size (a consequence of promotion) — basket line count
    # collider / selection: approval depends on bureau score and delinquency
    dec = M.load("finance", "applications_declined", data)
    cols = ["bureau_score", "delinq_2y", "inquiries_6m"]
    allap = pd.concat([acc[cols], dec[cols]])
    a["d4_corr_bd_all"] = _r(allap.corr().loc["bureau_score", "delinq_2y"], 3)
    a["d4_corr_bd_booked"] = _r(acc[cols].corr().loc["bureau_score", "delinq_2y"], 3)
    a["d4_corr_id_all"] = _r(allap.corr().loc["inquiries_6m", "delinq_2y"], 3)
    a["d4_corr_id_booked"] = _r(acc[cols].corr().loc["inquiries_6m", "delinq_2y"], 3)
    a["d4_n_applicants"], a["d4_n_declined"] = len(allap), len(dec)
    lowb = allap.bureau_score <= 600
    a["d4_delinq_low_all"] = _r(100 * (allap[lowb].delinq_2y > 0).mean(), 1)
    a["d4_delinq_low_booked"] = _r(100 * (acc[acc.bureau_score <= 600].delinq_2y > 0).mean(), 1)

    # ================= L4.5 end-to-end =================
    r09 = M.R09(data)
    a["d4_r09_lift"], a["d4_r09_ci"], a["d4_r09_p"] = _r(100 * r09["measured"], 1), [_r(100 * r09["ci_low"], 1), _r(100 * r09["ci_high"], 1)], _r(r09["p_value"], 4)
    # guardrail: other categories in test stores (halo / cannibalisation) and Hair Care revenue
    others = sc[(sc.category != "Hair Care")]
    opre = others[others.week.between(54, 69)].groupby("store_id").revenue.sum() / 16
    opost = others[others.week.between(70, 77)].groupby("store_id").revenue.sum() / 8
    og = opost / opre
    og = og / og[grp == "control"].mean()
    d_, l_, h_, p_ = M.welch_ci(og[grp == "test"], og[grp == "control"])
    a["d4_guard_other_pct"], a["d4_guard_other_ci"], a["d4_guard_other_p"] = _r(100 * d_, 1), [_r(100 * l_, 1), _r(100 * h_, 1)], _r(p_, 3)
    hr_pre = h[h.week.between(54, 69)].groupby("store_id").revenue.mean()
    hr_post = h[h.week.between(70, 77)].groupby("store_id").revenue.mean()
    hg = hr_post / hr_pre
    hg = hg / hg[grp == "control"].mean()
    d_, l_, h_, p_ = M.welch_ci(hg[grp == "test"], hg[grp == "control"])
    a["d4_hc_rev_lift"], a["d4_hc_rev_ci"] = _r(100 * d_, 1), [_r(100 * l_, 1), _r(100 * h_, 1)]
    # stores balance (SRM analogue at cluster level)
    a["d4_store_counts"] = {"test": int((grp == "test").sum()), "control": int((grp == "control").sum())}
    # finance champion/challenger
    f16 = M.F16(data)
    a["d4_f16_diff"], a["d4_f16_ci"] = _r(100 * f16["measured"], 1), [_r(100 * f16["ci_low"], 1), _r(100 * f16["ci_high"], 1)]
    g16 = acc[acc.strategy_group != "none"].groupby("strategy_group").cured_within_3m.agg(["sum", "size"])
    a["d4_f16_p"] = _sig(two_prop(g16.loc["challenger", "sum"], g16.loc["challenger", "size"], g16.loc["champion", "sum"], g16.loc["champion", "size"])[3], 2)
    cc_ = acc[acc.strategy_group != "none"]
    sh = (cc_.strategy_group == "challenger").mean()
    a["d4_f16_share_ch"] = _r(100 * sh, 1)
    a["d4_f16_srm_p"] = _r(stats.binomtest(int((cc_.strategy_group == "challenger").sum()), len(cc_), 0.2).pvalue, 3)
    comp = cc_.groupby("strategy_group").complaints_12m.mean()
    d_, l_, h_, p_ = M.welch_ci(cc_[cc_.strategy_group == "challenger"].complaints_12m, cc_[cc_.strategy_group == "champion"].complaints_12m)
    a["d4_f16_compl_ch"], a["d4_f16_compl_cp"] = _r(comp["challenger"], 3), _r(comp["champion"], 3)
    a["d4_f16_compl_diff"], a["d4_f16_compl_ci"], a["d4_f16_compl_p"] = _r(d_, 3), [_r(l_, 3), _r(h_, 3)], _r(p_, 3)
    rec = cc_.groupby("strategy_group").recovery_amount.mean()
    a["d4_f16_rec_ch"], a["d4_f16_rec_cp"] = _r(rec["challenger"], 0), _r(rec["champion"], 0)
    d_, l_, h_, p_ = M.welch_ci(cc_[cc_.strategy_group == "challenger"].recovery_amount, cc_[cc_.strategy_group == "champion"].recovery_amount)
    a["d4_f16_rec_diff"], a["d4_f16_rec_ci"], a["d4_f16_rec_p"] = _r(d_, 0), [_r(l_, 0), _r(h_, 0)], _sig(p_, 2)
    # balance on pre-treatment covariates
    bal = {}
    for col in ["bureau_score", "utilisation", "balance_current", "dti"]:
        x1, x0 = cc_[cc_.strategy_group == "challenger"][col].dropna(), cc_[cc_.strategy_group == "champion"][col].dropna()
        bal[col] = _r((x1.mean() - x0.mean()) / np.sqrt((x1.var() + x0.var()) / 2), 3)
    a["d4_f16_smd"] = bal
    a["d4_f16_max_smd"] = _r(max(abs(v) for v in bal.values()), 3)

    checks = {
        "SRM severe": a["d4_srm_p"] < 1e-5,
        "SRM located in 3.2 only": seg["3.2"]["p"] < 1e-5 and seg["3.1"]["p"] > 0.05 and seg["3.3"]["p"] > 0.05,
        "naive lift not significant": a["d4_naive_p"] > 0.05,
        "clean lift significant and near truth": a["d4_clean_p"] < 0.05 and a["d4_clean_ci"][0] < 1.5 < a["d4_clean_ci"][1],
        "v32 control inflated": a["d4_v32_conv_c"] > a["d4_v32_conv_t"],
        "clean SRM gone": a["d4_clean_srm_p"] > 0.05,
        "store CUPED big reduction": a["d4_store_varred_pct"] > 80 and a["d4_store_raw_p"] > 0.2 and a["d4_store_cuped_p"] < 0.01,
        "ecoupon CUPED small": a["d4_ec_varred_pct"] < 5,
        "naive peeking signals earlier than OBF or OBF never": a["d4_seq_first_obf"] is None or (a["d4_seq_first_naive"] is not None and a["d4_seq_first_naive"] <= a["d4_seq_first_obf"]),
        "bayes P(better) high": a["d4_bayes_p_better"] > 95,
        "sceptical prior shrinks": a["d4_bayes_skept_mean_pp"] < a["d4_clean_lift_pp"],
        "posterior between prior and raw": min(a["d4_prior_rate_pct"], a["d4_new_raw_pct"]) <= a["d4_post_mean_pct"] <= max(a["d4_prior_rate_pct"], a["d4_new_raw_pct"]),
        "new segment small": 40 <= a["d4_new_n"] <= 600,
        "naive promo negative": a["d4_promo_naive_pct"] < 0,
        "format-adjusted promo above truth": a["d4_promo_format_pct"] > a["d4_promo_format_display_pct"],
        "fully adjusted near 15": 8 < a["d4_promo_format_display_pct"] < 23,
        "display imprecise": a["d4_display_ci"][1] - a["d4_display_ci"][0] > 5,
        "selection attenuates": abs(a["d4_corr_bd_booked"]) < abs(a["d4_corr_bd_all"]) / 2,
        "guardrail other cats ns": a["d4_guard_other_p"] > 0.05,
        "F16 no SRM": a["d4_f16_srm_p"] > 0.01,
        "F16 complaints ns": a["d4_f16_compl_p"] > 0.05,
        "F16 balanced": a["d4_f16_max_smd"] < 0.1,
        "OBF stops late": a["d4_seq_first_obf"] is not None and a["d4_seq_first_obf"] >= 10,
        "z dips below 1.96 after first naive stop": min(a["d4_seq_z"][a["d4_seq_first_naive"]:]) < 1.96,
        "HC revenue lift CI excludes 0": a["d4_hc_rev_ci"][0] > 0,
        "F16 CI low above 2pp": a["d4_f16_ci"][0] >= 2.0,
        "R09 threshold 10 inside CI": a["d4_r09_ci"][0] < 10 < a["d4_r09_ci"][1],
        "posterior > 10% likely": a["d4_post_p_gt10"] > 80,
        "naive peeking early": a["d4_seq_first_naive"] is not None and a["d4_seq_first_naive"] <= 7,
    }
    bad = [k_ for k_, ok in checks.items() if not ok]
    if bad and __import__("os").environ.get("SB_NOGUARD"):
        print("GUARDS", bad)
    else:
        assert not bad, f"Day 4 narrative guards failed: {bad}"
    return a
