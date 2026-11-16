"""Interactive charts for the course site, built from the teaching data as Plotly JSON (no Plotly Python dependency).

    python -m tools.charts            # writes docs/assets/data/charts/<id>.json (also called by tools.build_site)

Lessons embed a chart with {{ chart("id", "caption") }}. Sliders and buttons are native Plotly controls, so every chart is
interactive offline: drag a slider to change a parameter, rotate 3-D charts with the mouse, click legend entries to toggle.
"""
from __future__ import annotations

import json
import math
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "data" / "charts"
REG: dict = {}
BLUE, RED, GREEN, ORANGE, GREY, PURPLE = "#3b6ea5", "#c0392b", "#1f7a4d", "#d4801f", "#7f8c8d", "#7b4fa0"


def chart(fn):
    REG[fn.__name__.removeprefix("c_")] = fn
    return fn


def L(title, x=None, y=None, **kw):
    lay = {"title": {"text": title, "font": {"size": 15}}, "margin": {"l": 55, "r": 20, "t": 60, "b": 50},
           "template": "plotly_white", "legend": {"orientation": "h", "y": -0.2}, "font": {"size": 12}}
    if x:
        lay["xaxis"] = {"title": {"text": x}}
    if y:
        lay["yaxis"] = {"title": {"text": y}}
    lay.update(kw)
    return lay


def slider(labels, visible_sets, prefix, titles=None, active=0):
    """Slider whose steps switch which traces are visible (and optionally the title)."""
    steps = []
    for i, (lab, vis) in enumerate(zip(labels, visible_sets)):
        args = [{"visible": vis}]
        if titles:
            args.append({"title.text": titles[i]})
        steps.append({"method": "update", "label": str(lab), "args": args})
    return [{"active": active, "currentvalue": {"prefix": prefix}, "pad": {"t": 45}, "steps": steps}]


def buttons(labels, visible_sets, titles=None, x=0.0, y=1.18):
    bts = []
    for i, (lab, vis) in enumerate(zip(labels, visible_sets)):
        args = [{"visible": vis}]
        if titles:
            args.append({"title.text": titles[i]})
        bts.append({"method": "update", "label": lab, "args": args})
    return [{"type": "buttons", "direction": "right", "x": x, "y": y, "xanchor": "left", "showactive": True, "buttons": bts}]


def r(a, nd=4):
    return [None if (isinstance(v, float) and not math.isfinite(v)) else round(float(v), nd) for v in np.asarray(a, float)]


def load(dom, t):
    return pd.read_parquet(ROOT / "data" / dom / f"{t}.parquet")


def sales():
    t = load("retail", "transactions").drop_duplicates("line_id")
    return t[~t.return_flag & (t.quantity > 0) & (t.unit_price / t.list_price < 20)]


# ----------------------------------------------------------------- Day 1–2: shape, distributions, CLT
@chart
def c_basket_skew():
    b = sales().groupby("basket_id").revenue.sum()
    mean, med = b.mean(), b.median()
    edges = np.linspace(0, b.quantile(0.995), 60)
    h, e = np.histogram(b.clip(upper=edges[-1]), edges)
    le = np.linspace(np.log10(max(b.min(), 0.5)), np.log10(b.max()), 50)
    hl, el = np.histogram(np.log10(b), le)
    data = [{"type": "bar", "x": r((e[:-1] + e[1:]) / 2, 2), "y": h.tolist(), "marker": {"color": BLUE}, "name": "baskets", "visible": True},
            {"type": "bar", "x": r(10 ** ((el[:-1] + el[1:]) / 2), 2), "y": hl.tolist(), "marker": {"color": GREEN}, "name": "baskets (log axis)", "visible": False}]
    shapes = [{"type": "line", "x0": mean, "x1": mean, "y0": 0, "y1": 1, "yref": "paper", "line": {"color": RED, "dash": "dash"}},
              {"type": "line", "x0": med, "x1": med, "y0": 0, "y1": 1, "yref": "paper", "line": {"color": ORANGE}}]
    lay = L(f"NorthStar basket value: mean {mean:.1f} (red) vs median {med:.1f} (orange)", "basket revenue", "number of baskets", shapes=shapes)
    lay["updatemenus"] = [{"type": "buttons", "direction": "right", "x": 0, "y": 1.18, "xanchor": "left", "buttons": [
        {"method": "update", "label": "linear axis", "args": [{"visible": [True, False]}, {"xaxis.type": "linear"}]},
        {"method": "update", "label": "log axis", "args": [{"visible": [False, True]}, {"xaxis.type": "log"}]}]}]
    return {"data": data, "layout": lay}


def _dist_slider(title, xlab, xs, params, pmf, plab, discrete=True, color=BLUE):
    data, vis = [], []
    for i, p in enumerate(params):
        y = pmf(xs, p)
        data.append({"type": "bar" if discrete else "scatter", "x": r(xs, 3), "y": r(y, 5), "name": f"{plab}={p}",
                     "visible": i == len(params) // 2, "marker": {"color": color}, "line": {"color": color, "width": 3},
                     "fill": None if discrete else "tozeroy"})
    vis = [[j == i for j in range(len(params))] for i in range(len(params))]
    lay = L(title, xlab, "probability" if discrete else "density")
    lay["sliders"] = slider(params, vis, plab + " = ", active=len(params) // 2)
    return {"data": data, "layout": lay}


@chart
def c_dist_poisson():
    xs = np.arange(0, 31)
    return _dist_slider("Poisson — items per basket (λ = average items). Drag λ.", "items in basket", xs,
                        [1, 2, 3, 4, 6, 8, 10, 14], lambda x, l: stats.poisson.pmf(x, l), "λ")


@chart
def c_dist_binomial():
    xs = np.arange(0, 41)
    return _dist_slider("Binomial — defaults among 200 new loans (p = default rate). Drag p.", "number of defaults", xs,
                        [0.01, 0.02, 0.03, 0.05, 0.08, 0.1, 0.15], lambda x, p: stats.binom.pmf(x, 200, p), "p", color=RED)


@chart
def c_dist_negbin():
    xs = np.arange(0, 21)
    # mean 2 claims per branch-month; dispersion k (smaller = more over-dispersed)
    return _dist_slider("Negative binomial — complaints per branch-month, mean 2. Smaller k = more over-dispersion.",
                        "complaints", xs, [0.3, 0.5, 1, 2, 5, 20, 1000],
                        lambda x, k: stats.nbinom.pmf(x, k, k / (k + 2.0)), "k", color=ORANGE)


@chart
def c_dist_lognormal():
    xs = np.linspace(1, 20000, 300)
    return _dist_slider("Lognormal — insurance claim size (median 2,400). Larger σ = heavier right tail.", "claim amount",
                        xs, [0.3, 0.5, 0.8, 1.0, 1.3, 1.6],
                        lambda x, s: stats.lognorm.pdf(x, s, scale=2400), "σ", discrete=False, color=PURPLE)


@chart
def c_clt():
    b = sales().groupby("basket_id").revenue.sum().values
    rng = np.random.default_rng(1)
    ns = [1, 2, 5, 10, 30, 100]
    data = []
    for i, n in enumerate(ns):
        m = rng.choice(b, (4000, n)).mean(axis=1)
        h, e = np.histogram(m, 50)
        data.append({"type": "bar", "x": r((e[:-1] + e[1:]) / 2, 2), "y": h.tolist(), "visible": i == 0, "marker": {"color": BLUE},
                     "name": f"n={n}"})
    vis = [[j == i for j in range(len(ns))] for i in range(len(ns))]
    titles = [f"Means of {n} random baskets (4,000 samples) — skew {stats.skew(rng.choice(b, (4000, n)).mean(axis=1)):.2f}" for n in ns]
    lay = L(titles[0], "average basket value", "count")
    lay["sliders"] = slider(ns, vis, "baskets per sample n = ", titles)
    return {"data": data, "layout": lay}


@chart
def c_benford():
    a = load("finance", "accounts")
    x = a.txn_amount_3m.dropna()
    x = x[x > 0]
    fd = (x / 10 ** np.floor(np.log10(x))).astype(int)
    obs = np.bincount(fd, minlength=10)[1:10] / len(fd)
    exp = np.log10(1 + 1 / np.arange(1, 10))
    return {"data": [{"type": "bar", "x": list(range(1, 10)), "y": r(obs), "name": "observed (transaction amounts)", "marker": {"color": BLUE}},
                     {"type": "scatter", "x": list(range(1, 10)), "y": r(exp), "name": "Benford's law", "mode": "lines+markers",
                      "line": {"color": RED}}],
            "layout": L("Leading digits of Meridian transaction amounts vs Benford's law", "first digit", "share")}


# ----------------------------------------------------------------- Linear algebra (L2.7)
@chart
def c_matrix_transform():
    gx, gy = np.meshgrid(np.linspace(-1, 1, 9), np.linspace(-1, 1, 9))
    pts = np.c_[gx.ravel(), gy.ravel()]
    mats = [("identity", [[1, 0], [0, 1]]), ("stretch x2 (scale a feature)", [[2, 0], [0, 1]]), ("shear", [[1, 0.8], [0, 1]]),
            ("rotate 30°", [[0.866, -0.5], [0.5, 0.866]]), ("correlated features [[1,.9],[.9,1]]", [[1, 0.9], [0.9, 1]]),
            ("near-singular [[1,.99],[.99,1]]", [[1, 0.99], [0.99, 1]]), ("projection onto x", [[1, 0], [0, 0]])]
    data, vis, titles = [], [], []
    for i, (nm, M) in enumerate(mats):
        M = np.array(M, float)
        q = pts @ M.T
        w, v = np.linalg.eig(M)
        data.append({"type": "scatter", "x": r(q[:, 0], 3), "y": r(q[:, 1], 3), "mode": "markers", "marker": {"color": BLUE, "size": 6},
                     "name": "transformed grid", "visible": i == 0})
        ex = []
        ey = []
        for k in range(2):
            if np.isreal(w[k]):
                vv = np.real(v[:, k]) * np.real(w[k])
                ex += [0, vv[0], None]
                ey += [0, vv[1], None]
        data.append({"type": "scatter", "x": r([e if e is not None else np.nan for e in ex], 3), "y": r([e if e is not None else np.nan for e in ey], 3),
                     "mode": "lines", "line": {"color": RED, "width": 4}, "name": "eigenvectors × eigenvalue", "visible": i == 0})
        det = np.linalg.det(M)
        titles.append(f"{nm}: det = {det:.2f} (area scale), eigenvalues = {', '.join(f'{np.real(x):.2f}' for x in w)}")
    n = len(mats)
    vis = [[j // 2 == i for j in range(2 * n)] for i in range(n)]
    lay = L(titles[0], "x₁", "x₂", xaxis={"range": [-2.6, 2.6], "zeroline": True}, yaxis={"range": [-2.2, 2.2], "scaleanchor": "x"})
    lay["sliders"] = slider([m[0].split(" (")[0].split(" [")[0] for m in mats], vis, "matrix: ", titles)
    return {"data": data, "layout": lay}


# ----------------------------------------------------------------- Day 3: inference
@chart
def c_ci_coverage():
    rng = np.random.default_rng(3)
    b = sales().groupby("basket_id").revenue.sum().values
    mu = b.mean()
    ns = [10, 30, 100, 400]
    data, cover = [], []
    for i, n in enumerate(ns):
        xs, ys, cols = [], [], []
        hit = 0
        for k in range(60):
            s = rng.choice(b, n)
            se = s.std(ddof=1) / np.sqrt(n)
            lo, hi = s.mean() - 1.96 * se, s.mean() + 1.96 * se
            ok = lo <= mu <= hi
            hit += ok
            data.append({"type": "scatter", "x": [round(lo, 2), round(hi, 2)], "y": [k, k], "mode": "lines",
                         "line": {"color": BLUE if ok else RED, "width": 2}, "showlegend": False, "visible": i == 0, "hoverinfo": "x"})
        cover.append(hit)
    per = 60
    vis = [[j // per == i for j in range(per * len(ns))] for i in range(len(ns))]
    titles = [f"60 samples of n = {n} baskets: {c} of 60 intervals ({c / 60:.0%}) contain the true mean {mu:.1f}" for n, c in zip(ns, cover)]
    lay = L(titles[0], "95% confidence interval for mean basket value", "sample",
            shapes=[{"type": "line", "x0": mu, "x1": mu, "y0": 0, "y1": 1, "yref": "paper", "line": {"color": "black", "dash": "dot"}}])
    lay["sliders"] = slider(ns, vis, "sample size n = ", titles)
    return {"data": data, "layout": lay}


@chart
def c_power():
    ds = [0.05, 0.1, 0.2, 0.3, 0.5]
    n = np.arange(10, 2001, 10)
    data = []
    for d in ds:
        pw = stats.norm.cdf(d * np.sqrt(n / 2) - 1.96)
        data.append({"type": "scatter", "x": n.tolist(), "y": r(pw, 3), "name": f"effect d = {d}", "mode": "lines"})
    return {"data": data, "layout": L("Power of a two-group test (α = 0.05) vs customers per group — hover to read",
                                       "customers per group", "power (chance of detecting the effect)",
                                       shapes=[{"type": "line", "x0": 10, "x1": 2000, "y0": 0.8, "y1": 0.8, "line": {"color": GREY, "dash": "dash"}}])}


@chart
def c_pvalue():
    x = np.linspace(-4.5, 4.5, 400)
    zs = [0.5, 1.0, 1.5, 1.96, 2.5, 3.0]
    data = [{"type": "scatter", "x": r(x, 3), "y": r(stats.norm.pdf(x), 4), "mode": "lines", "line": {"color": BLUE}, "name": "null distribution (no real lift)"}]
    vis, titles = [], []
    for i, z in enumerate(zs):
        xt = x[np.abs(x) >= z]
        for side in (xt[xt > 0], xt[xt < 0]):
            data.append({"type": "scatter", "x": r(side, 3), "y": r(stats.norm.pdf(side), 4), "fill": "tozeroy", "mode": "none",
                         "fillcolor": "rgba(192,57,43,0.5)", "showlegend": False, "visible": i == 3})
        titles.append(f"Observed z = {z}: two-sided p-value = {2 * (1 - stats.norm.cdf(z)):.3f} (red area)")
    for i in range(len(zs)):
        vis.append([True] + [j // 2 == i for j in range(2 * len(zs))])
    lay = L(titles[3], "test statistic z (promo lift ÷ its standard error)", "density")
    lay["sliders"] = slider(zs, vis, "observed z = ", titles, active=3)
    return {"data": data, "layout": lay}


# ----------------------------------------------------------------- Day 4: experiments
@chart
def c_bayes_ab():
    ab = load("retail", "ecoupon_ab")
    ab = ab[ab.app_version != "3.2"] if "app_version" in ab else ab
    ab = ab.sort_values("assignment_date")
    days = sorted(ab.assignment_date.unique())
    cut = [days[int(len(days) * f) - 1] for f in (0.1, 0.25, 0.5, 0.75, 1.0)]
    x = np.linspace(0, 0.3, 400)
    data, titles = [], []
    for i, c in enumerate(cut):
        s = ab[ab.assignment_date <= c]
        pb = []
        for arm, col in (("control", GREY), ("treatment", GREEN)):
            g = s[s.assigned_arm == arm]
            a_, b_ = 1 + g.converted_14d.sum(), 1 + (~g.converted_14d.astype(bool)).sum()
            pb.append((a_, b_))
            data.append({"type": "scatter", "x": r(x, 4), "y": r(stats.beta.pdf(x, a_, b_), 3), "mode": "lines", "fill": "tozeroy",
                         "line": {"color": col}, "name": arm, "visible": i == len(cut) - 1})
        rng = np.random.default_rng(0)
        p = (rng.beta(*pb[1], 20000) > rng.beta(*pb[0], 20000)).mean()
        titles.append(f"e-coupon test through {str(c)[:10]} ({len(s):,} users): P(treatment better) = {p:.1%}")
    vis = [[j // 2 == i for j in range(2 * len(cut))] for i in range(len(cut))]
    lay = L(titles[-1], "14-day conversion rate", "posterior density")
    lay["sliders"] = slider(["10%", "25%", "50%", "75%", "100%"], vis, "data collected: ", titles, active=len(cut) - 1)
    return {"data": data, "layout": lay}


# ----------------------------------------------------------------- Day 5: regression
@chart
def c_reg3d():
    p = load("retail", "price_elasticity_extract")
    p = p[(p.category == "Snacks") & ~p.stockout_flag & (p.units > 0)]
    p = p.assign(lp=np.log(p.shelf_price / p.list_price), lu=np.log(p.units), dp=p.display_flag.astype(int))
    s = p.sample(min(1500, len(p)), random_state=0)
    X = np.c_[np.ones(len(p)), p.lp, p.dp]
    beta = np.linalg.lstsq(X, p.lu, rcond=None)[0]
    gx = np.linspace(p.lp.quantile(0.01), p.lp.quantile(0.99), 15)
    gy = np.array([0, 1])
    Z = beta[0] + beta[1] * gx[None, :] + beta[2] * gy[:, None]
    return {"data": [{"type": "scatter3d", "x": r(s.lp, 3), "y": r(s.dp + np.random.default_rng(0).uniform(-0.08, 0.08, len(s)), 3),
                      "z": r(s.lu, 3), "mode": "markers", "marker": {"size": 2.5, "color": r(s.lu, 3), "colorscale": "Viridis"}, "name": "store-weeks"},
                     {"type": "surface", "x": r(gx, 3), "y": gy.tolist(), "z": [r(z, 3) for z in Z], "opacity": 0.6, "showscale": False,
                      "colorscale": [[0, RED], [1, RED]], "name": "fitted plane"}],
            "layout": L(f"Snacks: log units = {beta[0]:.2f} {beta[1]:+.2f}·log(price ÷ list) {beta[2]:+.2f}·display — drag to rotate",
                        scene={"xaxis": {"title": "log(price ÷ list)"}, "yaxis": {"title": "display (0/1)"}, "zaxis": {"title": "log units"}},
                        height=520)}


@chart
def c_overfit():
    rng = np.random.default_rng(5)
    wr = load("retail", "weekly_region_category")
    s = wr[(wr.category == "Beverages") & (wr.region == wr.region.iloc[0])].sort_values("week")
    x = (s.week.values - s.week.mean()) / s.week.std()
    y = s.units.values
    idx = rng.permutation(len(x))
    tr, te = idx[: int(0.6 * len(x))], idx[int(0.6 * len(x)):]
    degs = [1, 2, 3, 5, 8, 12, 16]
    xx = np.linspace(x.min(), x.max(), 300)
    data = [{"type": "scatter", "x": r(x[tr], 3), "y": r(y[tr], 1), "mode": "markers", "marker": {"color": BLUE}, "name": "training weeks"},
            {"type": "scatter", "x": r(x[te], 3), "y": r(y[te], 1), "mode": "markers", "marker": {"color": ORANGE}, "name": "held-out weeks"}]
    titles = []
    for i, d in enumerate(degs):
        c = np.polyfit(x[tr], y[tr], d)
        etr = np.sqrt(np.mean((np.polyval(c, x[tr]) - y[tr]) ** 2))
        ete = np.sqrt(np.mean((np.polyval(c, x[te]) - y[te]) ** 2))
        yy = np.clip(np.polyval(c, xx), y.min() - y.std() * 2, y.max() + y.std() * 2)
        data.append({"type": "scatter", "x": r(xx, 3), "y": r(yy, 1), "mode": "lines", "line": {"color": RED, "width": 3},
                     "name": f"degree {d}", "visible": i == 1})
        titles.append(f"Polynomial degree {d}: training RMSE {etr:,.0f} · held-out RMSE {ete:,.0f}")
    vis = [[True, True] + [j == i for j in range(len(degs))] for i in range(len(degs))]
    lay = L(titles[1], "week (standardised)", "Beverages units (one region)")
    lay["sliders"] = slider(degs, vis, "polynomial degree = ", titles, active=1)
    return {"data": data, "layout": lay}


@chart
def c_logistic_threshold():
    a = load("finance", "accounts")
    a = a.dropna(subset=["bureau_score"])
    x = a.bureau_score.values
    y = a.default_12m.astype(int).values
    import statsmodels.api as sm
    m = sm.Logit(y, sm.add_constant((x - 650) / 50)).fit(disp=0)
    xs = np.linspace(x.min(), x.max(), 200)
    p = m.predict(sm.add_constant((xs - 650) / 50))
    bins = pd.cut(x, np.arange(450, 860, 25))
    emp = pd.Series(y).groupby(bins, observed=True).mean()
    data = [{"type": "scatter", "x": [iv.mid for iv in emp.index], "y": r(emp.values), "mode": "markers", "marker": {"color": BLUE, "size": 8},
             "name": "observed default rate (25-point bins)"},
            {"type": "scatter", "x": r(xs, 1), "y": r(p), "mode": "lines", "line": {"color": RED, "width": 3}, "name": "logistic fit"}]
    ph = m.predict(sm.add_constant((x - 650) / 50))
    ths = [0.02, 0.04, 0.06, 0.1, 0.15, 0.25]
    titles, shapes_all = [], []
    for t in ths:
        f = ph >= t
        tp, fp, fn = (f & (y == 1)).sum(), (f & (y == 0)).sum(), (~f & (y == 1)).sum()
        titles.append(f"Decline if PD ≥ {t:.0%}: declines {f.mean():.0%} · catches {tp / (tp + fn):.0%} of defaulters · precision {tp / max(tp + fp, 1):.0%}")
    lay = L(titles[1], "bureau score", "probability of default (12 months)")
    lay["sliders"] = [{"active": 1, "currentvalue": {"prefix": "decline threshold PD ≥ "}, "pad": {"t": 45}, "steps": [
        {"method": "relayout", "label": f"{t:.0%}", "args": [{"title.text": titles[i],
                                                              "shapes": [{"type": "line", "x0": float(x.min()), "x1": float(x.max()), "y0": t, "y1": t,
                                                                          "line": {"color": GREEN, "dash": "dash"}}]}]}
        for i, t in enumerate(ths)]}]
    lay["shapes"] = [{"type": "line", "x0": float(x.min()), "x1": float(x.max()), "y0": ths[1], "y1": ths[1], "line": {"color": GREEN, "dash": "dash"}}]
    return {"data": data, "layout": lay}


def build(only=None):
    OUT.mkdir(parents=True, exist_ok=True)
    from tools import charts_ml  # noqa: F401  (registers the ML / AI charts)
    from tools import charts_cv  # noqa: F401  (registers the computer-vision charts)
    done = []
    for k, fn in REG.items():
        if only and k not in only:
            continue
        fig = fn()
        fig.setdefault("config", {"responsive": True, "displaylogo": False})
        (OUT / f"{k}.json").write_text(json.dumps(fig, separators=(",", ":"), default=float))
        done.append(k)
    return done


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT))
    from tools.charts import build as _build  # use the importable module so charts_ml registers into the same REG
    d = _build(set(sys.argv[1:]) or None)
    print(f"{len(d)} charts:", ", ".join(d))
