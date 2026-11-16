"""Computed answers for Day 6 (machine learning: features, trees/ensembles, alternatives, validation and leakage, imbalance,
evaluation and thresholds, explainability). Keys d6_. All models use fixed seeds; guards check the narrative."""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import partial_dependence, permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from . import measures as M

warnings.filterwarnings("ignore")


def _r(x, nd=3):
    return round(float(x), nd)


def ks_stat(y, s):
    y = np.asarray(y).astype(int)
    o = np.argsort(-np.asarray(s))
    yy = y[o]
    tpr = np.cumsum(yy) / yy.sum()
    fpr = np.cumsum(1 - yy) / (1 - yy).sum()
    return float(np.max(tpr - fpr))


def app_features(acc):
    X = pd.DataFrame(index=acc.index)
    X["age"] = acc.age.clip(18, 100)
    X["log_income"] = np.log(acc.income_annual.clip(lower=1000)).fillna(np.log(acc.income_annual.median()))
    X["income_missing"] = acc.income_annual.isna().astype(int)
    X["unverified"] = (~acc.income_verified_flag).astype(int)
    X["bureau_score"] = acc.bureau_score
    X["dti"] = acc.dti
    X["inquiries_6m"] = acc.inquiries_6m
    X["delinq_2y"] = acc.delinq_2y
    X["utilisation"] = acc.utilisation.fillna(0)
    X["card"] = (acc.product_type == "credit_card").astype(int)
    X["log_limit"] = np.log(acc.limit_or_loan_amount)
    X["partner"] = (acc.acquisition_channel == "partner").astype(int)
    X["online"] = (acc.acquisition_channel == "online").astype(int)
    X["tenure"] = acc.tenure_months_with_bank
    for e in ["student", "self-employed", "contract", "retired"]:
        X[f"emp_{e}"] = (acc.employment_type == e).astype(int)
    return X


def compute_day6(data=str(M.DATA)) -> dict:
    a: dict = {}
    acc = M.load("finance", "accounts", data)
    y = acc.default_12m.astype(int).to_numpy()
    X = app_features(acc)
    a["d6_n_feat_app"] = X.shape[1]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=0, stratify=y)
    a["d6_n_train"], a["d6_n_test"] = len(Xtr), len(Xte)

    def fit_eval(model, Xa=Xtr, Xb=Xte, ya=ytr, yb=yte):
        model.fit(Xa, ya)
        p = model.predict_proba(Xb)[:, 1]
        return model, p, {"auc": _r(roc_auc_score(yb, p)), "pr_auc": _r(average_precision_score(yb, p)), "ks": _r(ks_stat(yb, p)),
                          "brier": _r(brier_score_loss(yb, p), 4)}

    # ================= L6.2 trees and ensembles =================
    logit = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))
    models = {"logistic": logit,
              "tree_depth4": DecisionTreeClassifier(max_depth=4, min_samples_leaf=100, random_state=0),
              "tree_deep": DecisionTreeClassifier(min_samples_leaf=1, random_state=0),
              "random_forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=20, n_jobs=-1, random_state=0),
              "gbm": HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0, random_state=0)}
    res, preds, fitted = {}, {}, {}
    for k, m in models.items():
        fitted[k], preds[k], res[k] = fit_eval(m)
    a["d6_models"] = res
    a["d6_tree_deep_train_auc"] = _r(roc_auc_score(ytr, fitted["tree_deep"].predict_proba(Xtr)[:, 1]))
    a["d6_gbm_train_auc"] = _r(roc_auc_score(ytr, fitted["gbm"].predict_proba(Xtr)[:, 1]))
    a["d6_gbm_gain"] = _r(res["gbm"]["auc"] - res["logistic"]["auc"])
    # logistic with engineered non-linear terms (utilisation bands + young x high dti)
    Xe = X.copy()
    Xe["util_80"] = (X.utilisation > 0.8).astype(int)
    Xe["util_90"] = (X.utilisation > 0.9).astype(int)
    Xe["young_hidti"] = ((X.age < 25) & (X.dti > 0.45)).astype(int)
    Xetr, Xete = Xe.loc[Xtr.index], Xe.loc[Xte.index]
    _, pe, re_ = fit_eval(make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)), Xetr, Xete)
    a["d6_logit_eng"] = re_

    # ================= L6.3 alternative learners (bake-off on a sample) =================
    rs = np.random.default_rng(606)
    sub = rs.choice(len(Xtr), 6000, replace=False)
    Xs, ys = Xtr.iloc[sub], ytr[sub]
    bake = {"logistic": make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)),
            "naive_bayes": make_pipeline(StandardScaler(), GaussianNB()),
            "knn_k50": make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=50)),
            "svm_rbf": make_pipeline(StandardScaler(), SVC(C=1.0, probability=True, random_state=0)),
            "gbm": HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0, random_state=0)}
    bres, bpred = {}, {}
    for k, m in bake.items():
        _, bpred[k], bres[k] = fit_eval(m, Xs, Xte, ys, yte)
    stack = np.mean([pd.Series(bpred[k]).rank().to_numpy() for k in ["logistic", "svm_rbf", "gbm"]], axis=0)
    bres["average_of_3_ranks"] = {"auc": _r(roc_auc_score(yte, stack))}
    a["d6_bake"] = bres
    a["d6_bake_n"] = len(sub)

    # ================= L6.4 validation, leakage, out-of-time =================
    f10 = M.F10(data)
    a["d6_leak_auc"], a["d6_clean_auc_f10"] = f10["measured"], f10["clean_auc"]
    XL = X.copy()
    XL["collections_flag"] = acc.collections_flag.astype(int)
    XL["recovery_amount"] = acc.recovery_amount
    _, pl, rl = fit_eval(HistGradientBoostingClassifier(max_iter=200, random_state=0), XL.loc[Xtr.index], XL.loc[Xte.index])
    a["d6_leak_gbm_auc"] = rl["auc"]
    gl = HistGradientBoostingClassifier(max_iter=200, random_state=0).fit(XL.loc[Xtr.index], ytr)
    pim = permutation_importance(gl, XL.loc[Xte.index].iloc[:3000], yte[:3000], scoring="roc_auc", n_repeats=3, random_state=0)
    a["d6_leak_top"] = XL.columns[int(np.argmax(pim.importances_mean))]
    a["d6_collections_default_rate"] = _r(100 * acc[acc.collections_flag.astype(bool)].default_12m.mean(), 1)
    # cross-validation spread
    cvs = cross_val_score(make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)), X, y,
                          cv=StratifiedKFold(5, shuffle=True, random_state=0), scoring="roc_auc")
    a["d6_cv_aucs"] = [_r(v) for v in cvs]
    a["d6_cv_mean"], a["d6_cv_sd"] = _r(cvs.mean()), _r(cvs.std(ddof=1))
    # out-of-time
    old = (acc.vintage <= "2024Q4").to_numpy()
    new = ~old
    for nm, mdl in [("logistic", make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))),
                    ("gbm", HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0, random_state=0))]:
        mdl.fit(X[old], y[old])
        p_in = mdl.predict_proba(X[old])[:, 1]
        p_oot = mdl.predict_proba(X[new])[:, 1]
        a[f"d6_oot_{nm}_auc"] = _r(roc_auc_score(y[new], p_oot))
        a[f"d6_oot_{nm}_pred_pct"] = _r(100 * p_oot.mean(), 2)
    a["d6_oot_actual_pct"] = _r(100 * y[new].mean(), 2)
    a["d6_oot_train_actual_pct"] = _r(100 * y[old].mean(), 2)
    a["d6_oot_n_train"], a["d6_oot_n_test"] = int(old.sum()), int(new.sum())
    # small tuning grid for GBM (CV on training split)
    grid = {}
    for lr in (0.03, 0.1):
        for leaves in (7, 31):
            mdl = HistGradientBoostingClassifier(max_iter=300, learning_rate=lr, max_leaf_nodes=leaves, l2_regularization=1.0, random_state=0)
            sc_ = cross_val_score(mdl, Xtr, ytr, cv=StratifiedKFold(3, shuffle=True, random_state=0), scoring="roc_auc")
            grid[f"lr{lr}_leaves{leaves}"] = _r(sc_.mean())
    a["d6_grid"] = grid
    a["d6_grid_best"] = max(grid, key=grid.get)
    a["d6_grid_range"] = _r(max(grid.values()) - min(grid.values()))

    # ================= L6.5 imbalance: fraud =================
    links = M.load("finance", "devices_addresses", data)
    cnt = links.groupby("link_id").account_id.nunique()
    links = links.assign(share=links.link_id.map(cnt))
    shared = links.groupby(["account_id", "link_type"]).share.max().unstack().reindex(acc.account_id).fillna(1)
    F = pd.DataFrame({"inquiries_6m": acc.inquiries_6m.to_numpy(), "new_to_bank": (acc.tenure_months_with_bank < 6).astype(int).to_numpy(),
                      "partner": (acc.acquisition_channel == "partner").astype(int).to_numpy(), "digital_share": acc.digital_share.to_numpy(),
                      "device_shared_by": shared["device"].to_numpy(), "address_shared_by": shared["address"].to_numpy(),
                      "bureau_score": acc.bureau_score.to_numpy()})
    yf = acc.fraud_flag.astype(int).to_numpy()
    a["d6_fraud_rate"] = _r(100 * yf.mean(), 2)
    a["d6_fraud_n"] = int(yf.sum())
    Ftr, Fte, yftr, yfte = train_test_split(F, yf, test_size=0.4, random_state=1, stratify=yf)
    a["d6_allzero_acc"] = _r(100 * (1 - yfte.mean()), 2)
    fm = {}
    for nm, mdl in [("logistic", make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))),
                    ("logistic_weighted", make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, class_weight="balanced"))),
                    ("gbm", HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, random_state=0))]:
        mdl.fit(Ftr, yftr)
        p = mdl.predict_proba(Fte)[:, 1]
        o = np.argsort(-p)
        top = {}
        for k in (50, 100, 200):
            top[k] = _r(100 * yfte[o[:k]].mean(), 1)
        rec100 = yfte[o[:100]].sum() / yfte.sum()
        acc05 = ((p >= 0.5).astype(int) == yfte).mean()
        fm[nm] = {"roc_auc": _r(roc_auc_score(yfte, p)), "pr_auc": _r(average_precision_score(yfte, p)), "prec_at": top,
                  "recall_at100": _r(100 * rec100, 1), "acc_at_05": _r(100 * acc05, 2), "flagged_at_05": int((p >= 0.5).sum()),
                  "mean_p": _r(100 * p.mean(), 2)}
    a["d6_fraud"] = fm
    a["d6_fraud_test_n"], a["d6_fraud_test_pos"] = len(yfte), int(yfte.sum())
    ring = (F.device_shared_by >= 5)
    a["d6_ring_fraud_rate"] = _r(100 * yf[ring.to_numpy()].mean(), 1)
    a["d6_ring_n"] = int(ring.sum())

    # ================= L6.6 evaluation and thresholds (default, logistic engineered) =================
    p = pe
    o = np.argsort(-p)
    yy = yte[o]
    dec = np.array_split(np.arange(len(yy)), 10)
    lift = [_r(yy[d].mean() / yte.mean(), 2) for d in dec]
    a["d6_lift_deciles"] = lift
    a["d6_top_decile_capture"] = _r(100 * yy[dec[0]].sum() / yte.sum(), 1)
    a["d6_top3_capture"] = _r(100 * yy[np.concatenate(dec[:3])].sum() / yte.sum(), 1)
    a["d6_gini"] = _r(2 * re_["auc"] - 1)
    a["d6_ks"] = re_["ks"]
    # calibration by decile of predicted PD (ascending)
    oc = np.argsort(p)
    cal = []
    for d in np.array_split(oc, 10):
        cal.append([_r(100 * p[d].mean(), 2), _r(100 * yte[d].mean(), 2)])
    a["d6_calib"] = cal
    a["d6_brier"] = re_["brier"]
    a["d6_brier_base"] = _r(brier_score_loss(yte, np.full(len(yte), ytr.mean())), 4)
    # thresholds and costs: LGD x EAD for a missed default vs lost margin for a declined good
    ead = acc.loc[Xte.index, "limit_or_loan_amount"].to_numpy() * 0.6
    cost_fn = 0.6 * ead  # LGD 60%
    margin = acc.loc[Xte.index, "limit_or_loan_amount"].to_numpy() * 0.5 * acc.loc[Xte.index, "interest_rate"].to_numpy() * 0.5
    thr_rows = []
    for t in (0.02, 0.04, 0.06, 0.08, 0.10, 0.15, 0.20, 0.30):
        dec_ = p >= t
        fn = (~dec_) & (yte == 1)
        fp = dec_ & (yte == 0)
        thr_rows.append({"t": t, "decline_pct": _r(100 * dec_.mean(), 1), "recall": _r(100 * (dec_ & (yte == 1)).sum() / yte.sum(), 1),
                         "precision": _r(100 * (dec_ & (yte == 1)).sum() / max(dec_.sum(), 1), 1),
                         "cost": _r((cost_fn[fn].sum() + margin[fp].sum()) / 1e6, 2)})
    a["d6_thr"] = thr_rows
    best = min(thr_rows, key=lambda r: r["cost"])
    a["d6_thr_best"] = best
    a["d6_thr_cost_none"] = _r(cost_fn[yte == 1].sum() / 1e6, 2)
    a["d6_avg_cost_fn"] = _r(cost_fn[yte == 1].mean(), 0)
    a["d6_avg_cost_fp"] = _r(margin[yte == 0].mean(), 0)
    a["d6_acc_at_05"] = _r(100 * ((p >= 0.5).astype(int) == yte).mean(), 1)

    # ================= L6.7 explainability =================
    g = fitted["gbm"]
    pim = permutation_importance(g, Xte.iloc[:4000], yte[:4000], scoring="roc_auc", n_repeats=5, random_state=0)
    imp = pd.Series(pim.importances_mean, index=X.columns).sort_values(ascending=False)
    a["d6_perm_imp"] = {k: _r(v, 4) for k, v in imp.head(6).items()}
    pdp = partial_dependence(g, Xtr.iloc[:5000], ["utilisation"], grid_resolution=6, percentiles=(0.0, 1.0), kind="average", response_method="predict_proba", method="brute")
    grid_vals = pdp["grid_values"][0] if "grid_values" in pdp else pdp["values"][0]
    a["d6_pdp_util"] = [[_r(gv, 2), _r(100 * v, 2)] for gv, v in zip(grid_vals, pdp["average"][0])]
    # logistic reason codes for one declined applicant: contribution = beta * (x - mean) on standardised scale
    lg = fitted["logistic"]
    sc_ = lg.named_steps["standardscaler"]
    co = lg.named_steps["logisticregression"].coef_[0]
    z = sc_.transform(Xte)
    contrib = z * co
    i = int(np.argmax(p))
    top = np.argsort(-contrib[i])[:3]
    a["d6_case_pd"] = _r(100 * fitted["logistic"].predict_proba(Xte.iloc[[i]])[:, 1][0], 1)
    a["d6_case_reasons"] = [X.columns[j] for j in top]
    a["d6_case_values"] = {X.columns[j]: _r(Xte.iloc[i, j], 3) for j in top}

    # ================= L6.1 feature engineering =================
    pm = M.load("finance", "performance_monthly", data)
    early = pm[pm.month_on_book <= 3].groupby("account_id").agg(max_dpd_3=("dpd", "max"), avg_util_3=("utilisation", "mean"),
                                                                  pay_ratio_3=("payment", "sum"), min_due_3=("minimum_due", "sum"))
    early["pay_ratio_3"] = (early.pay_ratio_3 / early.min_due_3.replace(0, np.nan)).clip(0, 10).fillna(1)
    early = early.drop(columns="min_due_3").reindex(acc.account_id).fillna({"max_dpd_3": 0, "avg_util_3": 0, "pay_ratio_3": 1})
    early.index = acc.index
    Xb = pd.concat([X, early], axis=1)
    _, pb, rb = fit_eval(HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0, random_state=0),
                         Xb.loc[Xtr.index], Xb.loc[Xte.index])
    a["d6_beh_auc"] = rb["auc"]
    a["d6_beh_gain"] = _r(rb["auc"] - res["gbm"]["auc"])
    a["d6_beh_dpd_default"] = _r(100 * acc[(early.max_dpd_3 > 0).to_numpy()].default_12m.mean(), 1)
    a["d6_beh_nodpd_default"] = _r(100 * acc[(early.max_dpd_3 == 0).to_numpy()].default_12m.mean(), 1)
    # retail: repeat purchase in weeks 79-104 from features in weeks 1-78 (and a leaky version)
    tx = M.load("retail", "transactions", data).drop_duplicates("line_id")
    s = tx[~tx.return_flag & (tx.quantity > 0) & (tx.unit_price / tx.list_price < 20)]

    def cust_feats(df_, end):
        g_ = df_.groupby("customer_id")
        f_ = pd.DataFrame({"baskets": g_.basket_id.nunique(), "revenue": g_.revenue.sum(), "recency_w": end - g_.week.max(),
                           "promo_share": g_.promo_flag.mean(), "n_categories": g_.category.nunique(),
                           "loyal": g_.loyalty_flag.first().astype(int), "tenure_m": g_.tenure_months.first()})
        f_["log_rev"] = np.log1p(f_.pop("revenue"))
        return f_
    past = s[s.week <= 78]
    fut = set(s[s.week > 78].customer_id)
    cf = cust_feats(past, 78)
    yc = cf.index.isin(fut).astype(int)
    a["d6_r_customers"], a["d6_r_repeat_pct"] = len(cf), _r(100 * yc.mean(), 1)
    ctr, cte, yctr, ycte = train_test_split(cf, yc, test_size=0.3, random_state=0, stratify=yc)
    _, pr_, rr_ = fit_eval(make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)), ctr, cte, yctr, ycte)
    _, prg, rrg = fit_eval(HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=7, random_state=0), ctr, cte, yctr, ycte)
    a["d6_r_auc_logit"], a["d6_r_auc_gbm"] = rr_["auc"], rrg["auc"]
    cl_ = cust_feats(s, 104).reindex(cf.index)  # leaky: features computed over the whole period, including the target window
    ltr, lte = cl_.loc[ctr.index], cl_.loc[cte.index]
    _, _, rlk = fit_eval(make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)), ltr, lte, yctr, ycte)
    a["d6_r_auc_leaky"] = rlk["auc"]
    lr_ = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)).fit(ctr, yctr)
    a["d6_r_coefs"] = {k: _r(v, 3) for k, v in zip(cf.columns, lr_.named_steps["logisticregression"].coef_[0])}
    o2 = np.argsort(-pr_)
    a["d6_r_top_decile_rate"] = _r(100 * ycte[o2[: len(o2) // 10]].mean(), 1)
    a["d6_r_bottom_decile_rate"] = _r(100 * ycte[o2[-(len(o2) // 10):]].mean(), 1)

    checks = {
        "deep tree overfits": a["d6_tree_deep_train_auc"] > 0.95 and res["tree_deep"]["auc"] < res["logistic"]["auc"],
        "gbm ~ logistic (small gain)": -0.03 < a["d6_gbm_gain"] < 0.05,
        "retail genuine signal absent": a["d6_r_auc_logit"] < 0.6,
        "engineered logistic close to gbm": abs(re_["auc"] - res["gbm"]["auc"]) < 0.03,
        "leak AUC very high": a["d6_leak_gbm_auc"] > 0.95 and a["d6_leak_top"] in ("collections_flag", "recovery_amount"),
        "oot under-predicts default": a["d6_oot_logistic_pred_pct"] < a["d6_oot_actual_pct"] - 2,
        "oot AUC lower": a["d6_oot_logistic_auc"] < res["logistic"]["auc"],
        "accuracy paradox": a["d6_allzero_acc"] > 99,
        "PR-AUC ≪ ROC-AUC": fm["logistic"]["pr_auc"] < fm["logistic"]["roc_auc"] / 2,
        "precision@50 ≫ base": fm["gbm"]["prec_at"][50] > 5 * a["d6_fraud_rate"],
        "ring fraud high": a["d6_ring_fraud_rate"] > 30,
        "weighted flags many at 0.5": fm["logistic_weighted"]["flagged_at_05"] > 5 * fm["logistic"]["flagged_at_05"],
        "lift top decile > 3": lift[0] > 3,
        "best threshold low": best["t"] <= 0.15,
        "behavioural features help": a["d6_beh_gain"] > 0.005,
        "retail leaky inflated": a["d6_r_auc_leaky"] > a["d6_r_auc_logit"] + 0.05,
        "top PD reasons sensible": len(a["d6_case_reasons"]) == 3,
        "pdp rising": a["d6_pdp_util"][-1][1] > a["d6_pdp_util"][0][1],
        "logistic wins bake-off": max(bres, key=lambda k: bres[k]["auc"]) == "logistic",
        "average doesn't beat best": bres["average_of_3_ranks"]["auc"] <= bres["logistic"]["auc"],
        "NB poorly calibrated": bres["naive_bayes"]["brier"] > 2 * bres["logistic"]["brier"],
        "oot gap favours logistic": a["d6_oot_logistic_auc"] >= a["d6_oot_gbm_auc"],
        "fraud ROC high, PR modest": fm["logistic"]["roc_auc"] > 0.88 and 0.12 < fm["logistic"]["pr_auc"] < 0.4,
        "precision@100 about a quarter": 15 <= fm["logistic"]["prec_at"][100] <= 40,
        "weights keep ranking": abs(fm["logistic_weighted"]["prec_at"][100] - fm["logistic"]["prec_at"][100]) <= 5,
        "bureau top, partner top3": list(a["d6_perm_imp"])[0] == "bureau_score" and "partner" in list(a["d6_perm_imp"])[:3],
        "pdp steep after 0.7": a["d6_pdp_util"][4][1] > a["d6_pdp_util"][3][1] + 1,
        "calibrated in-sample": abs(a["d6_calib"][-1][0] - a["d6_calib"][-1][1]) < 3,
        "grid range small": a["d6_grid_range"] < 0.03,
    }
    bad = [k for k, ok in checks.items() if not ok]
    if bad and __import__("os").environ.get("SB_NOGUARD"):
        print("GUARDS", bad)
    else:
        assert not bad, f"Day 6 narrative guards failed: {bad}"
    return a
