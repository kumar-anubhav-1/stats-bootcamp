"""Interactive charts for Days 6–9: model zoo, validation, forecasting, segmentation, pricing, risk, monitoring, neural nets,
attention and diffusion. Registered into tools.charts.REG on import."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy import stats

from tools.charts import BLUE, GREEN, GREY, ORANGE, PURPLE, RED, ROOT, L, buttons, chart, load, r, sales, slider


def answers():
    p = ROOT / "validator" / "answers.json"
    return json.loads(p.read_text()) if p.exists() else {}


def credit_xy(n=4000, seed=0):
    a = load("finance", "accounts")
    a = a[(a.product_type == "credit_card")].dropna(subset=["bureau_score", "utilisation"])
    a = a.sample(min(n, len(a)), random_state=seed)
    X = np.c_[a.bureau_score.values, a.utilisation.clip(0, 1.5).values]
    return X, a.default_12m.astype(int).values


# ----------------------------------------------------------------- the ML ladder (mental map as a chart)
LADDER = [
    # name, complexity(1-10), interpretability(1-10), family, industry use
    ("Linear regression", 1, 10, "regression", "Forecast weekly Beverages units from price, temperature, holidays"),
    ("Logistic regression", 1.5, 9.2, "classification", "Credit scorecard: probability a card customer defaults"),
    ("Naive Bayes", 2, 8, "classification", "First-pass triage of complaint text into categories"),
    ("K-nearest neighbours", 2.5, 7, "classification / regression", "'Customers like you' recommendations; look-alike stores"),
    ("Decision tree", 3, 8.6, "classification / regression", "Transparent approval rules; churn drivers for a call script"),
    ("K-means", 3.3, 6.6, "unsupervised", "Customer segments for CRM (promo hunters, families, bulk buyers)"),
    ("PCA", 3.8, 5.6, "unsupervised", "Compress 12 category-share features; spot collinear credit variables"),
    ("Support vector machine", 4.4, 3.9, "classification / regression", "High-dimensional text or transaction-pattern classification"),
    ("Random forest", 5, 4.9, "classification / regression", "Fraud scoring with many interacting signals"),
    ("Gradient boosting", 6, 4.1, "classification / regression", "Default and fraud models; demand forecasting with drivers"),
    ("Neural network (MLP)", 7, 2.6, "deep learning", "Large tabular or mixed data; embeddings of customers/products"),
    ("Transformer", 8.6, 1.7, "deep learning / GenAI", "LLMs: summarise complaints, RAG over policies, demand from text signals"),
    ("Diffusion model", 9.6, 0.8, "deep learning / GenAI", "Generate product imagery; synthetic data for rare fraud patterns"),
]


POS = {'Linear regression': 'top center', 'Logistic regression': 'middle right', 'Naive Bayes': 'middle left', 'K-nearest neighbours': 'middle left', 'Decision tree': 'middle right', 'K-means': 'middle right', 'PCA': 'middle right', 'Support vector machine': 'bottom center', 'Random forest': 'top center', 'Gradient boosting': 'middle right', 'Neural network (MLP)': 'top center', 'Transformer': 'top center', 'Diffusion model': 'bottom center'}


@chart
def c_ml_ladder():
    fam_col = {"regression": BLUE, "classification": RED, "classification / regression": ORANGE, "unsupervised": GREEN,
               "deep learning": PURPLE, "deep learning / GenAI": "#2c3e50"}
    data = []
    for fam, col in fam_col.items():
        rows = [x for x in LADDER if x[3] == fam]
        data.append({"type": "scatter", "mode": "markers+text", "name": fam, "x": [x[1] for x in rows], "y": [x[2] for x in rows],
                     "text": [x[0] for x in rows], "textposition": [POS.get(x[0], "top center") for x in rows], "marker": {"size": 16, "color": col},
                     "customdata": [x[4] for x in rows], "hovertemplate": "<b>%{text}</b><br>%{customdata}<extra></extra>"})
    return {"data": data, "layout": L("The ML ladder: more complex models need more data and explain less — hover for an industry use",
                                       "complexity / data hunger →", "interpretability →", height=560,
                                       xaxis={"range": [-0.3, 11], "title": {"text": "complexity / data hunger →"}},
                                       yaxis={"range": [-0.5, 11], "title": {"text": "interpretability →"}})}


# ----------------------------------------------------------------- model zoo: decision surfaces on real credit data
@chart
def c_model_zoo():
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.naive_bayes import GaussianNB
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.neural_network import MLPClassifier
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import SVC
    from sklearn.tree import DecisionTreeClassifier
    X, y = credit_xy()
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=0, stratify=y)
    sc = lambda m: make_pipeline(StandardScaler(), m)
    models = [("Logistic regression", sc(LogisticRegression())),
              ("Naive Bayes", sc(GaussianNB())),
              ("KNN k=5", sc(KNeighborsClassifier(5))), ("KNN k=50", sc(KNeighborsClassifier(50))),
              ("Decision tree depth 3", DecisionTreeClassifier(max_depth=3, random_state=0)),
              ("Decision tree depth 12", DecisionTreeClassifier(max_depth=12, random_state=0)),
              ("SVM (RBF)", sc(SVC(C=1.0, gamma="scale", probability=True, random_state=0))),
              ("Random forest", RandomForestClassifier(300, min_samples_leaf=20, random_state=0)),
              ("Gradient boosting", GradientBoostingClassifier(random_state=0, max_depth=2, n_estimators=150)),
              ("Neural network (MLP)", sc(MLPClassifier(hidden_layer_sizes=(16, 8), alpha=1e-2, max_iter=600, random_state=0)))]
    gx = np.linspace(np.percentile(X[:, 0], 1), np.percentile(X[:, 0], 99), 60)
    gy = np.linspace(0, 1.3, 50)
    G = np.c_[np.repeat(gx[None, :], len(gy), 0).ravel(), np.repeat(gy[:, None], len(gx), 1).ravel()]
    s = np.random.default_rng(0).choice(len(Xte), 500, replace=False)
    pts = {"type": "scatter", "x": r(Xte[s, 0], 0), "y": r(Xte[s, 1], 3), "mode": "markers", "name": "test accounts (red = defaulted)",
           "marker": {"size": 4, "color": [RED if v else "#222" for v in yte[s]], "opacity": 0.6}}
    data, titles = [], []
    for i, (nm, m) in enumerate(models):
        m.fit(Xtr, ytr)
        auc = roc_auc_score(yte, m.predict_proba(Xte)[:, 1])
        aut = roc_auc_score(ytr, m.predict_proba(Xtr)[:, 1])
        Z = m.predict_proba(G)[:, 1].reshape(len(gy), len(gx))
        data.append({"type": "heatmap", "x": r(gx, 1), "y": r(gy, 3), "z": [r(z, 3) for z in Z], "zmin": 0, "zmax": 0.15,
                     "colorscale": [[0, "#1f7a4d"], [0.35, "#f1c40f"], [1, "#c0392b"]], "colorbar": {"title": {"text": "PD"}}, "visible": i == 0, "name": nm})
        titles.append(f"{nm}: train AUC {aut:.3f} · test AUC {auc:.3f} — colour = predicted default risk")
    n = len(models)
    vis = [[j == i for j in range(n)] + [True] for i in range(n)]
    lay = L(titles[0], "bureau score", "card utilisation", height=560)
    lay["sliders"] = slider([m[0] for m in models], vis, "model: ", titles)
    return {"data": data + [pts], "layout": lay}


@chart
def c_tree_depth():
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.tree import DecisionTreeClassifier
    a = load("finance", "accounts")
    feat = ["bureau_score", "dti", "inquiries_6m", "delinq_2y", "utilisation", "digital_share", "interest_rate"]
    d = a[feat + ["default_12m"]].fillna(0)
    Xtr, Xte, ytr, yte = train_test_split(d[feat], d.default_12m.astype(int), test_size=0.3, random_state=0, stratify=d.default_12m)
    depths = list(range(1, 21))
    tr, te = [], []
    for k in depths:
        m = DecisionTreeClassifier(max_depth=k, random_state=0).fit(Xtr, ytr)
        tr.append(roc_auc_score(ytr, m.predict_proba(Xtr)[:, 1]))
        te.append(roc_auc_score(yte, m.predict_proba(Xte)[:, 1]))
    best = depths[int(np.argmax(te))]
    return {"data": [{"type": "scatter", "x": depths, "y": r(tr, 3), "name": "training AUC", "line": {"color": BLUE}},
                     {"type": "scatter", "x": depths, "y": r(te, 3), "name": "test AUC", "line": {"color": RED}}],
            "layout": L(f"Overfitting: a deeper tree memorises training accounts — best test AUC at depth {best}", "tree depth", "AUC")}


@chart
def c_roc_pr():
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score, roc_curve
    from sklearn.model_selection import train_test_split
    a = load("finance", "accounts")
    feat = ["bureau_score", "dti", "inquiries_6m", "delinq_2y", "digital_share"]
    d = a.dropna(subset=feat)
    X = (d[feat] - d[feat].mean()) / d[feat].std()
    data = []
    for tgt, col, nm in (("default_12m", BLUE, "default (4%)"), ("fraud_flag", RED, "fraud (rare)")):
        y = d[tgt].astype(int)
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=0, stratify=y)
        p = LogisticRegression(max_iter=2000).fit(Xtr, ytr).predict_proba(Xte)[:, 1]
        f, t, _ = roc_curve(yte, p)
        pr, rc, _ = precision_recall_curve(yte, p)
        k = max(1, len(f) // 300)
        data.append({"type": "scatter", "x": r(f[::k], 3), "y": r(t[::k], 3), "name": f"ROC {nm}: AUC {roc_auc_score(yte, p):.2f}",
                     "line": {"color": col}})
        k = max(1, len(pr) // 300)
        data.append({"type": "scatter", "x": r(rc[::k], 3), "y": r(pr[::k], 3), "xaxis": "x2", "yaxis": "y2",
                     "name": f"PR {nm}: AP {average_precision_score(yte, p):.2f} (base {yte.mean():.1%})", "line": {"color": col, "dash": "dot"}})
    lay = L("Same model, two lenses: ROC looks fine for rare fraud; precision–recall shows the reality",
            xaxis={"domain": [0, 0.45], "title": {"text": "false positive rate"}}, yaxis={"title": {"text": "true positive rate"}},
            xaxis2={"domain": [0.55, 1], "title": {"text": "recall"}}, yaxis2={"anchor": "x2", "title": {"text": "precision"}}, height=460)
    return {"data": data, "layout": lay}


# ----------------------------------------------------------------- forecasting
@chart
def c_forecast():
    w = load("retail", "weekly_region_category")
    s = w[w.category == "Beverages"].groupby("week").units.sum().sort_index()
    y = s.values.astype(float)
    h = 26
    tr, te = y[:-h], y[-h:]
    wk = s.index.values
    snaive = tr[-52:][:h]
    ma = np.repeat(tr[-8:].mean(), h)
    t = np.arange(len(tr))
    Xs = np.c_[np.ones(len(tr)), t, np.sin(2 * np.pi * t / 52), np.cos(2 * np.pi * t / 52)]
    b = np.linalg.lstsq(Xs, tr, rcond=None)[0]
    tf = np.arange(len(tr), len(y))
    reg = np.c_[np.ones(h), tf, np.sin(2 * np.pi * tf / 52), np.cos(2 * np.pi * tf / 52)] @ b
    mase_d = np.mean(np.abs(tr[52:] - tr[:-52]))
    meth = [("seasonal naive (same week last year)", snaive, GREEN), ("8-week moving average", ma, ORANGE),
            ("trend + annual seasonality regression", reg, PURPLE)]
    data = [{"type": "scatter", "x": wk.tolist(), "y": r(y, 0), "name": "actual units", "line": {"color": "#222"}}]
    titles = []
    for i, (nm, f, c) in enumerate(meth):
        data.append({"type": "scatter", "x": wk[-h:].tolist(), "y": r(f, 0), "name": nm, "line": {"color": c, "width": 3, "dash": "dash"},
                     "visible": i == 0})
        titles.append(f"Beverages, last 26 weeks held out — {nm}: MASE {np.mean(np.abs(te - f)) / mase_d:.2f} (below 1 beats naive)")
    vis = [[True] + [j == i for j in range(len(meth))] for i in range(len(meth))]
    lay = L(titles[0], "week", "chain units",
            shapes=[{"type": "rect", "x0": int(wk[-h]), "x1": int(wk[-1]), "y0": 0, "y1": 1, "yref": "paper", "fillcolor": "rgba(0,0,0,0.05)", "line": {"width": 0}}])
    lay["updatemenus"] = buttons([m[0].split(" (")[0] for m in meth], vis, titles)
    return {"data": data, "layout": lay}


# ----------------------------------------------------------------- segmentation
def _cust():
    from validator import measures as M
    f = M.customer_features()
    f = f[f.baskets >= 2]
    X = np.c_[np.log1p(f.revenue), f.promo_share, np.log1p(f.baskets)]
    return f, X


@chart
def c_kmeans3d():
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    f, X = _cust()
    Z = (X - X.mean(0)) / X.std(0)
    ks = [2, 3, 4, 5, 6]
    pal = [BLUE, RED, GREEN, ORANGE, PURPLE, GREY]
    data, titles = [], []
    for i, k in enumerate(ks):
        lab = KMeans(k, n_init=10, random_state=0).fit_predict(Z)
        data.append({"type": "scatter3d", "x": r(X[:, 0], 3), "y": r(X[:, 1], 3), "z": r(X[:, 2], 3), "mode": "markers",
                     "marker": {"size": 3, "color": [pal[c] for c in lab]}, "visible": i == 3, "name": f"k={k}"})
        titles.append(f"NorthStar customers, k = {k} clusters: silhouette {silhouette_score(Z, lab):.2f} — drag to rotate")
    vis = [[j == i for j in range(len(ks))] for i in range(len(ks))]
    lay = L(titles[3], height=560, scene={"xaxis": {"title": "log revenue"}, "yaxis": {"title": "promo share"}, "zaxis": {"title": "log baskets"}})
    lay["sliders"] = slider(ks, vis, "number of clusters k = ", titles, active=3)
    return {"data": data, "layout": lay}


@chart
def c_pca3d():
    from sklearn.decomposition import PCA
    from validator import measures as M
    f = M.customer_features()
    f = f[f.baskets >= 2]
    cats = [c for c in f.columns if c[0].isupper()]
    X = f[cats + ["promo_share", "avg_price_ratio"]].fillna(0).values
    Z = (X - X.mean(0)) / X.std(0)
    p = PCA(3).fit(Z)
    P = p.transform(Z)
    ev = p.explained_variance_ratio_
    return {"data": [{"type": "scatter3d", "x": r(P[:, 0], 3), "y": r(P[:, 1], 3), "z": r(P[:, 2], 3), "mode": "markers",
                      "marker": {"size": 3, "color": r(f.promo_share, 3), "colorscale": "Viridis", "colorbar": {"title": {"text": "promo share"}}},
                      "name": "customers"}],
            "layout": L(f"PCA of 14 shopping features: first 3 components keep {ev.sum():.0%} of the variance — rotate it", height=560,
                        scene={"xaxis": {"title": f"PC1 ({ev[0]:.0%})"}, "yaxis": {"title": f"PC2 ({ev[1]:.0%})"}, "zaxis": {"title": f"PC3 ({ev[2]:.0%})"}})}


# ----------------------------------------------------------------- pricing
@chart
def c_elasticity():
    a = answers()
    els = {"Snacks": a.get("d8_el_snacks", -1.8), "Dairy": a.get("d8_el_dairy", -0.6)}
    s = sales()
    m = np.linspace(0.8, 1.3, 51)
    data = []
    for cat, col in (("Snacks", RED), ("Dairy", BLUE)):
        g = s[s.category == cat]
        cost = (g.unit_cost * g.quantity).sum() / (g.list_price * g.quantity).sum()
        e = els[cat]
        units = m ** e
        margin = units * (m - cost) / (1 - cost)
        data.append({"type": "scatter", "x": r(m * 100 - 100, 1), "y": r(units * 100 - 100, 2), "name": f"{cat} units (ε = {e:.2f})",
                     "line": {"color": col, "dash": "dot"}})
        data.append({"type": "scatter", "x": r(m * 100 - 100, 1), "y": r(margin * 100 - 100, 2), "name": f"{cat} gross margin",
                     "line": {"color": col, "width": 3}})
    return {"data": data, "layout": L("Price change vs units and margin (constant-elasticity model) — hover any point",
                                       "price change (%)", "change vs today (%)",
                                       shapes=[{"type": "line", "x0": -20, "x1": 30, "y0": 0, "y1": 0, "line": {"color": GREY}},
                                               {"type": "line", "x0": 0, "x1": 0, "y0": 0, "y1": 1, "yref": "paper", "line": {"color": GREY}}])}


# ----------------------------------------------------------------- credit and risk
@chart
def c_vintage():
    a = answers()
    vc = a.get("d8_vintage_curves", {})
    data = [{"type": "scatter", "x": list(range(len(c))), "y": c, "name": v, "mode": "lines+markers",
             "line": {"width": 4 if v.startswith("2025") else 2}} for v, c in vc.items()]
    return {"data": data, "layout": L("Vintage curves: cumulative 90+ DPD by months on book — 2025 vintages go bad much faster",
                                       "months on book", "cumulative 90+ DPD (%)")}


@chart
def c_km():
    acc = load("finance", "accounts")
    T, E = acc.months_observed.values, acc.churn_flag.astype(int).values

    def km(t, e):
        ts = np.arange(0, 25)
        s, out = 1.0, []
        for k in ts:
            if k > 0:
                at = (t >= k).sum()
                d = ((t == k) & (e == 1)).sum()
                s *= 1 - d / at if at else 1
            out.append(s)
        return ts, np.array(out)

    data = []
    for lab, mk, col in (("all accounts", np.ones(len(T), bool), "#222"), ("no complaints", acc.complaints_12m.values == 0, GREEN),
                         ("1+ complaints", acc.complaints_12m.values >= 1, RED)):
        ts, s = km(T[mk], E[mk])
        data.append({"type": "scatter", "x": ts.tolist(), "y": r(s * 100, 2), "name": lab, "line": {"shape": "hv", "color": col, "width": 3}})
    naive = acc[acc.churn_flag].churn_month.astype(float).mean()
    return {"data": data, "layout": L(f"Kaplan–Meier: share of Meridian accounts still open (naive 'average churn month' {naive:.1f} is misleading)",
                                       "months since opening", "% still open")}


@chart
def c_did_event():
    ev = answers().get("d9_r09_event", {})
    w = sorted(int(k) for k in ev)
    v = [ev[str(k)] for k in w]
    return {"data": [{"type": "scatter", "x": w, "y": v, "mode": "lines+markers", "name": "test − control gap (log points, %)", "line": {"color": BLUE}}],
            "layout": L("Hair Care promotion event study: flat before week 70, jump during weeks 70–77", "week", "test vs control gap (%)",
                        shapes=[{"type": "rect", "x0": 69.5, "x1": 77.5, "y0": 0, "y1": 1, "yref": "paper", "fillcolor": "rgba(31,122,77,0.12)", "line": {"width": 0}},
                                {"type": "line", "x0": min(w), "x1": max(w), "y0": 0, "y1": 0, "line": {"color": GREY}}])}


@chart
def c_var():
    pol, cl = load("finance", "policies"), load("finance", "claims")
    n = cl.groupby("policy_id").size().reindex(pol.policy_id, fill_value=0)
    lam = n.sum() / pol.exposure_years.sum() * len(pol)
    rng = np.random.default_rng(20261115)
    counts = rng.poisson(rng.gamma(4, lam / 4, 20000))
    agg = np.array([rng.choice(cl.claim_amount.values, c).sum() for c in counts]) / 1e6
    h, e = np.histogram(agg, 80)
    data = [{"type": "bar", "x": r((e[:-1] + e[1:]) / 2, 3), "y": h.tolist(), "marker": {"color": BLUE}, "name": "simulated years"}]
    levels = [0.90, 0.95, 0.99, 0.995]
    steps = []
    for q in levels:
        v = np.quantile(agg, q)
        es = agg[agg >= v].mean()
        steps.append({"method": "relayout", "label": f"{q:.1%}", "args": [{
            "title.text": f"Annual claims: expected {agg.mean():.2f}M · VaR {q:.1%} = {v:.2f}M · expected shortfall = {es:.2f}M",
            "shapes": [{"type": "line", "x0": v, "x1": v, "y0": 0, "y1": 1, "yref": "paper", "line": {"color": RED, "width": 3}},
                       {"type": "line", "x0": es, "x1": es, "y0": 0, "y1": 1, "yref": "paper", "line": {"color": PURPLE, "dash": "dash", "width": 3}}]}]})
    lay = L(steps[-1]["args"][0]["title.text"], "total claims in a year (millions)", "simulated years")
    lay["shapes"] = steps[-1]["args"][0]["shapes"]
    lay["sliders"] = [{"active": 3, "currentvalue": {"prefix": "confidence level: "}, "pad": {"t": 45}, "steps": steps}]
    return {"data": data, "layout": lay}


@chart
def c_psi():
    a = load("finance", "accounts")
    early = a[a.vintage.str.startswith("2023")].app_score
    late = a[a.vintage.isin(["2025Q2", "2025Q3"])].app_score
    t = load("retail", "transactions")
    on = t[(t.channel != "in-store") & t.promo_flag & (t.discount_pct > 0)]
    data = [{"type": "histogram", "x": r(early.sample(min(3000, len(early)), random_state=0), 0), "histnorm": "percent", "name": "2023 vintages",
             "opacity": 0.6, "marker": {"color": BLUE}},
            {"type": "histogram", "x": r(late.sample(min(3000, len(late)), random_state=0), 0), "histnorm": "percent", "name": "2025Q2–Q3",
             "opacity": 0.6, "marker": {"color": RED}},
            {"type": "histogram", "x": r(on[on.week < 80].discount_pct, 3), "histnorm": "percent", "name": "before week 80", "opacity": 0.6,
             "marker": {"color": BLUE}, "visible": False},
            {"type": "histogram", "x": r(on[on.week >= 80].discount_pct, 3), "histnorm": "percent", "name": "week 80+", "opacity": 0.6,
             "marker": {"color": RED}, "visible": False}]
    lay = L("Population drift: application scores of new vintages shifted (PSI ≈ 0.27)", "application score", "% of accounts", barmode="overlay")
    lay["updatemenus"] = buttons(["credit score drift (F11)", "discount logging change (R19)"],
                                 [[True, True, False, False], [False, False, True, True]],
                                 ["Population drift: application scores of new vintages shifted (PSI ≈ 0.27)",
                                  "Not drift — a bug: online discount logged as 0.2 instead of 20 from week 80"])
    return {"data": data, "layout": lay}


# ----------------------------------------------------------------- neural networks, attention, diffusion
@chart
def c_activations():
    z = np.linspace(-5, 5, 201)
    fns = [("ReLU", np.maximum(0, z)), ("Leaky ReLU (a=0.1)", np.where(z > 0, z, 0.1 * z)), ("Sigmoid", 1 / (1 + np.exp(-z))),
           ("Tanh", np.tanh(z)), ("GELU", 0.5 * z * (1 + np.tanh(np.sqrt(2 / np.pi) * (z + 0.044715 * z ** 3))))]
    return {"data": [{"type": "scatter", "x": r(z, 2), "y": r(f, 3), "name": n, "line": {"width": 3}} for n, f in fns],
            "layout": L("Activation functions — click legend entries to compare", "z (weighted sum + bias)", "σ(z)")}


@chart
def c_gradient_descent():
    # loss surface of a 2-parameter price-response model on real Snacks data: log units = w0 + w1 * log(price/list)
    p = load("retail", "price_elasticity_extract")
    p = p[(p.category == "Snacks") & ~p.stockout_flag & (p.units > 0)]
    x = np.log(p.shelf_price / p.list_price).values
    y = np.log(p.units).values
    x = (x - x.mean()) / x.std()
    y = y - y.mean()

    def loss(w0, w1):
        return np.mean((y - w0 - w1 * x) ** 2)

    W0, W1 = np.meshgrid(np.linspace(-2, 2, 41), np.linspace(-2.5, 1.5, 41))
    Z = np.vectorize(loss)(W0, W1)
    surf = {"type": "surface", "x": r(W0[0], 2), "y": r(W1[:, 0], 2), "z": [r(z, 3) for z in Z], "colorscale": "Blues", "opacity": 0.55,
            "showscale": False, "name": "MSE loss"}

    def path(lr, adam=False, steps=40):
        w = np.array([-1.8, 1.4])
        m, v, out = np.zeros(2), np.zeros(2), [w.copy()]
        for t in range(1, steps + 1):
            g = np.array([-2 * np.mean(y - w[0] - w[1] * x), -2 * np.mean((y - w[0] - w[1] * x) * x)])
            if adam:
                m = 0.9 * m + 0.1 * g
                v = 0.999 * v + 0.001 * g ** 2
                w = w - lr * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
            else:
                w = w - lr * g
            w = np.clip(w, -2.5, 2.5)
            out.append(w.copy())
        return np.array(out)

    cfg = [("GD η=0.02 (too slow)", 0.02, False), ("GD η=0.2", 0.2, False), ("GD η=0.9 (oscillates)", 0.9, False),
           ("GD η=1.05 (diverges)", 1.05, False), ("Adam η=0.15", 0.15, True)]
    data, titles = [surf], []
    for i, (nm, lr, ad) in enumerate(cfg):
        P = path(lr, ad)
        zz = [loss(a, b) for a, b in P]
        data.append({"type": "scatter3d", "x": r(P[:, 0], 3), "y": r(P[:, 1], 3), "z": r(np.array(zz) + 0.12, 3), "mode": "lines+markers",
                     "marker": {"size": 4, "color": ORANGE}, "line": {"color": RED, "width": 8}, "visible": i == 1, "name": nm})
        titles.append(f"{nm}: loss after 40 steps = {zz[-1]:.3f} — rotate the bowl")
    vis = [[True] + [j == i for j in range(len(cfg))] for i in range(len(cfg))]
    lay = L(titles[1], height=560, scene={"xaxis": {"title": "w₀ (intercept)"}, "yaxis": {"title": "w₁ (price effect)"}, "zaxis": {"title": "loss"},
                                     "camera": {"eye": {"x": 1.3, "y": -1.5, "z": 1.6}}})
    lay["sliders"] = slider([c[0].split(" (")[0] for c in cfg], vis, "optimiser: ", titles, active=1)
    return {"data": data, "layout": lay}


@chart
def c_attention():
    toks = ["customer", "missed", "two", "payments", "after", "losing", "job", "—", "offer", "hardship", "plan"]
    # small interpretable embeddings: [person, payment, time/count, hardship, action]
    E = np.array([[1, .1, 0, .2, 0], [.2, .9, .1, .4, 0], [0, .2, 1, 0, 0], [.1, 1, .2, .3, 0], [0, 0, .9, .1, 0], [.3, .1, .2, 1, 0],
                  [.4, .2, 0, .9, 0], [0, 0, 0, 0, 0], [.2, .1, 0, .2, 1], [.2, .5, 0, 1, .4], [.1, .4, 0, .3, .9]], float)
    S = E @ E.T / np.sqrt(E.shape[1])
    A = np.exp(S * 3)
    A = A / A.sum(1, keepdims=True)
    return {"data": [{"type": "heatmap", "x": toks, "y": toks, "z": [r(a, 3) for a in A], "colorscale": "Blues",
                      "hovertemplate": "query %{y} attends to %{x}: %{z}<extra></extra>"}],
            "layout": L("Self-attention (illustrative): each word (row) weighs every other word (column) — softmax(QKᵀ/√d)",
                        "key (attended-to word)", "query word", height=520, yaxis={"autorange": "reversed", "title": {"text": "query word"}})}


@chart
def c_diffusion():
    """Diffusion on a 2-D toy: three customer 'segments'. Forward = add noise; reverse = denoise with the exact score."""
    rng = np.random.default_rng(0)
    mus = np.array([[-2, -1], [2, -1], [0, 2.2]])
    sd = 0.35
    n = 450
    x0 = mus[rng.integers(0, 3, n)] + rng.normal(0, sd, (n, 2))
    T = 60
    betas = np.linspace(1e-3, 0.12, T)
    abar = np.cumprod(1 - betas)
    frames_f = [0, 10, 20, 35, 59]
    fw = [np.sqrt(abar[t]) * x0 + np.sqrt(1 - abar[t]) * rng.normal(size=x0.shape) for t in frames_f]

    def score(x, t):
        m = np.sqrt(abar[t]) * mus
        v = abar[t] * sd ** 2 + (1 - abar[t])
        d = x[:, None, :] - m[None]
        lw = -0.5 * (d ** 2).sum(-1) / v
        w = np.exp(lw - lw.max(1, keepdims=True))
        w /= w.sum(1, keepdims=True)
        return -(w[..., None] * d).sum(1) / v

    x = rng.normal(size=(n, 2))
    rev = {T - 1: x.copy()}
    for t in range(T - 1, 0, -1):
        b = betas[t]
        x = (x + b * score(x, t)) / np.sqrt(1 - b) + np.sqrt(b) * rng.normal(size=x.shape) * 0.6
        if t in (45, 30, 15, 1):
            rev[t] = x.copy()
    seq = [("data", fw[0])] + [(f"noise t={t}", fw[i]) for i, t in enumerate(frames_f) if i > 0] + \
          [(f"denoise t={t}", rev[t]) for t in (45, 30, 15, 1)]
    data, titles = [], []
    for i, (lab, X) in enumerate(seq):
        data.append({"type": "scatter", "x": r(X[:, 0], 3), "y": r(X[:, 1], 3), "mode": "markers",
                     "marker": {"size": 5, "color": GREEN if lab.startswith("denoise") else (BLUE if lab == "data" else ORANGE), "opacity": 0.7},
                     "visible": i == 0, "name": lab})
        titles.append({"data": "Real data: three customer segments", }.get(lab, ("Forward process — adding noise step by step: " if lab.startswith("noise")
                                                                                  else "Reverse process — the model removes noise and new samples appear: ") + lab))
    vis = [[j == i for j in range(len(seq))] for i in range(len(seq))]
    lay = L(titles[0], "feature 1", "feature 2", xaxis={"range": [-4.5, 4.5]}, yaxis={"range": [-4, 4.5], "scaleanchor": "x"}, height=520)
    lay["sliders"] = slider([s[0] for s in seq], vis, "step: ", titles)
    return {"data": data, "layout": lay}


@chart
def c_training_curve():
    """Train vs validation log-loss per epoch (computed in validator/answers_ladder.py): weak vs strong L2 penalty."""
    cv = answers().get("d9n_curves", {})
    data = []
    for key, col, nm in (("weak", RED, "weak penalty (α=0.00001)"), ("strong", GREEN, "strong L2 penalty (α=1)")):
        if key not in cv:
            continue
        ep = list(range(1, len(cv[key]["train"]) + 1))
        data.append({"type": "scatter", "x": ep, "y": cv[key]["train"], "name": f"training loss — {nm}", "line": {"color": col, "dash": "dot"}})
        data.append({"type": "scatter", "x": ep, "y": cv[key]["val"], "name": f"validation loss — {nm}", "line": {"color": col, "width": 3}})
    return {"data": data, "layout": L("Training a network on 3,000 accounts: without a penalty, validation loss turns up (overfitting) — stop early or regularise",
                                       "epoch (passes over the training data)", "log-loss (cross-entropy)")}
