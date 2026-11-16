"""rcp_ab_test: experiment readout — hygiene first, then the effect, guardrails and a decision.

Navigator nodes N-EXP-SRM → N-TEST-2G-* → N-EXP-CUPED → N-BAYES-AB. Steps:
  1. sample-ratio-mismatch (SRM) check against the planned split, overall and by `segment` columns;
  2. primary metric at the unit of randomisation (aggregates to `unit` if given; optional pre/post baseline);
  3. CUPED adjustment with a pre-treatment `covariate` (variance reduction reported);
  4. frequentist (difference, relative lift, CI, p) and Bayesian (P(treatment better), expected loss) readouts;
  5. guardrail metrics (must not get worse beyond a tolerance);
  6. decision text: STOP if SRM fails; otherwise ship / don't ship / inconclusive against the practical threshold.

Roles: arm (required), outcome (required), unit (optional), covariate (optional), date (optional, for cumulative looks).
Params:
  arms: [treatment, control]                   labels (default: two most frequent)
  planned_split: {treatment: 0.5, control: 0.5}
  srm_alpha: 0.001
  segments: [app_version, platform]            columns to locate an SRM
  baseline: {period_col, pre: [a, b], post: [c, d]}   outcome = post mean per unit; covariate = pre mean per unit
  log_covariate: false                         use log(covariate) for CUPED (skewed spend)
  guardrails: [{metric: col, direction: higher_is_worse|lower_is_worse, tolerance: 0.0}]
  alpha: 0.05 · practical_threshold: smallest absolute effect worth shipping · bayes_draws: 100000 · seed: 42
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, fmt, output_dir, read_dataset, schema_check, write_run

RECIPE = "rcp_ab_test"
SCHEMA = {"arm": {"required": True, "kind": "category"}, "outcome": {"required": True}, "unit": {"required": False},
          "covariate": {"required": False}, "date": {"required": False}}


def _binary(s):
    return set(pd.Series(s).dropna().unique()) <= {0, 1, True, False}


def effect(y1, y0, binary, alpha):
    y1, y0 = np.asarray(y1, float), np.asarray(y0, float)
    d = y1.mean() - y0.mean()
    se = np.sqrt(y1.var(ddof=1) / len(y1) + y0.var(ddof=1) / len(y0))
    if binary:
        pp = (y1.sum() + y0.sum()) / (len(y1) + len(y0))
        z = d / np.sqrt(pp * (1 - pp) * (1 / len(y1) + 1 / len(y0)))
        p = 2 * stats.norm.sf(abs(z))
        crit = stats.norm.ppf(1 - alpha / 2)
    else:
        df = (y1.var(ddof=1) / len(y1) + y0.var(ddof=1) / len(y0)) ** 2 / (
            (y1.var(ddof=1) / len(y1)) ** 2 / (len(y1) - 1) + (y0.var(ddof=1) / len(y0)) ** 2 / (len(y0) - 1))
        p = 2 * stats.t.sf(abs(d / se), df)
        crit = stats.t.ppf(1 - alpha / 2, df)
    return {"t_mean": y1.mean(), "c_mean": y0.mean(), "diff": d, "se": se, "ci_low": d - crit * se, "ci_high": d + crit * se,
            "p": float(p), "rel_lift": d / y0.mean() if y0.mean() else None, "n_t": len(y1), "n_c": len(y0)}


def run(cfg: dict):
    log = RowLog()
    df = read_dataset(cfg)
    log.add("load", len(df), len(df), cfg["dataset"]["path"])
    errors, warnings = schema_check(df, cfg, SCHEMA)
    if errors:
        raise SchemaError("\n".join(errors))
    df = apply_filters(df, cfg, log)
    c, prm = cfg["columns"], cfg.get("params", {}) or {}
    arm, y, u, cov = c["arm"], c["outcome"], c.get("unit"), c.get("covariate")
    alpha = float(prm.get("alpha", 0.05))
    arms = prm.get("arms") or list(df[arm].value_counts().index[:2])
    t_lab, c_lab = arms
    b = len(df)
    df = df[df[arm].isin(arms)]
    log.add("keep the two arms", b, len(df), f"{t_lab} vs {c_lab}")
    guards = prm.get("guardrails", []) or []
    gcols = [g["metric"] for g in guards]
    base = prm.get("baseline")
    if base:
        if not u:
            raise SchemaError("params.baseline needs a `unit` role (e.g. store_id).")
        pc = base["period_col"]
        pre = df[df[pc].between(*base["pre"])].groupby(u)[y].mean().rename("_pre")
        post = df[df[pc].between(*base["post"])].groupby(u)[y].mean().rename(y)
        armu = df.groupby(u)[arm].first()
        b = len(df)
        df = pd.concat([post, pre, armu], axis=1).reset_index()
        cov = "_pre"
        log.add(f"aggregate to {u} (post mean; pre mean as covariate)", b, len(df), "unit of randomisation")
    elif u:
        b = len(df)
        agg = {y: "mean", arm: "first", **({cov: "mean"} if cov else {}), **{g: "mean" for g in gcols}}
        df = df.groupby(u, as_index=False).agg(agg)
        log.add(f"aggregate to {u}", b, len(df), "unit of randomisation")
    df[y] = df[y].astype(float)
    binary = _binary(df[y]) and not (u or base)
    out = output_dir(cfg, RECIPE)
    m: dict = {"arms": arms, "unit": u or "row", "binary": bool(binary)}
    # 1. SRM
    split = prm.get("planned_split") or {t_lab: 0.5, c_lab: 0.5}
    cnt = df[arm].value_counts().reindex(arms).fillna(0)
    exp = np.array([split[t_lab], split[c_lab]]) * cnt.sum()
    srm_p = float(stats.chisquare(cnt.values, exp).pvalue)
    srm_alpha = float(prm.get("srm_alpha", 0.001))
    seg_rows = []
    for sc in prm.get("segments", []) or []:
        if sc not in df.columns:
            warnings.append(f"segment column `{sc}` not found")
            continue
        for v, g in df.groupby(sc):
            cc = g[arm].value_counts().reindex(arms).fillna(0)
            e_ = np.array([split[t_lab], split[c_lab]]) * cc.sum()
            seg_rows.append({"segment": f"{sc}={v}", "n_t": int(cc[t_lab]), "n_c": int(cc[c_lab]),
                             "share_t": cc[t_lab] / cc.sum(), "p": float(stats.chisquare(cc.values, e_).pvalue)})
    seg = pd.DataFrame(seg_rows)
    srm_fail = srm_p < srm_alpha
    m.update({"counts": cnt.astype(int).to_dict(), "planned_split": split, "srm_p": srm_p, "srm_fail": bool(srm_fail),
              "srm_by_segment": seg.set_index("segment").round(8).to_dict(orient="index") if len(seg) else {}})
    # 2. primary
    T, C = df[df[arm] == t_lab], df[df[arm] == c_lab]
    prim = effect(T[y], C[y], binary, alpha)
    m["primary"] = prim
    # 3. CUPED
    cup = None
    if cov:
        x = df[cov].astype(float)
        if prm.get("log_covariate"):
            x = np.log(x.clip(lower=1e-9))
        ok = x.notna()
        theta = np.cov(df.loc[ok, y], x[ok])[0, 1] / x[ok].var()
        ya = df[y] - theta * (x - x[ok].mean())
        cup = effect(ya[ok & (df[arm] == t_lab)], ya[ok & (df[arm] == c_lab)], False, alpha)
        cup["theta"] = theta
        cup["variance_reduction"] = 1 - ya[ok].var() / df.loc[ok, y].var()
        cup["rel_lift"] = cup["diff"] / C[y].mean()
        m["cuped"] = cup
    # 4. Bayesian
    rng = np.random.default_rng(int(prm.get("seed", 42)))
    S = int(prm.get("bayes_draws", 100_000))
    if binary:
        kt, nt, kc, nc = T[y].sum(), len(T), C[y].sum(), len(C)
        pt, pc_ = rng.beta(1 + kt, 1 + nt - kt, S), rng.beta(1 + kc, 1 + nc - kc, S)
        dd = pt - pc_
    else:
        src = cup if cup else prim
        dd = rng.normal(src["diff"], src["se"], S)
    m["bayes"] = {"p_treatment_better": float((dd > 0).mean()), "ci_low": float(np.percentile(dd, 2.5)), "ci_high": float(np.percentile(dd, 97.5)),
                  "expected_loss_if_ship": float(np.maximum(-dd, 0).mean()), "expected_loss_if_keep": float(np.maximum(dd, 0).mean())}
    # 5. guardrails
    grows = []
    for g in guards:
        col = g["metric"]
        if col not in df.columns:
            warnings.append(f"guardrail `{col}` not found")
            continue
        e = effect(T[col].dropna(), C[col].dropna(), _binary(df[col]), alpha)
        tol = float(g.get("tolerance", 0.0))
        worse_dir = 1 if g.get("direction", "higher_is_worse") == "higher_is_worse" else -1
        breach = (worse_dir * e["ci_low"] > tol) if worse_dir == 1 else (-e["ci_high"] > tol)
        grows.append({"metric": col, "t": e["t_mean"], "c": e["c_mean"], "diff": e["diff"], "ci_low": e["ci_low"], "ci_high": e["ci_high"],
                      "p": e["p"], "direction": g.get("direction", "higher_is_worse"), "breach": bool(breach)})
    gdf = pd.DataFrame(grows)
    m["guardrails"] = gdf.set_index("metric").to_dict(orient="index") if len(gdf) else {}
    # 6. decision
    thr = prm.get("practical_threshold")
    best = cup if cup else prim
    if srm_fail:
        decision = "STOP — sample-ratio mismatch. Do not read the effect until assignment/logging is fixed."
    elif len(gdf) and gdf.breach.any():
        decision = "DON'T SHIP — a guardrail is significantly worse: " + ", ".join(gdf[gdf.breach].metric)
    elif best["ci_low"] > (thr or 0):
        decision = "SHIP — the whole CI is above " + (f"the practical threshold ({thr})." if thr else "zero.")
    elif best["ci_high"] < (thr or 0):
        decision = "DON'T SHIP — the effect is reliably below the practical threshold." if thr else "DON'T SHIP — the effect is reliably negative."
    elif best["ci_low"] > 0:
        decision = "SHIP WITH CAUTION — positive effect, but the CI includes values below the practical threshold."
    else:
        decision = "INCONCLUSIVE — the CI includes zero; extend or redesign (see MDE)."
    m["decision"] = decision
    # cumulative looks (descriptive)
    if c.get("date") and binary:
        dcol = c["date"]
        rows = []
        for dday in sorted(df[dcol].unique()):
            sub = df[df[dcol] <= dday]
            e = effect(sub[sub[arm] == t_lab][y], sub[sub[arm] == c_lab][y], True, alpha)
            rows.append({"date": dday, "n": len(sub), "diff": e["diff"], "p": e["p"]})
        looks = pd.DataFrame(rows)
        looks.to_csv(out / "cumulative_looks.csv", index=False)
        m["looks_naive_significant"] = int((looks.p < alpha).sum())
        fig, ax = plt.subplots(figsize=(7, 3.2))
        ax.plot(range(1, len(looks) + 1), looks.p, "o-")
        ax.axhline(alpha, color="red", ls="--")
        ax.set_xlabel("look (cumulative day)")
        ax.set_ylabel("p-value")
        ax.set_title("p-value at each daily look — why peeking misleads")
        plt.tight_layout()
        plt.savefig(out / "looks.png", dpi=120)
        plt.close()
    write_run(out, RECIPE, cfg, data_hash(df), m, log, errors, warnings)
    pct = (lambda v: f"{100 * v:+.2f} pp") if binary else (lambda v: f"{v:+.3f}")
    L = [f"# Experiment readout: `{y}` — {t_lab} vs {c_lab}", "", f"**Decision: {decision}**", "",
         f"Unit of analysis: **{u or 'row'}** · α = {alpha}", "", "## 1. Sample-ratio check", "",
         f"Planned {t_lab}:{c_lab} = {split[t_lab]:.0%}:{split[c_lab]:.0%}; observed {int(cnt[t_lab]):,}:{int(cnt[c_lab]):,} "
         f"({cnt[t_lab] / cnt.sum():.1%} {t_lab}). χ² p = {fmt(srm_p, 3)} → " + ("**SRM — results are not trustworthy.**" if srm_fail else "no mismatch.")]
    if len(seg):
        L += ["", "| Segment | n treatment | n control | share treatment | p |", "| --- | --- | --- | --- | --- |"]
        L += [f"| {r.segment} | {r.n_t:,} | {r.n_c:,} | {r.share_t:.1%} | {fmt(r.p, 3)} |" for r in seg.itertuples()]
        seg["col"] = seg.segment.str.split("=").str[0]
        local, spread = [], []
        for col, g in seg.groupby("col", sort=False):
            nb = int((g.p < srm_alpha).sum())
            if 0 < nb < len(g):
                local += list(g[g.p < srm_alpha].segment)
            elif nb == len(g) and nb > 0:
                spread.append(col)
        if local:
            L += ["", "The mismatch is **localised** in: **" + ", ".join(local) + "** — check logging/eligibility there."]
        if spread:
            L += ["", "It appears in every level of " + ", ".join(f"`{x}`" for x in spread) + " — those columns carry the problem but do not explain it."]
        m["srm_localised_in"] = local
    L += ["", "## 2. Primary metric", "", "| | Treatment | Control | Difference | 95% CI | Relative | p |", "| --- | --- | --- | --- | --- | --- | --- |",
          f"| unadjusted | {prim['t_mean']:.4f} | {prim['c_mean']:.4f} | {pct(prim['diff'])} | {pct(prim['ci_low'])} to {pct(prim['ci_high'])} | "
          f"{100 * prim['rel_lift']:+.1f}% | {fmt(prim['p'], 3)} |"]
    if cup:
        L.append(f"| CUPED | | | {pct(cup['diff'])} | {pct(cup['ci_low'])} to {pct(cup['ci_high'])} | {100 * cup['rel_lift']:+.1f}% | {fmt(cup['p'], 3)} |")
        L += ["", f"CUPED with `{c.get('covariate') or 'pre-period ' + y}` removed **{100 * cup['variance_reduction']:.1f}%** of the variance "
              f"(θ = {cup['theta']:.3f}); SE {prim['se']:.4g} → {cup['se']:.4g}."]
    bz = m["bayes"]
    L += ["", "## 3. Bayesian reading", "", f"P({t_lab} better) = **{bz['p_treatment_better']:.1%}** · 95% credible interval {pct(bz['ci_low'])} to {pct(bz['ci_high'])} · "
          f"expected loss if we ship = {pct(bz['expected_loss_if_ship'])}, if we keep control = {pct(bz['expected_loss_if_keep'])} "
          f"({'uniform Beta(1,1) priors' if binary else 'flat prior, normal approximation'})."]
    if len(gdf):
        L += ["", "## 4. Guardrails", "", "| Metric | Treatment | Control | Difference | 95% CI | p | Breach |", "| --- | --- | --- | --- | --- | --- | --- |"]
        L += [f"| {r.metric} | {r.t:.4g} | {r.c:.4g} | {r.diff:+.4g} | {r.ci_low:+.4g} to {r.ci_high:+.4g} | {fmt(r.p, 3)} | {'**yes**' if r.breach else 'no'} |" for r in gdf.itertuples()]
    L += ["", "## How to read this", "",
          "- **Hygiene first.** An SRM means users went missing or were mis-assigned non-randomly; any effect estimate may be biased.",
          "- Report the effect with its CI and compare with the practical threshold, not only with zero.",
          "- CUPED only helps when the pre-period covariate is strongly correlated with the outcome.",
          "- Guardrails protect what must not get worse (complaints, margin, other categories).",
          "- Cumulative daily p-values are descriptive; stopping at the first p < α inflates false positives (use a sequential design).", "",
          "Files: `metrics.json`, `cumulative_looks.csv` and `looks.png` (if a date role is mapped), `row_accounting.md`."]
    (out / "narrative.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:32]))
    return out
