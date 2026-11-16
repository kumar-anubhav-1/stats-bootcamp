"""rcp_scorecard: WoE/IV binning, logistic scorecard with points, Gini/KS, optional vintage table.

Navigator node N-ML-SCORECARD. Roles: target (0/1, required), features (required), vintage (optional), mob (optional).
Params: bins: {feature: [edges] | quantiles: 5}; missing values form their own bin · pdo 20 · base_score 600 · base_odds 50 ·
  min_iv 0.02 (features below are dropped from the scorecard)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import roc_auc_score

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, output_dir, read_dataset, schema_check, write_run

RECIPE = "rcp_scorecard"
SCHEMA = {"target": {"required": True}, "vintage": {"required": False}}


def binned(s, spec):
    if not (pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s)):
        return s.astype(str).fillna("missing")
    if isinstance(spec, list):
        b = pd.cut(s, [-np.inf] + list(spec) + [np.inf])
    else:
        b = pd.qcut(s, int(spec or 5), duplicates="drop")
    return b.astype(str).where(s.notna(), "missing")


def run(cfg: dict):
    log = RowLog()
    df = read_dataset(cfg)
    log.add("load", len(df), len(df), cfg["dataset"]["path"])
    errors, warnings_ = schema_check(df, cfg, SCHEMA)
    if errors:
        raise SchemaError("\n".join(errors))
    df = apply_filters(df, cfg, log)
    c, prm = cfg["columns"], cfg.get("params", {}) or {}
    y = df[c["target"]].astype(int)
    feats = list(c.get("features") or [])
    bins = prm.get("bins", {})
    rows, B, W, ivs = [], {}, {}, {}
    for f in feats:
        b = binned(df[f], bins.get(f, 5))
        t = pd.crosstab(b, y)
        g, bd = t[0] / t[0].sum(), t[1] / t[1].sum()
        woe = np.log((g + 1e-6) / (bd + 1e-6))
        iv = float(((g - bd) * woe).sum())
        ivs[f], B[f], W[f] = iv, b, woe
        for lvl in t.index:
            rows.append({"feature": f, "bin": lvl, "n": int(t.loc[lvl].sum()), "bad_rate": float(t.loc[lvl, 1] / t.loc[lvl].sum()), "woe": float(woe[lvl])})
    woe_tab = pd.DataFrame(rows)
    keep = [f for f in feats if ivs[f] >= float(prm.get("min_iv", 0.02))]
    X = pd.DataFrame({f: B[f].map(W[f]) for f in keep})
    lg = sm.Logit(y, sm.add_constant(X)).fit(disp=0)
    pdo, bs, bo = float(prm.get("pdo", 20)), float(prm.get("base_score", 600)), float(prm.get("base_odds", 50))
    factor = pdo / np.log(2)
    offset = bs - factor * np.log(bo)
    n = len(keep)
    pts = {f: {lvl: int(round(-(lg.params[f] * w + lg.params["const"] / n) * factor + offset / n)) for lvl, w in W[f].items()} for f in keep}
    woe_tab["points"] = [pts.get(r.feature, {}).get(r.bin) for r in woe_tab.itertuples()]
    score = sum(B[f].map(pts[f]) for f in keep)
    auc = roc_auc_score(y, -score)
    o = np.argsort(score.values)
    yy = y.values[o]
    ks = float(np.max(np.cumsum(yy) / yy.sum() - np.cumsum(1 - yy) / (1 - yy).sum()))
    out = output_dir(cfg, RECIPE)
    woe_tab.to_csv(out / "woe_points.csv", index=False)
    m = {"iv": {k: float(v) for k, v in sorted(ivs.items(), key=lambda kv: -kv[1])}, "features_in_scorecard": keep, "gini": 2 * auc - 1, "ks": ks,
         "score_mean": float(score.mean()), "pdo": pdo, "base_score": bs, "base_odds": bo}
    if c.get("vintage"):
        vt = df.groupby(c["vintage"])[c["target"]].agg(["mean", "size"])
        m["vintage_bad_rate"] = {str(k): float(v) for k, v in vt["mean"].items()}
    write_run(out, RECIPE, cfg, data_hash(pd.concat([X, y], axis=1)), m, log, errors, warnings_)
    band = lambda v: "very strong — verify (expected for bureau scores; else suspect leakage)" if v > 0.5 else "strong" if v > 0.3 else "medium" if v > 0.1 else "weak" if v > 0.02 else "not useful"
    L = [f"# Scorecard: `{c['target']}`", "", f"Points: {bs:g} at odds {bo:g}:1, {pdo:g} points to double the odds · Gini **{2 * auc - 1:.3f}** · KS **{ks:.3f}**", "",
         "## Information value", "", "| Feature | IV | Strength |", "| --- | --- | --- |"]
    L += [f"| {k} | {v:.3f} | {band(v)} |" for k, v in m["iv"].items()]
    L += ["", "## Points by bin", "", "| Feature | Bin | n | Bad rate | WoE | Points |", "| --- | --- | --- | --- | --- | --- |"]
    L += [f"| {r.feature} | {r.bin} | {r.n:,} | {r.bad_rate:.2%} | {r.woe:+.2f} | {'' if r.points is None or (isinstance(r.points, float) and np.isnan(r.points)) else int(r.points)} |" for r in woe_tab[woe_tab.feature.isin(keep)].itertuples()]
    if "vintage_bad_rate" in m:
        L += ["", "## Bad rate by vintage", "", "| Vintage | Bad rate |", "| --- | --- |"] + [f"| {k} | {v:.2%} |" for k, v in m["vintage_bad_rate"].items()]
    L += ["", "## How to read this", "", "- WoE = ln(%good ÷ %bad) per bin; IV sums the separation. IV > 0.5 is suspicious (leakage or a policy variable).",
          "- Missing values get their own bin — missingness is often predictive (income missing).", "- Points add up to a score; higher = lower risk. Check monotonic WoE for explainability.",
          "- Booked-only data: performance of declined applicants is unknown (reject inference).", "", "Files: `woe_points.csv`, `metrics.json`."]
    (out / "narrative.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:24]))
    return out
