"""rcp_two_group_test: compare two groups the right way and say what it means.

Navigator node N-TEST-2G. The recipe
  1. maps roles, applies filters, accounts for every row;
  2. analyses at the right unit (aggregates to `cluster` if randomisation was by store/branch);
  3. optionally converts the outcome to growth vs a pre-period (params.baseline);
  4. detects outcome type (binary vs continuous) and checks assumptions;
  5. runs the primary test chosen by Navigator rules plus robustness tests;
  6. reports effect sizes with confidence intervals and a plain-English verdict.

Roles: group (required), target (required), cluster (optional), id (optional).
Params (all optional):
  groups: [treatment_label, control_label]        default: two most frequent values
  aggregate_to: none | cluster                     default: cluster if a cluster role is mapped
  aggregate_fn: mean | sum                         default: mean
  baseline: {period_col, pre: [a, b], post: [c, d]}   outcome becomes post/pre per cluster
  alternative: two-sided | greater | less          default: two-sided
  alpha: 0.05
  practical_threshold: smallest effect worth acting on (same units as % lift, e.g. 0.03)
  n_boot: 5000, seed: 42
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, fmt, output_dir, read_dataset, schema_check, write_run

RECIPE = "rcp_two_group_test"
SCHEMA = {"group": {"required": True, "kind": "category"}, "target": {"required": True, "kind": "numeric"},
          "cluster": {"kind": "id"}, "id": {"kind": "id"}}


def _is_binary(x: pd.Series) -> bool:
    v = pd.unique(x.dropna())
    return len(v) <= 2 and set(np.asarray(v, float)) <= {0.0, 1.0}


def _icc(df, cl, y):
    g = df.groupby(cl)[y]
    k = g.size().mean()
    msb = (g.mean().var(ddof=1)) * k
    msw = g.var(ddof=1).mean()
    return float(max(0.0, (msb - msw) / (msb + (k - 1) * msw))) if (msb + (k - 1) * msw) > 0 else 0.0, float(k)


def _boot_diff(a, b, n_boot, rng, rel=False):
    ia = rng.integers(0, len(a), (n_boot, len(a)))
    ib = rng.integers(0, len(b), (n_boot, len(b)))
    ma, mb = a[ia].mean(1), b[ib].mean(1)
    d = ma / mb - 1 if rel else ma - mb
    return np.percentile(d, [2.5, 97.5])


def _perm_p(a, b, n_perm, rng):
    pool = np.concatenate([a, b])
    obs = a.mean() - b.mean()
    cnt = 0
    for _ in range(n_perm):
        rng.shuffle(pool)
        cnt += abs(pool[: len(a)].mean() - pool[len(a):].mean()) >= abs(obs)
    return (cnt + 1) / (n_perm + 1)


def run(cfg: dict):
    log = RowLog()
    df = read_dataset(cfg)
    log.add("load", len(df), len(df), cfg["dataset"]["path"])
    errors, warnings = schema_check(df, cfg, SCHEMA)
    if errors:
        raise SchemaError("\n".join(errors))
    df = apply_filters(df, cfg, log)
    c, prm = cfg["columns"], cfg["params"]
    g, y, cl = c["group"], c["target"], c.get("cluster")
    alpha = float(prm.get("alpha", 0.05))
    alt = prm.get("alternative", "two-sided")
    rng = np.random.default_rng(int(prm.get("seed", 42)))
    n_boot = int(prm.get("n_boot", 5000))
    notes: list[str] = []

    before = len(df)
    df = df.dropna(subset=[g, y] + ([cl] if cl else []))
    log.add("drop rows with missing group/target", before, len(df))
    labels = prm.get("groups") or df[g].value_counts().index[:2].tolist()
    if len(labels) != 2:
        raise SchemaError(f"Need exactly two groups in `{g}`; found {df[g].unique().tolist()}.")
    before = len(df)
    df = df[df[g].isin(labels)].copy()
    log.add(f"keep groups {labels}", before, len(df))
    if df[g].nunique() < 2:
        raise SchemaError(f"After filtering only one group remains in `{g}`. Check filters and `params.groups`.")
    df[y] = df[y].astype(float)
    unit = "row"
    row_level_n = df[g].value_counts().to_dict()

    # unit of analysis
    agg_to = prm.get("aggregate_to", "cluster" if cl else "none")
    icc = deff = None
    base = prm.get("baseline")
    if cl and agg_to == "none":
        icc, k = _icc(df, cl, y)
        deff = 1 + (k - 1) * icc
        notes.append(f"Units were grouped by `{cl}` but the analysis is at row level. ICC = {icc:.3f}, design effect = {deff:.1f}: "
                     f"standard errors are about {np.sqrt(deff):.1f}x too small. Aggregate to `{cl}` unless rows were randomised individually.")
    if base:
        if not cl:
            raise SchemaError("params.baseline needs a `cluster` role (e.g. store_id) to compute growth per unit.")
        pc = base["period_col"]
        pre = df[df[pc].between(*base["pre"])].groupby([cl, g])[y].agg(prm.get("aggregate_fn", "mean"))
        post = df[df[pc].between(*base["post"])].groupby([cl, g])[y].agg(prm.get("aggregate_fn", "mean"))
        gr = (post / pre).dropna().rename(y).reset_index()
        log.add(f"growth per {cl}: post {base['post']} / pre {base['pre']}", len(df), len(gr), "one row per cluster")
        df, unit = gr, cl
        notes.append(f"Outcome = each {cl}'s mean in weeks {base['post']} divided by its own mean in {base['pre']}. "
                     "This removes size differences between units (a paired, within-unit comparison).")
    elif cl and agg_to == "cluster":
        before = len(df)
        df = df.groupby([cl, g], as_index=False)[y].agg(prm.get("aggregate_fn", "mean"))
        log.add(f"aggregate to {cl}", before, len(df), "one row per cluster = unit of randomisation")
        unit = cl
        if df[cl].duplicated().any():
            notes.append(f"Some `{cl}` values appear in both groups — check the assignment.")

    a = df.loc[df[g] == labels[0], y].to_numpy()
    b = df.loc[df[g] == labels[1], y].to_numpy()
    binary = _is_binary(df[y]) and unit == "row"
    res: dict = {"groups": labels, "unit_of_analysis": unit, "n": {labels[0]: len(a), labels[1]: len(b)},
                 "row_level_n": row_level_n, "outcome_type": "binary" if binary else "continuous"}
    if min(len(a), len(b)) < 2:
        raise SchemaError(f"Too few units after preparation: {res['n']}.")

    tests, eff = {}, {}
    if binary:
        x1, x0, n1, n0 = a.sum(), b.sum(), len(a), len(b)
        p1, p0 = x1 / n1, x0 / n0
        pp = (x1 + x0) / (n1 + n0)
        se0 = np.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n0))
        z = (p1 - p0) / se0 if se0 > 0 else np.nan
        pz = {"two-sided": 2 * stats.norm.sf(abs(z)), "greater": stats.norm.sf(z), "less": stats.norm.cdf(z)}[alt]
        tab = np.array([[x1, n1 - x1], [x0, n0 - x0]])
        exp_min = (tab.sum(1)[:, None] * tab.sum(0)[None, :] / tab.sum()).min()
        tests["two_proportion_z"] = {"z": z, "p_value": pz}
        tests["chi_square"] = {"p_value": stats.chi2_contingency(tab, correction=False)[1]}
        tests["fisher_exact"] = {"p_value": stats.fisher_exact(tab, alternative={"two-sided": "two-sided", "greater": "greater", "less": "less"}[alt])[1]}
        primary = "two_proportion_z" if exp_min >= 5 else "fisher_exact"
        se = np.sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / n0)
        zc = stats.norm.ppf(1 - alpha / 2)
        rr = p1 / p0 if p0 > 0 else np.nan
        orr = (x1 * (n0 - x0)) / ((n1 - x1) * x0) if min(x0, n1 - x1) > 0 else np.nan
        se_lor = np.sqrt(1 / x1 + 1 / (n1 - x1) + 1 / x0 + 1 / (n0 - x0)) if min(x1, x0, n1 - x1, n0 - x0) > 0 else np.nan
        se_lrr = np.sqrt((1 - p1) / x1 + (1 - p0) / x0) if min(x1, x0) > 0 else np.nan
        eff = {"rate": {labels[0]: p1, labels[1]: p0}, "risk_difference": p1 - p0,
               "risk_difference_ci": [p1 - p0 - zc * se, p1 - p0 + zc * se],
               "relative_risk": rr, "relative_risk_ci": list(np.exp(np.log(rr) + np.array([-zc, zc]) * se_lrr)) if rr == rr else None,
               "odds_ratio": orr, "odds_ratio_ci": list(np.exp(np.log(orr) + np.array([-zc, zc]) * se_lor)) if orr == orr else None,
               "pct_lift": rr - 1 if rr == rr else np.nan,
               "nnt": 1 / abs(p1 - p0) if p1 != p0 else np.inf, "min_expected_cell": exp_min}
        mde = (stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(0.8)) * np.sqrt(p0 * (1 - p0) * (1 / n1 + 1 / n0))
        eff["mde_80pct_power_abs"] = mde
        assumptions = {"min_expected_cell_count": exp_min, "independent_units": "assumed — check design"}
    else:
        da, db = pd.Series(a), pd.Series(b)
        sk = (da.skew(), db.skew())
        norm_p = []
        for arr in (a, b):
            arr_s = arr if len(arr) <= 5000 else rng.choice(arr, 5000, replace=False)
            norm_p.append(stats.shapiro(arr_s).pvalue if len(arr_s) >= 3 else np.nan)
        lev = stats.levene(a, b, center="median").pvalue
        wt = stats.ttest_ind(a, b, equal_var=False, alternative=alt)
        st = stats.ttest_ind(a, b, equal_var=True, alternative=alt)
        mw = stats.mannwhitneyu(a, b, alternative=alt)
        tests["welch_t"] = {"t": wt.statistic, "p_value": wt.pvalue, "df": float(wt.df)}
        tests["student_t"] = {"t": st.statistic, "p_value": st.pvalue}
        tests["mann_whitney"] = {"U": mw.statistic, "p_value": mw.pvalue,
                                 "prob_superiority": mw.statistic / (len(a) * len(b))}
        tests["permutation"] = {"p_value": _perm_p(a.copy(), b.copy(), int(prm.get("n_perm", 5000)), rng)}
        heavy = max(abs(sk[0]), abs(sk[1])) > 2
        small = min(len(a), len(b)) < 30
        primary = "mann_whitney" if (heavy and small) else "welch_t"
        diff = a.mean() - b.mean()
        va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
        se = np.sqrt(va + vb)
        dfw = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
        tc = stats.t.ppf(1 - alpha / 2, dfw)
        sp = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
        d = diff / sp if sp > 0 else np.nan
        j = 1 - 3 / (4 * (len(a) + len(b)) - 9)
        boot = _boot_diff(a, b, n_boot, rng)
        boot_rel = _boot_diff(a, b, n_boot, rng, rel=True)
        eff = {"mean": {labels[0]: a.mean(), labels[1]: b.mean()}, "median": {labels[0]: np.median(a), labels[1]: np.median(b)},
               "sd": {labels[0]: a.std(ddof=1), labels[1]: b.std(ddof=1)},
               "difference": diff, "difference_ci_welch": [diff - tc * se, diff + tc * se],
               "difference_ci_bootstrap": list(boot), "pct_lift": a.mean() / b.mean() - 1 if b.mean() else np.nan,
               "pct_lift_ci_bootstrap": list(boot_rel), "cohens_d": d, "hedges_g": d * j,
               "median_difference": np.median(a) - np.median(b)}
        mde = (stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(0.8)) * sp * np.sqrt(1 / len(a) + 1 / len(b))
        eff["mde_80pct_power_abs"] = mde
        assumptions = {"skewness": {labels[0]: sk[0], labels[1]: sk[1]}, "shapiro_p": {labels[0]: norm_p[0], labels[1]: norm_p[1]},
                       "levene_p": lev, "n_per_group_ge_30": not small}
        if heavy:
            notes.append(f"Outcome is heavily skewed (skew {sk[0]:.1f} / {sk[1]:.1f}). Means are sensitive to a few extreme values; "
                         "compare with the median difference and Mann-Whitney result.")
        if min(norm_p) < 0.05 and not small:
            notes.append("Shapiro-Wilk rejects normality, but with ≥30 units per group the t-test on means is still reliable (CLT) "
                         "unless tails are very heavy. Normality tests reject trivially at large n — look at the Q-Q plot instead.")
        if lev < 0.05:
            notes.append("Variances differ (Levene p < 0.05): Welch's t-test (not Student's) is the correct choice.")
    res["outcome_label"] = f"{y} growth index (post ÷ pre)" if base else y
    res.update({"primary_test": primary, "tests": tests, "effects": eff, "assumptions": assumptions,
                "icc": icc, "design_effect": deff, "alpha": alpha, "alternative": alt})

    # verdict
    p = tests[primary]["p_value"]
    lift = eff.get("pct_lift")
    ci = eff.get("pct_lift_ci_bootstrap") if not binary else (
        [eff["relative_risk_ci"][0] - 1, eff["relative_risk_ci"][1] - 1] if eff.get("relative_risk_ci") else None)
    thr = prm.get("practical_threshold")
    sig = p < alpha
    if sig and thr is not None and ci is not None:
        practical = "clears" if ci[0] >= thr else ("may not clear" if ci[0] < thr <= ci[1] else "is below")
    else:
        practical = None
    res["verdict"] = {"statistically_significant": bool(sig), "p_value": p, "practical_vs_threshold": practical}

    out = output_dir(cfg, RECIPE)
    # tables
    rows = [{"test": k, **{kk: vv for kk, vv in v.items()}} for k, v in tests.items()]
    pd.DataFrame(rows).to_csv(out / "tests.csv", index=False)
    pd.json_normalize(eff, sep=".").T.rename(columns={0: "value"}).to_csv(out / "effects.csv")
    df.to_csv(out / "analysis_units.csv", index=False)
    # plots
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    if binary:
        rates = [eff["rate"][labels[0]], eff["rate"][labels[1]]]
        errs = [1.96 * np.sqrt(r * (1 - r) / n) for r, n in zip(rates, (len(a), len(b)))]
        ax[0].bar(labels, rates, yerr=errs, color=["#b5651d", "#3b6ea5"], capsize=6)
        ax[0].set_title(f"{y} rate with 95% CI")
        ax[1].axis("off")
        ax[1].text(0, 0.5, f"Risk difference {eff['risk_difference']:+.4f}\nRelative risk {fmt(eff['relative_risk'])}\n"
                   f"Odds ratio {fmt(eff['odds_ratio'])}\nPrimary test: {primary}, p = {fmt(p, 4)}", fontsize=11)
    else:
        ax[0].boxplot([a, b], tick_labels=labels, showfliers=True)
        ax[0].set_title(f"{y} by group (unit: {unit})")
        for arr, lab, col in ((a, labels[0], "#b5651d"), (b, labels[1], "#3b6ea5")):
            xs = np.sort(arr)
            ax[1].plot(xs, np.arange(1, len(xs) + 1) / len(xs), label=lab, color=col)
        ax[1].set_title("ECDF")
        ax[1].legend()
    plt.tight_layout()
    plt.savefig(out / "comparison.png", dpi=120)
    plt.close()
    if not binary:
        fig, ax = plt.subplots(1, 2, figsize=(8, 3.4))
        for i, (arr, lab) in enumerate(((a, labels[0]), (b, labels[1]))):
            stats.probplot(arr, plot=ax[i])
            ax[i].set_title(f"Q-Q: {lab}")
        plt.tight_layout()
        plt.savefig(out / "qq.png", dpi=110)
        plt.close()

    write_run(out, RECIPE, cfg, data_hash(df), res, log, errors, warnings)
    narrative = _narrative(cfg, res, notes, warnings, log)
    (out / "narrative.md").write_text(narrative)
    print(narrative)
    return out


def _narrative(cfg, r, notes, warnings, log) -> str:
    L, e, v = r["groups"], r["effects"], r["verdict"]
    y = cfg["columns"]["target"]
    lines = [f"# Two-group comparison: {cfg['dataset'].get('name', '')} — `{y}` by `{cfg['columns']['group']}`", "",
             f"**Unit of analysis:** {r['unit_of_analysis']} · **n:** {L[0]} = {r['n'][L[0]]:,}, {L[1]} = {r['n'][L[1]]:,} · "
             f"**Outcome:** {r['outcome_type']} · **Primary test:** {r['primary_test'].replace('_', ' ')} ({r['alternative']}, α = {r['alpha']})", "",
             "## Result in one paragraph", ""]
    if r["outcome_type"] == "binary":
        rd, ci = e["risk_difference"], e["risk_difference_ci"]
        lines.append(f"The {y} rate is **{e['rate'][L[0]]:.2%}** for {L[0]} vs **{e['rate'][L[1]]:.2%}** for {L[1]}: a difference of "
                     f"**{100 * rd:+.2f} percentage points** (95% CI {100 * ci[0]:+.2f} to {100 * ci[1]:+.2f}), relative risk "
                     f"{fmt(e['relative_risk'])}, odds ratio {fmt(e['odds_ratio'])}. p = {fmt(v['p_value'], 4)}. "
                     f"With these sample sizes the smallest difference detectable with 80% power is about "
                     f"{100 * e['mde_80pct_power_abs']:.2f} pp.")
    else:
        lo, hi = e["pct_lift_ci_bootstrap"]
        lines.append(f"Mean {r['outcome_label']}: **{fmt(e['mean'][L[0]])}** ({L[0]}) vs **{fmt(e['mean'][L[1]])}** ({L[1]}), a difference of "
                     f"**{fmt(e['difference'])}** (95% CI {fmt(e['difference_ci_welch'][0])} to {fmt(e['difference_ci_welch'][1])}), "
                     f"i.e. **{100 * e['pct_lift']:+.1f}%** (bootstrap 95% CI {100 * lo:+.1f}% to {100 * hi:+.1f}%). "
                     f"p = {fmt(v['p_value'], 4)}; Hedges' g = {fmt(e['hedges_g'], 2)}. Medians differ by {fmt(e['median_difference'])}.")
    lines += ["", "## What it means", ""]
    if v["statistically_significant"]:
        lines.append("- The difference is **statistically significant**: unlikely to be chance alone *if* the design assumptions hold.")
    else:
        lines.append("- The difference is **not statistically significant**. This is *not* proof of no effect: check the confidence "
                     "interval and the minimum detectable effect before concluding anything.")
    if v["practical_vs_threshold"]:
        lines.append(f"- Against your practical threshold the effect **{v['practical_vs_threshold']}** it (judged on the lower CI bound).")
    lines.append("- Size the decision on the **confidence interval**, not the p-value.")
    if notes or warnings:
        lines += ["", "## Assumptions and warnings", ""] + [f"- {n}" for n in notes + warnings]
    lines += ["", "## Robustness", "", "| Test | p-value |", "| --- | --- |"]
    lines += [f"| {k.replace('_', ' ')} | {fmt(t['p_value'], 4)} |" for k, t in r["tests"].items()]
    lines += ["", "## Row accounting", "", log.markdown(), "",
              "Files: `tests.csv`, `effects.csv`, `analysis_units.csv`, `comparison.png`, `qq.png`, `metrics.json`, `schema_report.md`."]
    return "\n".join(lines) + "\n"
