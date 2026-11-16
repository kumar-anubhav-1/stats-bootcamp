"""Computed answers for Day 9 (causal methods, survival, deep learning vs GBM, insurance and portfolio risk, fairness and conformal
prediction, monitoring and drift, storytelling). Keys d9_."""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

from . import measures as M

warnings.filterwarnings("ignore")


def _r(x, nd=3):
    return round(float(x), nd)


def twfe(y, d, unit, time, iters=30):
    """Two-way fixed-effects coefficient of d on y by alternating demeaning (balanced or not)."""
    df = pd.DataFrame({"y": y.values, "d": d.astype(float).values, "u": unit.values, "t": time.values})
    for _ in range(iters):
        for col in ("y", "d"):
            df[col] -= df.groupby("u")[col].transform("mean")
            df[col] -= df.groupby("t")[col].transform("mean")
    b = (df.d * df.y).sum() / (df.d ** 2).sum()
    resid = df.y - b * df.d
    # cluster-robust SE by unit
    g = (df.d * resid).groupby(df.u).sum()
    se = np.sqrt((g ** 2).sum()) / (df.d ** 2).sum()
    return float(b), float(se)


def km_at(sf, t):
    tt, s = sf.surv_times, sf.surv_prob
    idx = np.searchsorted(tt, t, side="right") - 1
    return float(s[idx]) if idx >= 0 else 1.0


def compute_day9(data=str(M.DATA)) -> dict:
    a: dict = {}
    acc = M.load("finance", "accounts", data)

    # ================= L9.1 causal =================
    r9 = M.R09(data)
    a["d9_r09_did_ratio"] = _r(100 * r9["measured"], 1)
    a["d9_r09_naive_post"] = _r(100 * r9["naive_post_lift"], 1)
    a["d9_r09_naive_p"] = r9["naive_p_value"]
    sc = M.load("retail", "weekly_store_category", data)
    h = sc[(sc.category == "Hair Care") & sc.week.between(54, 77)].copy()
    h["treat"] = (h.experiment_group == "test").astype(int)
    h["post"] = (h.week >= 70).astype(int)
    h["ly"] = np.log(h.units.clip(lower=1))
    b, se = twfe(h.ly, h.treat * h.post, h.store_id, h.week)
    a["d9_r09_twfe_pct"] = _r(100 * (np.exp(b) - 1), 1)
    a["d9_r09_twfe_ci"] = [_r(100 * (np.exp(b - 1.96 * se) - 1), 1), _r(100 * (np.exp(b + 1.96 * se) - 1), 1)]
    pre = h[h.week < 70]
    m = smf.ols("ly ~ C(store_id) + C(week) + treat:week", pre).fit(cov_type="cluster", cov_kwds={"groups": pre.store_id})
    a["d9_r09_pretrend_slope"] = _r(100 * m.params["treat:week"], 2)
    a["d9_r09_pretrend_p"] = _r(m.pvalues["treat:week"], 3)
    # event study (week-by-week test effects relative to week 69)
    ev = {}
    for w in range(54, 78):
        if w == 69:
            continue
        sub = h[h.week.isin([69, w])]
        bb, _ = twfe(sub.ly, sub.treat * (sub.week == w), sub.store_id, sub.week, iters=5)
        ev[w] = _r(100 * bb, 1)
    a["d9_r09_event"] = ev
    a["d9_r09_pre_max_abs"] = _r(max(abs(v) for w, v in ev.items() if w < 69), 1)

    # R20 loyalty: naive vs adjusted vs within-customer (joiners) two-way FE
    r20 = M.R20(data)
    a["d9_r20_naive"] = _r(100 * r20["measured"], 1)
    tx = M.load("retail", "transactions", data).drop_duplicates("line_id")
    cust = M.load("retail", "customers", data)
    seg = pd.read_parquet(M.ROOT / "instructor" / "truth" / "retail" / "customer_segments.parquet")
    s = tx[~tx.return_flag & (tx.quantity > 0) & (tx.unit_price / tx.list_price < 50) & tx.customer_id.notna()]
    s = s[~s.customer_id.isin(seg[seg.bulk].customer_id)]
    bk = s.groupby("basket_id").agg(rev=("revenue", "sum"), loyal=("loyalty_flag", "first"), cid=("customer_id", "first"),
                                    week=("week", "first"), store=("store_id", "first"), date=("date", "first")).reset_index()
    bk = bk.merge(cust[["customer_id", "loyalty_flag", "signup_date", "age_band", "household_size"]].rename(
        columns={"customer_id": "cid", "loyalty_flag": "member"}), on="cid", how="left")
    bk["lrev"] = np.log(bk.rev)
    start = pd.Timestamp(tx.date.min())
    bk["joiner"] = bk.member & (pd.to_datetime(bk.signup_date) > start + pd.Timedelta(days=60))
    bk["age_band"] = bk.age_band.fillna("unknown")
    bk["hh"] = bk.household_size.astype("float").fillna(-1).astype(int).astype(str)
    ma = smf.ols("lrev ~ loyal + C(age_band) + C(hh) + C(store) + C(week)", bk).fit()
    a["d9_r20_adj_demo"] = _r(100 * (np.exp(ma.params["loyal[T.True]"]) - 1), 1)
    w = bk[bk.joiner | ~bk.member]
    b, se = twfe(w.lrev, w.loyal, w.cid, w.week)
    a["d9_r20_twfe"] = _r(100 * (np.exp(b) - 1), 1)
    a["d9_r20_twfe_ci"] = [_r(100 * (np.exp(b - 1.96 * se) - 1), 1), _r(100 * (np.exp(b + 1.96 * se) - 1), 1)]
    a["d9_r20_n_joiners"] = int(bk[bk.joiner].cid.nunique())
    a["d9_r20_true"] = 5.0
    # pre-join spend of joiners vs never-members (selection evidence)
    pj = bk[bk.joiner & ~bk.loyal].groupby("cid").rev.mean().mean()
    nm = bk[~bk.member].groupby("cid").rev.mean().mean()
    a["d9_r20_prejoin_gap"] = _r(100 * (pj / nm - 1), 1)
    f16 = M.F16(data)
    a["d9_f16_diff"] = _r(100 * f16["measured"], 1)
    a["d9_f16_ci"] = [_r(100 * f16["ci_low"], 1), _r(100 * f16["ci_high"], 1)]

    # ================= L9.2 survival =================
    from statsmodels.duration.hazard_regression import PHReg
    from statsmodels.duration.survfunc import SurvfuncRight, survdiff
    T, E = acc.months_observed.astype(float), acc.churn_flag.astype(int)
    sf = SurvfuncRight(T.values, E.values)
    a["d9_censored_pct"] = _r(100 * (1 - E.mean()), 1)
    a["d9_km_s6"], a["d9_km_s12"], a["d9_km_s24"] = (_r(100 * km_at(sf, t), 1) for t in (6, 12, 24))
    a["d9_naive_churn_rate"] = _r(100 * E.mean(), 1)
    a["d9_naive_mean_churners"] = _r(acc[acc.churn_flag].churn_month.astype(float).mean(), 1)
    grid = np.arange(0, 24)
    a["d9_rmst24"] = _r(sum(km_at(sf, t) for t in grid), 1)
    comp = (acc.complaints_12m >= 1).astype(int)
    for k, lab in ((0, "none"), (1, "any")):
        sfg = SurvfuncRight(T[comp == k].values, E[comp == k].values)
        a[f"d9_km_s24_compl_{lab}"] = _r(100 * km_at(sfg, 24), 1)
    stat, p = survdiff(T.values, E.values, comp.values)
    a["d9_logrank_chi2"], a["d9_logrank_p"] = _r(stat, 1), float(f"{p:.2g}")
    X = pd.DataFrame({"complaints_12m": acc.complaints_12m, "digital_share_10pp": acc.digital_share * 10,
                      "interest_rate_pp": acc.interest_rate * 100 if acc.interest_rate.max() < 1.5 else acc.interest_rate,
                      "tenure_years": acc.tenure_months_with_bank / 12})
    cox = PHReg(T.values, X.values, status=E.values, ties="efron").fit()
    hr = np.exp(cox.params)
    ci = np.exp(cox.conf_int())
    a["d9_cox"] = {c: {"hr": _r(hr[i], 3), "ci": [_r(ci[i][0], 3), _r(ci[i][1], 3)], "p": float(f"{cox.pvalues[i]:.2g}")}
                   for i, c in enumerate(X.columns)}
    # PH check: complaints HR in months 1–12 vs 13–24
    e1 = (E.values == 1) & (T.values <= 12)
    c1 = PHReg(np.minimum(T.values, 12), X.values, status=e1.astype(int), ties="efron").fit()
    keep = T.values > 12
    c2 = PHReg(T.values[keep] - 12, X.values[keep], status=E.values[keep], ties="efron").fit()
    a["d9_ph_hr_early"], a["d9_ph_hr_late"] = _r(np.exp(c1.params[0]), 3), _r(np.exp(c2.params[0]), 3)
    # retail: time to repeat purchase
    bas = tx[~tx.return_flag & tx.customer_id.notna()].drop_duplicates("basket_id")[["customer_id", "date"]]
    bas["date"] = pd.to_datetime(bas.date)
    bas = bas.sort_values(["customer_id", "date"])
    end = bas.date.max()
    late = bas[bas.date >= end - pd.Timedelta(days=364)]
    g = late.groupby("customer_id").date
    first = g.min()
    second = late.groupby("customer_id").date.apply(lambda x: x[x > x.min()].min() if (x > x.min()).any() else pd.NaT)
    gap = (second - first).dt.days
    ev_ = gap.notna()
    dur = gap.fillna((end - first).dt.days).clip(lower=1)
    sfr = SurvfuncRight(dur.values.astype(float), ev_.values.astype(int))
    a["d9_repeat_median_days"] = _r(sfr.quantile(0.5), 0)
    loy = cust.set_index("customer_id").loyalty_flag.reindex(dur.index).fillna(False)
    for k, lab in ((True, "member"), (False, "non")):
        sfl = SurvfuncRight(dur[loy == k].values.astype(float), ev_[loy == k].values.astype(int))
        a[f"d9_repeat_median_{lab}"] = _r(sfl.quantile(0.5), 0)
    a["d9_repeat_censored"] = _r(100 * (1 - ev_.mean()), 1)

    # ================= L9.3 deep learning vs GBM =================
    feat = ["bureau_score", "dti", "inquiries_6m", "delinq_2y", "utilisation", "income_annual", "digital_share", "interest_rate"]
    d = acc[feat + ["default_12m"]].copy()
    d["util_missing"] = d.utilisation.isna().astype(int)
    d["inc_missing"] = d.income_annual.isna().astype(int)
    d["utilisation"] = d.utilisation.fillna(0)
    d["income_annual"] = np.log1p(d.income_annual.clip(lower=0).fillna(d.income_annual.median()))
    Xd, yd = d.drop(columns="default_12m").astype(float), d.default_12m.astype(int)
    Xtr, Xte, ytr, yte = train_test_split(Xd, yd, test_size=0.3, random_state=0, stratify=yd)
    sc_ = StandardScaler().fit(Xtr)
    res = {}
    lr = LogisticRegression(max_iter=3000).fit(sc_.transform(Xtr), ytr)
    res["logistic"] = roc_auc_score(yte, lr.predict_proba(sc_.transform(Xte))[:, 1])
    gb = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, random_state=0).fit(Xtr, ytr)
    res["gbm"] = roc_auc_score(yte, gb.predict_proba(Xte)[:, 1])
    mlp = MLPClassifier(hidden_layer_sizes=(32, 16), alpha=1e-2, max_iter=400, random_state=0).fit(sc_.transform(Xtr), ytr)
    res["mlp"] = roc_auc_score(yte, mlp.predict_proba(sc_.transform(Xte))[:, 1])
    a["d9_dl_auc"] = {k: _r(v, 3) for k, v in res.items()}
    # small data: 1,500 training rows
    idx = Xtr.sample(1500, random_state=1).index
    small = {}
    sc2 = StandardScaler().fit(Xtr.loc[idx])
    small["logistic"] = roc_auc_score(yte, LogisticRegression(max_iter=3000).fit(sc2.transform(Xtr.loc[idx]), ytr.loc[idx]).predict_proba(sc2.transform(Xte))[:, 1])
    small["mlp"] = roc_auc_score(yte, MLPClassifier(hidden_layer_sizes=(32, 16), alpha=1e-2, max_iter=400,
                                                    random_state=0).fit(sc2.transform(Xtr.loc[idx]), ytr.loc[idx]).predict_proba(sc2.transform(Xte))[:, 1])
    a["d9_dl_small_auc"] = {k: _r(v, 3) for k, v in small.items()}
    a["d9_dl_n_params"] = int(sum(c.size for c in mlp.coefs_) + sum(c.size for c in mlp.intercepts_))
    a["d9_dl_lr_params"] = int(Xd.shape[1] + 1)

    # ================= L9.4 insurance and portfolio risk =================
    f17 = M.F17(data)
    pol = M.load("finance", "policies", data)
    cl = M.load("finance", "claims", data)
    a["d9_ins_dispersion"] = f17["measured"]
    a["d9_ins_freq"] = _r(f17["claim_frequency"], 4)
    a["d9_ins_mean_sev"], a["d9_ins_median_sev"] = f17["mean_severity"], f17["median_severity"]
    a["d9_ins_top3_share"] = _r(100 * f17["top3_share_of_losses"], 1)
    a["d9_ins_loss_ratio"] = f17["loss_ratio"]
    cat_thr = cl.claim_amount.nlargest(3).min()
    noncat = cl[cl.claim_amount < cat_thr]
    a["d9_ins_loss_ratio_excat"] = _r(noncat.claim_amount.sum() / pol.premium.sum(), 3)
    a["d9_ins_cat_loading_pct"] = _r(100 * (cl.claim_amount.sum() / noncat.claim_amount.sum() - 1), 1)
    n = cl.groupby("policy_id").size().reindex(pol.policy_id, fill_value=0).values
    off = np.log(pol.exposure_years.values)
    Xc = np.ones((len(n), 1))
    pois = sm.GLM(n, Xc, family=sm.families.Poisson(), offset=off).fit()
    nb = sm.NegativeBinomial(n, Xc, offset=off).fit(disp=0)
    a["d9_ins_aic_pois"], a["d9_ins_aic_nb"] = _r(pois.aic, 1), _r(nb.aic, 1)
    alpha = float(nb.params[-1])
    a["d9_ins_nb_alpha"] = _r(alpha, 2)
    # Monte Carlo aggregate annual loss (frequency NB, severity bootstrap incl. catastrophe tail)
    rng = np.random.default_rng(20261115)
    lam = n.sum() / pol.exposure_years.sum() * len(pol)  # claims per portfolio-year (one year exposure each)
    S = 20000
    r_ = 1 / alpha * len(pol)  # aggregate NB: sum of policy NBs
    counts = rng.negative_binomial(r_, r_ / (r_ + lam), S)
    sev = cl.claim_amount.values
    agg = np.array([rng.choice(sev, c).sum() for c in counts])
    prem = pol.premium.sum() / pol.exposure_years.sum() * len(pol)
    q = np.quantile(agg, 0.995)
    a["d9_ins_el"] = _r(agg.mean() / 1e6, 2)
    a["d9_ins_var995"] = _r(q / 1e6, 2)
    a["d9_ins_es995"] = _r(agg[agg >= q].mean() / 1e6, 2)
    a["d9_ins_premium"] = _r(prem / 1e6, 2)
    a["d9_ins_capital"] = _r((q - agg.mean()) / 1e6, 2)
    # credit portfolio loss: Vasicek one-factor
    ead = (acc.limit_or_loan_amount * np.where(acc.product_type == "credit_card", 0.6, 0.8)).values
    lgd, rho = 0.6, 0.15

    def vasicek(pd_, S=20000, seed=7):
        r = np.random.default_rng(seed)
        z = r.standard_normal(S)
        cond = stats.norm.cdf((stats.norm.ppf(pd_) - np.sqrt(rho) * z[:, None]) / np.sqrt(1 - rho))
        # expected loss given factor (large-portfolio approximation per segment) — exposures grouped by PD band
        return (cond * ead_w).sum(axis=1) * lgd

    pd_base = acc.default_12m.mean()
    ead_w = np.array([ead.sum()])
    L0 = vasicek(np.array([pd_base]))
    q0 = np.quantile(L0, 0.999)
    a["d9_cr_pd"] = _r(100 * pd_base, 2)
    a["d9_cr_ead"] = _r(ead.sum() / 1e6, 1)
    a["d9_cr_el"] = _r(L0.mean() / 1e6, 2)
    a["d9_cr_var999"] = _r(q0 / 1e6, 2)
    a["d9_cr_es999"] = _r(L0[L0 >= q0].mean() / 1e6, 2)
    a["d9_cr_capital"] = _r((q0 - L0.mean()) / 1e6, 2)
    L1 = vasicek(np.array([2.5 * pd_base]))
    a["d9_cr_stress_el"] = _r(L1.mean() / 1e6, 2)
    a["d9_cr_stress_var999"] = _r(np.quantile(L1, 0.999) / 1e6, 2)

    # ================= L9.5 fairness and conformal =================
    f15 = M.F15(data)
    a["d9_di"] = f15["measured"]
    a["d9_appr_A"], a["d9_appr_B"] = _r(100 * f15["approval_A"], 1), _r(100 * f15["approval_B"], 1)
    a["d9_r4_share_B"] = _r(100 * f15["r4_share_B"], 1)
    a["d9_appr_by_region"] = {k: _r(100 * v, 1) for k, v in f15["approval_by_region"].items()}
    dec = M.load("finance", "applications_declined", data)
    apps = pd.concat([acc[["protected_group", "region"]].assign(approved=1), dec[["protected_group", "region"]].assign(approved=0)])
    wr = apps.assign(r4=apps.region == "R4").groupby(["r4", "protected_group"]).approved.mean()
    a["d9_appr_nonR4"] = {g: _r(100 * wr[(False, g)], 1) for g in ("A", "B")}
    a["d9_appr_R4"] = {g: _r(100 * wr[(True, g)], 1) for g in ("A", "B")}
    a["d9_di_nonR4"] = _r(wr[(False, "B")] / wr[(False, "A")], 3)
    # booked-population model fairness (protected attribute excluded from features)
    dd = acc.copy()
    dd["util"] = dd.utilisation.fillna(0)
    dd["r4"] = (dd.region == "R4").astype(int)
    Xf = dd[["bureau_score", "dti", "inquiries_6m", "delinq_2y", "util", "r4"]].astype(float)
    yf = dd.default_12m.astype(int)
    Xa, Xb, ya, yb, ga, gb_ = train_test_split(Xf, yf, dd.protected_group, test_size=0.4, random_state=0, stratify=yf)
    s3 = StandardScaler().fit(Xa)
    lm = LogisticRegression(max_iter=3000).fit(s3.transform(Xa), ya)
    pb = lm.predict_proba(s3.transform(Xb))[:, 1]
    thr = np.quantile(pb, 0.85)  # decline top 15% risk
    fair = {}
    for gname in ("A", "B"):
        mk = (gb_ == gname).values
        flag = pb[mk] >= thr
        yy = yb.values[mk]
        fair[gname] = {"n": int(mk.sum()), "flag_rate": _r(100 * flag.mean(), 1), "default_rate": _r(100 * yy.mean(), 2),
                       "mean_pd": _r(100 * pb[mk].mean(), 2), "tpr": _r(100 * flag[yy == 1].mean(), 1),
                       "fpr": _r(100 * flag[yy == 0].mean(), 1)}
    a["d9_fair"] = fair
    a["d9_fair_coef_r4"] = _r(lm.coef_[0][-1], 3)
    # split conformal prediction sets (90%)
    Xa2, Xcal, ya2, ycal = train_test_split(Xa, ya, test_size=0.3, random_state=1, stratify=ya)
    s4 = StandardScaler().fit(Xa2)
    lc = LogisticRegression(max_iter=3000).fit(s4.transform(Xa2), ya2)
    pc = lc.predict_proba(s4.transform(Xcal))
    scores = 1 - pc[np.arange(len(ycal)), ycal.values]
    alpha_c = 0.10
    qh = np.quantile(scores, np.ceil((len(scores) + 1) * (1 - alpha_c)) / len(scores), method="higher")
    pt = lc.predict_proba(s4.transform(Xb))
    sets = (1 - pt) <= qh
    cover = sets[np.arange(len(yb)), yb.values].mean()
    a["d9_conf_coverage"] = _r(100 * cover, 1)
    a["d9_conf_qhat"] = _r(qh, 3)
    a["d9_conf_both_share"] = _r(100 * (sets.sum(axis=1) == 2).mean(), 1)
    a["d9_conf_cov_def"] = _r(100 * sets[yb.values == 1, 1].mean(), 1)
    a["d9_conf_cov_nondef"] = _r(100 * sets[yb.values == 0, 0].mean(), 1)
    # class-conditional (Mondrian) conformal: separate quantile per true class
    qk = {}
    for k in (0, 1):
        sk = scores[ycal.values == k]
        qk[k] = np.quantile(sk, min(1.0, np.ceil((len(sk) + 1) * (1 - alpha_c)) / len(sk)), method="higher")
    sets_m = np.column_stack([(1 - pt[:, k]) <= qk[k] for k in (0, 1)])
    a["d9_confm_cov_def"] = _r(100 * sets_m[yb.values == 1, 1].mean(), 1)
    a["d9_confm_cov_nondef"] = _r(100 * sets_m[yb.values == 0, 0].mean(), 1)
    a["d9_confm_both_share"] = _r(100 * (sets_m.sum(axis=1) == 2).mean(), 1)
    a["d9_confm_single_def_share"] = _r(100 * ((sets_m[:, 1]) & (~sets_m[:, 0])).mean(), 1)

    # ================= L9.6 monitoring =================
    r19 = M.R19(data)
    a["d9_r19_psi"] = _r(r19["measured"], 2)
    a["d9_r19_med_before"], a["d9_r19_med_after"] = r19["median_discount_before"], r19["median_discount_after"]
    a["d9_r19_online_before"], a["d9_r19_online_after"] = _r(100 * r19["online_share_before"], 1), _r(100 * r19["online_share_after"], 1)
    on = tx[(tx.channel != "in-store") & tx.promo_flag]
    fixed = np.where((on.week >= 80) & (on.discount_pct <= 1), on.discount_pct * 100, on.discount_pct)
    a["d9_r19_psi_fixed"] = _r(M.psi(fixed[on.week.values < 80], fixed[on.week.values >= 80]), 3)
    first_bad = on[(on.discount_pct > 0) & (on.discount_pct <= 1)].week.min()
    a["d9_r19_first_week"] = int(first_bad)
    f11, f12, f18 = M.F11(data), M.F12(data), M.F18(data)
    a["d9_f11_psi"] = f11["measured"]
    a["d9_f11_by_vintage"] = f11["psi_by_vintage"]
    a["d9_f11_mix"] = {k: _r(100 * v, 1) for k, v in f11["late_channel_mix"].items()}
    a["d9_f12_auc_early"], a["d9_f12_auc_late"], a["d9_f12_delta"] = f12["auc_early"], f12["auc_late"], f12["measured"]
    a["d9_f12_def_early"], a["d9_f12_def_late"] = _r(100 * f12["default_early"], 2), _r(100 * f12["default_late"], 2)
    a["d9_f12_csi_util"] = f12["csi_utilisation"]
    cc = acc[acc.product_type == "credit_card"].dropna(subset=["utilisation"])
    late_m = cc.vintage.isin(["2025Q2", "2025Q3"])
    sl = {}
    for nm_, part in (("early", cc[~late_m]), ("late", cc[late_m])):
        mm = smf.logit("default_12m ~ utilisation + bureau_score", part.assign(default_12m=part.default_12m.astype(int))).fit(disp=0)
        sl[nm_] = _r(mm.params["utilisation"], 2)
    a["d9_f12_util_slope"] = sl
    # calibration drift: early-trained PD model applied to late vintages
    ea, la = acc[~acc.vintage.isin(["2025Q2", "2025Q3"])], acc[acc.vintage.isin(["2025Q2", "2025Q3"])]
    cm = smf.logit("y ~ app_score", ea.assign(y=ea.default_12m.astype(int))).fit(disp=0)
    pl = cm.predict(la)
    a["d9_cal_pred_late"], a["d9_cal_actual_late"] = _r(100 * pl.mean(), 2), _r(100 * la.default_12m.mean(), 2)
    a["d9_f18_gap"], a["d9_f18_declined_share"] = f18["measured"], _r(100 * f18["declined_share"], 1)
    a["d9_f18_low_default"] = _r(100 * f18["booked_low_score_default"], 1)

    checks = {
        "R09 TWFE ≈ 12%": 5 < a["d9_r09_twfe_pct"] < 22,
        "R09 pre-trend not significant": a["d9_r09_pretrend_p"] > 0.05,
        "R20 naive ≫ TWFE": a["d9_r20_naive"] > 25 and -3 < a["d9_r20_twfe"] < 12,
        "R20 demographic adjustment still biased": a["d9_r20_adj_demo"] > 15,
        "censored ≈ 70%": 65 < a["d9_censored_pct"] < 75,
        "complaints raise hazard": 1.4 < a["d9_cox"]["complaints_12m"]["hr"] < 2.2,
        "digital lowers hazard": a["d9_cox"]["digital_share_10pp"]["hr"] < 1,
        "logrank significant": a["d9_logrank_p"] < 0.001,
        "MLP not better than GBM": a["d9_dl_auc"]["mlp"] <= a["d9_dl_auc"]["gbm"] + 0.01,
        "NB beats Poisson": a["d9_ins_aic_nb"] < a["d9_ins_aic_pois"],
        "ES ≥ VaR": a["d9_ins_es995"] >= a["d9_ins_var995"] and a["d9_cr_es999"] >= a["d9_cr_var999"],
        "DI < 0.8": a["d9_di"] < 0.8,
        "proxy: DI near 1 outside R4": a["d9_di_nonR4"] > 0.9,
        "conformal coverage ≈ 90": 87 < a["d9_conf_coverage"] < 93,
        "marginal conformal misses defaulters": a["d9_conf_cov_def"] < 50,
        "mondrian covers defaulters": a["d9_confm_cov_def"] > 80,
        "R19 fix removes drift": a["d9_r19_psi_fixed"] < 0.1 < a["d9_r19_psi"],
        "F11 PSI > 0.25": a["d9_f11_psi"] > 0.25,
        "F12 AUC down": a["d9_f12_delta"] < -0.03,
        "calibration under-predicts late": a["d9_cal_pred_late"] < a["d9_cal_actual_late"],
    }
    bad = [k for k, ok in checks.items() if not ok]
    if bad and __import__("os").environ.get("SB_NOGUARD"):
        print("GUARDS", bad)
    else:
        assert not bad, f"Day 9 narrative guards failed: {bad}"
    return a
