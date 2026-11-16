"""rcp_distribution_fit: which distribution describes this variable?

Navigator tree T-DIST. Continuous: fits normal, lognormal, gamma, Weibull, exponential (positive data) and compares
AIC, KS distance and tail quantiles; counts: Poisson vs negative binomial with a dispersion check.

Roles: target (numeric, required). Params:
  kind: auto | continuous | count
  unit/agg: aggregate rows first (e.g. basket_id, sum)
  candidates: list to restrict the families
  exclude_above: drop values above this (e.g. catastrophic claims) — reported in row accounting
  tail_quantiles: [0.9, 0.99]
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, fmt, output_dir, read_dataset, schema_check, write_run

RECIPE = "rcp_distribution_fit"
SCHEMA = {"target": {"required": True, "kind": "numeric"}}
CONT = {"normal": (stats.norm, {}), "lognormal": (stats.lognorm, {"floc": 0}), "gamma": (stats.gamma, {"floc": 0}),
        "weibull": (stats.weibull_min, {"floc": 0}), "exponential": (stats.expon, {"floc": 0})}


def run(cfg: dict):
    log = RowLog()
    df = read_dataset(cfg)
    log.add("load", len(df), len(df), cfg["dataset"]["path"])
    errors, warnings = schema_check(df, cfg, SCHEMA)
    if errors:
        raise SchemaError("\n".join(errors))
    df = apply_filters(df, cfg, log)
    c, prm = cfg["columns"], cfg["params"]
    y = c["target"]
    if prm.get("unit"):
        b = len(df)
        df = df.groupby(prm["unit"], as_index=False)[y].agg(prm.get("agg", "sum"))
        log.add(f"aggregate to {prm['unit']}", b, len(df))
    b = len(df)
    df = df.dropna(subset=[y])
    log.add(f"drop missing {y}", b, len(df))
    if prm.get("exclude_above") is not None:
        b = len(df)
        df = df[df[y] <= prm["exclude_above"]]
        log.add(f"exclude values above {prm['exclude_above']}", b, len(df), "treated separately (e.g. large losses)")
    x = df[y].astype(float).to_numpy()
    kind = prm.get("kind", "auto")
    if kind == "auto":
        kind = "count" if np.all(np.equal(np.mod(x, 1), 0)) and x.min() >= 0 and len(np.unique(x)) < 200 else "continuous"
    out = output_dir(cfg, RECIPE)
    qs = prm.get("tail_quantiles", [0.9, 0.99])
    rows, metrics = [], {"n": int(len(x)), "kind": kind, "mean": x.mean(), "var": x.var(ddof=1), "skew": float(pd.Series(x).skew())}

    if kind == "count":
        lam = x.mean()
        disp = x.var(ddof=1) / lam if lam > 0 else np.nan
        ll_p = stats.poisson.logpmf(x, lam).sum()
        # NB by method of moments then likelihood check
        if disp > 1:
            r = lam / (disp - 1)
            p = r / (r + lam)
            ll_nb = stats.nbinom.logpmf(x, r, p).sum()
        else:
            r, p, ll_nb = np.inf, 1.0, ll_p
        rows = [{"family": "poisson", "params": f"λ={lam:.4g}", "aic": 2 - 2 * ll_p},
                {"family": "negative binomial", "params": f"r={r:.4g}, p={p:.4g}", "aic": 4 - 2 * ll_nb}]
        z = (disp - 1) * np.sqrt((len(x) - 1) / 2)
        metrics.update({"dispersion": disp, "dispersion_z": z,
                        "zeros_obs": float((x == 0).mean()), "zeros_poisson": float(stats.poisson.pmf(0, lam))})
        fig, ax = plt.subplots(figsize=(7, 3.4))
        k = np.arange(0, int(np.percentile(x, 99.5)) + 2)
        ax.bar(k, [(x == i).mean() for i in k], color="#3b6ea5", label="observed")
        ax.plot(k, stats.poisson.pmf(k, lam), "o-", color="#b5651d", label="Poisson")
        if disp > 1:
            ax.plot(k, stats.nbinom.pmf(k, r, p), "s--", color="#1f7a4d", label="neg. binomial")
        ax.legend()
        ax.set_title(f"{y}: observed vs fitted count distributions")
        plt.tight_layout()
        plt.savefig(out / "fit.png", dpi=120)
        plt.close()
    else:
        cands = prm.get("candidates") or (list(CONT) if x.min() > 0 else ["normal"])
        fitted = {}
        for nm in cands:
            dist, kw = CONT[nm]
            par = dist.fit(x, **kw)
            kpar = len(par) - len(kw)
            ll = dist.logpdf(x, *par).sum()
            ks = stats.kstest(x, dist.cdf, args=par).statistic
            row = {"family": nm, "params": ", ".join(f"{v:.4g}" for v in par), "aic": 2 * kpar - 2 * ll, "ks_distance": ks}
            for q in qs:
                row[f"q{q}_fitted"] = dist.ppf(q, *par)
            fitted[nm] = (dist, par)
            rows.append(row)
        for q in qs:
            metrics[f"q{q}_empirical"] = float(np.quantile(x, q))
        fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
        best = min(rows, key=lambda r_: r_["aic"])["family"]
        lx = np.log10(x) if x.min() > 0 and pd.Series(x).skew() > 2 else x
        ax[0].hist(lx, bins=60, density=False, color="#3b6ea5")
        ax[0].set_title(f"{y}" + (" (log10)" if lx is not x else ""))
        dist, par = fitted[best]
        pp = (np.arange(1, len(x) + 1) - 0.5) / len(x)
        ax[1].scatter(dist.ppf(pp, *par), np.sort(x), s=4, color="#b5651d")
        lim = [np.sort(x)[0], np.sort(x)[-1]]
        ax[1].plot(lim, lim, color="grey", lw=1)
        ax[1].set_title(f"Q-Q vs best fit ({best})")
        ax[1].set_xlabel("theoretical")
        ax[1].set_ylabel("observed")
        plt.tight_layout()
        plt.savefig(out / "fit.png", dpi=120)
        plt.close()
    tab = pd.DataFrame(rows).sort_values("aic")
    tab["delta_aic"] = tab.aic - tab.aic.min()
    tab.to_csv(out / "fit_table.csv", index=False)
    metrics["fits"] = tab.set_index("family").drop(columns=["params"]).round(6).to_dict(orient="index")
    write_run(out, RECIPE, cfg, data_hash(df), metrics, log, errors, warnings)

    L = [f"# Distribution fit: `{y}`", "", f"**n = {len(x):,}** · type: {kind} · mean {fmt(x.mean())} · variance {fmt(x.var(ddof=1))} · skew {metrics['skew']:.2f}", ""]
    if kind == "count":
        L += [f"**Dispersion (variance ÷ mean) = {metrics['dispersion']:.3f}** (z ≈ {metrics['dispersion_z']:.1f}; 1 = Poisson). "
              f"Zeros: observed {metrics['zeros_obs']:.2%} vs Poisson {metrics['zeros_poisson']:.2%}.", ""]
    L += ["| Family | Parameters | AIC | ΔAIC |" + (" KS distance |" if kind != "count" else "") + "".join(f" fitted P{int(q * 100)} |" for q in qs if kind != "count"),
          "| --- | --- | --- | --- |" + (" --- |" if kind != "count" else "") + "".join(" --- |" for q in qs if kind != "count")]
    for r_ in tab.to_dict(orient="records"):
        line = f"| {r_['family']} | {r_['params']} | {r_['aic']:,.0f} | {r_['delta_aic']:,.1f} |"
        if kind != "count":
            line += f" {r_['ks_distance']:.3f} |" + "".join(f" {fmt(r_[f'q{q}_fitted'])} |" for q in qs)
        L.append(line)
    if kind != "count":
        L += ["", "Empirical quantiles: " + ", ".join(f"P{int(q * 100)} = {fmt(metrics[f'q{q}_empirical'])}" for q in qs)]
    L += ["", "## How to read this", "",
          "- **Lower AIC = better fit**, penalising extra parameters. ΔAIC < 2: practically tied; > 10: clearly worse.",
          "- Check the **Q-Q plot** and **tail quantiles**: a family can win on AIC yet miss the tail that matters for risk.",
          "- KS / Anderson-Darling p-values reject almost everything at large n — use them as distances, not verdicts.",
          "- Over-dispersed counts (variance ≫ mean) → negative binomial, not Poisson.", "",
          "Files: `fit_table.csv`, `fit.png`, `metrics.json`, `row_accounting.md`."]
    (out / "narrative.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:14]))
    return out
