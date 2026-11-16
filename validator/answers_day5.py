"""Computed answers for Day 5 (regression, diagnostics, logistic, regularisation, GLMs, non-linearity/mixed models, capstone).
Keys d5_. Narrative claims are guarded at the end."""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor

from . import measures as M

warnings.filterwarnings("ignore")


def _r(x, nd=4):
    return round(float(x), nd)


def _sig(x, n=3):
    return float(f"{float(x):.{n}g}")


def _pct(b):
    return 100 * (np.exp(b) - 1)


def auc(y, s):
    y = np.asarray(y).astype(int)
    r = stats.rankdata(s)
    n1 = y.sum()
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y) - n1)))


def compute_day5(data=str(M.DATA)) -> dict:
    a: dict = {}
    sc = M.load("retail", "weekly_store_category", data)
    ws = M.load("retail", "weekly_store", data)
    acc = M.load("finance", "accounts", data)
    rng = np.random.default_rng(505)

    # ================= L5.1 OLS =================
    bev = sc[sc.category == "Beverages"].merge(ws[["store_id", "week", "avg_temperature_c", "holiday_flag", "format", "region"]], on=["store_id", "week"])
    bev = bev[bev.units > 0].copy()
    m = smf.ols("np.log(units) ~ promo_sku_share + stockout_sku_share + avg_temperature_c + holiday_flag + C(store_id)", bev).fit()
    ci = m.conf_int()
    a["d5_bev_n"] = int(m.nobs)
    a["d5_bev_r2"] = _r(m.rsquared, 3)
    for k, nm in [("avg_temperature_c", "temp"), ("holiday_flag[T.True]", "hol"), ("promo_sku_share", "promo"), ("stockout_sku_share", "stock")]:
        a[f"d5_bev_{nm}_b"] = _r(m.params[k], 4)
        a[f"d5_bev_{nm}_ci"] = [_r(ci.loc[k, 0], 4), _r(ci.loc[k, 1], 4)]
    a["d5_bev_temp_pct"] = _r(_pct(m.params["avg_temperature_c"]), 2)
    a["d5_bev_hol_pct"] = _r(_pct(m.params["holiday_flag[T.True]"]), 1)
    a["d5_bev_promo10_pct"] = _r(_pct(0.1 * m.params["promo_sku_share"]), 1)
    a["d5_bev_stock10_pct"] = _r(_pct(0.1 * m.params["stockout_sku_share"]), 1)
    a["d5_true_temp_pct"], a["d5_true_hol_pct"] = 2.0, 40
    # without store effects (format only) – raw units vs log
    mr = smf.ols("units ~ promo_sku_share + avg_temperature_c + holiday_flag + C(format)", bev).fit()
    ml = smf.ols("np.log(units) ~ promo_sku_share + avg_temperature_c + holiday_flag + C(format)", bev).fit()
    a["d5_raw_temp_b"], a["d5_raw_hol_b"] = _r(mr.params["avg_temperature_c"], 2), _r(mr.params["holiday_flag[T.True]"], 1)
    a["d5_raw_r2"], a["d5_log_r2"] = _r(mr.rsquared, 3), _r(ml.rsquared, 3)
    a["d5_bev_mean_units"] = _r(bev.units.mean(), 1)
    # finance: limit drivers and pricing
    fa = acc.dropna(subset=["income_annual"])
    fa = fa[fa.income_annual > 0].copy()
    ml2 = smf.ols("np.log(limit_or_loan_amount) ~ np.log(income_annual) + product_type", fa).fit()
    a["d5_lim_elast"], a["d5_lim_r2"] = _r(ml2.params["np.log(income_annual)"], 3), _r(ml2.rsquared, 3)
    a["d5_lim_loan_pct"] = _r(_pct(ml2.params["product_type[T.personal_loan]"]), 1)
    mp = smf.ols("I(100*interest_rate) ~ bureau_score + product_type + dti", acc).fit()
    a["d5_rate_bureau_100"] = _r(100 * mp.params["bureau_score"], 2)
    a["d5_rate_loan"] = _r(mp.params["product_type[T.personal_loan]"], 2)
    a["d5_rate_dti_p"] = _r(mp.pvalues["dti"], 3)
    a["d5_rate_r2"] = _r(mp.rsquared, 3)

    # ================= L5.2 diagnostics =================
    a["d5_bp_raw_p"] = _sig(het_breuschpagan(mr.resid, mr.model.exog)[1], 2)
    a["d5_bp_log_p"] = _sig(het_breuschpagan(ml.resid, ml.model.exog)[1], 2)
    a["d5_raw_resid_skew"] = _r(pd.Series(mr.resid).skew(), 2)
    a["d5_log_resid_skew"] = _r(pd.Series(ml.resid).skew(), 2)
    hc = mr.get_robustcov_results("HC3")
    j = list(mr.params.index).index("avg_temperature_c")
    a["d5_raw_temp_se"], a["d5_raw_temp_se_hc3"] = _r(mr.bse["avg_temperature_c"], 3), _r(hc.bse[j], 3)
    infl = m.get_influence()
    cook = infl.cooks_distance[0]
    a["d5_cook_max"] = _r(cook.max(), 4)
    a["d5_cook_n_4n"] = int((cook > 4 / m.nobs).sum())
    # VIF and unstable signs (F06), credit cards
    cc = fa[fa.product_type == "credit_card"].copy()
    X = sm.add_constant(cc[["income_annual", "limit_or_loan_amount", "bureau_score", "dti"]])
    a["d5_vif"] = {c: _r(variance_inflation_factor(X.values, i), 1) for i, c in enumerate(X.columns) if c != "const"}
    a["d5_il_corr_cards"] = _r(np.corrcoef(cc.income_annual, cc.limit_or_loan_amount)[0, 1], 4)
    signs = []
    cc["d"] = cc.default_12m.astype(int)
    cc["inc10k"], cc["lim10k"] = cc.income_annual / 1e4, cc.limit_or_loan_amount / 1e4
    for s_ in range(1, 6):
        sub = cc.sample(3000, random_state=s_)
        l_ = smf.logit("d ~ inc10k + lim10k + bureau_score", sub).fit(disp=0)
        signs.append({"inc": _r(l_.params["inc10k"], 3), "lim": _r(l_.params["lim10k"], 3), "inc_se": _r(l_.bse["inc10k"], 3)})
    a["d5_flip"] = signs
    a["d5_flip_n_inc_pos"] = int(sum(s_["inc"] > 0 for s_ in signs))
    l1 = smf.logit("d ~ inc10k + bureau_score", cc.sample(3000, random_state=1)).fit(disp=0)
    a["d5_inc_only_b"], a["d5_inc_only_se"] = _r(l1.params["inc10k"], 3), _r(l1.bse["inc10k"], 3)

    # ================= L5.3 logistic =================
    d = acc.copy()
    d["y"] = d.default_12m.astype(int)
    d["unverified"] = (~d.income_verified_flag).astype(int)
    d["bureau50"] = d.bureau_score / 50
    d["util10"] = d.utilisation.fillna(0) * 10
    d["card"] = (d.product_type == "credit_card").astype(int)
    lg = smf.logit("y ~ bureau50 + util10 + dti + unverified + C(acquisition_channel) + card", d).fit(disp=0)
    orr = np.exp(lg.params)
    oci = np.exp(lg.conf_int())
    keys = {"bureau50": "bureau", "util10": "util", "dti": "dti", "unverified": "unver", "C(acquisition_channel)[T.partner]": "partner", "C(acquisition_channel)[T.online]": "online"}
    for k, nm in keys.items():
        a[f"d5_or_{nm}"] = _r(orr[k], 3)
        a[f"d5_or_{nm}_ci"] = [_r(oci.loc[k, 0], 3), _r(oci.loc[k, 1], 3)]
    a["d5_logit_auc"] = _r(auc(d.y, lg.predict(d)), 3)
    a["d5_logit_pseudo_r2"] = _r(lg.prsquared, 3)
    base_p = lg.predict(d).mean()
    a["d5_logit_mean_p"] = _r(100 * base_p, 2)
    # marginal effect of partner at the mean
    me = lg.get_margeff(at="overall")
    mi = list(lg.params.index[1:]).index("C(acquisition_channel)[T.partner]")
    a["d5_me_partner_pp"] = _r(100 * me.margeff[mi], 2)
    # retail: return probability by category / channel / price
    tx = M.load("retail", "transactions", data).drop_duplicates("line_id")
    t = tx[(tx.unit_price / tx.list_price < 20)].copy()
    t["y"] = t.return_flag.astype(int)
    t["lp"] = np.log(t.unit_price.clip(lower=0.05))
    t["elec"] = (t.category == "Electronics").astype(int)
    t["online"] = (t.channel != "in-store").astype(int)  # delivery or click-and-collect
    lr = smf.logit("y ~ elec + lp + online + loyalty_flag", t).fit(disp=0)
    a["d5_ret_or_elec"] = _r(np.exp(lr.params["elec"]), 2)
    a["d5_ret_or_elec_ci"] = [_r(np.exp(lr.conf_int().loc["elec", 0]), 2), _r(np.exp(lr.conf_int().loc["elec", 1]), 2)]
    a["d5_ret_or_lp"] = _r(np.exp(lr.params["lp"]), 3)
    a["d5_ret_or_online"] = _r(np.exp(lr.params["online"]), 3)
    a["d5_ret_or_online_p"] = _r(lr.pvalues["online"], 3)
    a["d5_ret_auc"] = _r(auc(t.y, lr.predict(t)), 3)

    # ================= L5.4 regularisation and model selection =================
    from sklearn.linear_model import LassoCV, LogisticRegression, LogisticRegressionCV, RidgeCV, LinearRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import r2_score, roc_auc_score
    from sklearn.model_selection import KFold, StratifiedKFold
    kf = KFold(5, shuffle=True, random_state=0)
    b2 = bev.copy()
    b2["ly"] = np.log(b2.units)
    dummies = pd.get_dummies(b2.store_id, prefix="s", drop_first=True, dtype=float)
    base_cols = ["promo_sku_share", "stockout_sku_share", "avg_temperature_c"]
    Xr = pd.concat([b2[base_cols].astype(float), b2.holiday_flag.astype(float).rename("holiday"), dummies], axis=1)
    noise = pd.DataFrame(rng.normal(size=(len(b2), 16)), index=b2.index, columns=[f"noise_{i:02d}" for i in range(1, 17)])
    Xr = pd.concat([Xr, noise], axis=1)
    a["d5_reg_p"] = Xr.shape[1]
    tr, te = b2.week <= 78, b2.week > 78
    sc_ = StandardScaler().fit(Xr[tr])
    Xtr, Xte = sc_.transform(Xr[tr]), sc_.transform(Xr[te])
    ytr, yte = b2.ly[tr].to_numpy(), b2.ly[te].to_numpy()
    ols = LinearRegression().fit(Xtr, ytr)
    rid = RidgeCV(alphas=np.logspace(-3, 3, 25)).fit(Xtr, ytr)
    las = LassoCV(cv=kf, random_state=0, alphas=np.logspace(-4, 0, 60), max_iter=20000).fit(Xtr, ytr)
    a["d5_r2_ols_tr"], a["d5_r2_ols_te"] = _r(ols.score(Xtr, ytr), 3), _r(ols.score(Xte, yte), 3)
    a["d5_r2_ridge_te"], a["d5_r2_lasso_te"] = _r(rid.score(Xte, yte), 3), _r(las.score(Xte, yte), 3)
    coef = pd.Series(las.coef_, index=Xr.columns)
    a["d5_lasso_kept"] = int((coef != 0).sum())
    a["d5_lasso_noise_kept"] = int((coef[coef.index.str.startswith("noise")] != 0).sum())
    a["d5_lasso_alpha"] = _sig(las.alpha_, 3)
    # small-sample overfitting: fit on 8 weeks only
    tr8 = b2.week.between(77, 78)  # 80 rows for 59 features
    Xs = StandardScaler().fit(Xr[tr8])
    ols8 = LinearRegression().fit(Xs.transform(Xr[tr8]), b2.ly[tr8])
    las8 = LassoCV(cv=kf, random_state=0, alphas=np.logspace(-4, 0, 60), max_iter=20000).fit(Xs.transform(Xr[tr8]), b2.ly[tr8])
    a["d5_n8"] = int(tr8.sum())
    a["d5_r2_ols8_tr"], a["d5_r2_ols8_te"] = _r(ols8.score(Xs.transform(Xr[tr8]), b2.ly[tr8]), 3), _r(ols8.score(Xs.transform(Xr[te]), yte), 3)
    a["d5_r2_las8_te"] = _r(las8.score(Xs.transform(Xr[te]), yte), 3)
    c8 = pd.Series(las8.coef_, index=Xr.columns)
    a["d5_las8_kept"] = int((c8 != 0).sum())
    a["d5_las8_noise_kept"] = int((c8[c8.index.str.startswith("noise")] != 0).sum())
    o8 = pd.Series(ols8.coef_, index=Xr.columns)
    a["d5_ols8_noise_maxabs"] = _r(o8[o8.index.str.startswith("noise")].abs().max(), 3)
    # AIC / BIC: nested models on full data
    fits = {"temp+holiday": "np.log(units) ~ avg_temperature_c + holiday_flag + C(store_id)",
            "+promo+stockout": "np.log(units) ~ avg_temperature_c + holiday_flag + promo_sku_share + stockout_sku_share + C(store_id)",
            "+region×temp": "np.log(units) ~ avg_temperature_c*C(region) + holiday_flag + promo_sku_share + stockout_sku_share + C(store_id)"}
    a["d5_ic"] = {}
    for k, f in fits.items():
        mm = smf.ols(f, bev).fit()
        a["d5_ic"][k] = {"aic": _r(mm.aic, 0), "bic": _r(mm.bic, 0), "k": int(mm.df_model + 1)}
    # finance: logistic with 20 real + 20 noise features, L1 path
    feats = ["age", "tenure_months_with_bank", "interest_rate", "utilisation", "dti", "bureau_score", "inquiries_6m", "delinq_2y",
             "txn_count_3m", "digital_share", "branch_visits_6m", "complaints_12m", "card", "unverified"]
    dd = d.copy()
    dd["log_income"] = np.log(dd.income_annual.clip(lower=1000)).fillna(np.log(dd.income_annual.median()))
    dd["income_missing"] = dd.income_annual.isna().astype(int)
    dd["log_limit"] = np.log(dd.limit_or_loan_amount)
    dd["partner"] = (dd.acquisition_channel == "partner").astype(int)
    dd["online"] = (dd.acquisition_channel == "online").astype(int)
    dd["student"] = (dd.employment_type == "student").astype(int)
    feats += ["log_income", "income_missing", "log_limit", "partner", "online", "student"]
    nz = pd.DataFrame(rng.normal(size=(len(dd), 20)), index=dd.index, columns=[f"noise_{i:02d}" for i in range(1, 21)])
    Xf = pd.concat([dd[feats].astype(float).fillna(0), nz], axis=1)
    idx = rng.permutation(len(dd))
    itr, ite = idx[:4000], idx[4000:]
    sf = StandardScaler().fit(Xf.iloc[itr])
    Xtr_, Xte_ = sf.transform(Xf.iloc[itr]), sf.transform(Xf.iloc[ite])
    ytr_, yte_ = dd.y.to_numpy()[itr], dd.y.to_numpy()[ite]
    full = LogisticRegression(C=1e6, max_iter=5000).fit(Xtr_, ytr_)
    skf = StratifiedKFold(5, shuffle=True, random_state=0)
    Cs = np.logspace(-3, 1, 20)
    l1cv = LogisticRegressionCV(Cs=Cs, cv=skf, penalty="l1", solver="liblinear", scoring="roc_auc", max_iter=5000, random_state=0).fit(Xtr_, ytr_)
    sc_cv = l1cv.scores_[1]
    mean_, se_ = sc_cv.mean(axis=0), sc_cv.std(axis=0, ddof=1) / np.sqrt(sc_cv.shape[0])
    best = int(np.argmax(mean_))
    c1se = float(Cs[int(np.argmax(mean_ >= mean_[best] - se_[best]))])  # smallest C within 1 SE of the best
    l1se = LogisticRegression(C=c1se, penalty="l1", solver="liblinear", max_iter=5000).fit(Xtr_, ytr_)
    cf_best = pd.Series(l1cv.coef_[0], index=Xf.columns)
    a["d5_f_l1best_kept"] = int((cf_best != 0).sum())
    a["d5_f_l1best_noise_kept"] = int((cf_best[cf_best.index.str.startswith("noise")] != 0).sum())
    a["d5_f_auc_l1best_te"] = _r(roc_auc_score(yte_, l1cv.predict_proba(Xte_)[:, 1]), 3)
    cf = pd.Series(l1se.coef_[0], index=Xf.columns)
    l1cv = l1se
    a["d5_f_p"], a["d5_f_ntr"] = Xf.shape[1], len(itr)
    a["d5_f_auc_full_tr"] = _r(roc_auc_score(ytr_, full.predict_proba(Xtr_)[:, 1]), 3)
    a["d5_f_auc_full_te"] = _r(roc_auc_score(yte_, full.predict_proba(Xte_)[:, 1]), 3)
    a["d5_f_auc_l1_te"] = _r(roc_auc_score(yte_, l1cv.predict_proba(Xte_)[:, 1]), 3)
    a["d5_f_l1_kept"] = int((cf != 0).sum())
    a["d5_f_l1_noise_kept"] = int((cf[cf.index.str.startswith("noise")] != 0).sum())
    a["d5_f_l1_top"] = [k for k in cf.abs().sort_values(ascending=False).index[:5]]

    # ================= L5.5 GLMs =================
    bev["exposure_w"] = 1.0
    gp = smf.glm("units ~ promo_sku_share + avg_temperature_c + holiday_flag + C(store_id)", bev, family=sm.families.Poisson()).fit()
    a["d5_pois_disp"] = _r(gp.pearson_chi2 / gp.df_resid, 2)
    gnb = smf.negativebinomial("units ~ promo_sku_share + avg_temperature_c + holiday_flag + C(store_id)", bev).fit(disp=0, maxiter=200)
    a["d5_nb_alpha"] = _r(gnb.params["alpha"], 4)
    a["d5_pois_aic"], a["d5_nb_aic"] = _r(gp.aic, 0), _r(gnb.aic, 0)
    a["d5_pois_temp_se"], a["d5_nb_temp_se"] = _r(gp.bse["avg_temperature_c"], 5), _r(gnb.bse["avg_temperature_c"], 5)
    a["d5_pois_temp_pct"], a["d5_nb_temp_pct"] = _r(_pct(gp.params["avg_temperature_c"]), 2), _r(_pct(gnb.params["avg_temperature_c"]), 2)
    # insurance frequency with exposure offset
    pol = M.load("finance", "policies", data)
    cl = M.load("finance", "claims", data)
    nclaims = cl.groupby("policy_id").size()
    pol = pol.assign(n=pol.policy_id.map(nclaims).fillna(0).astype(int))
    mot = pol[pol["product"] == "motor"].copy()
    mot["vg"] = mot.vehicle_group.astype(int)
    fp = smf.glm("n ~ C(driver_age_band) + vg + C(region)", mot, family=sm.families.Poisson(), offset=np.log(mot.exposure_years)).fit()
    fn = smf.glm("n ~ C(driver_age_band) + vg + C(region)", mot, family=sm.families.NegativeBinomial(alpha=1.0), offset=np.log(mot.exposure_years)).fit()
    a["d5_freq_n"], a["d5_freq_claims"] = len(mot), int(mot.n.sum())
    a["d5_freq_rate"] = _r(mot.n.sum() / mot.exposure_years.sum(), 4)
    a["d5_freq_pois_disp"] = _r(fp.pearson_chi2 / fp.df_resid, 2)
    a["d5_freq_pois_aic"], a["d5_freq_nb_aic"] = _r(fp.aic, 0), _r(fn.aic, 0)
    yb = [k for k in fp.params.index if "driver_age_band" in k]
    a["d5_freq_rr"] = {k.split("T.")[1].rstrip("]"): _r(np.exp(fp.params[k]), 2) for k in yb}
    a["d5_freq_rr_vg"] = _r(np.exp(fp.params["vg"]), 3)
    a["d5_freq_base_band"] = sorted(mot.driver_age_band.dropna().unique())[0]
    # severity: gamma GLM vs lognormal, with and without the catastrophic claims
    sev = cl.merge(pol[["policy_id", "product"]], on="policy_id")
    gsev = smf.glm("claim_amount ~ C(claim_type)", sev, family=sm.families.Gamma(sm.families.links.Log())).fit()
    a["d5_sev_n"] = len(sev)
    a["d5_sev_mean"] = _r(sev.claim_amount.mean(), 0)
    a["d5_sev_by_type"] = {k: _r(v, 0) for k, v in sev.groupby("claim_type").claim_amount.mean().items()}
    cap = sev.claim_amount.quantile(0.99)
    a["d5_sev_cap"] = _r(cap, 0)
    a["d5_sev_mean_capped"] = _r(sev.claim_amount.clip(upper=cap).mean(), 0)
    a["d5_large_loading_pct"] = _r(100 * (sev.claim_amount.mean() / sev.claim_amount.clip(upper=cap).mean() - 1), 1)
    a["d5_gamma_disp"] = _r(gsev.scale, 3)
    # pure premium and loss ratio by product
    lr_ = {}
    for prod_, g in pol.groupby("product"):
        cl_ = cl[cl.policy_id.isin(g.policy_id)].claim_amount.sum()
        lr_[prod_] = _r(cl_ / g.premium.sum(), 3)
    a["d5_loss_ratio"] = lr_
    a["d5_pure_premium_motor"] = _r(cl[cl.policy_id.isin(mot.policy_id)].claim_amount.sum() / mot.exposure_years.sum(), 1)

    # ================= L5.6 non-linearity, interactions, mixed models =================
    cards = d[d.product_type == "credit_card"].copy()
    cards["u"] = cards.utilisation
    lin = smf.logit("y ~ u + bureau50", cards).fit(disp=0)
    cards["ub"] = pd.cut(cards.u, [-0.01, 0.5, 0.7, 0.8, 0.9, 2.0], labels=["≤50", "50–70", "70–80", "80–90", ">90"])
    binm = smf.logit("y ~ C(ub) + bureau50", cards).fit(disp=0)
    spl = smf.logit("y ~ bs(u, df=4) + bureau50", cards).fit(disp=0)
    a["d5_util_lin_aic"], a["d5_util_bin_aic"], a["d5_util_spl_aic"] = _r(lin.aic, 0), _r(binm.aic, 0), _r(spl.aic, 0)
    a["d5_util_lin_auc"], a["d5_util_bin_auc"], a["d5_util_spl_auc"] = _r(auc(cards.y, lin.predict(cards)), 3), _r(auc(cards.y, binm.predict(cards)), 3), _r(auc(cards.y, spl.predict(cards)), 3)
    obs = cards.groupby("ub", observed=True).y.mean()
    a["d5_util_obs"] = {str(k): _r(100 * v, 1) for k, v in obs.items()}
    pl = cards.assign(pred=lin.predict(cards)).groupby("ub", observed=True).pred.mean()
    a["d5_util_lin_pred"] = {str(k): _r(100 * v, 1) for k, v in pl.items()}
    a["d5_util_ratio"] = _r(obs.iloc[-1] / obs.iloc[0], 1)
    # interaction young x high DTI (F05)
    d["young"] = (d.age < 25).astype(int)
    d["hidti"] = (d.dti > 0.45).astype(int)
    mi_ = smf.logit("y ~ young * hidti + bureau50", d).fit(disp=0)
    a["d5_int_or"] = _r(np.exp(mi_.params["young:hidti"]), 2)
    a["d5_int_ci"] = [_r(np.exp(mi_.conf_int().loc["young:hidti", 0]), 2), _r(np.exp(mi_.conf_int().loc["young:hidti", 1]), 2)]
    a["d5_int_p"] = _r(mi_.pvalues["young:hidti"], 4)
    a["d5_int_n_cell"] = int((d.young & d.hidti).sum())
    cell = d.groupby(["young", "hidti"]).y.mean()
    a["d5_int_rates"] = {f"{'young' if k[0] else 'older'}_{'hiDTI' if k[1] else 'loDTI'}": _r(100 * v, 2) for k, v in cell.items()}
    # mixed model: basket value with store random intercept
    tx2 = tx[~tx.return_flag & (tx.quantity > 0) & (tx.unit_price / tx.list_price < 20)]
    bk = tx2.groupby("basket_id").agg(rev=("revenue", "sum"), store=("store_id", "first"), fmt=("format", "first"))
    bk["lr"] = np.log(bk.rev)
    mm = smf.mixedlm("lr ~ C(fmt)", bk, groups=bk["store"]).fit(reml=True)
    var_s, var_e = float(mm.cov_re.iloc[0, 0]), float(mm.scale)
    a["d5_mix_icc"] = _r(var_s / (var_s + var_e), 3)
    ns = bk.groupby("store").size()
    small_store = ns.idxmin()
    k_ = var_s / (var_s + var_e / ns[small_store])
    raw_dev = bk[bk.store == small_store].lr.mean() - (bk.lr.mean())
    a["d5_mix_small_store"], a["d5_mix_small_n"] = small_store, int(ns[small_store])
    a["d5_mix_shrink"] = _r(k_, 2)
    a["d5_mix_n_median"] = int(ns.median())
    a["d5_mix_shrink_median"] = _r(var_s / (var_s + var_e / ns.median()), 2)

    # ================= L5.7 capstone =================
    s = tx2.copy()
    s["q"] = pd.to_datetime(s.date).dt.to_period("Q").astype(str)
    s["seg"] = s.category + "|" + s.promo_flag.map({True: "promo", False: "regular"})

    def mrate(df_):
        return df_.margin.sum() / df_.revenue.sum()
    q0, q1 = s[s.q == "2025Q1"], s[s.q == "2025Q2"]
    a["d5_cap_m_q1"], a["d5_cap_m_q2"] = _r(100 * mrate(q0), 2), _r(100 * mrate(q1), 2)
    a["d5_cap_m_q3"] = _r(100 * mrate(s[s.q == "2025Q3"]), 2)
    w0 = q0.groupby("seg").revenue.sum() / q0.revenue.sum()
    w1 = q1.groupby("seg").revenue.sum() / q1.revenue.sum()
    r0 = q0.groupby("seg").apply(mrate)
    r1 = q1.groupby("seg").apply(mrate)
    segs = w0.index.union(w1.index)
    w0, w1, r0, r1 = (x.reindex(segs).fillna(0) for x in (w0, w1, r0, r1))
    r0 = r0.where(w0 > 0, r1)
    r1 = r1.where(w1 > 0, r0)
    mix = ((w1 - w0) * r0).sum()
    rate = (w1 * (r1 - r0)).sum()
    a["d5_cap_mix_pp"], a["d5_cap_rate_pp"] = _r(100 * mix, 2), _r(100 * rate, 2)
    contrib = (w1 * (r1 - r0)).sort_values()
    a["d5_cap_top_rate"] = {k: _r(100 * v, 2) for k, v in contrib.head(3).items()}
    a["d5_cap_promo_m_q1"] = _r(100 * mrate(q0[q0.promo_flag]), 1)
    a["d5_cap_promo_m_q2"] = _r(100 * mrate(q1[q1.promo_flag]), 1)
    a["d5_cap_disc_q1"], a["d5_cap_disc_q2"] = _r(q0[q0.promo_flag].discount_pct.mean(), 1), _r(q1[q1.promo_flag].discount_pct.mean(), 1)
    a["d5_cap_promo_share_q1"], a["d5_cap_promo_share_q2"] = _r(100 * q0.promo_flag.mean(), 1), _r(100 * q1.promo_flag.mean(), 1)
    reg0, reg1 = q0[~q0.promo_flag], q1[~q1.promo_flag]
    a["d5_cap_reg_m_q1"], a["d5_cap_reg_m_q2"] = _r(100 * mrate(reg0), 1), _r(100 * mrate(reg1), 1)
    a["d5_cap_reg_pidx_q1"] = _r((reg0.unit_price / reg0.list_price).mean(), 3)
    a["d5_cap_reg_pidx_q2"] = _r((reg1.unit_price / reg1.list_price).mean(), 3)
    a["d5_cap_reg_cidx_q1"] = _r((reg0.unit_cost / reg0.list_price).mean(), 3)
    a["d5_cap_reg_cidx_q2"] = _r((reg1.unit_cost / reg1.list_price).mean(), 3)
    a["d5_cap_reg_pidx_q3"] = _r((s[(s.q == "2025Q3") & ~s.promo_flag].unit_price / s[(s.q == "2025Q3") & ~s.promo_flag].list_price).mean(), 3)
    rp = s[~s.promo_flag & s.q.isin(["2025Q1", "2025Q2"])].groupby(["q", "region"]).apply(lambda x: (x.unit_price / x.list_price).mean()).unstack()
    a["d5_cap_reg_pidx_by_region"] = {r_: [_r(rp.loc["2025Q1", r_], 3), _r(rp.loc["2025Q2", r_], 3)] for r_ in rp.columns}
    # line-level regression of margin rate on discount depth
    pr = s[s.promo_flag & s.q.isin(["2025Q1", "2025Q2"])].copy()
    pr["mr"] = pr.margin / pr.revenue
    rm = smf.ols("mr ~ discount_pct + C(category) + C(q)", pr).fit()
    a["d5_cap_mr_per_disc_pp"] = _r(100 * rm.params["discount_pct"], 2)
    a["d5_cap_q2_effect_after_disc_pp"] = _r(100 * rm.params["C(q)[T.2025Q2]"], 2)
    a["d5_cap_q2_effect_after_disc_p"] = _r(rm.pvalues["C(q)[T.2025Q2]"], 3)
    rm0 = smf.ols("mr ~ C(category) + C(q)", pr).fit()
    a["d5_cap_q2_effect_raw_pp"] = _r(100 * rm0.params["C(q)[T.2025Q2]"], 2)
    # finance: approvals
    dec = M.load("finance", "applications_declined", data)
    ap = pd.concat([pd.DataFrame({"q": pd.to_datetime(acc.origination_date).dt.to_period("Q").astype(str), "ch": acc.acquisition_channel, "ok": 1}),
                    pd.DataFrame({"q": pd.to_datetime(dec.application_date).dt.to_period("Q").astype(str), "ch": dec.acquisition_channel, "ok": 0})])
    a["d5_appr_q1"] = _r(100 * ap[ap.q == "2025Q1"].ok.mean(), 1)
    a["d5_appr_q2"] = _r(100 * ap[ap.q == "2025Q2"].ok.mean(), 1)
    a["d5_appr_hist"] = _r(100 * ap[ap.q < "2025Q2"].ok.mean(), 1)
    byc = ap[ap.q.isin(["2025Q1", "2025Q2"])].groupby(["q", "ch"]).ok.agg(["mean", "size"])
    a["d5_appr_by_ch"] = {f"{q}_{c}": _r(100 * r["mean"], 1) for (q, c), r in byc.iterrows()}
    a["d5_partner_share_q2"] = _r(100 * (ap[ap.q == "2025Q2"].ch == "partner").mean(), 1)
    a["d5_partner_first_q"] = ap[ap.ch == "partner"].q.min()
    nonp = ap[(ap.ch != "partner")].groupby("q").ok.mean()
    a["d5_appr_nonpartner_q2"] = _r(100 * nonp["2025Q2"], 1)
    a["d5_appr_nonpartner_q1"] = _r(100 * nonp["2025Q1"], 1)

    checks = {
        "temp near 2%": 1.5 < a["d5_bev_temp_pct"] < 2.5 and a["d5_bev_temp_ci"][0] < 0.0198 < a["d5_bev_temp_ci"][1],
        "holiday near 40%": 30 < a["d5_bev_hol_pct"] < 55,
        "BP raw ≪ log": a["d5_bp_raw_p"] < a["d5_bp_log_p"],
        "VIF large": a["d5_vif"]["income_annual"] > 50,
        "signs flip": 0 < a["d5_flip_n_inc_pos"] < 5,
        "limit elasticity ≈ 1": 0.95 < a["d5_lim_elast"] < 1.05,
        "unverified OR > 1": a["d5_or_unver_ci"][0] > 1,
        "partner OR > 1": a["d5_or_partner_ci"][0] > 1,
        "electronics OR > 1": a["d5_ret_or_elec_ci"][0] > 1,
        "OLS overfits small sample": a["d5_r2_ols8_te"] < a["d5_r2_las8_te"] and a["d5_r2_ols8_tr"] > a["d5_r2_ols8_te"] + 0.05,
        "L1 1-SE keeps fewer noise": a["d5_f_l1_noise_kept"] <= a["d5_f_l1best_noise_kept"],
        "lasso drops most noise (small n)": a["d5_las8_noise_kept"] <= 8 and a["d5_f_l1best_noise_kept"] <= 3,
        "big-n lasso ≈ OLS": abs(a["d5_r2_lasso_te"] - a["d5_r2_ols_te"]) < 0.01,
        "BIC prefers promo model": a["d5_ic"]["+promo+stockout"]["bic"] < a["d5_ic"]["temp+holiday"]["bic"],
        "Poisson overdispersed": a["d5_pois_disp"] > 2 and a["d5_nb_aic"] < a["d5_pois_aic"],
        "freq NB better or close": a["d5_freq_nb_aic"] <= a["d5_freq_pois_aic"] + 2 or a["d5_freq_pois_disp"] < 1.3,
        "N, S, W cut; E not": all(a["d5_cap_reg_pidx_by_region"][r_][1] < a["d5_cap_reg_pidx_by_region"][r_][0] for r_ in ["North", "South", "West"]) and a["d5_cap_reg_pidx_by_region"]["East"][1] >= a["d5_cap_reg_pidx_by_region"]["East"][0],
        "Q3 recovered": a["d5_cap_reg_pidx_q3"] > a["d5_cap_reg_pidx_q2"] + 0.01 and a["d5_cap_m_q3"] > a["d5_cap_m_q2"] + 1,
        "discount adjustment shrinks Q2 effect": abs(a["d5_cap_q2_effect_after_disc_pp"]) < abs(a["d5_cap_q2_effect_raw_pp"]),
        "1-SE AUC not above best": a["d5_f_auc_l1_te"] <= a["d5_f_auc_l1best_te"] + 0.005,
        "motor loss ratio > 1": a["d5_loss_ratio"]["motor"] > 1,
        "young drivers riskier": a["d5_freq_rr"]["25-34"] < 0.75,
        "region×temp lowers AIC and BIC": a["d5_ic"]["+region×temp"]["bic"] < a["d5_ic"]["+promo+stockout"]["bic"],
        "large-loss loading > 20%": a["d5_large_loading_pct"] > 20,
        "spline beats linear": a["d5_util_spl_aic"] < a["d5_util_lin_aic"] - 4,
        "linear under-predicts top band": a["d5_util_lin_pred"][">90"] < a["d5_util_obs"][">90"] - 1.5,
        "util ratio steep": a["d5_util_ratio"] > 3,
        "interaction > 1": a["d5_int_or"] > 1.2,
        "small ICC": a["d5_mix_icc"] < 0.1,
        "margin fell in Q2": a["d5_cap_m_q2"] < a["d5_cap_m_q1"] - 1.5,
        "shelf price index fell, cost flat": a["d5_cap_reg_pidx_q2"] < a["d5_cap_reg_pidx_q1"] - 0.01 and abs(a["d5_cap_reg_cidx_q2"] - a["d5_cap_reg_cidx_q1"]) < 0.005,
        "promo margin fell": a["d5_cap_promo_m_q2"] < a["d5_cap_promo_m_q1"] - 3,
        "rate effect dominates": abs(a["d5_cap_rate_pp"]) > abs(a["d5_cap_mix_pp"]),
        "approvals fell": a["d5_appr_q2"] < a["d5_appr_q1"] - 10,
        "non-partner stable": abs(a["d5_appr_nonpartner_q2"] - a["d5_appr_nonpartner_q1"]) < 2,
        "partner majority": a["d5_partner_share_q2"] > 50 and a["d5_partner_first_q"] == "2025Q2",
    }
    bad = [k for k, ok in checks.items() if not ok]
    if bad and __import__("os").environ.get("SB_NOGUARD"):
        print("GUARDS", bad)
    else:
        assert not bad, f"Day 5 narrative guards failed: {bad}"
    return a
