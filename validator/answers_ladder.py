"""Computed answers for L6.8 (the ML ladder: one bake-off per business problem) and L9.8 (inside neural networks). Keys d6l_ / d9n_."""
from __future__ import annotations

import time
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingClassifier, RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import average_precision_score, mean_absolute_error, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC, SVR
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from . import measures as M

warnings.filterwarnings("ignore")


def _r(x, nd=3):
    return round(float(x), nd)


def compute_ladder(data=str(M.DATA)) -> dict:
    a: dict = {}
    sc = lambda m: make_pipeline(StandardScaler(), m)
    # ---------- finance: probability of default, same features and split for every model ----------
    acc = M.load("finance", "accounts", data)
    feat = ["bureau_score", "dti", "inquiries_6m", "delinq_2y", "utilisation", "digital_share", "interest_rate", "tenure_months_with_bank"]
    d = acc[feat + ["default_12m"]].copy()
    d["util_missing"] = d.utilisation.isna().astype(int)
    d = d.fillna(0)
    X, y = d.drop(columns="default_12m").astype(float), d.default_12m.astype(int)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=0, stratify=y)
    sub = Xtr.sample(6000, random_state=0).index  # SVM and KNN are slow on large n: fair note in the lesson
    models = [("Logistic regression", sc(LogisticRegression(max_iter=3000)), False, "high"),
              ("Naive Bayes", sc(GaussianNB()), False, "medium"),
              ("K-nearest neighbours (k=50)", sc(KNeighborsClassifier(50)), True, "medium"),
              ("Decision tree (depth 5)", DecisionTreeClassifier(max_depth=5, min_samples_leaf=50, random_state=0), False, "high"),
              ("Support vector machine (RBF)", sc(SVC(probability=True, random_state=0)), True, "low"),
              ("Random forest", RandomForestClassifier(300, min_samples_leaf=20, n_jobs=-1, random_state=0), False, "low"),
              ("Gradient boosting", HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, random_state=0), False, "low"),
              ("Neural network (MLP 32-16)", sc(MLPClassifier(hidden_layer_sizes=(32, 16), alpha=1e-2, max_iter=400, random_state=0)), False, "very low")]
    tab = {}
    for nm, m, small, interp in models:
        t0 = time.time()
        Xa, ya = (Xtr.loc[sub], ytr.loc[sub]) if small else (Xtr, ytr)
        m.fit(Xa, ya)
        p = m.predict_proba(Xte)[:, 1]
        tab[nm] = {"auc": _r(roc_auc_score(yte, p)), "pr_auc": _r(average_precision_score(yte, p)),
                   "train_rows": int(len(Xa)), "seconds": _r(time.time() - t0, 1), "interpretability": interp}
    a["d6l_credit"] = tab
    a["d6l_credit_best"] = max(tab, key=lambda k: tab[k]["auc"])
    a["d6l_credit_base"] = _r(100 * y.mean(), 2)
    # ---------- retail: weekly Beverages units per store, forecast the last 16 weeks ----------
    sc_ = M.load("retail", "weekly_store_category", data)
    st = M.load("retail", "stores", data)
    cal = M.load("retail", "calendar", data).groupby("week").agg(holiday=("holiday_flag", "max"), payday=("payday_flag", "max"), month=("month", "first"))
    b = sc_[sc_.category == "Beverages"].merge(st[["store_id", "format", "size_sqm", "city_tier", "region"]], on="store_id").merge(cal, left_on="week", right_index=True)
    b = b.sort_values(["store_id", "week"])
    b["lag52"] = b.groupby("store_id").units.shift(52)
    b["lag4mean"] = b.groupby("store_id").units.transform(lambda s: s.shift(1).rolling(4).mean())
    b = b.dropna(subset=["lag52", "lag4mean"])
    Xr = pd.get_dummies(b[["size_sqm", "city_tier", "holiday", "payday", "month", "promo_sku_share", "lag52", "lag4mean", "format", "region"]],
                        columns=["format", "region"], dtype=float).astype(float)
    Xr["sin"] = np.sin(2 * np.pi * b.week / 52)
    Xr["cos"] = np.cos(2 * np.pi * b.week / 52)
    yr = b.units.astype(float)
    last = b.week.max() - 16
    tr, te = b.week <= last, b.week > last
    naive = b.loc[te, "lag52"]
    regs = [("Linear regression", sc(LinearRegression())), ("K-nearest neighbours (k=10)", sc(KNeighborsRegressor(10))),
            ("Decision tree (depth 6)", DecisionTreeRegressor(max_depth=6, random_state=0)), ("Support vector regression", sc(SVR(C=50))),
            ("Random forest", RandomForestRegressor(300, min_samples_leaf=5, n_jobs=-1, random_state=0)),
            ("Gradient boosting", GradientBoostingRegressor(random_state=0)), ("Neural network (MLP)", sc(MLPRegressor(hidden_layer_sizes=(32, 16), alpha=1e-2, max_iter=1500, random_state=0)))]
    rt = {"Seasonal naive (same week last year)": {"mae": _r(mean_absolute_error(yr[te], naive), 1)}}
    for nm, m in regs:
        m.fit(Xr[tr], yr[tr])
        rt[nm] = {"mae": _r(mean_absolute_error(yr[te], m.predict(Xr[te])), 1)}
    base = rt["Seasonal naive (same week last year)"]["mae"]
    for k in rt:
        rt[k]["vs_naive"] = _r(100 * (rt[k]["mae"] / base - 1), 1)
    a["d6l_demand"] = rt
    a["d6l_demand_best"] = min(rt, key=lambda k: rt[k]["mae"])
    a["d6l_demand_mean_units"] = _r(yr[te].mean(), 0)
    a["d6l_demand_n_test"] = int(te.sum())
    lin = rt["Linear regression"]["mae"]
    best = rt[a["d6l_demand_best"]]["mae"]
    a["d6l_demand_gain_vs_linear"] = _r(100 * (1 - best / lin), 1)
    lo = tab["Logistic regression"]["auc"]
    a["d6l_credit_gain_vs_logistic"] = _r(tab[a["d6l_credit_best"]]["auc"] - lo, 3)

    # ---------- L9.8: inside a neural network ----------
    from sklearn.metrics import log_loss
    f2 = ["bureau_score", "dti", "inquiries_6m", "delinq_2y", "utilisation", "digital_share", "interest_rate"]
    d2 = acc[f2 + ["default_12m"]].fillna(0)
    A, B, ya, yb = train_test_split(d2[f2].values, d2.default_12m.astype(int).values, train_size=3000, test_size=6000, random_state=0,
                                    stratify=d2.default_12m)
    s2 = StandardScaler().fit(A)
    A, B = s2.transform(A), s2.transform(B)
    curves = {}
    for key, alpha in (("weak", 1e-5), ("strong", 1.0)):
        m = MLPClassifier(hidden_layer_sizes=(64, 32), alpha=alpha, learning_rate_init=0.003, random_state=0)
        tr, va = [], []
        for ep in range(120):
            m.partial_fit(A, ya, classes=[0, 1])
            tr.append(round(log_loss(ya, m.predict_proba(A)[:, 1]), 4))
            va.append(round(log_loss(yb, m.predict_proba(B)[:, 1]), 4))
        curves[key] = {"train": tr, "val": va}
        a[f"d9n_{key}_best_epoch"] = int(np.argmin(va) + 1)
        a[f"d9n_{key}_val_min"] = float(min(va))
        a[f"d9n_{key}_val_end"] = va[-1]
        a[f"d9n_{key}_train_end"] = tr[-1]
    a["d9n_curves"] = curves
    a["d9n_n_params"] = int(7 * 64 + 64 + 64 * 32 + 32 + 32 + 1)
    # a single neuron = logistic regression on two raw features
    c2 = acc.dropna(subset=["utilisation", "bureau_score"])
    lg = LogisticRegression(max_iter=3000).fit(c2[["utilisation", "bureau_score"]].values, c2.default_12m.astype(int))
    w1, w2 = lg.coef_[0]
    b0 = lg.intercept_[0]
    z = b0 + w1 * 0.9 + w2 * 620
    a["d9n_neuron"] = {"w_util": _r(w1, 3), "w_bureau": _r(w2, 4), "b": _r(b0, 3), "z": _r(z, 3), "p": _r(100 / (1 + np.exp(-z)), 1)}

    checks = {"logistic competitive on credit": tab[a["d6l_credit_best"]]["auc"] - lo < 0.03,
              "models beat naive on demand": best < base,
              "weak penalty overfits": a["d9n_weak_val_end"] > a["d9n_weak_val_min"] * 1.1,
              "strong penalty stable": a["d9n_strong_val_end"] < a["d9n_weak_val_end"]}
    bad = [k for k, ok in checks.items() if not ok]
    if bad and __import__("os").environ.get("SB_NOGUARD"):
        print("GUARDS", bad)
    else:
        assert not bad, f"Ladder guards failed: {bad}"
    return a
