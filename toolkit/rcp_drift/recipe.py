"""rcp_drift: population and concept drift between a reference and a current window (PSI/CSI, scale checks, performance decay).

Navigator node N-MON-PSI. Roles: period (required, used in the window expressions), target (optional binary), score (optional numeric).
Params:
  reference: "week < 80"         pandas query selecting the reference (development) window
  current:   "week >= 80"        pandas query selecting the monitored window
  features: [discount_pct, ...]  numeric or categorical columns to monitor
  bins: 10                       quantile bins from the reference window
  thresholds: [0.10, 0.25]       PSI bands: stable / monitor / act
  score_higher_is_riskier: true  orientation of `score` for AUC
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, md_table, output_dir, read_dataset, schema_check, write_run

RECIPE = "rcp_drift"
SCHEMA = {"period": {"required": True}, "target": {"required": False}, "score": {"required": False, "kind": "numeric"}}


def psi_numeric(ref, cur, bins=10):
    ref, cur = np.asarray(ref, float), np.asarray(cur, float)
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    e = np.histogram(ref, edges)[0] / len(ref)
    a = np.histogram(cur, edges)[0] / len(cur)
    e, a = np.clip(e, 1e-4, None), np.clip(a, 1e-4, None)
    return float(((a - e) * np.log(a / e)).sum())


def psi_categorical(ref, cur):
    e = ref.astype(str).value_counts(normalize=True)
    a = cur.astype(str).value_counts(normalize=True)
    idx = e.index.union(a.index)
    e, a = e.reindex(idx, fill_value=0).clip(lower=1e-4), a.reindex(idx, fill_value=0).clip(lower=1e-4)
    return float(((a - e) * np.log(a / e)).sum()), {k: (round(float(e[k]), 4), round(float(a[k]), 4)) for k in idx}


def run(cfg: dict):
    log = RowLog()
    df = read_dataset(cfg)
    log.add("load", len(df), len(df), cfg["dataset"]["path"])
    errors, warnings_ = schema_check(df, cfg, SCHEMA)
    prm = cfg.get("params", {}) or {}
    feats = prm.get("features") or []
    miss = [f for f in feats if f not in df.columns]
    if miss:
        errors.append(f"features not in dataset: {miss}")
    if errors:
        raise SchemaError("\n".join(errors))
    df = apply_filters(df, cfg, log)
    c = cfg["columns"]
    ref, cur = df.query(prm["reference"], engine="python"), df.query(prm["current"], engine="python")
    log.add(f"reference: {prm['reference']}", len(df), len(ref))
    log.add(f"current: {prm['current']}", len(df), len(cur))
    if len(ref) < 50 or len(cur) < 50:
        raise SchemaError(f"Windows too small (reference {len(ref)}, current {len(cur)} rows).")
    lo, hi = prm.get("thresholds", [0.10, 0.25])
    band = lambda v: "act" if v >= hi else ("monitor" if v >= lo else "stable")
    rows, cats = [], {}
    for f in feats:
        r, k = ref[f].dropna(), cur[f].dropna()
        if pd.api.types.is_numeric_dtype(r) and not pd.api.types.is_bool_dtype(r):
            v = psi_numeric(r, k, int(prm.get("bins", 10)))
            mr, mk = float(r.median()), float(k.median())
            ratio = mk / mr if mr else np.nan
            scale = "possible unit change (≈×100 or ÷100)" if ratio and (80 < ratio < 120 or 1 / 120 < ratio < 1 / 80) else ""
            rows.append({"feature": f, "type": "numeric", "psi": round(v, 4), "band": band(v), "ref_median": round(mr, 4),
                         "cur_median": round(mk, 4), "ref_missing": round(float(ref[f].isna().mean()), 4),
                         "cur_missing": round(float(cur[f].isna().mean()), 4), "note": scale})
        else:
            v, shares = psi_categorical(r, k)
            cats[f] = shares
            rows.append({"feature": f, "type": "categorical", "psi": round(v, 4), "band": band(v), "ref_median": None,
                         "cur_median": None, "ref_missing": round(float(ref[f].isna().mean()), 4),
                         "cur_missing": round(float(cur[f].isna().mean()), 4), "note": ""})
    tab = pd.DataFrame(rows).sort_values("psi", ascending=False)
    perf = {}
    y, s = c.get("target"), c.get("score")
    if y and s:
        sign = 1 if prm.get("score_higher_is_riskier", True) else -1
        for nm, part in (("reference", ref), ("current", cur)):
            p = part.dropna(subset=[y, s])
            if p[y].nunique() == 2:
                perf[nm] = {"auc": round(float(roc_auc_score(p[y].astype(int), sign * p[s])), 4),
                            "event_rate": round(float(p[y].astype(float).mean()), 4), "n": int(len(p))}
        if len(perf) == 2:
            perf["auc_change"] = round(perf["current"]["auc"] - perf["reference"]["auc"], 4)
            perf["score_psi"] = round(psi_numeric(ref[s].dropna(), cur[s].dropna()), 4)
    out = output_dir(cfg, RECIPE)
    tab.to_csv(out / "drift_table.csv", index=False)
    fig, ax = plt.subplots(figsize=(8, 0.45 * len(tab) + 1.2))
    col = tab.band.map({"stable": "#4caf50", "monitor": "#ff9800", "act": "#e53935"})
    ax.barh(tab.feature[::-1], np.minimum(tab.psi[::-1], 1.0), color=col[::-1])
    for x_ in (lo, hi):
        ax.axvline(x_, ls=":", color="grey")
    ax.set_xlabel("PSI (capped at 1.0 for display)")
    plt.tight_layout()
    plt.savefig(out / "drift.png", dpi=110)
    plt.close()
    metrics = {"n_reference": int(len(ref)), "n_current": int(len(cur)),
               "psi": {r["feature"]: r["psi"] for r in rows}, "bands": {r["feature"]: r["band"] for r in rows},
               "unit_flags": [r["feature"] for r in rows if r["note"]], "categorical_shares": cats, "performance": perf}
    write_run(out, RECIPE, cfg, data_hash(df[feats]), metrics, log, errors, warnings_)
    L = [f"# Drift report: `{prm['reference']}` → `{prm['current']}`", "",
         f"Reference {len(ref):,} rows; current {len(cur):,} rows. PSI bands: < {lo} stable, {lo}–{hi} monitor, ≥ {hi} act.", "",
         md_table(tab.set_index("feature")[["type", "psi", "band", "ref_median", "cur_median", "cur_missing", "note"]], nd=4), ""]
    for f, sh in cats.items():
        L += [f"**{f}** shares (reference → current): " + "; ".join(f"{k} {a:.1%} → {b:.1%}" for k, (a, b) in sh.items()), ""]
    if perf.get("auc_change") is not None:
        L += [f"**Performance:** AUC {perf['reference']['auc']:.3f} → {perf['current']['auc']:.3f} ({perf['auc_change']:+.3f}); "
              f"event rate {perf['reference']['event_rate']:.2%} → {perf['current']['event_rate']:.2%}; score PSI {perf['score_psi']:.3f}.", ""]
    L += ["## How to read this", "",
          "- PSI measures how much a distribution moved, not whether the model got worse; check performance separately (concept drift).",
          "- A median that moved by ≈ ×100 is almost always a **unit/logging change** — fix the pipeline before retraining anything.",
          "- Large PSI with stable relationships (population drift) → recalibrate or re-weight; falling AUC with stable inputs (concept drift) → rebuild.",
          "- Look at categorical shares: a channel-mix shift often explains several numeric drifts at once.", "",
          "Files: `drift_table.csv`, `drift.png`, `metrics.json`."]
    (out / "narrative.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:14]))
    return out
