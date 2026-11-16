"""rcp_regression: OLS / logistic / GLM with diagnostics and a business-reading coefficient table.

Navigator nodes N-REG-OLS, N-REG-LOGIT, N-REG-GLM, N-REG-VIF. Roles: target (required), features (list, required unless
params.formula), cluster (optional: cluster-robust SEs), exposure (optional: offset log(exposure) for count models).
Params:
  family: ols | logit | poisson | negbin | gamma        default ols (logit if target is 0/1)
  formula: "np.log(units) ~ promo_sku_share + C(store_id)"   optional statsmodels formula using column names
  log_target: false            (ols) model log(target); coefficients read as % change
  robust: HC3 | cluster | none  default HC3 for ols, cluster if a cluster role is mapped
  negbin_alpha: estimated if omitted (count models: NB2 by maximum likelihood)
  hide: ["C(store_id)"]        prefixes of terms to leave out of the narrative table (fixed effects)
Outputs: coefficients with CIs and plain-English reading, fit statistics (R², AIC, BIC, AUC, dispersion), diagnostics (Breusch-Pagan,
residual skew, VIF, Cook's distance), residual plots.
"""
from __future__ import annotations

import re
import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, fmt, output_dir, read_dataset, schema_check, write_run

warnings.filterwarnings("ignore")
RECIPE = "rcp_regression"
SCHEMA = {"target": {"required": True}, "cluster": {"required": False}, "exposure": {"required": False}}


def _auc(y, s):
    y = np.asarray(y).astype(int)
    r = stats.rankdata(s)
    n1 = y.sum()
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y) - n1)))


def run(cfg: dict):
    log = RowLog()
    df = read_dataset(cfg)
    log.add("load", len(df), len(df), cfg["dataset"]["path"])
    errors, warnings_ = schema_check(df, cfg, SCHEMA)
    if errors:
        raise SchemaError("\n".join(errors))
    df = apply_filters(df, cfg, log)
    c, prm = cfg["columns"], cfg.get("params", {}) or {}
    y = c["target"]
    feats = c.get("features") or []
    for f_ in feats:
        if f_ not in df.columns:
            raise SchemaError(f"feature `{f_}` not found in the dataset.")
    binary = set(df[y].dropna().unique()) <= {0, 1, True, False}
    fam = prm.get("family") or ("logit" if binary else "ols")
    if binary:
        df[y] = df[y].astype(int)
    for col in df.columns:
        if str(df[col].dtype) == "boolean" or df[col].dtype == bool:
            df[col] = df[col].astype(float)
    lhs = f"np.log({y})" if (fam == "ols" and prm.get("log_target")) else y
    formula = prm.get("formula") or f"{lhs} ~ " + " + ".join(feats)
    used = sorted(set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", formula)) & set(df.columns))
    b = len(df)
    df = df.dropna(subset=used)
    if prm.get("log_target") or "np.log(" + y in formula:
        df = df[df[y] > 0]
    log.add("drop rows with missing/invalid model variables", b, len(df), ", ".join(used))
    if len(df) < 30:
        raise SchemaError("Fewer than 30 complete rows — check filters and column mapping.")
    cl, ex = c.get("cluster"), c.get("exposure")
    offset = np.log(df[ex]) if ex else None
    robust = prm.get("robust", "cluster" if cl else ("HC3" if fam == "ols" else "none"))
    fit_kw = {}
    if robust == "cluster" and cl:
        fit_kw = {"cov_type": "cluster", "cov_kwds": {"groups": pd.factorize(df[cl])[0]}}
    elif robust == "HC3":
        fit_kw = {"cov_type": "HC3"}
    if fam == "ols":
        m = smf.ols(formula, df).fit(**fit_kw)
    elif fam == "logit":
        m = smf.logit(formula, df).fit(disp=0, **fit_kw)
    elif fam == "poisson":
        m = smf.glm(formula, df, family=sm.families.Poisson(), offset=offset).fit(**fit_kw)
    elif fam == "negbin":
        alpha = prm.get("negbin_alpha")
        if alpha is None:
            nb = smf.negativebinomial(formula, df, offset=offset).fit(disp=0, maxiter=300)
            alpha = float(nb.params["alpha"])
        m = smf.glm(formula, df, family=sm.families.NegativeBinomial(alpha=alpha), offset=offset).fit(**fit_kw)
    elif fam == "gamma":
        m = smf.glm(formula, df, family=sm.families.Gamma(sm.families.links.Log())).fit(**fit_kw)
    else:
        raise SchemaError(f"Unknown family `{fam}`; use ols, logit, poisson, negbin or gamma.")
    ci = m.conf_int()
    log_scale = fam in ("logit", "poisson", "negbin", "gamma") or formula.split("~")[0].strip().startswith("np.log(")
    rows = []
    for k in m.params.index:
        if k == "Intercept":
            continue
        bval, lo, hi = m.params[k], ci.loc[k, 0], ci.loc[k, 1]
        if fam == "logit":
            read, eff, elo, ehi = "odds ratio", np.exp(bval), np.exp(lo), np.exp(hi)
        elif log_scale:
            read, eff, elo, ehi = "% change", 100 * (np.exp(bval) - 1), 100 * (np.exp(lo) - 1), 100 * (np.exp(hi) - 1)
        else:
            read, eff, elo, ehi = "units", bval, lo, hi
        rows.append({"term": k, "coef": bval, "se": m.bse[k], "p": m.pvalues[k], "effect": eff, "effect_low": elo, "effect_high": ehi, "reading": read})
    coef = pd.DataFrame(rows)
    out = output_dir(cfg, RECIPE)
    coef.to_csv(out / "coefficients.csv", index=False)
    metrics: dict = {"family": fam, "formula": formula, "n": int(m.nobs), "robust": robust,
                     "coefficients": coef.set_index("term")[["coef", "se", "p", "effect"]].round(8).to_dict(orient="index")}
    fitstats = []
    if fam == "ols":
        metrics.update({"r2": m.rsquared, "adj_r2": m.rsquared_adj, "aic": m.aic, "bic": m.bic})
        fitstats += [f"R² = {m.rsquared:.3f} (adjusted {m.rsquared_adj:.3f})", f"AIC {m.aic:,.0f} · BIC {m.bic:,.0f}"]
        bp = het_breuschpagan(m.resid, m.model.exog)[1]
        sk = float(pd.Series(m.resid).skew())
        metrics.update({"breusch_pagan_p": bp, "resid_skew": sk})
        cook = m.get_influence().cooks_distance[0] if m.nobs <= 50_000 else np.zeros(int(m.nobs))
        metrics["cooks_max"] = float(cook.max())
        metrics["cooks_over_4_over_n"] = int((cook > 4 / m.nobs).sum())
        resid, fitted = m.resid, m.fittedvalues
    elif fam == "logit":
        pr = m.predict(df)
        a_ = _auc(df[y], pr)
        metrics.update({"auc": a_, "pseudo_r2": m.prsquared, "aic": m.aic, "bic": m.bic, "event_rate": float(df[y].mean())})
        fitstats += [f"AUC {a_:.3f} · McFadden pseudo-R² {m.prsquared:.3f}", f"AIC {m.aic:,.0f} · BIC {m.bic:,.0f}", f"event rate {df[y].mean():.2%}"]
        resid, fitted = df[y] - pr, pr
    else:
        disp = float(m.pearson_chi2 / m.df_resid)
        metrics.update({"aic": m.aic, "deviance": m.deviance, "pearson_dispersion": disp})
        fitstats += [f"AIC {m.aic:,.0f} · deviance {m.deviance:,.0f}", f"Pearson dispersion {disp:.2f}" +
                     (" — **over-dispersed: use negative binomial or robust SEs**" if (fam == "poisson" and disp > 1.5) else "")]
        resid, fitted = m.resid_pearson, m.fittedvalues
    # VIF on numeric main-effect columns of the design matrix
    X = pd.DataFrame(m.model.exog, columns=m.model.exog_names)
    hide = prm.get("hide", []) or []
    vcols = [k for k in X.columns if k != "Intercept" and not any(k.startswith(h) for h in hide) and X[k].nunique() > 2]
    vif = {}
    if 1 < len(vcols) <= 40:
        Xv = sm.add_constant(X[vcols])
        vif = {k: float(variance_inflation_factor(Xv.values, i)) for i, k in enumerate(Xv.columns) if k != "const"}
    metrics["vif"] = vif
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    ax[0].scatter(fitted, resid, s=4, alpha=0.3)
    ax[0].axhline(0, color="red")
    ax[0].set_xlabel("fitted")
    ax[0].set_ylabel("residual")
    ax[0].set_title("Residuals vs fitted")
    stats.probplot(np.asarray(resid, float), plot=ax[1])
    ax[1].set_title("Q-Q of residuals")
    plt.tight_layout()
    plt.savefig(out / "diagnostics.png", dpi=110)
    plt.close()
    write_run(out, RECIPE, cfg, data_hash(df[used]), metrics, log, errors, warnings_)
    show = coef[~coef.term.apply(lambda t: any(t.startswith(h) for h in hide))]
    L = [f"# Regression: `{formula}`", "", f"Family **{fam}** · n = {int(m.nobs):,} · standard errors: {robust}", "", "## Fit", ""] + [f"- {x}" for x in fitstats]
    L += ["", "## Coefficients (business reading)", "", "| Term | Effect | 95% CI | p | Reading |", "| --- | --- | --- | --- | --- |"]
    for r in show.itertuples():
        unit = "%" if r.reading == "% change" else ""
        L.append(f"| {r.term} | {r.effect:+.3g}{unit} | {r.effect_low:+.3g} to {r.effect_high:+.3g}{unit} | {fmt(r.p, 3)} | "
                 + ("odds × per unit" if r.reading == "odds ratio" else ("% change in outcome per unit" if r.reading == "% change" else "change in outcome per unit")) + " |")
    if len(show) < len(coef):
        L.append(f"\n{len(coef) - len(show)} fixed-effect terms hidden ({', '.join(hide)}).")
    L += ["", "## Diagnostics", ""]
    if fam == "ols":
        L += [f"- Breusch-Pagan p = {fmt(metrics['breusch_pagan_p'], 3)} " + ("→ **heteroscedastic**: robust SEs used; consider a log transform." if metrics["breusch_pagan_p"] < 0.05 else "→ no evidence of unequal variance."),
              f"- Residual skew {metrics['resid_skew']:.2f}" + (" — skewed; check the Q-Q plot / transform the target." if abs(metrics["resid_skew"]) > 1 else ""),
              f"- Cook's distance: max {metrics['cooks_max']:.3g}; {metrics['cooks_over_4_over_n']} rows above 4/n (inspect, don't auto-delete)."]
    if vif:
        L += [f"- VIF: " + ", ".join(f"{k} {v:.1f}" for k, v in vif.items()) + (" — **collinearity (VIF > 5)**: coefficients unstable; combine, drop or regularise." if max(vif.values()) > 5 else "")]
    L += ["", "## How to read this", "",
          "- Coefficients are associations holding the other terms fixed — causal only with a design or a defensible DAG (L4.4).",
          "- Log outcome / log-link models: effects are % changes; logistic models: odds ratios (not risk ratios when outcomes are common).",
          "- Check diagnostics before trusting p-values: unequal variance, skewed residuals, influential points, collinearity.",
          "- Report effects in business units with CIs; R² measures fit, not usefulness or causality.", "",
          "Files: `coefficients.csv`, `diagnostics.png`, `metrics.json`, `row_accounting.md`."]
    (out / "narrative.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:30]))
    return out
