"""Computed answers for Day 8 (clustering/PCA, RFM/CLV/cohorts, basket rules, pricing/promotions, anomaly detection, fraud rings and
structuring, credit risk scorecards/vintages/roll rates). Keys d8_."""
from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from . import measures as M

warnings.filterwarnings("ignore")


def _r(x, nd=3):
    return round(float(x), nd)


def woe_iv(x_bins, y):
    t = pd.crosstab(x_bins, y)
    t.columns = ["good", "bad"] if list(t.columns) == [False, True] or list(t.columns) == [0, 1] else t.columns
    g, b = t["good"] / t["good"].sum(), t["bad"] / t["bad"].sum()
    woe = np.log((g + 1e-6) / (b + 1e-6))
    iv = float(((g - b) * woe).sum())
    rate = t["bad"] / (t["good"] + t["bad"])
    return pd.DataFrame({"n": t.sum(axis=1), "bad_rate": rate, "woe": woe}), iv


def compute_day8(data=str(M.DATA)) -> dict:
    a: dict = {}
    tx = M.load("retail", "transactions", data).drop_duplicates("line_id")
    acc = M.load("finance", "accounts", data)
    s = tx[~tx.return_flag & (tx.quantity > 0) & (tx.unit_price / tx.list_price < 20)]

    # ================= L8.1 clustering and PCA =================
    f = M.customer_features(data)
    f = f[f.baskets >= 2]
    X = f.copy()
    X[["revenue", "avg_basket", "baskets"]] = np.log1p(X[["revenue", "avg_basket", "baskets"]])
    Xs = StandardScaler().fit_transform(X)
    sil = {}
    for k in range(2, 9):
        km = KMeans(k, n_init=20, random_state=0).fit(Xs)
        sil[k] = _r(silhouette_score(Xs, km.labels_), 3)
    a["d8_sil"] = sil
    a["d8_sil_best_k"] = max(sil, key=sil.get)
    km5 = KMeans(5, n_init=20, random_state=0).fit(Xs)
    f["cl"] = km5.labels_
    a["d8_n_cust_clust"] = len(f)
    r23 = M.R23(data)
    a["d8_ari"] = r23["measured"]
    prof = f.groupby("cl").agg(n=("baskets", "size"), baskets=("baskets", "median"), revenue=("revenue", "median"),
                               promo=("promo_share", "mean"), price=("avg_price_ratio", "mean"))
    cats = [c for c in f.columns if c not in ("baskets", "revenue", "promo_share", "avg_price_ratio", "avg_list_price", "avg_basket", "cl")]
    topcat = f.groupby("cl")[cats].mean().idxmax(axis=1)
    prof["top_category"] = topcat
    a["d8_profiles"] = {int(k): {"n": int(r.n), "baskets": _r(r.baskets, 1), "revenue": _r(r.revenue, 0), "promo_pct": _r(100 * r.promo, 1),
                                 "top": str(r.top_category)} for k, r in prof.sort_values("revenue", ascending=False).iterrows()}
    pca = PCA().fit(Xs)
    a["d8_pca_2"] = _r(100 * pca.explained_variance_ratio_[:2].sum(), 1)
    a["d8_pca_n_for_80"] = int(np.argmax(np.cumsum(pca.explained_variance_ratio_) >= 0.8) + 1)
    a["d8_n_feat_clust"] = Xs.shape[1]
    # unscaled clustering trap: revenue dominates
    km_raw = KMeans(5, n_init=20, random_state=0).fit(f[X.columns].values)
    a["d8_ari_unscaled"] = _r(adjusted_rand_score(km5.labels_, km_raw.labels_), 3)

    # ================= L8.2 RFM, CLV, cohorts =================
    c = s.groupby("customer_id").agg(last=("week", "max"), freq=("basket_id", "nunique"), mon=("revenue", "sum"), margin=("margin", "sum"),
                                     first=("week", "min"))
    c["R"] = pd.qcut(-(104 - c["last"]).rank(method="first"), 5, labels=False) + 1
    c["F"] = pd.qcut(c.freq.rank(method="first"), 5, labels=False) + 1
    c["M"] = pd.qcut(c.mon.rank(method="first"), 5, labels=False) + 1
    c["rfm"] = c.R + c.F + c.M
    top = c.rfm >= 13
    a["d8_rfm_top_share_cust"] = _r(100 * top.mean(), 1)
    a["d8_rfm_top_share_rev"] = _r(100 * c[top].mon.sum() / c.mon.sum(), 1)
    a["d8_top10_rev_share"] = _r(100 * c.mon.nlargest(int(len(c) * 0.1)).sum() / c.mon.sum(), 1)
    # simple CLV: annual margin x retention-based lifetime (geometric), discount 10%
    first_half = set(s[s.week <= 52].customer_id)
    second = set(s[s.week > 52].customer_id)
    ret = len(first_half & second) / len(first_half)
    a["d8_retention_y2"] = _r(100 * ret, 1)
    ann_margin = c.margin.sum() / 2 / len(c)
    d = 0.10
    clv = ann_margin * (1 + d) / (1 + d - ret)
    a["d8_ann_margin_per_cust"], a["d8_clv"] = _r(ann_margin, 1), _r(clv, 0)
    a["d8_clv_top_decile"] = _r((c.margin.nlargest(int(len(c) * 0.1)).mean() / 2) * (1 + d) / (1 + d - ret), 0)
    # finance cohort retention: share of accounts not churned within 12 months, by origination year
    acc["oy"] = pd.to_datetime(acc.origination_date).dt.year
    obs12 = acc[acc.months_observed >= 12]
    ch12 = obs12.churn_flag & (obs12.churn_month <= 12)
    a["d8_ret12_by_year"] = {int(y): _r(100 * (1 - v), 1) for y, v in ch12.groupby(obs12.oy).mean().items()}
    a["d8_censored_pct"] = _r(100 * (~acc.churn_flag).mean(), 1)

    # ================= L8.3 market basket =================
    r21 = M.R21(data)
    a["d8_pasta"] = r21["detail"]["Pasta->Pasta Sauce"]
    a["d8_beer"] = r21["detail"]["Beer->Chips"]
    p = pd.concat([M.load("retail", "products", data), M.load("retail", "products_archive", data)]).set_index("sku").subcategory
    t = tx[~tx.return_flag].assign(sub=lambda x: x.sku.map(p))
    bs = t.groupby("basket_id")["sub"].agg(set)
    nb = len(bs)
    from collections import Counter
    single = Counter(x for b in bs for x in b)
    pairs = Counter((x, y) for b in bs for x in b for y in b if x < y)
    rules = []
    for (x, y), n_xy in pairs.items():
        if n_xy / nb < 0.01:
            continue
        for A, B in ((x, y), (y, x)):
            sup = n_xy / nb
            conf = n_xy / single[A]
            lift = conf / (single[B] / nb)
            rules.append((A, B, sup, conf, lift))
    rdf = pd.DataFrame(rules, columns=["A", "B", "support", "confidence", "lift"])
    rdf = rdf.assign(_l=rdf.lift.round(6), _c=rdf.confidence.round(6)).sort_values(["_l", "_c", "A"], ascending=[False, False, True]).drop(columns=["_l", "_c"])
    a["d8_n_baskets_rules"] = nb
    a["d8_n_rules_sup1"] = len(rdf)
    a["d8_top_rules"] = [{"rule": f"{r.A} → {r.B}", "support": _r(100 * r.support, 1), "confidence": _r(100 * r.confidence, 1), "lift": _r(r.lift, 2)}
                         for r in rdf.drop_duplicates(subset=["support", "lift"]).head(5).itertuples()]
    # trivial high-confidence rule: consequent very common
    common = max(single, key=single.get)
    a["d8_most_common_sub"], a["d8_most_common_share"] = common, _r(100 * single[common] / nb, 1)
    hc = rdf[(rdf.B == common)].sort_values("confidence", ascending=False).head(1)
    if len(hc):
        a["d8_trivial_rule"] = {"rule": f"{hc.A.iloc[0]} → {common}", "confidence": _r(100 * hc.confidence.iloc[0], 1), "lift": _r(hc.lift.iloc[0], 2)}
    else:
        a["d8_trivial_rule"] = None

    # ================= L8.4 pricing and promotions =================
    r13 = M.R13(data)
    a["d8_el_snacks"], a["d8_el_dairy"] = r13["measured"], r13["measured_dairy"]
    a["d8_el_snacks_se"] = r13["detail"]["Snacks"]["poisson_se"]
    a["d8_el_snacks_nopromo"] = r13["detail"]["Snacks"]["loglog_no_promo_controls"]
    a["d8_el_dairy_nopromo"] = r13["detail"]["Dairy"]["loglog_no_promo_controls"]
    a["d8_el_true_snacks"], a["d8_el_true_dairy"] = -1.8, -0.6
    prod = M.load("retail", "products", data)
    for cat, e in (("Snacks", a["d8_el_snacks"]), ("Dairy", a["d8_el_dairy"])):
        pc = prod[prod.category == cat]
        cost_ratio = float((pc.unit_cost / pc.list_price).mean())
        a[f"d8_cost_ratio_{cat.lower()}"] = _r(cost_ratio, 3)
        if e < -1:
            opt = e / (1 + e)  # optimal price / cost (Lerner rule, constant elasticity)
            a[f"d8_opt_markup_{cat.lower()}"] = _r(opt, 2)
            a[f"d8_opt_vs_list_{cat.lower()}"] = _r(100 * (opt * cost_ratio - 1), 1)
        else:
            a[f"d8_opt_markup_{cat.lower()}"] = None
    # price change simulation: +5% price -> units and margin change (constant elasticity)
    for cat, e in (("snacks", a["d8_el_snacks"]), ("dairy", a["d8_el_dairy"])):
        cr = a[f"d8_cost_ratio_{cat}"]
        q = 1.05 ** e
        m0, m1 = 1 - cr, 1.05 - cr
        a[f"d8_p5_units_{cat}"] = _r(100 * (q - 1), 1)
        a[f"d8_p5_margin_{cat}"] = _r(100 * (q * m1 / m0 - 1), 1)
    r10 = M.R10(data)
    a["d8_cannibal_victim_pct"] = _r(100 * r10["measured"], 1)
    a["d8_cannibal_gain_pp"], a["d8_cannibal_loss_pp"] = r10["promoted_share_gain_pp"], r10["victim_share_loss_pp"]
    a["d8_cannibal_share"] = _r(100 * r10["cannibalised_share_of_gain"], 0)
    # promo ROI on Snacks (simple): incremental units from promotions in the extract
    e = M.load("retail", "price_elasticity_extract", data)
    sn = e[(e.category == "Snacks") & ~e.stockout_flag]
    base = sn[~sn.promo_flag].groupby(["sku", "store_id"]).units.mean()
    pr = sn[sn.promo_flag].copy()
    pr["base"] = pr.set_index(["sku", "store_id"]).index.map(base)
    pr = pr.dropna(subset=["base"])
    pr["disc"] = 1 - pr.shelf_price / pr.list_price
    inc = (pr.units - pr.base).sum()
    a["d8_promo_uplift_pct"] = _r(100 * (pr.units.sum() / pr.base.sum() - 1), 1)
    a["d8_promo_avg_disc"] = _r(100 * pr.disc.mean(), 1)
    cr = a["d8_cost_ratio_snacks"]
    lp_mean = float(pr.list_price.mean())
    gain = inc * lp_mean * (1 - pr.disc.mean() - cr)
    cost = (pr.base * pr.list_price * pr.disc).sum()
    a["d8_promo_roi"] = _r(gain / cost, 2)
    a["d8_promo_margin_rate_on_promo"] = _r(100 * (1 - pr.disc.mean() - cr), 1)

    # ================= L8.5 anomaly detection (returns abuse) =================
    truth = json.loads((M.ROOT / "instructor" / "truth" / "retail" / "truth.json").read_text())
    ab = set(truth["planted"]["R17_customers"])
    cu = tx.groupby("customer_id").agg(ret=("return_flag", "sum"), n=("return_flag", "size"), stores=("store_id", "nunique"))
    cu = cu[cu.n >= 5]
    cu["rate"] = cu.ret / (cu.n - cu.ret).clip(lower=1)
    med = cu.rate.median()
    mad = (cu.rate - med).abs().median() * 1.4826
    a["d8_mad_zero"] = bool(mad == 0)
    if mad == 0:
        mad = 1.2533 * (cu.rate - med).abs().mean()
    a["d8_zero_return_share"] = _r(100 * (cu.ret == 0).mean(), 1)
    cu["rz"] = (cu.rate - med) / mad
    cu["z"] = (cu.rate - cu.rate.mean()) / cu.rate.std()
    a["d8_r17_n_cust"], a["d8_r17_n_true"] = len(cu), len(ab & set(cu.index))
    a["d8_r17_rate_true"], a["d8_r17_rate_other"] = _r(100 * M.R17(data)["measured"], 1), _r(100 * M.R17(data)["others"], 1)
    K = len(ab)
    def pr_at(score):
        top = set(score.nlargest(K).index)
        return _r(100 * len(top & ab) / K, 0)
    a["d8_prec_robustz"] = pr_at(cu.rz)
    feats = cu[["rate", "ret", "n", "stores"]].astype(float)
    iso = IsolationForest(n_estimators=300, contamination="auto", random_state=0).fit(feats)
    cu["iso"] = -iso.score_samples(feats)
    a["d8_prec_iso"] = pr_at(cu.iso)
    a["d8_prec_returns_count"] = pr_at(cu.ret.astype(float))
    a["d8_rule20_recall"] = _r(100 * M.R17(data)["rule_recall_rate_gt_20pct"], 0)
    a["d8_rule20_precision"] = _r(100 * M.R17(data)["rule_precision_rate_gt_20pct"], 0)
    for cont in (0.01, 0.02, 0.05):
        a[f"d8_flag_at_{int(cont * 100)}pct"] = int(np.ceil(cont * len(cu)))
    a["d8_r17_stores"] = int(tx[tx.customer_id.isin(ab)].store_id.nunique())

    # ================= L8.6 fraud rings and structuring =================
    f07 = M.F07(data)
    a["d8_rings"], a["d8_ring_sizes"], a["d8_ring_fraud"] = f07["measured"], f07["sizes"], f07["fraud_rates"]
    a["d8_largest_other_comp"] = f07["largest_other_component"]
    a["d8_base_fraud_pct"] = _r(100 * acc.fraud_flag.mean(), 2)
    f08 = M.F08(data)
    a["d8_bunch_ratio"], a["d8_struct_accounts"] = f08["measured"], f08["accounts_6plus_months"]
    a["d8_dep_below"], a["d8_dep_above"] = f08["deposits_just_below"], f08["deposits_just_above"]
    pm = M.load("finance", "performance_monthly", data)
    cd = pm[pm.cash_deposit_max > 0].cash_deposit_max
    hist = np.histogram(cd, bins=np.arange(5000, 15001, 1000))[0]
    a["d8_dep_hist"] = [int(x) for x in hist]
    a["d8_struct_truth_n"] = len(truth.get("planted_finance", {}).get("F08_accounts", [])) if isinstance(truth.get("planted_finance"), dict) else None

    # ================= L8.7 credit risk =================
    y = acc.default_12m
    bins = {
        "bureau_score": pd.cut(acc.bureau_score, [0, 600, 650, 700, 750, 1000]),
        "utilisation": pd.cut(acc.utilisation.fillna(-1), [-2, -0.5, 0.5, 0.7, 0.8, 0.9, 5], labels=["loan (n/a)", "≤50%", "50–70%", "70–80%", "80–90%", ">90%"]),
        "income": pd.Series(np.where(acc.income_annual.isna(), "missing", pd.qcut(acc.income_annual, 4, labels=["Q1", "Q2", "Q3", "Q4"]).astype(str)), index=acc.index),
        "channel": acc.acquisition_channel,
        "dti": pd.cut(acc.dti, [-1, 0.2, 0.35, 0.45, 5]),
        "inquiries_6m": pd.cut(acc.inquiries_6m, [-1, 0, 1, 3, 100]),
        "age": pd.cut(acc.age, [0, 25, 35, 50, 65, 200]),
        "tenure": pd.cut(acc.tenure_months_with_bank, [-1, 6, 24, 60, 1000]),
    }
    ivs, tables = {}, {}
    for k, b in bins.items():
        tb, iv = woe_iv(b.astype(str), y)
        ivs[k], tables[k] = _r(iv, 3), tb
    a["d8_iv"] = dict(sorted(ivs.items(), key=lambda kv: -kv[1]))
    inc = tables["income"]
    a["d8_income_missing_bad"] = _r(100 * inc.loc["missing", "bad_rate"], 1)
    a["d8_income_missing_woe"] = _r(inc.loc["missing", "woe"], 2)
    ut = tables["utilisation"]
    a["d8_util_woe"] = {k: _r(ut.loc[k, "woe"], 2) for k in ["≤50%", "50–70%", "70–80%", "80–90%", ">90%"] if k in ut.index}
    # scorecard: logistic on WoE of top variables -> points (PDO 20, 600 at odds 50:1)
    import statsmodels.api as sm
    use = ["bureau_score", "utilisation", "channel", "income", "dti", "inquiries_6m"]
    W = pd.DataFrame({k: bins[k].astype(str).map(tables[k].woe) for k in use})
    lg = sm.Logit(y.astype(int), sm.add_constant(W)).fit(disp=0)
    pdo, base_score, base_odds = 20, 600, 50
    factor = pdo / np.log(2)
    offset = base_score - factor * np.log(base_odds)
    a["d8_sc_factor"], a["d8_sc_offset"] = _r(factor, 2), _r(offset, 1)
    n = len(use)
    pts = {}
    for k in use:
        beta = lg.params[k]
        pts[k] = {str(lvl): int(round(-(beta * w + lg.params["const"] / n) * factor + offset / n)) for lvl, w in tables[k].woe.items()}
    a["d8_points_bureau"] = pts["bureau_score"]
    a["d8_points_util"] = {k: v for k, v in pts["utilisation"].items()}
    score = sum(bins[k].astype(str).map(pts[k]) for k in use)
    a["d8_score_mean"] = _r(score.mean(), 0)
    from sklearn.metrics import roc_auc_score
    a["d8_sc_auc"] = _r(roc_auc_score(y, -score), 3)
    a["d8_sc_gini"] = _r(2 * a["d8_sc_auc"] - 1, 3)
    o = np.argsort(-score.values)
    yy = y.values[o].astype(int)
    a["d8_sc_ks"] = _r(np.max(np.cumsum(yy[::-1]) / yy.sum() - np.cumsum(1 - yy[::-1]) / (1 - yy).sum()), 3)
    # vintage curves: cumulative default (90+ DPD ever) by months on book for selected vintages
    vin = acc.set_index("account_id").vintage
    pm["vintage"] = pm.account_id.map(vin)
    pm["bad"] = pm.dpd >= 90
    first_bad = pm[pm.bad].groupby("account_id").month_on_book.min()
    curves = {}
    for v_ in ["2023Q1", "2024Q1", "2024Q4", "2025Q2"]:
        ids = vin[vin == v_].index
        nacc = len(ids)
        fb = first_bad.reindex(ids).dropna()
        curves[v_] = {mob: _r(100 * (fb <= mob).sum() / nacc, 2) for mob in (3, 6, 9, 12)}
    a["d8_vintage_curves"] = curves
    # roll rates: monthly transition matrix of delinquency buckets (last 12 calendar months)
    pm = pm.sort_values(["account_id", "month_on_book"])
    pm["next"] = pm.groupby("account_id").delinquency_bucket.shift(-1)
    recent = pm[(pm.calendar_month >= sorted(pm.calendar_month.unique())[-13]) & pm.next.notna()]
    order = ["current", "1-29", "30-59", "60-89", "90+"]
    rr = pd.crosstab(recent.delinquency_bucket, recent.next, normalize="index").reindex(index=order, columns=order).fillna(0)
    a["d8_roll"] = {fr: {to: _r(100 * rr.loc[fr, to], 1) for to in order} for fr in order}
    a["d8_roll_30_60"], a["d8_roll_60_90"] = _r(100 * rr.loc["30-59", "60-89"], 1), _r(100 * rr.loc["60-89", "90+"], 1)
    a["d8_roll_cure_30"] = _r(100 * rr.loc["30-59", "current"], 1)
    # reject inference (F18)
    f18 = M.F18(data)
    dec = M.load("finance", "applications_declined", data)
    a["d8_app_gap"], a["d8_declined_share"] = f18["measured"], _r(100 * f18["declined_share"], 1)
    a["d8_booked_low_default"] = _r(100 * f18["booked_low_score_default"], 1)
    a["d8_dec_bureau_median"], a["d8_acc_bureau_median"] = int(dec.bureau_score.median()), int(acc.bureau_score.median())
    a["d8_dec_below600"] = _r(100 * (dec.bureau_score < 600).mean(), 1)
    a["d8_acc_below600"] = _r(100 * (acc.bureau_score < 600).mean(), 1)

    checks = {
        "best k plausible": 2 <= a["d8_sil_best_k"] <= 8,
        "ARI modest": 0.2 < a["d8_ari"] < 0.8,
        "unscaled differs": a["d8_ari_unscaled"] < 0.8,
        "top decile rev share > 25%": a["d8_top10_rev_share"] > 25,
        "pasta lift ≈ 3.5": 2.8 < a["d8_pasta"]["lift"] < 4.2,
        "beer lift ≈ 2.2": 1.8 < a["d8_beer"]["lift"] < 3.2,
        "snacks elastic, dairy inelastic": a["d8_el_snacks"] < -1.4 and -0.9 < a["d8_el_dairy"] < -0.3,
        "dairy confounded without promo controls": a["d8_el_dairy_nopromo"] < a["d8_el_dairy"] - 0.2,
        "dairy price rise raises margin": a["d8_p5_margin_dairy"] > 0,
        "snacks price rise margin effect smaller": a["d8_p5_margin_snacks"] < a["d8_p5_margin_dairy"],
        "cannibalisation ≈ 20%": -0.30 < a["d8_cannibal_victim_pct"] / 100 < -0.10,
        "robust z beats plain count": a["d8_prec_robustz"] >= a["d8_prec_returns_count"],
        "rings 3": a["d8_rings"] == 3,
        "bunching": a["d8_bunch_ratio"] > 3,
        "both +5% raise margin, dairy more": 0 < a["d8_p5_margin_snacks"] < a["d8_p5_margin_dairy"],
        "promo ROI < 1": a["d8_promo_roi"] < 1,
        "robust z precision ≥ 50": a["d8_prec_robustz"] >= 50,
        "IV bureau top": list(a["d8_iv"])[0] == "bureau_score",
        "income missing riskier": a["d8_income_missing_bad"] > 10,
        "util WoE monotone-ish": a["d8_util_woe"]["≤50%"] > a["d8_util_woe"][">90%"],
        "vintage 2025Q2 worse": a["d8_vintage_curves"]["2025Q2"][9] > 2 * a["d8_vintage_curves"]["2024Q1"][9],
        "roll 60-90 > 30-60": a["d8_roll_60_90"] > a["d8_roll_30_60"],
        "declined lower bureau": a["d8_dec_bureau_median"] < a["d8_acc_bureau_median"],
        "scorecard gini reasonable": 0.4 < a["d8_sc_gini"] < 0.8,
    }
    bad = [k for k, ok in checks.items() if not ok]
    if bad and __import__("os").environ.get("SB_NOGUARD"):
        print("GUARDS", bad)
    else:
        assert not bad, f"Day 8 narrative guards failed: {bad}"
    return a
