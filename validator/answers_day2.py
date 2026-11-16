"""Computed answers for Day 2 (probability, distributions, sampling, simulation, Benford, linear algebra). Keys d2_."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from . import measures as M


def _r(x, nd=4):
    return round(float(x), nd)


def compute_day2(data=str(M.DATA)) -> dict:
    a: dict = {}
    tx = M.load("retail", "transactions", data).drop_duplicates("line_id")
    acc = M.load("finance", "accounts", data)
    sales = tx[~tx.return_flag & (tx.quantity > 0)]
    clean = sales[sales.unit_price / sales.list_price < 20]
    rng = np.random.default_rng(2026)

    # ---------- L2.1 probability, conditional probability, Bayes ----------
    ret = tx.return_flag
    a["d2_p_return"] = _r(100 * ret.sum() / (~ret).sum(), 2)
    el = tx.category == "Electronics"
    a["d2_p_return_elec"] = _r(100 * tx[el].return_flag.sum() / (~tx[el].return_flag).sum(), 2)
    a["d2_p_return_food"] = _r(100 * tx[tx.category.isin(["Fresh Produce", "Dairy", "Bakery"])].return_flag.sum()
                               / (~tx[tx.category.isin(["Fresh Produce", "Dairy", "Bakery"])].return_flag).sum(), 2)
    pp, pd_ = sales.promo_flag.mean(), sales.display_flag.mean()
    joint = (sales.promo_flag & sales.display_flag).mean()
    a["d2_p_promo"], a["d2_p_display"] = _r(100 * pp, 1), _r(100 * pd_, 1)
    a["d2_p_both"], a["d2_p_both_if_indep"] = _r(100 * joint, 2), _r(100 * pp * pd_, 2)
    a["d2_p_disp_given_promo"] = _r(100 * sales[sales.promo_flag].display_flag.mean(), 1)
    # data-based alert: inquiries_6m >= 4
    alert = acc.inquiries_6m >= 4
    f = acc.fraud_flag
    a["d2_alert_rule"] = "inquiries_6m ≥ 4"
    a["d2_fraud_base_pct"] = _r(100 * f.mean(), 2)
    a["d2_alert_rate_pct"] = _r(100 * alert.mean(), 2)
    sens, fpr = alert[f].mean(), alert[~f].mean()
    a["d2_alert_sens_pct"], a["d2_alert_fpr_pct"] = _r(100 * sens, 1), _r(100 * fpr, 1)
    ppv_bayes = sens * f.mean() / (sens * f.mean() + fpr * (1 - f.mean()))
    a["d2_alert_ppv_bayes_pct"] = _r(100 * ppv_bayes, 2)
    a["d2_alert_ppv_direct_pct"] = _r(100 * f[alert].mean(), 2)
    a["d2_alert_lift"] = _r(f[alert].mean() / f.mean(), 1)
    n10k = 10_000
    a["d2_nf_fraud"] = int(round(n10k * f.mean()))
    a["d2_nf_caught"] = int(round(n10k * f.mean() * sens))
    a["d2_nf_false"] = int(round(n10k * (1 - f.mean()) * fpr))
    # textbook Bayes (diagnostic)
    a["d2_tb_ppv_pct"] = _r(100 * 0.9 * 0.01 / (0.9 * 0.01 + 0.05 * 0.99), 1)
    # conditional default by channel; odds
    pdp = acc[acc.acquisition_channel == "partner"].default_12m.mean()
    pdb = acc[acc.acquisition_channel == "branch"].default_12m.mean()
    a["d2_pd_partner_pct"], a["d2_pd_branch_pct"] = _r(100 * pdp, 2), _r(100 * pdb, 2)
    a["d2_odds_partner"], a["d2_odds_branch"] = _r(pdp / (1 - pdp), 4), _r(pdb / (1 - pdb), 4)
    a["d2_logodds_partner"] = _r(np.log(pdp / (1 - pdp)), 3)
    a["d2_p_partner"] = _r(100 * (acc.acquisition_channel == "partner").mean(), 1)
    a["d2_p_partner_given_default"] = _r(100 * (acc[acc.default_12m].acquisition_channel == "partner").mean(), 1)
    # expected loss per account (illustrative LGD 60%, EAD = limit for cards, balance for loans)
    ead = np.where(acc.product_type == "credit_card", acc.limit_or_loan_amount, acc.limit_or_loan_amount * 0.6)
    el_ = acc.default_12m.mean() * 0.6 * ead.mean()
    a["d2_ead_mean"] = _r(ead.mean(), 0)
    a["d2_el_per_account"] = _r(el_, 0)

    # ---------- L2.2 discrete distributions ----------
    sk = M.load("retail", "weekly_sku_chain", data)
    prod = M.load("retail", "products", data)
    reg_sku = prod[~prod.long_tail_flag].sku
    disp = sk[sk.sku.isin(reg_sku)].groupby("sku").units.agg(lambda u: u.var() / u.mean())
    a["d2_sku_disp_median"] = _r(disp.median(), 1)
    sc = M.load("retail", "weekly_store_category", data)
    one = sc[(sc.store_id == "S001") & (sc.category == "Dairy")].units
    a["d2_s1_dairy_mean"], a["d2_s1_dairy_var"] = _r(one.mean(), 1), _r(one.var(), 1)
    a["d2_s1_dairy_disp"] = _r(one.var() / one.mean(), 1)
    # binomial: defaults per vintage vs binomial expectation
    v = acc.groupby("vintage").default_12m.agg(["sum", "size", "mean"])
    p0 = acc.default_12m.mean()
    v["exp_sd"] = np.sqrt(v["size"] * p0 * (1 - p0))
    v["z"] = (v["sum"] - v["size"] * p0) / v["exp_sd"]
    a["d2_vint_n"] = int(len(v))
    a["d2_vint_rate_min"], a["d2_vint_rate_max"] = _r(100 * v["mean"].min(), 2), _r(100 * v["mean"].max(), 2)
    a["d2_vint_chi2_p"] = float(f"{stats.chi2_contingency(np.c_[v['sum'], v['size'] - v['sum']])[1]:.3g}")
    early = v.loc[[i for i in v.index if not i.startswith("2025Q2") and not i.startswith("2025Q3")]]
    a["d2_vint_early_chi2_p"] = _r(stats.chi2_contingency(np.c_[early['sum'], early['size'] - early['sum']])[1], 3)
    # binomial probability: P(X >= k) for a vintage of 2,400 at 4%
    n_, k_ = 2400, 120
    a["d2_binom_mean"], a["d2_binom_sd"] = _r(n_ * p0, 1), _r(np.sqrt(n_ * p0 * (1 - p0)), 1)
    a["d2_binom_p_ge120"] = _r(100 * stats.binom.sf(k_ - 1, n_, p0), 2)
    # hypergeometric audit sampling
    a["d2_hyp_p_detect"] = _r(100 * (1 - stats.hypergeom.pmf(0, 200, 10, 50)), 1)
    a["d2_binom_p_detect"] = _r(100 * (1 - (1 - 10 / 200) ** 50), 1)
    a["d2_hyp_n_for_95"] = int(next(n for n in range(1, 201) if 1 - stats.hypergeom.pmf(0, 200, 10, n) >= 0.95))
    # geometric: baskets until the first promo basket
    b = clean.groupby("basket_id").promo_flag.max()
    pb = b.mean()
    a["d2_p_promo_basket"] = _r(100 * pb, 1)
    a["d2_geom_mean_wait"] = _r(1 / pb, 2)
    a["d2_geom_p_within3"] = _r(100 * (1 - (1 - pb) ** 3), 1)
    # Poisson: claims per policy
    pol = M.load("finance", "policies", data)
    cl = M.load("finance", "claims", data)
    nclaim = cl.groupby("policy_id").size().reindex(pol.policy_id, fill_value=0)
    lam = nclaim.mean()
    a["d2_claim_mean"] = _r(lam, 4)
    a["d2_claim_disp"] = _r(nclaim.var() / lam, 3)
    a["d2_claim_p0_obs"] = _r(100 * (nclaim == 0).mean(), 2)
    a["d2_claim_p0_pois"] = _r(100 * stats.poisson.pmf(0, lam), 2)
    a["d2_claim_p2_obs"] = _r(100 * (nclaim >= 2).mean(), 3)
    a["d2_claim_p2_pois"] = _r(100 * stats.poisson.sf(1, lam), 3)
    # beta-binomial idea: store return rates spread vs binomial
    st = tx.groupby("store_id").agg(r=("return_flag", "sum"), n=("return_flag", "size"))
    st["rate"] = st.r / st.n
    pbar = st.r.sum() / st.n.sum()
    a["d2_store_ret_sd_obs"] = _r(100 * st.rate.std(), 2)
    a["d2_store_ret_sd_binom"] = _r(100 * np.sqrt(pbar * (1 - pbar) / st.n).mean(), 2)

    # ---------- L2.3 continuous distributions ----------
    basket = clean.groupby("basket_id").revenue.sum()
    bpos = basket[basket > 0].values
    fits = {}
    for nm, dist, kw in (("lognormal", stats.lognorm, {"floc": 0}), ("gamma", stats.gamma, {"floc": 0}),
                         ("weibull", stats.weibull_min, {"floc": 0}), ("normal", stats.norm, {})):
        par = dist.fit(bpos, **kw)
        ll = dist.logpdf(bpos, *par).sum()
        k = len(par) - (1 if kw else 0)
        fits[nm] = _r(2 * k - 2 * ll, 0)
    a["d2_basket_aic"] = fits
    a["d2_basket_best"] = min(fits, key=fits.get)
    sev = cl.claim_amount.values
    sev_nc = sev[sev < 100_000]
    sf = {}
    for nm, dist in (("gamma", stats.gamma), ("lognormal", stats.lognorm), ("exponential", stats.expon)):
        par = dist.fit(sev_nc, floc=0)
        sf[nm] = _r(2 * (len(par) - 1) - 2 * dist.logpdf(sev_nc, *par).sum(), 0)
    a["d2_sev_aic"] = sf
    a["d2_sev_best"] = min(sf, key=sf.get)
    a["d2_sev_mean_all"], a["d2_sev_mean_nocat"] = _r(sev.mean(), 0), _r(sev_nc.mean(), 0)
    gpar = stats.gamma.fit(sev_nc, floc=0)
    a["d2_sev_gamma_shape"] = _r(gpar[0], 2)
    a["d2_sev_p99_gamma"] = _r(stats.gamma.ppf(0.99, *gpar), 0)
    a["d2_sev_p99_emp"] = _r(np.quantile(sev, 0.99), 0)
    # Weibull for time between a customer's baskets (gaps)
    bd = clean.groupby("basket_id").agg(c=("customer_id", "first"), d=("date", "first"))
    bd["d"] = pd.to_datetime(bd.d)
    bd = bd.sort_values(["c", "d"])
    gaps = bd.groupby("c").d.diff().dt.days.dropna()
    gaps = gaps[gaps > 0].values
    wk, _, wsc = stats.weibull_min.fit(gaps, floc=0)
    a["d2_gap_median_days"] = _r(np.median(gaps), 0)
    a["d2_gap_mean_days"] = _r(gaps.mean(), 0)
    a["d2_gap_weibull_k"] = _r(wk, 2)
    a["d2_gap_n"] = int(len(gaps))
    # normal: bureau score
    bs = acc.bureau_score
    a["d2_bureau_within1sd_pct"] = _r(100 * ((bs - bs.mean()).abs() <= bs.std()).mean(), 1)
    a["d2_bureau_within2sd_pct"] = _r(100 * ((bs - bs.mean()).abs() <= 2 * bs.std()).mean(), 1)
    # Cauchy vs normal running means
    c = rng.standard_cauchy(100_000)
    nrm = rng.normal(size=100_000)
    a["d2_cauchy_mean_1k"], a["d2_cauchy_mean_100k"] = _r(c[:1000].mean(), 2), _r(c.mean(), 2)
    a["d2_normal_mean_1k"], a["d2_normal_mean_100k"] = _r(nrm[:1000].mean(), 3), _r(nrm.mean(), 3)
    # t vs normal critical values
    a["d2_t_crit_df5"], a["d2_t_crit_df30"], a["d2_z_crit"] = _r(stats.t.ppf(0.975, 5), 3), _r(stats.t.ppf(0.975, 30), 3), _r(stats.norm.ppf(0.975), 3)
    # weekly price changes: Laplace vs normal (price extract)
    pe = M.load("retail", "price_elasticity_extract", data).sort_values(["store_id", "sku", "week"], kind="stable")
    ch = np.log(pe.shelf_price).groupby([pe.store_id, pe.sku]).diff().dropna()
    ch = ch[ch != 0].values
    lp = stats.laplace.fit(ch)
    npar = stats.norm.fit(ch)
    a["d2_pc_aic_laplace"] = _r(2 * 2 - 2 * stats.laplace.logpdf(ch, *lp).sum(), 0)
    a["d2_pc_aic_normal"] = _r(2 * 2 - 2 * stats.norm.logpdf(ch, *npar).sum(), 0)
    a["d2_pc_kurt"] = _r(pd.Series(ch).kurt(), 1)

    # ---------- L2.4 sampling and bias ----------
    y = acc.default_12m.astype(float).values
    strata = acc.acquisition_channel.values
    N = len(y)
    srs, strat = [], []
    shares = pd.Series(strata).value_counts(normalize=True)
    idx_by = {s: np.where(strata == s)[0] for s in shares.index}
    for _ in range(2000):
        srs.append(y[rng.choice(N, 500, replace=False)].mean())
        est = 0.0
        for s_, w in shares.items():
            k = max(2, int(round(500 * w)))
            est += w * y[rng.choice(idx_by[s_], k, replace=False)].mean()
        strat.append(est)
    a["d2_srs_se_pp"], a["d2_strat_se_pp"] = _r(100 * np.std(srs), 3), _r(100 * np.std(strat), 3)
    a["d2_true_default_pct"] = _r(100 * y.mean(), 2)
    # convenience sample: branch-only
    a["d2_branch_only_pct"] = _r(100 * acc[acc.acquisition_channel == "branch"].default_12m.mean(), 2)
    r14 = M.R14(data)
    a["d2_simpson_overall_pct"] = _r(100 * r14["measured"], 1)
    a["d2_simpson_within"] = {k: _r(100 * v_, 1) for k, v_ in r14["within_format_lift"].items()}
    a["d2_simpson_promo_share"] = {k: _r(100 * v_, 1) for k, v_ in r14["promo_share_by_format"].items()}
    r16 = M.R16(data)
    a["d2_surv_current_pct"], a["d2_surv_true_pct"] = _r(100 * r16["measured"], 1), _r(100 * r16["true_category_growth"], 1)
    r20 = M.R20(data)
    a["d2_loyal_naive_pct"] = _r(100 * r20["measured"], 1)
    dec = M.load("finance", "applications_declined", data)
    a["d2_declined_n"], a["d2_declined_score"] = int(len(dec)), _r(dec.app_score.mean(), 0)
    a["d2_booked_score"] = _r(acc.app_score.mean(), 0)
    a["d2_booked_low_def_pct"] = _r(100 * acc[acc.app_score < acc.app_score.quantile(0.1)].default_12m.mean(), 1)
    a["d2_disp_promo_pct"] = _r(100 * sales[sales.promo_flag].display_flag.mean(), 1)
    a["d2_disp_nonpromo_pct"] = _r(100 * sales[~sales.promo_flag].display_flag.mean(), 1)

    # ---------- L2.5 LLN, CLT, Monte Carlo ----------
    bv = basket.values
    out = {}
    for n in (5, 30, 200):
        means = np.array([rng.choice(bv, n).mean() for _ in range(4000)])
        out[n] = {"skew": _r(pd.Series(means).skew(), 2), "se_sim": _r(means.std(), 2), "se_formula": _r(bv.std() / np.sqrt(n), 2)}
    a["d2_clt"] = out
    a["d2_pop_skew"] = _r(pd.Series(bv).skew(), 1)
    run = np.cumsum(rng.choice(bv, 3000)) / np.arange(1, 3001)
    a["d2_lln_mean_10"], a["d2_lln_mean_100"], a["d2_lln_mean_3000"] = _r(run[9], 1), _r(run[99], 1), _r(run[2999], 1)
    a["d2_pop_mean"] = _r(bv.mean(), 2)
    # Monte Carlo: Hair Care rollout P&L using the L3.4 estimate and its uncertainty
    r09 = M.R09(data)
    lift_mu = r09["measured"]
    lift_se = (r09["ci_high"] - r09["ci_low"]) / (2 * 1.96)
    base_units = 40 * 52 * M.load("retail", "weekly_store_category", data).query("category == 'Hair Care'").groupby("store_id").units.mean().mean()
    margin = 2.0
    cost = 0.10 * base_units * margin            # rollout cost = margin on 10% of baseline units (the break-even lift)
    sims = rng.normal(lift_mu, lift_se, 100_000)
    pnl = sims * base_units * margin - cost
    a["d2_mc_lift_mu_pct"], a["d2_mc_lift_se_pct"] = _r(100 * lift_mu, 1), _r(100 * lift_se, 1)
    a["d2_mc_base_units"] = _r(base_units, 0)
    a["d2_mc_cost"] = _r(cost, 0)
    a["d2_mc_p_loss_pct"] = _r(100 * (pnl < 0).mean(), 1)
    a["d2_mc_pnl_mean"] = _r(pnl.mean(), 0)
    a["d2_mc_pnl_p5"], a["d2_mc_pnl_p95"] = _r(np.percentile(pnl, 5), 0), _r(np.percentile(pnl, 95), 0)
    # Monte Carlo portfolio loss (preview of VaR)
    pd_i = np.full(len(acc), acc.default_12m.mean())
    ead_i = np.where(acc.product_type == "credit_card", acc.limit_or_loan_amount, 0.6 * acc.limit_or_loan_amount)
    losses = []
    for _ in range(2000):
        z = rng.normal()                     # one systematic factor (Vasicek-style, rho = 0.05)
        rho = 0.05
        pcond = stats.norm.cdf((stats.norm.ppf(pd_i[0]) - np.sqrt(rho) * z) / np.sqrt(1 - rho))
        d = rng.random(len(acc)) < pcond
        lgd = rng.beta(3, 2, d.sum())
        losses.append((ead_i[d] * lgd).sum())
    losses = np.array(losses)
    a["d2_port_el"], a["d2_port_p99"] = _r(losses.mean(), 0), _r(np.percentile(losses, 99), 0)
    a["d2_port_ratio"] = _r(np.percentile(losses, 99) / losses.mean(), 2)

    # ---------- L2.6 Benford ----------
    r18, f09 = M.R18(data), M.F09(data)
    a["d2_ben_s033"], a["d2_ben_peer_med_r"], a["d2_ben_peer_max_r"] = r18["measured"], r18["peer_median_mad"], r18["peer_max_mad"]
    a["d2_round_s033_pct"], a["d2_round_peer_pct"] = _r(100 * r18["rounded_share"], 1), _r(100 * r18["peer_rounded_share"], 1)
    a["d2_ben_br07"], a["d2_ben_peer_med_f"], a["d2_ben_peer_max_f"] = f09["measured"], f09["peer_median_mad"], f09["peer_max_mad"]
    # first-digit distributions
    def fd(x):
        x = np.asarray(x, float)
        x = x[x > 0]
        d = (x / 10 ** np.floor(np.log10(x))).astype(int)
        return np.bincount(d, minlength=10)[1:10] / len(d)
    ben = np.log10(1 + 1 / np.arange(1, 10))
    s033 = tx[(tx.store_id == "S033") & ~tx.return_flag].revenue
    a["d2_ben_digit1_s033_pct"] = _r(100 * fd(s033)[0], 1)
    a["d2_ben_digit1_theory_pct"] = _r(100 * ben[0], 1)
    br = acc[acc.branch_id == "BR07"].txn_amount_3m
    a["d2_ben_digit1_br07_pct"] = _r(100 * fd(br)[0], 1)
    obs = np.bincount((br[br > 0] / 10 ** np.floor(np.log10(br[br > 0]))).astype(int), minlength=10)[1:10]
    a["d2_ben_br07_chi2_p"] = float(f"{stats.chisquare(obs, ben * obs.sum()).pvalue:.3g}")
    a["d2_ben_br07_n"] = int(obs.sum())
    def _mad(s_):
        s_ = s_[s_ > 0]
        p_ = np.bincount((s_ / 10 ** np.floor(np.log10(s_))).astype(int), minlength=10)[1:10] / len(s_)
        return np.abs(p_ - ben).mean()
    mads = acc.groupby("branch_id").txn_amount_3m.apply(_mad).drop("BR07")
    smallb = mads.idxmax()
    sb = acc[(acc.branch_id == smallb) & (acc.txn_amount_3m > 0)].txn_amount_3m
    sp = np.bincount((sb / 10 ** np.floor(np.log10(sb))).astype(int), minlength=10)[1:10] / len(sb)
    a["d2_small_branch"], a["d2_small_branch_n"] = smallb, int(len(sb))
    a["d2_small_branch_mad"] = _r(np.abs(sp - ben).mean(), 4)
    a["d2_small_branch_expmad"] = _r(np.sqrt(2 / np.pi) * np.mean(np.sqrt(ben * (1 - ben) / len(sb))), 4)
    # span (orders of magnitude) — why retail line revenue is not Benford-friendly
    a["d2_span_retail"] = _r(np.log10(sales.revenue.quantile(0.99) / sales.revenue.quantile(0.01)), 2)
    a["d2_span_finance"] = _r(np.log10(acc.txn_amount_3m.quantile(0.99) / acc.txn_amount_3m.quantile(0.01)), 2)

    # ---------- L2.7 linear algebra ----------
    cols = ["income_annual", "limit_or_loan_amount", "bureau_score", "dti", "inquiries_6m"]
    X = acc[acc.income_annual > 0][cols].dropna()
    Z = (X - X.mean()) / X.std()
    R = np.corrcoef(Z.T.values)
    ev = np.sort(np.linalg.eigvalsh(R))[::-1]
    a["d2_eig"] = [_r(e, 3) for e in ev]
    a["d2_eig_ratio"] = _r(ev[0] / ev[-1], 0)
    a["d2_eig_share1"] = _r(100 * ev[0] / ev.sum(), 1)
    vec = np.linalg.eigh(R)[1][:, 0]
    a["d2_small_eig_loadings"] = {c_: _r(v_, 2) for c_, v_ in zip(cols, vec)}
    a["d2_det"] = float(f"{np.linalg.det(R):.3g}")
    # least squares: units ~ price index + promo for one SKU via normal equations vs lstsq
    e = M.load("retail", "price_elasticity_extract", data)
    s1 = e[(e.sku == e.sku.iloc[0]) & (e.units > 0)]
    Xd = np.c_[np.ones(len(s1)), np.log(s1.shelf_price / s1.list_price), s1.promo_flag.astype(float)]
    yv = np.log(s1.units.values)
    beta_ne = np.linalg.solve(Xd.T @ Xd, Xd.T @ yv)
    beta_ls = np.linalg.lstsq(Xd, yv, rcond=None)[0]
    a["d2_ls_beta"] = [_r(b_, 3) for b_ in beta_ls]
    a["d2_ls_agree"] = bool(np.allclose(beta_ne, beta_ls))
    resid = yv - Xd @ beta_ls
    a["d2_ls_orth"] = float(f"{np.abs(Xd.T @ resid).max():.1e}")
    # SVD of customer x category share matrix
    cat = pd.crosstab(clean.customer_id, clean.category, values=clean.revenue, aggfunc="sum").fillna(0)
    cat = cat.div(cat.sum(axis=1), axis=0)
    cat = cat[(clean.groupby("customer_id").basket_id.nunique() >= 3).reindex(cat.index).fillna(False)]
    s = np.linalg.svd(cat.values - cat.values.mean(0), compute_uv=False)
    a["d2_svd_share2"] = _r(100 * (s[:2] ** 2).sum() / (s ** 2).sum(), 1)
    a["d2_svd_n"] = int(len(cat))
    # cosine similarity between categories (customer spend vectors)
    cv = pd.crosstab(clean.customer_id, clean.category, values=clean.revenue, aggfunc="sum").fillna(0)
    def cos(x, y_):
        return float(x @ y_ / (np.linalg.norm(x) * np.linalg.norm(y_)))
    sub = M.load("retail", "products", data).set_index("sku").subcategory
    sub = pd.concat([sub, M.load("retail", "products_archive", data).set_index("sku").subcategory])
    sv = pd.crosstab(clean.basket_id, clean.sku.map(sub))
    a["d2_cos_pasta_sauce"] = _r(cos(sv["Pasta"].values, sv["Pasta Sauce"].values), 3)
    a["d2_cos_pasta_shampoo"] = _r(cos(sv["Pasta"].values, sv["Shampoo"].values), 3)

    # guards
    checks = {
        "electronics returned more than fresh food": a["d2_p_return_elec"] > a["d2_p_return_food"],
        "promo and display dependent": a["d2_p_both"] > 3 * a["d2_p_both_if_indep"],
        "alert PPV well below sensitivity": a["d2_alert_ppv_bayes_pct"] < a["d2_alert_sens_pct"] / 3,
        "Bayes equals direct PPV": abs(a["d2_alert_ppv_bayes_pct"] - a["d2_alert_ppv_direct_pct"]) < 0.01,
        "SKU sales over-dispersed": a["d2_sku_disp_median"] > 1.5,
        "vintages differ beyond binomial": a["d2_vint_chi2_p"] < 0.001,
        "hypergeometric > binomial detection": a["d2_hyp_p_detect"] > a["d2_binom_p_detect"],
        "basket best fit not normal": a["d2_basket_best"] != "normal",
        "Laplace beats normal for price changes": a["d2_pc_aic_laplace"] < a["d2_pc_aic_normal"],
        "stratified SE <= SRS SE": a["d2_strat_se_pp"] <= a["d2_srs_se_pp"] * 1.02,
        "CLT: skew falls with n": a["d2_clt"][5]["skew"] > a["d2_clt"][30]["skew"] > a["d2_clt"][200]["skew"],
        "Monte Carlo loss probability between 5% and 50%": 5 < a["d2_mc_p_loss_pct"] < 50,
        "finance Benford peers conform better than retail peers": a["d2_ben_peer_med_f"] < a["d2_ben_peer_med_r"],
        "smallest eigenvalue small (collinearity)": a["d2_eig"][-1] < 0.1,
        "least squares agree": a["d2_ls_agree"],
        "worst honest branch is marginal only because it is small": a["d2_small_branch_mad"] < 0.02 and a["d2_small_branch_mad"] - a["d2_small_branch_expmad"] < 0.006,
        "pasta-sauce cosine > pasta-shampoo": a["d2_cos_pasta_sauce"] > 3 * a["d2_cos_pasta_shampoo"],
        "Poisson under-predicts multi-claim policies by more than half": a["d2_claim_p2_obs"] > 2 * a["d2_claim_p2_pois"],
        "electronics ~4x fresh-food return rate": 3 < a["d2_p_return_elec"] / a["d2_p_return_food"] < 6,
        "rollout loss probability roughly one in five": 14 < a["d2_mc_p_loss_pct"] < 26,
        "two SVD components ~ half the variance": 38 < a["d2_svd_share2"] < 56,
        "gamma P99 below empirical P99": a["d2_sev_p99_gamma"] < a["d2_sev_p99_emp"],
        "branch-only sample understates by > 25%": a["d2_branch_only_pct"] < 0.75 * a["d2_true_default_pct"],
        "bureau roughly normal": 64 < a["d2_bureau_within1sd_pct"] < 72 and 93 < a["d2_bureau_within2sd_pct"] < 97.5,
        "vintages before 2025Q2 consistent with one rate": a["d2_vint_early_chi2_p"] > 0.05,
    }
    bad = [k for k, ok in checks.items() if not ok]
    assert not bad, f"Day 2 narrative no longer supported by the data: {bad}"
    return a
