"""rcp_anomaly_scan: entity-level anomaly scores, graph rings and threshold bunching — three modes.

Navigator nodes N-ANOM-MULTI, N-ANOM-GRAPH, N-ANOM-STRUCT. Params.mode:
  score    — roles: entity. params: aggregate {name: [col, func]}, ratio {name: [numerator, denominator]}, metric (main metric for robust z),
             min_rows, contamination [0.01, 0.02, 0.05], top_n. Methods: robust z (median/MAD) on `metric`, Isolation Forest on all features.
  graph    — roles: entity, link (rows = entity–link pairs, e.g. account–device). params: min_size 6, label (optional 0/1 column file)
  bunching — roles: value. params: threshold 10000, band 0.1 (compares counts in [t(1−band), t) vs [t, t(1+band)))
"""
from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, output_dir, read_dataset, write_run
from toolkit.common.entity import entity_table

RECIPE = "rcp_anomaly_scan"


def run(cfg: dict):
    log = RowLog()
    df = read_dataset(cfg)
    log.add("load", len(df), len(df), cfg["dataset"]["path"])
    df = apply_filters(df, cfg, log)
    c, prm = cfg["columns"], cfg.get("params", {}) or {}
    mode = prm.get("mode", "score")
    for role, col in c.items():
        if col not in df.columns:
            raise SchemaError(f"role `{role}` → column `{col}` not found.")
    out = output_dir(cfg, RECIPE)
    L, m = [], {"mode": mode}
    if mode == "score":
        ent = c["entity"]
        if prm.get("drop_duplicates"):
            df = df.drop_duplicates(list(prm["drop_duplicates"]))
        cnt = df.groupby(ent).size()
        df = df[df[ent].isin(cnt[cnt >= int(prm.get("min_rows", 1))].index)]
        X = entity_table(df, ent, prm.get("aggregate"))
        for k, (num, den) in (prm.get("ratio") or {}).items():
            X[k] = X[num] / X[den].clip(lower=1)
        X = X.fillna(0)
        met = prm.get("metric", X.columns[0])
        med = X[met].median()
        mad = 1.4826 * (X[met] - med).abs().median()
        scale_note = "MAD"
        if mad == 0:  # most entities identical (e.g. zero returns): fall back to the mean absolute deviation
            mad, scale_note = 1.2533 * (X[met] - med).abs().mean() or 1e-9, "mean absolute deviation (MAD = 0)"
        X["robust_z"] = (X[met] - med) / mad
        iso = IsolationForest(n_estimators=300, random_state=int(prm.get("seed", 0))).fit(X.drop(columns="robust_z"))
        X["iso_score"] = -iso.score_samples(X.drop(columns="robust_z"))
        X["iso_rank"] = X.iso_score.rank(ascending=False)
        X = X.sort_values("robust_z", ascending=False)
        X.to_csv(out / "scores.csv")
        n = len(X)
        conts = prm.get("contamination", [0.01, 0.02, 0.05])
        both = {}
        for ct in conts:
            k = int(np.ceil(ct * n))
            a_ = set(X.nlargest(k, "robust_z").index)
            b_ = set(X.nlargest(k, "iso_score").index)
            both[str(ct)] = {"k": k, "overlap": len(a_ & b_)}
        top = X.head(int(prm.get("top_n", 15)))
        m.update({"entities": n, "metric": met, "median": float(med), "mad": float(mad), "flag_counts": both,
                  "n_robust_z_gt_3_5": int((X.robust_z > 3.5).sum()), "_tolerance": {"rtol": 0.05, "atol": 0.02}})
        L = [f"# Anomaly scan: `{ent}` on `{met}`", "", f"{n:,} entities. Median {med:.4g}; scale from {scale_note} = {mad:.4g}. {m['n_robust_z_gt_3_5']} entities have robust z > 3.5.", "",
             "| Contamination | Flagged | Overlap robust-z vs Isolation Forest |", "| --- | --- | --- |"]
        L += [f"| {float(k):.0%} | {v['k']} | {v['overlap']} |" for k, v in both.items()]
        L += ["", f"## Top {len(top)} by robust z", "", "| Entity | " + " | ".join(X.columns[:6]) + " |", "| --- | " + " | ".join("---" for _ in X.columns[:6]) + " |"]
        L += [f"| {i} | " + " | ".join(f"{r[col]:.3g}" for col in X.columns[:6]) + " |" for i, r in top.iterrows()]
        L += ["", "- Robust z (median/MAD) is not distorted by the outliers it hunts; plain z-scores are (masking).",
              "- Choose contamination from **review capacity** (alert budget), then check stability of the flagged list across methods."]
    elif mode == "graph":
        ent, lk = c["entity"], c["link"]
        G = nx.Graph()
        G.add_edges_from(zip("E:" + df[ent].astype(str), "L:" + df[lk].astype(str)))
        comps = [{n[2:] for n in comp if n.startswith("E:")} for comp in nx.connected_components(G)]
        ms = int(prm.get("min_size", 6))
        big = sorted([cc for cc in comps if len(cc) >= ms], key=len, reverse=True)
        lab = prm.get("label")
        rates = None
        if lab:
            lt = pd.read_parquet(lab["path"]).set_index(lab["key"])[lab["column"]].astype(float)
            rates = [float(lt.reindex(list(cc)).mean()) for cc in big]
            m["base_rate"] = float(lt.mean())
        sizes = pd.Series([len(cc) for cc in comps]).value_counts().sort_index()
        pd.DataFrame([{"component": i, "size": len(cc), "members": ";".join(sorted(cc))} for i, cc in enumerate(big)]).to_csv(out / "components.csv", index=False)
        m.update({"entities": int(df[ent].nunique()), "components_ge_min": len(big), "sizes": [len(cc) for cc in big],
                  "label_rates": rates, "largest_other": int(max((len(cc) for cc in comps if len(cc) < ms), default=0))})
        L = [f"# Linked-entity graph: `{ent}` via `{lk}`", "", f"{m['entities']:,} entities. Components with ≥ {ms} entities: **{len(big)}** (sizes {m['sizes']}). "
             f"Largest other component: {m['largest_other']}.", ""]
        if rates is not None:
            L += [f"Label rate in large components: {', '.join(f'{r:.0%}' for r in rates)} vs base {m['base_rate']:.2%}.", ""]
        L += ["- Many accounts sharing devices/addresses is rare among genuine customers (households share 2–3).", "- Review whole components, not single accounts."]
    elif mode == "bunching":
        v = df[c["value"]].astype(float)
        v = v[v > 0]
        t, band = float(prm.get("threshold", 10000)), float(prm.get("band", 0.1))
        below = int(v.between(t * (1 - band), t - 1e-9).sum())
        above = int(v.between(t, t * (1 + band)).sum())
        edges = np.linspace(t * (1 - 5 * band), t * (1 + 5 * band), 11)
        hist = np.histogram(v, bins=edges)[0]
        m.update({"threshold": t, "below": below, "above": above, "ratio": below / max(above, 1), "hist": hist.tolist(), "edges": edges.tolist()})
        L = [f"# Threshold bunching: `{c['value']}` around {t:,.0f}", "", f"Values in [{t * (1 - band):,.0f}, {t:,.0f}): **{below:,}** · in [{t:,.0f}, {t * (1 + band):,.0f}): **{above:,}** · ratio **{below / max(above, 1):.1f}**.", "",
             "| Bin | Count |", "| --- | --- |"] + [f"| {edges[i]:,.0f}–{edges[i + 1]:,.0f} | {hist[i]:,} |" for i in range(len(hist))]
        L += ["", "- A smooth distribution declines through the threshold; a spike just below it signals structuring (avoiding a reporting limit).",
              "- Identify entities repeatedly just below the threshold; escalate per AML procedure."]
    else:
        raise SchemaError("params.mode must be score, graph or bunching")
    write_run(out, RECIPE, cfg, data_hash(df.iloc[:, :3]), m, log, [], [])
    (out / "narrative.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:22]))
    return out
