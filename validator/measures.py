"""Measure every planted phenomenon from the generated files.

Each function returns a dict with at least {"measured": float} and is used by
  * datagen/tests (anomaly proofs against tolerance bands in the register),
  * the register builder (writes measured values into the answer key),
  * quiz/exercise answer keys (numbers are computed, never typed).
Usage:  python -m validator.measures [--data data] [--json out.json]
"""
from __future__ import annotations

import argparse
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


@lru_cache(maxsize=64)
def load(domain: str, table: str, data: str = str(DATA)) -> pd.DataFrame:
    return pd.read_parquet(Path(data) / domain / f"{table}.parquet")


def benford_mad(x) -> float:
    x = np.asarray(x, float)
    x = x[x > 0]
    fd = (x / 10 ** np.floor(np.log10(x))).astype(int)
    obs = np.bincount(fd, minlength=10)[1:10] / len(fd)
    return float(np.abs(obs - np.log10(1 + 1 / np.arange(1, 10))).mean())


def psi(expected, actual, bins=10) -> float:
    expected, actual = np.asarray(expected, float), np.asarray(actual, float)
    edges = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    e = np.histogram(expected, edges)[0] / len(expected) + 1e-4
    a = np.histogram(actual, edges)[0] / len(actual) + 1e-4
    return float(((a - e) * np.log(a / e)).sum())


def welch_ci(x, y, conf=0.95):
    x, y = np.asarray(x, float), np.asarray(y, float)
    d = x.mean() - y.mean()
    vx, vy = x.var(ddof=1) / len(x), y.var(ddof=1) / len(y)
    se = np.sqrt(vx + vy)
    df = (vx + vy) ** 2 / (vx ** 2 / (len(x) - 1) + vy ** 2 / (len(y) - 1))
    t = stats.t.ppf(0.5 + conf / 2, df)
    return d, d - t * se, d + t * se, float(2 * stats.t.sf(abs(d / se), df))


# ------------------------------------------------------------------ retail
def _tx(d):
    return load("retail", "transactions", d)


def _sales(d):
    t = _tx(d)
    return t[~t.return_flag & (t.quantity > 0)].drop_duplicates("line_id")


def R01(d=str(DATA)):
    t = _tx(d).drop_duplicates("line_id")
    return {"measured": int(((t.quantity < 0) & ~t.return_flag).sum())}


def R02(d=str(DATA)):
    t = _tx(d).drop_duplicates("line_id")
    return {"measured": int((t.unit_price / t.list_price > 20).sum())}


def R03(d=str(DATA)):
    t = _tx(d)
    n = int(t.line_id.duplicated().sum())
    s = t[~t.return_flag]
    over = s.revenue.sum() / s.drop_duplicates("line_id").revenue.sum() - 1
    return {"measured": n, "revenue_overstatement_pct": round(100 * over, 2)}


def R04(d=str(DATA)):
    t = _tx(d)
    m = t.temperature_c.isna()
    tab = pd.crosstab(t.region, m)
    return {"measured": round(float(m.mean()), 4), "chi2_p_region": round(float(stats.chi2_contingency(tab)[1]), 4)}


def R05(d=str(DATA)):
    c = load("retail", "customers", d)
    r = c.groupby("loyalty_flag").age_band.apply(lambda s: s.isna().mean())
    return {"measured": round(float(r[False]), 4), "member_rate": round(float(r[True]), 4)}


def R06(d=str(DATA)):
    s = _sales(d)
    b = s.groupby("basket_id").agg(rev=("revenue", "sum"), lines=("line_id", "count"), hh=("household_size", "first"))
    miss = b.hh.isna()
    return {"measured": round(float(b[miss].lines.mean() / b[~miss].lines.mean()), 3),
            "basket_rev_median_missing": round(float(b[miss].rev.median()), 2),
            "basket_rev_median_known": round(float(b[~miss].rev.median()), 2),
            "missing_rate": round(float(load("retail", "customers", d).household_size.isna().mean()), 4)}


def R07(d=str(DATA)):
    s = _sales(d)
    s = s[s.unit_price / s.list_price < 50]
    cr = s.groupby("customer_id").revenue.sum().sort_values(ascending=False)
    b = s.groupby("basket_id").revenue.sum()
    return {"measured": round(float(cr.head(25).sum() / cr.sum()), 4),
            "mean_over_median_basket": round(float(b.mean() / b.median()), 3),
            "p99_basket": round(float(b.quantile(0.99)), 2), "median_basket": round(float(b.median()), 2)}


def R08(d=str(DATA), store="S017"):
    ws = load("retail", "weekly_store", d)
    s = ws[ws.store_id == store].set_index("week").revenue
    o = ws[ws.store_id != store].groupby("week").revenue.sum()
    r = (s / o).values
    # simple least-squares single change point on the share series
    best, bk = np.inf, None
    for k in range(8, len(r) - 8):
        sse = ((r[:k] - r[:k].mean()) ** 2).sum() + ((r[k:] - r[k:].mean()) ** 2).sum()
        if sse < best:
            best, bk = sse, k
    return {"measured": int(bk + 1), "level_ratio": round(float(r[bk:].mean() / r[:bk].mean()), 3)}


def R09(d=str(DATA), category="Hair Care", weeks=(70, 77), pre=(54, 69)):
    sc = load("retail", "weekly_store_category", d)
    h = sc[sc.category == category]
    pre_m = h[h.week.between(*pre)].groupby("store_id").units.mean()
    post_m = h[h.week.between(*weeks)].groupby("store_id").units.mean()
    grp = h.groupby("store_id").experiment_group.first()
    g = post_m / pre_m
    cbar = g[grp == "control"].mean()
    diff, lo, hi, p = welch_ci(g[grp == "test"] / cbar, g[grp == "control"] / cbar)
    nd, nlo, nhi, np_ = welch_ci(post_m[grp == "test"], post_m[grp == "control"])
    return {"measured": round(float(diff), 4), "ci_low": round(float(lo), 4), "ci_high": round(float(hi), 4),
            "p_value": round(p, 5), "naive_post_lift": round(float(post_m[grp == "test"].mean() / post_m[grp == "control"].mean() - 1), 4),
            "naive_p_value": round(np_, 4), "n_test": int((grp == "test").sum()), "n_control": int((grp == "control").sum())}


def R10(d=str(DATA), weeks=(15, 16, 17, 40, 41, 42, 90, 91, 92)):
    sk = load("retail", "weekly_sku_chain", d)
    p = load("retail", "products", d)
    victim = p.loc[p.product_name == "Lustra Shampoo 200ml", "sku"].iloc[0]
    promoted = p.loc[p.product_name == "Lustra Shampoo 400ml", "sku"].iloc[0]
    hc = sk.merge(p[["sku", "category"]], on="sku")
    cat = hc[(hc.category == "Hair Care") & (hc.sku != promoted)].groupby("week").units.sum()
    v = sk[sk.sku == victim].set_index("week").units
    pr = sk[sk.sku == promoted].set_index("week").units
    share = v / cat
    nb = [w for w in v.index if w not in weeks and min(abs(w - x) for x in weeks) <= 4]
    gain = (pr / cat).loc[list(weeks)].mean() - (pr / cat).loc[nb].mean()
    loss = share.loc[nb].mean() - share.loc[list(weeks)].mean()
    return {"measured": round(float(share.loc[list(weeks)].mean() / share.loc[nb].mean() - 1), 4),
            "promoted_share_gain_pp": round(100 * float(gain), 2), "victim_share_loss_pp": round(100 * float(loss), 2),
            "cannibalised_share_of_gain": round(float(loss / gain), 3), "victim_sku": victim, "promoted_sku": promoted}


def R11(d=str(DATA)):
    s = _sales(d)
    bd = s.drop_duplicates("basket_id")
    dow = pd.to_datetime(bd.date).dt.dayofweek.value_counts()
    ws = load("retail", "weekly_store", d).groupby("week").units.sum()
    cal = load("retail", "calendar", d).drop_duplicates("week").set_index("week")
    q4 = cal.quarter.eq(4) & ~cal.holiday_flag
    oth = ~cal.quarter.eq(4) & ~cal.holiday_flag
    return {"measured": round(float(dow.loc[[4, 5]].mean() / dow.loc[[0, 1, 2, 3]].mean()), 3),
            "q4_vs_other": round(float(ws[q4].mean() / ws[oth].mean()), 3),
            "holiday_vs_non": round(float(ws[cal.holiday_flag].mean() / ws[~cal.holiday_flag].mean()), 3)}


def R12(d=str(DATA)):
    td = pd.read_parquet(ROOT / "instructor" / "truth" / "retail" / "true_demand_sku_week.parquet")
    sk = load("retail", "weekly_sku_chain", d)
    return {"measured": round(float(1 - td.observed_expected_units.sum() / td.true_expected_units.sum()), 4),
            "stockout_cell_share": round(float(sk.stockout_store_count.sum() / (40 * len(sk))), 4)}


def R13(d=str(DATA)):
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    e = load("retail", "price_elasticity_extract", d)
    out = {}
    for cat in ("Snacks", "Dairy"):
        x = e[(e.category == cat) & ~e.stockout_flag].copy()
        x["lp"] = np.log(x.shelf_price / x.list_price)
        m = smf.glm("units ~ lp + promo_flag + display_flag + C(sku) + C(store_id) + C(week)", x,
                    family=sm.families.Poisson()).fit()
        x2 = x[x.units > 0].copy()
        x2["lu"] = np.log(x2.units)
        m2 = smf.ols("lu ~ lp + promo_flag + display_flag + C(sku) + C(store_id) + C(week)", x2).fit()
        m3 = smf.ols("lu ~ lp + C(sku) + C(store_id) + C(week)", x2).fit()
        out[cat] = {"poisson": round(float(m.params["lp"]), 3), "poisson_se": round(float(m.bse["lp"]), 3),
                    "loglog_ols": round(float(m2.params["lp"]), 3), "loglog_no_promo_controls": round(float(m3.params["lp"]), 3)}
    return {"measured": out["Snacks"]["poisson"], "measured_dairy": out["Dairy"]["poisson"], "detail": out}


def R14(d=str(DATA)):
    s = _sales(d)
    s = s[s.unit_price / s.list_price < 50]
    overall = s.groupby("promo_flag").quantity.mean()
    by = s.groupby(["format", "promo_flag"]).quantity.mean().unstack()
    within = (by[True] / by[False] - 1).round(3).to_dict()
    return {"measured": round(float(overall[True] / overall[False] - 1), 4), "within_format_lift": within,
            "promo_share_by_format": s.groupby("format").promo_flag.mean().round(3).to_dict()}


def R15(d=str(DATA)):
    s = _sales(d)
    r = s.groupby("promo_flag").display_flag.mean()
    return {"measured": round(float(r[True]), 4), "display_rate_non_promo": round(float(r[False]), 4)}


def R16(d=str(DATA)):
    sk = load("retail", "weekly_sku_chain", d)
    p = load("retail", "products", d)
    pa = pd.concat([p, load("retail", "products_archive", d)])
    x = sk.merge(pa[["sku", "category"]], on="sku")
    x = x[x.category == "Snacks"]
    x["year"] = np.where(x.week <= 52, 1, 2)
    tot = x.groupby("year").units.sum()
    cur = x[x.sku.isin(p.sku)].groupby("year").units.sum()
    return {"measured": round(float(cur[2] / cur[1] - 1), 4), "true_category_growth": round(float(tot[2] / tot[1] - 1), 4)}


def R17(d=str(DATA)):
    t = _tx(d).drop_duplicates("line_id")
    truth = json.loads((ROOT / "instructor" / "truth" / "retail" / "truth.json").read_text())
    ab = truth["planted"]["R17_customers"]
    rr = t.groupby(t.customer_id.isin(ab)).apply(lambda x: x.return_flag.sum() / (~x.return_flag).sum(), include_groups=False)
    cust = t.groupby("customer_id").agg(ret=("return_flag", "sum"), n=("return_flag", "size"))
    cust = cust[cust.n >= 5]
    rate = cust.ret / (cust.n - cust.ret).clip(lower=1)
    flagged = set(rate[rate > 0.20].index)
    return {"measured": round(float(rr[True]), 4), "others": round(float(rr[False]), 4),
            "rule_recall_rate_gt_20pct": round(len(flagged & set(ab)) / len(ab), 3),
            "rule_precision_rate_gt_20pct": round(len(flagged & set(ab)) / max(len(flagged), 1), 3)}


def R18(d=str(DATA), store="S033"):
    t = _tx(d).drop_duplicates("line_id")
    t = t[~t.return_flag]
    mads = t.groupby("store_id").revenue.apply(lambda s: benford_mad(s.values))
    rounded = ((t.revenue * 100).round().astype("int64") % 50 == 0).groupby(t.store_id).mean()
    return {"measured": round(float(mads[store]), 4), "peer_median_mad": round(float(mads.drop(store).median()), 4),
            "peer_max_mad": round(float(mads.drop(store).max()), 4), "rounded_share": round(float(rounded[store]), 3),
            "peer_rounded_share": round(float(rounded.drop(store).median()), 3), "worst_store": mads.idxmax()}


def R19(d=str(DATA), week=80):
    t = _tx(d).drop_duplicates("line_id")
    on = t[(t.channel != "in-store") & t.promo_flag]
    bas = t.drop_duplicates("basket_id")
    share = bas.groupby(bas.week >= week).channel.apply(lambda x: (x != "in-store").mean())
    return {"measured": round(psi(on[on.week < week].discount_pct, on[on.week >= week].discount_pct), 3),
            "median_discount_before": float(on[on.week < week].discount_pct.median()),
            "median_discount_after": float(on[on.week >= week].discount_pct.median()),
            "online_share_before": round(float(share[False]), 3), "online_share_after": round(float(share[True]), 3)}


def R20(d=str(DATA)):
    s = _sales(d)
    s = s[s.unit_price / s.list_price < 50]
    seg = pd.read_parquet(ROOT / "instructor" / "truth" / "retail" / "customer_segments.parquet")
    s = s[~s.customer_id.isin(seg[seg.bulk].customer_id)]
    b = s.groupby("basket_id").agg(rev=("revenue", "sum"), loyal=("loyalty_flag", "first"))
    return {"measured": round(float(b[b.loyal].rev.mean() / b[~b.loyal].rev.mean() - 1), 4), "true_causal": 0.05}


def R21(d=str(DATA)):
    t = _tx(d).drop_duplicates("line_id")
    t = t[~t.return_flag]
    p = pd.concat([load("retail", "products", d), load("retail", "products_archive", d)]).set_index("sku").subcategory
    t = t.assign(sub=t.sku.map(p))
    bs = t.groupby("basket_id")["sub"].agg(set)
    out = {}
    for a, b in (("Pasta", "Pasta Sauce"), ("Beer", "Chips")):
        A = bs.apply(lambda s: a in s)
        B = bs.apply(lambda s: b in s)
        out[f"{a}->{b}"] = {"lift": round(float((A & B).mean() / (A.mean() * B.mean())), 3),
                            "support": round(float((A & B).mean()), 4), "confidence": round(float((A & B).mean() / A.mean()), 3)}
    return {"measured": out["Pasta->Pasta Sauce"]["lift"], "measured_beer_chips": out["Beer->Chips"]["lift"], "detail": out}


def R22(d=str(DATA)):
    sk = load("retail", "weekly_sku_chain", d)
    adi = sk.groupby("sku").units.apply(lambda u: len(u) / max((u > 0).sum(), 1))
    return {"measured": round(float((adi > 1.32).mean()), 4)}


def customer_features(d=str(DATA)):
    s = _sales(d)
    s = s[s.unit_price / s.list_price < 50]
    g = s.groupby("customer_id")
    f = pd.DataFrame({"baskets": g.basket_id.nunique(), "revenue": g.revenue.sum(),
                      "promo_share": g.promo_flag.mean(), "avg_price_ratio": g.apply(lambda x: (x.unit_price / x.list_price).mean(), include_groups=False),
                      "avg_list_price": g.list_price.median()})
    f["avg_basket"] = f.revenue / f.baskets
    cat = pd.crosstab(s.customer_id, s.category, normalize="index")
    return f.join(cat)


def R23(d=str(DATA)):
    from sklearn.cluster import KMeans
    from sklearn.metrics import adjusted_rand_score
    from sklearn.preprocessing import StandardScaler
    f = customer_features(d)
    seg = pd.read_parquet(ROOT / "instructor" / "truth" / "retail" / "customer_segments.parquet").set_index("customer_id")
    f = f[(f.baskets >= 2)]
    X = f.copy()
    X[["revenue", "avg_basket", "baskets"]] = np.log1p(X[["revenue", "avg_basket", "baskets"]])
    Xs = StandardScaler().fit_transform(X)
    km = KMeans(5, n_init=20, random_state=0).fit(Xs)
    return {"measured": round(float(adjusted_rand_score(seg.loc[f.index, "segment"], km.labels_)), 3),
            "n_customers": int(len(f))}


def R24(d=str(DATA)):
    ab = load("retail", "ecoupon_ab", d)
    cnt = ab.assigned_arm.value_counts()
    srm_p = stats.chisquare(cnt.values).pvalue
    conv = ab.groupby("assigned_arm").converted_14d.mean()
    clean = ab[ab.app_version != "3.2"].groupby("assigned_arm").converted_14d.mean()
    return {"measured": round(float(cnt["treatment"] / cnt.sum()), 4), "srm_p": float(srm_p),
            "observed_lift_pp": round(100 * float(conv["treatment"] - conv["control"]), 2),
            "lift_excl_v32_pp": round(100 * float(clean["treatment"] - clean["control"]), 2),
            "true_lift_pp": 1.5}


# ------------------------------------------------------------------ finance
def _acc(d):
    return load("finance", "accounts", d)


def F01(d=str(DATA)):
    a = _acc(d)
    return {"measured": int(((a.age >= 120) | (a.age < 18)).sum()), "negative_income": int((a.income_annual < 0).sum())}


def F02(d=str(DATA)):
    a = _acc(d)
    m = a.income_annual.isna()
    r = a.groupby(m).default_12m.mean()
    return {"measured": round(float(r[True] / r[False]), 3), "missing_rate": round(float(m.mean()), 4),
            "default_missing": round(float(r[True]), 4), "default_known": round(float(r[False]), 4)}


def F03(d=str(DATA)):
    a = _acc(d)
    return {"measured": round(float(a.default_12m.mean()), 4), "fraud_rate": round(float(a.fraud_flag.mean()), 4),
            "accuracy_if_predict_no_fraud": round(float(1 - a.fraud_flag.mean()), 4)}


def F04(d=str(DATA)):
    a = _acc(d)
    c = a[a.product_type == "credit_card"]
    lo = c[c.utilisation <= 0.5].default_12m.mean()
    hi = c[c.utilisation > 0.9].default_12m.mean()
    bands = c.groupby(pd.cut(c.utilisation, [-0.01, 0.5, 0.7, 0.8, 0.9, 2]), observed=True).default_12m.mean()
    return {"measured": round(float(hi / lo), 3), "by_band": {str(k): round(float(v), 4) for k, v in bands.items()}}


def F05(d=str(DATA)):
    import statsmodels.formula.api as smf
    a = _acc(d)
    x = a[a.age.between(18, 100)].copy()
    x["young"], x["hidti"], x["y"] = (x.age < 25).astype(int), (x.dti > 0.45).astype(int), x.default_12m.astype(int)
    m = smf.logit("y ~ young * hidti + bureau_score + inquiries_6m", x).fit(disp=0)
    k = "young:hidti"
    return {"measured": round(float(np.exp(m.params[k])), 3), "p_value": float(m.pvalues[k])}


def F06(d=str(DATA)):
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    a = _acc(d)
    x = a[(a.income_annual > 0)][["income_annual", "limit_or_loan_amount", "bureau_score", "dti"]].dropna()
    r = x[["income_annual", "limit_or_loan_amount"]].corr().iloc[0, 1]
    X = ((x - x.mean()) / x.std()).assign(const=1.0).values
    return {"measured": round(float(variance_inflation_factor(X, 0)), 2), "corr": round(float(r), 3)}


def F07(d=str(DATA)):
    import networkx as nx
    a = _acc(d).set_index("account_id")
    L = load("finance", "devices_addresses", d)
    G = nx.Graph()
    G.add_edges_from(zip(L.account_id, L.link_id))
    comps = [{n for n in c if n.startswith("A")} for c in nx.connected_components(G)]
    big = sorted([c for c in comps if len(c) >= 6], key=len, reverse=True)
    rates = [round(float(a.loc[list(c)].fraud_flag.mean()), 3) for c in big]
    return {"measured": len(big), "sizes": [len(c) for c in big], "fraud_rates": rates,
            "largest_other_component": max(len(c) for c in comps if len(c) < 6)}


def F08(d=str(DATA), thr=10_000):
    pm = load("finance", "performance_monthly", d)
    c = pm[pm.cash_deposit_max > 0]
    near = c.cash_deposit_max.between(0.9 * thr, thr - 0.01)
    above = c.cash_deposit_max.between(thr, 1.1 * thr)
    acc = (c[near].groupby("account_id").size() >= 6).sum()
    return {"measured": round(float(near.sum() / max(above.sum(), 1)), 2), "accounts_6plus_months": int(acc),
            "deposits_just_below": int(near.sum()), "deposits_just_above": int(above.sum())}


def F09(d=str(DATA), branch="BR07"):
    a = _acc(d)
    mads = a.groupby("branch_id").txn_amount_3m.apply(lambda s: benford_mad(s.values))
    return {"measured": round(float(mads[branch]), 4), "peer_max_mad": round(float(mads.drop(branch).max()), 4),
            "peer_median_mad": round(float(mads.drop(branch).median()), 4), "worst_branch": mads.idxmax()}


def F10(d=str(DATA)):
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split
    a = _acc(d)
    feat = ["bureau_score", "dti", "inquiries_6m", "delinq_2y", "app_score"]
    x = a.dropna(subset=feat)
    y = x.default_12m.astype(int)
    res = {}
    for nm, cols in (("clean", feat), ("leaky", feat + ["recovery_amount", "collections_flag"])):
        X = x[cols].astype(float)
        X = (X - X.mean()) / X.std()
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=0, stratify=y)
        m = LogisticRegression(max_iter=2000).fit(Xtr, ytr)
        res[nm] = round(float(roc_auc_score(yte, m.predict_proba(Xte)[:, 1])), 3)
    return {"measured": res["leaky"], "clean_auc": res["clean"]}


def F11(d=str(DATA)):
    a = _acc(d)
    base = a[a.vintage.str.startswith("2023")].app_score
    late = a[a.vintage.isin(["2025Q2", "2025Q3"])].app_score
    by = {v: round(psi(base, a[a.vintage == v].app_score), 3) for v in sorted(a.vintage.unique())}
    mix = a[a.vintage.isin(["2025Q2", "2025Q3"])].acquisition_channel.value_counts(normalize=True).round(3).to_dict()
    return {"measured": round(psi(base, late), 3), "psi_by_vintage": by, "late_channel_mix": mix}


def F12(d=str(DATA)):
    from sklearn.metrics import roc_auc_score
    a = _acc(d)
    early = a[~a.vintage.isin(["2025Q2", "2025Q3"])]
    late = a[a.vintage.isin(["2025Q2", "2025Q3"])]
    ae, al = roc_auc_score(early.default_12m, -early.app_score), roc_auc_score(late.default_12m, -late.app_score)
    c = a[a.product_type == "credit_card"]
    csi_util = psi(c[c.vintage.str.startswith("2023")].utilisation.dropna(), c[c.vintage.isin(["2025Q2", "2025Q3"])].utilisation.dropna())
    return {"measured": round(float(al - ae), 3), "auc_early": round(float(ae), 3), "auc_late": round(float(al), 3),
            "default_early": round(float(early.default_12m.mean()), 4), "default_late": round(float(late.default_12m.mean()), 4),
            "csi_utilisation": round(csi_util, 3)}


def F13(d=str(DATA)):
    a = _acc(d)
    return {"measured": round(float(1 - a.churn_flag.mean()), 4),
            "naive_mean_months_churners": round(float(a[a.churn_flag].churn_month.mean()), 2)}


def F14(d=str(DATA)):
    a = _acc(d)
    b = a.balance_current.sort_values(ascending=False)
    return {"measured": round(float(b.head(int(0.01 * len(b))).sum() / b.sum()), 4),
            "mean_over_median": round(float(b.mean() / b[b > 0].median()), 3)}


def F15(d=str(DATA)):
    a = _acc(d)
    dec = load("finance", "applications_declined", d)
    apps = pd.concat([a[["protected_group", "region"]].assign(approved=1), dec[["protected_group", "region"]].assign(approved=0)])
    r = apps.groupby("protected_group").approved.mean()
    return {"measured": round(float(r["B"] / r["A"]), 3), "approval_A": round(float(r["A"]), 4),
            "approval_B": round(float(r["B"]), 4),
            "r4_share_B": round(float(apps[apps.region == "R4"].protected_group.eq("B").mean()), 3),
            "approval_by_region": apps.groupby("region").approved.mean().round(4).to_dict()}


def F16(d=str(DATA)):
    a = _acc(d)
    c = a[a.strategy_group != "none"]
    x1 = c[c.strategy_group == "challenger"].cured_within_3m.astype(float)
    x0 = c[c.strategy_group == "champion"].cured_within_3m.astype(float)
    diff, lo, hi, p = welch_ci(x1, x0)
    return {"measured": round(float(diff), 4), "ci_low": round(float(lo), 4), "ci_high": round(float(hi), 4), "p_value": round(p, 5),
            "n_challenger": int(len(x1)), "n_champion": int(len(x0)),
            "cure_challenger": round(float(x1.mean()), 4), "cure_champion": round(float(x0.mean()), 4)}


def F17(d=str(DATA)):
    pol = load("finance", "policies", d)
    cl = load("finance", "claims", d)
    n = cl.groupby("policy_id").size().reindex(pol.policy_id, fill_value=0)
    top3 = cl.claim_amount.nlargest(3).sum() / cl.claim_amount.sum()
    return {"measured": round(float(n.var() / n.mean()), 3), "claim_frequency": round(float(n.sum() / pol.exposure_years.sum()), 4),
            "mean_severity": round(float(cl.claim_amount.mean()), 1), "median_severity": round(float(cl.claim_amount.median()), 1),
            "top3_share_of_losses": round(float(top3), 3),
            "loss_ratio": round(float(cl.claim_amount.sum() / pol.premium.sum()), 3)}


def F18(d=str(DATA)):
    a = _acc(d)
    dec = load("finance", "applications_declined", d)
    return {"measured": round(float(a.app_score.mean() - dec.app_score.mean()), 1),
            "declined_share": round(float(len(dec) / (len(dec) + len(a))), 4),
            "booked_low_score_default": round(float(a[a.app_score < a.app_score.quantile(0.1)].default_12m.mean()), 4)}


ALL = {k: v for k, v in globals().items() if (k[0] in "RF") and k[1:].isdigit() and callable(v)}


def run_all(data=str(DATA)) -> dict:
    out = {}
    for k in sorted(ALL, key=lambda s: (s[0] != "R", int(s[1:]))):
        out[k] = ALL[k](data)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(DATA))
    ap.add_argument("--json")
    a = ap.parse_args()
    res = run_all(a.data)
    for k, v in res.items():
        print(f"{k:<4} {v['measured']}")
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=2, default=str))
