"""rcp_multi_group_test: compare three or more groups (or any categorical association) the right way.

Navigator node N-TEST-KG. Roles: group (required), target (required), unit (optional: aggregate rows to this id first).
Params (all optional):
  kind: auto | numeric | binary | categorical     default auto (binary if target has two values, categorical if text)
  aggregate_fn: sum | mean (with unit)            default sum
  alpha: 0.05
  min_expected: 5          chi-square validity threshold for expected counts
  posthoc: true            pairwise comparisons with Holm correction
  drop_duplicates: [line_id]   remove re-ingested duplicate rows on these keys before aggregating
Numeric: classic ANOVA, Welch ANOVA (primary — robust to unequal variances), Kruskal-Wallis (robust to skew), Levene,
         eta², pairwise Welch t / Mann-Whitney with Holm.  Binary/categorical: chi-square, Cramér's V,
         standardised residuals, pairwise two-proportion tests with Holm, Fisher's exact when a 2×2 has small counts.
"""
from __future__ import annotations

import itertools

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, fmt, md_table, output_dir, read_dataset, schema_check, write_run

RECIPE = "rcp_multi_group_test"
SCHEMA = {"group": {"required": True, "kind": "category"}, "target": {"required": True}, "unit": {"required": False}}


def holm(p):
    p = np.asarray(p, float)
    o = np.argsort(p)
    adj = np.empty_like(p)
    run = 0.0
    for r, i in enumerate(o):
        run = max(run, min(1.0, (len(p) - r) * p[i]))
        adj[i] = run
    return adj


def welch_anova(groups):
    k = len(groups)
    n = np.array([len(g) for g in groups], float)
    m = np.array([np.mean(g) for g in groups])
    v = np.array([np.var(g, ddof=1) for g in groups])
    w = n / v
    mw = (w * m).sum() / w.sum()
    tmp = ((1 - w / w.sum()) ** 2 / (n - 1)).sum()
    f = ((w * (m - mw) ** 2).sum() / (k - 1)) / (1 + 2 * (k - 2) / (k ** 2 - 1) * tmp)
    df2 = (k ** 2 - 1) / (3 * tmp)
    return float(f), k - 1, float(df2), float(stats.f.sf(f, k - 1, df2))


def run(cfg: dict):
    log = RowLog()
    df = read_dataset(cfg)
    log.add("load", len(df), len(df), cfg["dataset"]["path"])
    errors, warnings = schema_check(df, cfg, SCHEMA)
    if errors:
        raise SchemaError("\n".join(errors))
    df = apply_filters(df, cfg, log)
    c, prm = cfg["columns"], cfg.get("params", {}) or {}
    g, y, u = c["group"], c["target"], c.get("unit")
    alpha = float(prm.get("alpha", 0.05))
    if prm.get("drop_duplicates"):
        b = len(df)
        df = df.drop_duplicates(list(prm["drop_duplicates"]))
        log.add(f"drop duplicates on {prm['drop_duplicates']}", b, len(df))
    b = len(df)
    df = df.dropna(subset=[g, y])
    log.add("drop rows with missing group/target", b, len(df))
    if u:
        b = len(df)
        df = df.groupby(u, as_index=False).agg(**{y: (y, prm.get("aggregate_fn", "sum")), g: (g, "first")})
        log.add(f"aggregate to {u}", b, len(df), f"one row per {u} = unit of analysis")
    kind = prm.get("kind", "auto")
    vals = df[y].dropna().unique()
    if kind == "auto":
        kind = "binary" if len(vals) == 2 else ("numeric" if pd.api.types.is_numeric_dtype(df[y]) else "categorical")
    levels = sorted(df[g].astype(str).unique())
    if len(levels) < 2:
        raise SchemaError(f"`{g}` has fewer than two groups after filtering.")
    df[g] = df[g].astype(str)
    out = output_dir(cfg, RECIPE)
    metrics: dict = {"kind": kind, "groups": levels, "n_total": int(len(df))}
    L = [f"# Comparing `{y}` across {len(levels)} groups of `{g}`", "", f"Unit of analysis: **{u or 'row'}** · outcome type: **{kind}** · α = {alpha}", ""]
    pw_rows = []
    if kind == "numeric":
        grp = {k: df.loc[df[g] == k, y].astype(float).to_numpy() for k in levels}
        summ = pd.DataFrame({k: {"n": len(x), "mean": x.mean(), "sd": x.std(ddof=1), "median": np.median(x),
                                 "skew": pd.Series(x).skew()} for k, x in grp.items()}).T
        f, pa = stats.f_oneway(*grp.values())
        wf, d1, d2, pw = welch_anova(list(grp.values()))
        h, pk = stats.kruskal(*grp.values())
        lev = stats.levene(*grp.values()).pvalue
        allv = np.concatenate(list(grp.values()))
        eta2 = sum(len(x) * (x.mean() - allv.mean()) ** 2 for x in grp.values()) / ((allv - allv.mean()) ** 2).sum()
        skewed = bool((summ["skew"].abs() > 1).any())
        primary = "Kruskal-Wallis" if skewed else "Welch ANOVA"
        metrics.update({"summary": summ.round(6).to_dict(orient="index"), "anova_f": f, "anova_p": pa, "welch_f": wf, "welch_df2": d2,
                        "welch_p": pw, "kruskal_h": h, "kruskal_p": pk, "levene_p": lev, "eta_squared": eta2, "primary": primary})
        for a_, b_ in itertools.combinations(levels, 2):
            x1, x2 = grp[a_], grp[b_]
            pw_rows.append({"pair": f"{a_} vs {b_}", "diff_mean": x1.mean() - x2.mean(), "diff_median": np.median(x1) - np.median(x2),
                            "welch_p": stats.ttest_ind(x1, x2, equal_var=False).pvalue, "mw_p": stats.mannwhitneyu(x1, x2).pvalue})
        pwd = pd.DataFrame(pw_rows)
        pwd["welch_p_holm"], pwd["mw_p_holm"] = holm(pwd.welch_p), holm(pwd.mw_p)
        L += ["## Group summary", "", "| Group | n | Mean | SD | Median | Skew |", "| --- | --- | --- | --- | --- | --- |"]
        L += [f"| {k} | {int(r.n):,} | {r['mean']:.2f} | {r.sd:.2f} | {r['median']:.2f} | {r['skew']:.1f} |" for k, r in summ.iterrows()]
        L += ["", "## Overall tests", "", "| Test | Statistic | p | Use when |", "| --- | --- | --- | --- |",
              f"| Classic ANOVA | F = {f:.2f} | {fmt(pa, 3)} | equal variances, roughly normal |",
              f"| **Welch ANOVA** | F = {wf:.2f} (df {d1}, {d2:.0f}) | {fmt(pw, 3)} | unequal variances (default for means) |",
              f"| Kruskal-Wallis | H = {h:.1f} | {fmt(pk, 3)} | skewed outcomes / medians |",
              f"| Levene (variances) | — | {fmt(lev, 3)} | p small → variances differ |", "",
              f"Effect size **η² = {eta2:.4f}** — the share of variation explained by `{g}`. " +
              ("Tiny: groups differ on average, but individual values overlap almost completely." if eta2 < 0.01 else
               "Small." if eta2 < 0.06 else "Medium or larger."), "",
              f"Primary test chosen: **{primary}** ({'some groups are heavily skewed' if skewed else 'skew is moderate'})."]
        sig = pwd[(pwd.mw_p_holm if skewed else pwd.welch_p_holm) < alpha]
        fig, ax = plt.subplots(figsize=(7, 3.6))
        ax.boxplot(list(grp.values()), showfliers=False)
        ax.set_xticks(range(1, len(levels) + 1), levels)
        ax.set_ylabel(y)
        ax.set_title(f"{y} by {g} (outliers hidden)")
        plt.tight_layout()
        plt.savefig(out / "groups.png", dpi=120)
        plt.close()
    else:
        tab = pd.crosstab(df[g], df[y])
        chi2, p, dof, exp = stats.chi2_contingency(tab, correction=False)
        v = float(np.sqrt(chi2 / (tab.to_numpy().sum() * (min(tab.shape) - 1))))
        res = (tab - exp) / np.sqrt(exp)
        min_exp = float(exp.min())
        metrics.update({"table": tab.to_dict(), "chi2": chi2, "dof": int(dof), "p": p, "cramers_v": v, "min_expected": min_exp,
                        "std_residuals": res.round(3).to_dict()})
        L += ["## Table", "", md_table(tab), "", f"Chi-square = {chi2:.1f}, df = {dof}, p = {fmt(p, 3)} · **Cramér's V = {v:.3f}** "
              + ("(very weak association)" if v < 0.1 else "(weak)" if v < 0.3 else "(moderate or strong)"), "",
              f"Smallest expected count: {min_exp:.1f} " + ("✓" if min_exp >= float(prm.get("min_expected", 5)) else "— **below 5: use Fisher's exact test or merge levels**."),
              "", "Standardised residuals (|r| > 2 marks cells that drive the result):", "", md_table(res.round(1))]
        if kind == "binary":
            pos = sorted(vals)[-1]
            rates = df.groupby(g)[y].apply(lambda s: (s == pos).mean())
            ns = df.groupby(g).size()
            metrics["rates"] = rates.to_dict()
            for a_, b_ in itertools.combinations(levels, 2):
                k1, n1, k2, n2 = rates[a_] * ns[a_], ns[a_], rates[b_] * ns[b_], ns[b_]
                t2 = [[int(round(k1)), int(n1 - round(k1))], [int(round(k2)), int(n2 - round(k2))]]
                small = min(np.outer([sum(r) for r in t2], [t2[0][0] + t2[1][0], t2[0][1] + t2[1][1]]).ravel() / (n1 + n2)) < 5
                pval = stats.fisher_exact(t2)[1] if small else stats.chi2_contingency(t2, correction=False)[1]
                pw_rows.append({"pair": f"{a_} vs {b_}", "diff_pp": 100 * (rates[a_] - rates[b_]), "p": pval, "test": "Fisher" if small else "z/χ²"})
            pwd = pd.DataFrame(pw_rows)
            pwd["p_holm"] = holm(pwd.p)
            sig = pwd[pwd.p_holm < alpha]
            L += ["", "## Rates", "", "| Group | n | Rate |", "| --- | --- | --- |"] + [f"| {k} | {ns[k]:,} | {100 * rates[k]:.2f}% |" for k in levels]
        else:
            pwd, sig = pd.DataFrame(), pd.DataFrame()
    if len(pw_rows):
        pwd.to_csv(out / "pairwise.csv", index=False)
        metrics["pairwise"] = pwd.set_index("pair").round(6).to_dict(orient="index")
        L += ["", "## Pairwise comparisons (Holm-adjusted)", "", md_table(pwd, index=False), "",
              "Significant after correction: " + (", ".join(sig.pair) if len(sig) else "none") + "."]
    L += ["", "## How to read this", "",
          "- The overall test says *whether* groups differ; post-hoc comparisons say *which*; the effect size says *whether it matters*.",
          "- Correct pairwise p-values for the number of comparisons (Holm). Uncorrected pairwise tests inflate false positives.",
          "- With many rows almost everything is 'significant'. Judge differences in business units and with η² / Cramér's V.",
          "- Analyse at the right unit (`unit` role): lines from the same basket or account are not independent.", "",
          "Files: `pairwise.csv`, `groups.png` (numeric), `metrics.json`, `row_accounting.md`."]
    write_run(out, RECIPE, cfg, data_hash(df), metrics, log, errors, warnings)
    (out / "narrative.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:30]))
    return out
