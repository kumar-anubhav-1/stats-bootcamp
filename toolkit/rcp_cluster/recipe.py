"""rcp_cluster: scale → (PCA) → K-Means over a range of k → silhouette → cluster profiles.

Navigator nodes N-CLUST-KMEANS, N-CLUST-GMM. Roles: entity (required). Params:
  aggregate: {name: [column, func]}  build entity features from rows (else numeric columns of an entity-level table)
  share_of: category                  add per-entity shares of a categorical column
  log: [names]                        log1p-transform skewed features
  min_rows: 2                         drop entities with fewer rows
  k_range: [2, 8] · k: chosen k for profiles (default: best silhouette) · scale: true · seed: 0
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, output_dir, read_dataset, schema_check, write_run
from toolkit.common.entity import entity_table

RECIPE = "rcp_cluster"
SCHEMA = {"entity": {"required": True}}


def run(cfg: dict):
    log = RowLog()
    df = read_dataset(cfg)
    log.add("load", len(df), len(df), cfg["dataset"]["path"])
    errors, warnings_ = schema_check(df, cfg, SCHEMA)
    if errors:
        raise SchemaError("\n".join(errors))
    df = apply_filters(df, cfg, log)
    c, prm = cfg["columns"], cfg.get("params", {}) or {}
    ent = c["entity"]
    if prm.get("drop_duplicates"):
        df = df.drop_duplicates(list(prm["drop_duplicates"]))
    cnt = df.groupby(ent).size()
    keep = cnt[cnt >= int(prm.get("min_rows", 1))].index
    df = df[df[ent].isin(keep)]
    X = entity_table(df, ent, prm.get("aggregate"), prm.get("share_of"), prm.get("log")).fillna(0)
    log.add("entity feature table", len(df), len(X), f"{X.shape[1]} features")
    seed = int(prm.get("seed", 0))
    Z = StandardScaler().fit_transform(X) if prm.get("scale", True) else X.values
    lo, hi = prm.get("k_range", [2, 8])
    sil = {}
    for k in range(int(lo), int(hi) + 1):
        lab = KMeans(k, n_init=20, random_state=seed).fit_predict(Z)
        sil[k] = float(silhouette_score(Z, lab))
    k = int(prm.get("k") or max(sil, key=sil.get))
    lab = KMeans(k, n_init=20, random_state=seed).fit_predict(Z)
    X["cluster"] = lab
    prof = X.groupby("cluster").mean()
    prof.insert(0, "n", X.groupby("cluster").size())
    z = (prof.drop(columns="n") - X.drop(columns="cluster").mean()) / X.drop(columns="cluster").std()
    desc = {cl: ", ".join(f"{f} {'↑' if v > 0 else '↓'}" for f, v in z.loc[cl].abs().sort_values(ascending=False).head(3).items()
                          for v in [z.loc[cl, f]]) for cl in z.index}
    pca = PCA().fit(Z)
    out = output_dir(cfg, RECIPE)
    X.to_csv(out / "assignments.csv")
    prof.to_csv(out / "profiles.csv")
    m = {"n_entities": int(len(X)), "n_features": int(Z.shape[1]), "silhouette": sil, "k": k,
         "sizes": X.cluster.value_counts().sort_index().to_dict(), "pca_var_2": float(pca.explained_variance_ratio_[:2].sum()),
         "_tolerance": {"rtol": 0.05, "atol": 0.02}}
    write_run(out, RECIPE, cfg, data_hash(X.reset_index()), m, log, errors, warnings_)
    best = max(sil.values())
    L = [f"# Clusters of `{ent}`", "", f"{len(X):,} entities · {Z.shape[1]} features (scaled) · first two principal components explain {m['pca_var_2']:.0%}", "",
         "| k | " + " | ".join(str(kk) for kk in sil) + " |", "| --- | " + " | ".join("---" for _ in sil) + " |",
         "| silhouette | " + " | ".join(f"{v:.3f}" for v in sil.values()) + " |", "",
         f"Chosen k = **{k}**. Best silhouette {best:.2f} — " + ("strong structure." if best > 0.5 else "moderate structure." if best > 0.25 else
                                                              "**weak structure**: segments overlap; judge them by actionability, not by the score."), "",
         "## Profiles (mean feature values; ↑/↓ = most distinctive vs average)", "", "| Cluster | n | Distinctive features |", "| --- | --- | --- |"]
    L += [f"| {cl} | {int(prof.loc[cl, 'n'])} | {desc[cl]} |" for cl in prof.index]
    L += ["", "## How to read this", "",
          "- Always scale features first; otherwise the largest-scale feature (revenue) decides the clusters.",
          "- Silhouette 0.25–0.5 is moderate, < 0.25 weak. Business data often has weak natural clusters — segments can still be useful.",
          "- A segment is good if it is **distinct, large enough, stable and actionable** (you would treat it differently).", "",
          "Files: `assignments.csv`, `profiles.csv`, `metrics.json`."]
    (out / "narrative.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:20]))
    return out
