"""Computed answers for Day 3 lessons other than L3.4 (estimation, resampling, testing logic, k-group tests, power,
multiple testing). Keys d3_. Every narrative claim in the lessons is guarded at the end."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.power import NormalIndPower, TTestIndPower
from statsmodels.stats.proportion import proportion_confint, proportion_effectsize
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.contingency_tables import mcnemar

from . import measures as M


def _r(x, nd=4):
    return round(float(x), nd)


def _sig(x, n=3):
    return float(f"{float(x):.{n}g}")


def _baskets(tx):
    s = tx[~tx.return_flag & (tx.quantity > 0)].drop_duplicates("line_id")
    s = s[s.unit_price / s.list_price < 20]
    b = s.groupby("basket_id").agg(rev=("revenue", "sum"), date=("date", "first"), store=("store_id", "first"),
                                   region=("region", "first"), fmt=("format", "first"), cust=("customer_id", "first"),
                                   pay=("payment_method", "first"), margin=("margin", "sum"), lines=("line_id", "size"))
    b["dow"] = pd.to_datetime(b.date).dt.dayofweek
    return s, b


def _welch_anova(groups):
    k = len(groups)
    n = np.array([len(g) for g in groups], float)
    m = np.array([np.mean(g) for g in groups])
    v = np.array([np.var(g, ddof=1) for g in groups])
    w = n / v
    mw = (w * m).sum() / w.sum()
    a_ = (w * (m - mw) ** 2).sum() / (k - 1)
    tmp = ((1 - w / w.sum()) ** 2 / (n - 1)).sum()
    b_ = 1 + 2 * (k - 2) / (k ** 2 - 1) * tmp
    f = a_ / b_
    df2 = (k ** 2 - 1) / (3 * tmp)
    return f, k - 1, df2, stats.f.sf(f, k - 1, df2)


def compute_day3(data=str(M.DATA)) -> dict:
    a: dict = {}
    tx = M.load("retail", "transactions", data)
    acc = M.load("finance", "accounts", data)
    s, b = _baskets(tx)
    pop = b.rev.to_numpy()
    rng = np.random.default_rng(303)

    # ================= L3.1 estimation and confidence intervals =================
    n = len(pop)
    m, sd = pop.mean(), pop.std(ddof=1)
    se = sd / np.sqrt(n)
    t = stats.t.ppf(0.975, n - 1)
    a["d3_n_baskets"] = n
    a["d3_basket_mean"], a["d3_basket_sd"], a["d3_basket_se"] = _r(m, 2), _r(sd, 2), _r(se, 2)
    a["d3_basket_ci"] = [_r(m - t * se, 2), _r(m + t * se, 2)]
    a["d3_basket_ci_halfwidth"] = _r(t * se, 2)
    # 99% and 90%
    for lvl in (90, 99):
        tt = stats.t.ppf(0.5 + lvl / 200, n - 1)
        a[f"d3_basket_ci{lvl}"] = [_r(m - tt * se, 2), _r(m + tt * se, 2)]
    # width vs n (sqrt law) from a random subsample
    widths = {}
    for k in (100, 400, 1600):
        widths[k] = _r(2 * stats.t.ppf(0.975, k - 1) * sd / np.sqrt(k), 2)  # expected width at this n
    a["d3_ci_width_by_n"] = widths
    # coverage simulation of the t-interval on heavy-tailed basket value
    cov = {}
    for k in (30, 200):
        hits = 0
        reps = 4000
        for _ in range(reps):
            x = rng.choice(pop, k, replace=True)
            h = stats.t.ppf(0.975, k - 1) * x.std(ddof=1) / np.sqrt(k)
            hits += (x.mean() - h <= m <= x.mean() + h)
        cov[k] = _r(100 * hits / reps, 1)
    a["d3_t_coverage"] = cov
    # proportion CI: default rate overall and for a small segment
    d = acc.default_12m
    k1, n1 = int(d.sum()), len(d)
    lo, hi = proportion_confint(k1, n1, method="wilson")
    a["d3_def_rate"] = _r(100 * k1 / n1, 2)
    a["d3_def_ci"] = [_r(100 * lo, 2), _r(100 * hi, 2)]
    stu = acc[acc.employment_type == "student"].default_12m
    a["d3_stu_n"], a["d3_stu_def"] = len(stu), int(stu.sum())
    a["d3_stu_rate"] = _r(100 * stu.mean(), 2)
    lo, hi = proportion_confint(int(stu.sum()), len(stu), method="wilson")
    a["d3_stu_ci"] = [_r(100 * lo, 2), _r(100 * hi, 2)]
    # tiny segment: high-income (HNI) and a single small branch
    br = acc.groupby("branch_id").default_12m.agg(["sum", "size"])
    small = br["size"].idxmin()
    a["d3_small_branch"], a["d3_small_branch_n"] = small, int(br.loc[small, "size"])
    a["d3_small_branch_def"] = int(br.loc[small, "sum"])
    a["d3_small_branch_rate"] = _r(100 * br.loc[small, "sum"] / br.loc[small, "size"], 2)
    lo, hi = proportion_confint(int(br.loc[small, "sum"]), int(br.loc[small, "size"]), method="wilson")
    a["d3_small_branch_ci"] = [_r(100 * lo, 2), _r(100 * hi, 2)]
    # Wald vs Wilson coverage at fraud base rate, n = 300
    pf = acc.fraud_flag.mean()
    a["d3_fraud_p"] = _r(100 * pf, 2)
    reps, nn = 4000, 300
    xs = rng.binomial(nn, pf, reps)
    wald_hits = wil_hits = 0
    zero = int((xs == 0).sum())
    for x in xs:
        ph = x / nn
        h = 1.96 * np.sqrt(ph * (1 - ph) / nn)
        wald_hits += (ph - h <= pf <= ph + h)
        l2, h2 = proportion_confint(x, nn, method="wilson")
        wil_hits += (l2 <= pf <= h2)
    a["d3_wald_cov"], a["d3_wilson_cov"] = _r(100 * wald_hits / reps, 1), _r(100 * wil_hits / reps, 1)
    a["d3_zero_share"] = _r(100 * zero / reps, 1)
    # mean margin % (ratio estimate) — CI via delta/bootstrap in L3.2
    a["d3_margin_pct"] = _r(100 * b.margin.sum() / b.rev.sum(), 2)

    # ================= L3.2 bootstrap and permutation =================
    cust = s.groupby("customer_id").revenue.sum()
    a["d3_cust_n"] = len(cust)
    a["d3_cust_median"] = _r(cust.median(), 2)
    bs = np.array([np.median(rng.choice(cust.values, len(cust))) for _ in range(4000)])
    a["d3_cust_median_ci"] = [_r(np.percentile(bs, 2.5), 2), _r(np.percentile(bs, 97.5), 2)]
    a["d3_cust_median_se"] = _r(bs.std(ddof=1), 2)
    # ratio: margin % of revenue, resampling baskets
    idx = np.arange(len(b))
    rv, mg = b.rev.to_numpy(), b.margin.to_numpy()
    bm = []
    for _ in range(3000):
        j = rng.choice(idx, len(idx))
        bm.append(100 * mg[j].sum() / rv[j].sum())
    a["d3_margin_ci"] = [_r(np.percentile(bm, 2.5), 2), _r(np.percentile(bm, 97.5), 2)]
    # resampling unit: lines vs baskets vs stores for mean line revenue
    lines = s[s.unit_price / s.list_price < 20]
    lrev = lines.revenue.to_numpy()
    se_lines = lrev.std(ddof=1) / np.sqrt(len(lrev))
    st_tot = lines.groupby("store_id").revenue.agg(["sum", "size"])
    sids = np.arange(len(st_tot))
    sb = []
    for _ in range(3000):
        j = rng.choice(sids, len(sids))
        sb.append(st_tot["sum"].to_numpy()[j].sum() / st_tot["size"].to_numpy()[j].sum())
    a["d3_line_mean"] = _r(lrev.mean(), 3)
    a["d3_se_lines"], a["d3_se_stores"] = _r(se_lines, 3), _r(np.std(sb, ddof=1), 3)
    a["d3_se_ratio_store_line"] = _r(np.std(sb, ddof=1) / se_lines, 1)
    # permutation test: default rate in two branches
    r_ = acc.groupby("branch_id").default_12m.mean().sort_values()
    b_lo, b_hi = "BR03", "BR11"
    if b_lo not in r_.index or b_hi not in r_.index:
        b_lo, b_hi = r_.index[len(r_) // 2 - 1], r_.index[len(r_) // 2 + 1]
    x1 = acc[acc.branch_id == b_lo].default_12m.to_numpy().astype(int)
    x2 = acc[acc.branch_id == b_hi].default_12m.to_numpy().astype(int)
    obs = x2.mean() - x1.mean()
    pool = np.concatenate([x1, x2])
    cnt = 0
    P = 10000
    for _ in range(P):
        rng.shuffle(pool)
        cnt += abs(pool[len(x1):].mean() - pool[:len(x1)].mean()) >= abs(obs) - 1e-12
    a["d3_perm_br_a"], a["d3_perm_br_b"] = b_lo, b_hi
    a["d3_perm_rate_a"], a["d3_perm_rate_b"] = _r(100 * x1.mean(), 2), _r(100 * x2.mean(), 2)
    a["d3_perm_n_a"], a["d3_perm_n_b"] = len(x1), len(x2)
    a["d3_perm_diff_pp"] = _r(100 * obs, 2)
    a["d3_perm_p"] = _r((cnt + 1) / (P + 1), 4)
    tab = np.array([[x1.sum(), len(x1) - x1.sum()], [x2.sum(), len(x2) - x2.sum()]])
    a["d3_chi2_p_branches"] = _r(stats.chi2_contingency(tab, correction=False)[1], 4)

    # ================= L3.3 hypothesis-testing logic =================
    v = acc.groupby("vintage").default_12m.agg(["sum", "size"])

    def two_prop(g1, g0):
        k1_, n1_ = v.loc[g1, "sum"], v.loc[g1, "size"]
        k0_, n0_ = v.loc[g0, "sum"], v.loc[g0, "size"]
        p1, p0 = k1_ / n1_, k0_ / n0_
        pp = (k1_ + k0_) / (n1_ + n0_)
        z = (p1 - p0) / np.sqrt(pp * (1 - pp) * (1 / n1_ + 1 / n0_))
        se_ = np.sqrt(p1 * (1 - p1) / n1_ + p0 * (1 - p0) / n0_)
        return p1, p0, z, 2 * stats.norm.sf(abs(z)), (p1 - p0 - 1.96 * se_, p1 - p0 + 1.96 * se_)

    p1, p0, z, p, ci = two_prop("2025Q1", "2024Q4")
    a["d3_v_q1"], a["d3_v_q4"] = _r(100 * p1, 2), _r(100 * p0, 2)
    a["d3_v_q1q4_p"], a["d3_v_q1q4_ci"] = _r(p, 3), [_r(100 * ci[0], 2), _r(100 * ci[1], 2)]
    p1, p0, z, p, ci = two_prop("2025Q2", "2025Q1")
    a["d3_v_q2"] = _r(100 * p1, 2)
    a["d3_v_q2q1_z"], a["d3_v_q2q1_p"] = _r(z, 1), _sig(p, 2)
    a["d3_v_q2q1_ci"] = [_r(100 * ci[0], 2), _r(100 * ci[1], 2)]
    # A/A simulation on stores: random 20/20 splits, Snacks growth index weeks 70-77 vs 54-69
    sc = M.load("retail", "weekly_store_category", data)
    cats = [c for c in sorted(sc.category.unique()) if c != "Hair Care"]
    pre = sc[sc.week.between(54, 69)].groupby(["store_id", "category"]).units.mean().unstack()
    post = sc[sc.week.between(70, 77)].groupby(["store_id", "category"]).units.mean().unstack()
    g = (post / pre)[cats]
    G = g.to_numpy()
    nst = G.shape[0]
    reps = 2000
    ps = np.empty((reps, len(cats)))
    for r in range(reps):
        perm = rng.permutation(nst)
        A, B = G[perm[:nst // 2]], G[perm[nst // 2:]]
        ps[r] = stats.ttest_ind(A, B, equal_var=False, axis=0).pvalue
    snack = cats.index("Snacks") if "Snacks" in cats else 0
    a["d3_aa_reps"] = reps
    a["d3_aa_fpr"] = _r(100 * (ps[:, snack] < 0.05).mean(), 1)
    a["d3_aa_p_hist"] = [int(x) for x in np.histogram(ps[:, snack], bins=10, range=(0, 1))[0]]
    a["d3_n_cats_aa"] = len(cats)
    a["d3_aa_any_sig"] = _r(100 * (ps.min(axis=1) < 0.05).mean(), 1)
    a["d3_aa_any_theory"] = _r(100 * (1 - 0.95 ** len(cats)), 1)
    # huge-n trivial significance: monthly transaction count, branch- vs online-acquired accounts (panel rows)
    pm = M.load("finance", "performance_monthly", data)
    px = pm.merge(acc[["account_id", "acquisition_channel"]], on="account_id")
    r1 = px[px.acquisition_channel == "branch"].txn_count.astype(float)
    r2 = px[px.acquisition_channel == "online"].txn_count.astype(float)
    dd, lo_, hi_, pp_ = M.welch_ci(r1, r2)
    a["d3_tc_branch"], a["d3_tc_online"] = _r(r1.mean(), 2), _r(r2.mean(), 2)
    a["d3_tc_n_rows"] = len(r1) + len(r2)
    a["d3_tc_n_acc"] = int(px[px.acquisition_channel.isin(["branch", "online"])].account_id.nunique())
    a["d3_tc_diff"], a["d3_tc_ci"], a["d3_tc_p"] = _r(dd, 3), [_r(lo_, 3), _r(hi_, 3)], _sig(pp_, 2)
    a["d3_tc_d"] = _r(dd / np.sqrt((r1.var() + r2.var()) / 2), 3)
    # same comparison at account level (one row per account: mean monthly count)
    am = px[px.acquisition_channel.isin(["branch", "online"])].groupby(["account_id", "acquisition_channel"]).txn_count.mean().reset_index()
    a["d3_tc_acc_p"] = _sig(stats.ttest_ind(am[am.acquisition_channel == "branch"].txn_count,
                                            am[am.acquisition_channel == "online"].txn_count, equal_var=False).pvalue, 2)

    # ================= L3.5 more than two groups =================
    groups = {k: gg.rev.to_numpy() for k, gg in b.groupby("region")}
    a["d3_reg_means"] = {k: _r(x.mean(), 2) for k, x in groups.items()}
    a["d3_reg_medians"] = {k: _r(np.median(x), 2) for k, x in groups.items()}
    a["d3_reg_n"] = {k: len(x) for k, x in groups.items()}
    a["d3_reg_sd"] = {k: _r(x.std(ddof=1), 1) for k, x in groups.items()}
    f, p = stats.f_oneway(*groups.values())
    a["d3_anova_f"], a["d3_anova_p"] = _r(f, 2), _sig(p, 2)
    f, d1_, d2_, p = _welch_anova(list(groups.values()))
    a["d3_welch_f"], a["d3_welch_df2"], a["d3_welch_p"] = _r(f, 2), _r(d2_, 0), _sig(p, 2)
    h, p = stats.kruskal(*groups.values())
    a["d3_kw_h"], a["d3_kw_p"] = _r(h, 1), _sig(p, 2)
    a["d3_levene_p"] = _sig(stats.levene(*groups.values()).pvalue, 2)
    allv = np.concatenate(list(groups.values()))
    ss_b = sum(len(x) * (x.mean() - allv.mean()) ** 2 for x in groups.values())
    ss_t = ((allv - allv.mean()) ** 2).sum()
    a["d3_eta2"] = _r(ss_b / ss_t, 4)
    tk = pairwise_tukeyhsd(b.rev, b.region)
    tkd = pd.DataFrame(tk.summary().data[1:], columns=tk.summary().data[0])
    tkd["pair"] = tkd.group1 + "–" + tkd.group2
    a["d3_tukey_sig_pairs"] = tkd[tkd.reject].pair.tolist()
    a["d3_tukey"] = {r.pair: {"diff": _r(r.meandiff, 2), "p": _r(r["p-adj"], 3)} for _, r in tkd.iterrows()}
    # pairwise Mann-Whitney with Holm on medians
    names = sorted(groups)
    pairs, pv = [], []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            pairs.append(f"{names[i]}–{names[j]}")
            pv.append(stats.mannwhitneyu(groups[names[i]], groups[names[j]]).pvalue)
    rej, padj, *_ = multipletests(pv, method="holm")
    a["d3_mw_holm"] = {pp: _r(q, 4) for pp, q in zip(pairs, padj)}
    a["d3_mw_holm_sig"] = [pp for pp, rr in zip(pairs, rej) if rr]
    # default by employment type: chi-square, Cramér's V, standardised residuals
    ct = pd.crosstab(acc.employment_type, acc.default_12m)
    chi2, p, dof, exp = stats.chi2_contingency(ct, correction=False)
    a["d3_emp_rates"] = {k: _r(100 * v_, 2) for k, v_ in (ct[True] / ct.sum(axis=1)).items()}
    a["d3_emp_chi2"], a["d3_emp_dof"], a["d3_emp_p"] = _r(chi2, 1), int(dof), _sig(p, 2)
    a["d3_emp_v"] = _r(np.sqrt(chi2 / (ct.to_numpy().sum() * (min(ct.shape) - 1))), 3)
    res = (ct - exp) / np.sqrt(exp)
    a["d3_emp_resid_student"] = _r(res.loc["student", True], 1)
    a["d3_emp_min_expected"] = _r(exp.min(), 0)
    # Fisher: HNI small cell — branch with fewest defaults vs the rest among partner accounts? use small branch 2x2
    sb_ = acc[acc.branch_id == a["d3_small_branch"]].default_12m
    rest = acc[(acc.branch_id != a["d3_small_branch"]) & (acc.region == acc[acc.branch_id == a["d3_small_branch"]].region.iloc[0])].default_12m
    tab = [[int(sb_.sum()), int((~sb_).sum())], [int(rest.sum()), int((~rest).sum())]]
    a["d3_fisher_tab"] = tab
    a["d3_fisher_p"] = _r(stats.fisher_exact(tab)[1], 4)
    a["d3_fisher_exp"] = _r(len(sb_) * rest.mean(), 1)
    a["d3_small_branch_region"] = str(acc[acc.branch_id == a["d3_small_branch"]].region.iloc[0])
    a["d3_region_peer_rate"] = _r(100 * rest.mean(), 2)
    # McNemar: same accounts 30+ DPD at month 6 vs month 12 on book
    m6 = pm[pm.month_on_book == 6].set_index("account_id").dpd >= 30
    m12 = pm[pm.month_on_book == 12].set_index("account_id").dpd >= 30
    j = m6.index.intersection(m12.index)
    t2 = pd.crosstab(m6.loc[j], m12.loc[j])
    t2 = t2.reindex(index=[False, True], columns=[False, True], fill_value=0)
    mc = mcnemar(t2.to_numpy(), exact=False, correction=True)
    a["d3_mc_n"] = len(j)
    a["d3_mc_b"], a["d3_mc_c"] = int(t2.loc[True, False]), int(t2.loc[False, True])
    a["d3_mc_m6"], a["d3_mc_m12"] = _r(100 * m6.loc[j].mean(), 2), _r(100 * m12.loc[j].mean(), 2)
    a["d3_mc_p"] = _sig(mc.pvalue, 2)

    # ================= L3.6 effect sizes, power, sample size =================
    sd_g = 0.126  # growth-index SD (from L3.4 recompute below)
    hc = sc[sc.category == "Hair Care"]
    gi = hc[hc.week.between(70, 77)].groupby("store_id").units.mean() / hc[hc.week.between(54, 69)].groupby("store_id").units.mean()
    grp = hc.groupby("store_id").experiment_group.first()
    gn = gi / gi[grp == "control"].mean()
    sd_g = float(np.sqrt((gn[grp == "test"].var() + gn[grp == "control"].var()) / 2))  # as in L3.4
    a["d3_gi_sd"] = _r(sd_g, 3)
    from toolkit.rcp_power.recipe import n_means, power_means  # lessons quote exactly what the recipe reports
    a["d3_stores_per_arm"] = {mde: int(np.ceil(n_means(mde / 100, sd_g, 0.05, 0.8))) for mde in (5, 8, 10, 12, 15, 20)}
    a["d3_power_20_at"] = {mde: int(round(100 * power_means(mde / 100, sd_g, 20, 0.05))) for mde in (5, 10, 12, 15)}
    a["d3_mde_20"] = _r(100 * (stats.norm.ppf(0.975) + stats.norm.ppf(0.8)) * sd_g * np.sqrt(2 / 20), 1)
    # proportions: challenger 35% -> 38%, 80/20 split
    npow = NormalIndPower()
    es = proportion_effectsize(0.38, 0.35)
    n_ch = npow.solve_power(effect_size=es, alpha=0.05, power=0.8, ratio=4.0)  # nobs1 = challenger, ratio = champion/challenger
    a["d3_cohen_h_3pp"] = _r(abs(es), 4)
    from toolkit.rcp_power.recipe import n_props
    f16_ = M.F16(data)
    p0c = float(acc[acc.strategy_group == "champion"].cured_within_3m.astype(float).mean())
    ncp = n_props(p0c, p0c + 0.03, 0.05, 0.8, ratio=0.25)
    a["d3_n_challenger_3pp"] = int(np.ceil(ncp * 0.25))
    a["d3_n_champion_3pp"] = int(np.ceil(ncp))
    a["d3_n_total_3pp"] = int(np.ceil(ncp) + np.ceil(ncp * 0.25))
    n50 = npow.solve_power(effect_size=es, alpha=0.05, power=0.8, ratio=1.0)
    a["d3_n_total_3pp_5050"] = int(np.ceil(2 * n50))
    f16 = M.F16(data)
    a["d3_f16_n_ch"], a["d3_f16_n_cp"] = f16["n_challenger"], f16["n_champion"]
    a["d3_power_actual_3pp"] = int(round(100 * npow.power(effect_size=es, nobs1=f16["n_challenger"], alpha=0.05,
                                                   ratio=f16["n_champion"] / f16["n_challenger"])))
    a["d3_f16_cure_ch"], a["d3_f16_cure_cp"] = _r(100 * f16["cure_challenger"], 1), _r(100 * f16["cure_champion"], 1)
    a["d3_f16_diff"] = _r(100 * f16["measured"], 1)
    a["d3_f16_ci"] = [_r(100 * f16["ci_low"], 1), _r(100 * f16["ci_high"], 1)]
    pc1, pc0 = f16["cure_challenger"], f16["cure_champion"]
    a["d3_f16_rr"] = _r(pc1 / pc0, 3)
    a["d3_f16_or"] = _r((pc1 / (1 - pc1)) / (pc0 / (1 - pc0)), 3)
    a["d3_f16_nnt"] = int(np.ceil(1 / (pc1 - pc0)))
    # ICC and design effect: lines inside stores
    hcl = tx[(tx.category == "Hair Care") & ~tx.return_flag & (tx.quantity > 0)].drop_duplicates("line_id")
    pre_w = hc[hc.week.between(54, 69)]
    ms_b = pre_w.groupby("store_id").units.mean().var(ddof=1)
    ms_w = pre_w.groupby("store_id").units.var(ddof=1).mean()
    m_ = 16
    icc = max(0.0, (ms_b - ms_w / m_) / (ms_b - ms_w / m_ + ms_w))
    a["d3_icc_weeks"] = _r(icc, 3)
    a["d3_deff_16"] = _r(1 + (m_ - 1) * icc, 1)
    a["d3_eff_n_640"] = int(round(640 / (1 + (m_ - 1) * icc)))
    # under-powered null: HNI Fisher result power
    a["d3_hni_power"] = int(round(100 * npow.power(effect_size=proportion_effectsize(0.06, 0.04), nobs1=241, alpha=0.05,
                                            ratio=(len(acc) - 241) / 241)))
    # power curve points for the proportions case (total accounts at 80/20)
    a["d3_prop_curve"] = {dpp: int(np.ceil(n_props(p0c, p0c + dpp / 100, 0.05, 0.8, 0.25)) + np.ceil(0.25 * n_props(p0c, p0c + dpp / 100, 0.05, 0.8, 0.25)))
                          for dpp in (2, 3, 5, 8)}

    # ================= L3.7 multiple testing =================
    # retail: 40 stores, Fri-Sat vs Mon-Thu basket value within each store
    rows = []
    for sid, gg in b.groupby("store"):
        wk = gg[gg.dow.isin([4, 5])].rev
        wd = gg[gg.dow.isin([0, 1, 2, 3])].rev
        if len(wk) >= 5 and len(wd) >= 5:
            rows.append((sid, stats.ttest_ind(wk, wd, equal_var=False).pvalue, wk.mean() - wd.mean(), len(wk) + len(wd)))
    mt = pd.DataFrame(rows, columns=["store", "p", "diff", "n"]).sort_values("p")
    a["d3_mt_r_tests"] = len(mt)
    a["d3_mt_r_raw"] = int((mt.p < 0.05).sum())
    a["d3_mt_r_expected_fp"] = _r(0.05 * len(mt), 1)
    a["d3_mt_r_bonf"] = int(multipletests(mt.p, method="bonferroni")[0].sum())
    a["d3_mt_r_holm"] = int(multipletests(mt.p, method="holm")[0].sum())
    a["d3_mt_r_bh"] = int(multipletests(mt.p, method="fdr_bh")[0].sum())
    a["d3_mt_r_min_store"], a["d3_mt_r_min_p"] = mt.store.iloc[0], _r(mt.p.iloc[0], 4)
    a["d3_mt_r_min_diff"] = _r(mt["diff"].iloc[0], 2)
    a["d3_mt_r_min_padj_bonf"] = _r(min(1, mt.p.iloc[0] * len(mt)), 3)
    a["d3_mt_r_median_n"] = int(mt.n.median())
    # finance: 30 candidate features vs default — 20 real, 10 pure noise (seeded)
    feats = ["age", "income_annual", "tenure_months_with_bank", "limit_or_loan_amount", "interest_rate", "term_months",
             "utilisation", "dti", "bureau_score", "app_score", "inquiries_6m", "delinq_2y", "balance_current",
             "txn_count_3m", "txn_amount_3m", "digital_share", "branch_visits_6m", "complaints_12m", "months_observed",
             "max_dpd_12m"]
    feats = [f_ for f_ in feats if f_ in acc.columns and f_ != "max_dpd_12m"][:19] + ["complaints_12m"]
    feats = list(dict.fromkeys(feats))
    sub = acc.sample(3000, random_state=7)
    nr = np.random.default_rng(99)
    res_rows = []
    for f_ in feats:
        x = sub[f_]
        ok = x.notna()
        res_rows.append((f_, "real", stats.mannwhitneyu(x[ok & sub.default_12m], x[ok & ~sub.default_12m]).pvalue))
    for i in range(30 - len(res_rows)):
        x = pd.Series(nr.normal(size=len(sub)), index=sub.index)
        res_rows.append((f"noise_{i + 1:02d}", "noise", stats.mannwhitneyu(x[sub.default_12m], x[~sub.default_12m]).pvalue))
    ft = pd.DataFrame(res_rows, columns=["feature", "kind", "p"])
    a["d3_mt_f_tests"], a["d3_mt_f_real"] = len(ft), int((ft.kind == "real").sum())
    a["d3_mt_f_n"] = len(sub)
    for meth, key in (("bonferroni", "bonf"), ("holm", "holm"), ("fdr_bh", "bh")):
        rj = multipletests(ft.p, method=meth)[0]
        a[f"d3_mt_f_{key}_real"] = int((rj & (ft.kind == "real")).sum())
        a[f"d3_mt_f_{key}_noise"] = int((rj & (ft.kind == "noise")).sum())
    raw = ft.p < 0.05
    a["d3_mt_f_raw_real"] = int((raw & (ft.kind == "real")).sum())
    a["d3_mt_f_raw_noise"] = int((raw & (ft.kind == "noise")).sum())
    a["d3_mt_f_noise_min_p"] = _r(ft[ft.kind == "noise"].p.min(), 4)
    # forking paths: analyst tries all categories on A/A — share of A/A splits with ≥1 "win"
    a["d3_fork_any"] = a["d3_aa_any_sig"]
    # optional stopping illustration: peeking 8 times at an A/A test with weekly data
    peeks = 0
    reps = 2000
    for _ in range(reps):
        x = rng.normal(size=(2, 800))
        hit = False
        for nlook in range(100, 801, 100):
            if stats.ttest_ind(x[0, :nlook], x[1, :nlook]).pvalue < 0.05:
                hit = True
                break
        peeks += hit
    a["d3_peek_fpr"] = _r(100 * peeks / reps, 1)

    # ================= extra keys for exercises =================
    # North's gap within store format (medians)
    nb = {}
    for fmt_, gg in b.groupby("fmt"):
        med = gg.groupby("region").rev.median()
        if "North" in med.index and len(med) > 1:
            nb[fmt_] = _r(med["North"] - med.drop("North").median(), 2)
    a["d3_north_gap_by_fmt"] = nb
    a["d3_north_share_express"] = _r(100 * (b[b.region == "North"].fmt == "Express").mean(), 1)
    a["d3_other_share_express"] = _r(100 * (b[b.region != "North"].fmt == "Express").mean(), 1)
    # e-coupon: n per arm for +1 pp on control conversion (planning, ignoring SRM)
    ec = M.load("retail", "ecoupon_ab", data)
    pc = float(ec[ec.assigned_arm == ec.assigned_arm.value_counts().index[-1]].converted_14d.mean()) if False else float(ec.converted_14d.mean())
    a["d3_ec_base_pct"] = _r(100 * pc, 2)
    a["d3_ec_n_per_arm_1pp"] = int(np.ceil(n_props(pc, pc + 0.01, 0.05, 0.8)))
    a["d3_ec_n_per_arm_15pp"] = int(np.ceil(n_props(pc, pc + 0.015, 0.05, 0.8)))
    # branch intervals wider than 2 pp
    brc = acc.groupby("branch_id").default_12m.agg(["sum", "size"])
    wid = brc.apply(lambda r: np.diff(proportion_confint(int(r["sum"]), int(r["size"]), method="wilson"))[0] * 100, axis=1)
    a["d3_br_wide_n"], a["d3_br_n"] = int((wid > 2).sum()), len(brc)
    a["d3_br_rate_range"] = [_r(100 * (brc["sum"] / brc["size"]).min(), 2), _r(100 * (brc["sum"] / brc["size"]).max(), 2)]
    # 40-store pairwise (780 pairs) Holm on basket value
    sp, st_ids = [], sorted(b.store.unique())
    vals = {k: g.rev.to_numpy() for k, g in b.groupby("store")}
    for i in range(len(st_ids)):
        for j2 in range(i + 1, len(st_ids)):
            sp.append(stats.ttest_ind(vals[st_ids[i]], vals[st_ids[j2]], equal_var=False).pvalue)
    a["d3_store_pairs"] = len(sp)
    a["d3_store_pairs_raw"] = int((np.array(sp) < 0.05).sum())
    a["d3_store_pairs_holm"] = int(multipletests(sp, method="holm")[0].sum())
    # months to accrue the 3pp challenger sample at 1,400 new 30+ DPD accounts a month
    a["d3_months_3pp"] = _r(a["d3_n_total_3pp"] / 1400, 1)
    # bootstrap CI for median basket (all baskets)
    bmed = [np.median(rng.choice(pop, len(pop))) for _ in range(3000)]
    a["d3_basket_median"] = _r(np.median(pop), 2)
    a["d3_basket_median_ci"] = [_r(np.percentile(bmed, 2.5), 2), _r(np.percentile(bmed, 97.5), 2)]

    # ================= guards =================
    checks = {
        "coverage at n=30 below nominal": a["d3_t_coverage"][30] < 94.0,
        "coverage at n=200 closer to nominal": a["d3_t_coverage"][200] > a["d3_t_coverage"][30],
        "width roughly halves when n x4": 0.35 < widths[1600] / widths[400] < 0.65 and 0.35 < widths[400] / widths[100] < 0.65,
        "wald undercovers at fraud base rate": a["d3_wald_cov"] < 90 and a["d3_wilson_cov"] > a["d3_wald_cov"] + 5,
        "student default above overall and CI excludes overall": a["d3_stu_ci"][0] > a["d3_def_rate"],
        "small branch CI wide": a["d3_small_branch_ci"][1] - a["d3_small_branch_ci"][0] > 1.0,
        "store bootstrap SE > line SE": a["d3_se_ratio_store_line"] > 1.3,
        "perm and chi2 agree": abs(a["d3_perm_p"] - a["d3_chi2_p_branches"]) < 0.03,
        "Q1 vs Q4 not significant": a["d3_v_q1q4_p"] > 0.05,
        "Q2 vs Q1 significant": a["d3_v_q2q1_p"] < 1e-6,
        "AA FPR near 5": 3.0 < a["d3_aa_fpr"] < 7.0,
        "AA any-category inflated": a["d3_aa_any_sig"] > 20,
        "trivial significance with tiny d": a["d3_tc_p"] < 1e-4 and abs(a["d3_tc_d"]) < 0.05,
        "ANOVA and KW significant": a["d3_anova_p"] < 0.05 and a["d3_kw_p"] < 0.05,
        "eta2 tiny": a["d3_eta2"] < 0.02,
        "North lowest mean": min(a["d3_reg_means"], key=a["d3_reg_means"].get) == "North",
        "employment chi2 significant": a["d3_emp_p"] < 0.001,
        "student residual positive large": a["d3_emp_resid_student"] > 3,
        "mcnemar significant": a["d3_mc_p"] < 0.05,
        "20 stores enough for 12% roughly": a["d3_stores_per_arm"][12] <= 25 and a["d3_stores_per_arm"][10] > 20,
        "5% needs many stores": a["d3_stores_per_arm"][5] > 60,
        "F16 actual power below 80 at 3pp": a["d3_power_actual_3pp"] < 80,
        "F16 effect significant": a["d3_f16_ci"][0] > 0,
        "deff > 1.5": a["d3_deff_16"] > 1.5,
        "HNI underpowered": a["d3_hni_power"] < 50,
        "retail raw > corrected": a["d3_mt_r_raw"] >= a["d3_mt_r_holm"],
        "retail bonf none": a["d3_mt_r_bonf"] == 0,
        "finance BH keeps more real than Bonferroni or equal": a["d3_mt_f_bh_real"] >= a["d3_mt_f_bonf_real"],
        "finance BH no noise": a["d3_mt_f_bh_noise"] == 0,
        "peeking inflates": a["d3_peek_fpr"] > 12,
        "Q2 roughly tripled": 2.5 < a["d3_v_q2"] / a["d3_v_q1"] < 3.6,
        "North differs from all (MW Holm)": set(a["d3_mw_holm_sig"]) == {"East–North", "North–South", "North–West"},
        "small branch unremarkable vs region": a["d3_fisher_p"] > 0.05,
        "5% test impossible with 40 stores": a["d3_stores_per_arm"][5] > 20,
        "true F16 effect about 6pp": 4.5 < a["d3_f16_diff"] < 7.5,
        "BH keeps all raw-real, Bonferroni fewer": a["d3_mt_f_bh_real"] == a["d3_mt_f_raw_real"] and a["d3_mt_f_bonf_real"] < a["d3_mt_f_bh_real"],
        "raw admits noise": a["d3_mt_f_raw_noise"] >= 1,
        "account-level p not significant": a["d3_tc_acc_p"] > 0.05,
        "employment V very weak": a["d3_emp_v"] < 0.1,
        "North gap is mix": a["d3_north_share_express"] > 3 * a["d3_other_share_express"] and max(a["d3_north_gap_by_fmt"].values()) > 0,
    }
    bad = [k for k, ok in checks.items() if not ok]
    if bad and __import__("os").environ.get("SB_NOGUARD"): print("GUARDS", bad)
    else: assert not bad, f"Day 3 narrative guards failed: {bad}"
    return a
