"""rcp_outliers: find extreme values with several methods and show how each treatment changes the answer.

Navigator node N-DESC-OUTLIER. Roles: target (numeric, required), id (optional), group (optional).
Params:
  unit: column to aggregate to first (e.g. basket_id), with agg: sum|mean  (default: none = row level)
  iqr_k: [1.5, 3]          Tukey fences
  z: 3                     plain z-score threshold
  robust_z: 3.5            modified z-score (median / MAD) threshold
  log_scale: auto          use log for plots when skewed and positive
  isolation_forest: {columns: [...], contamination: 0.01}   optional multivariate scan
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, fmt, output_dir, read_dataset, schema_check, write_run

RECIPE = "rcp_outliers"
SCHEMA = {"target": {"required": True, "kind": "numeric"}, "id": {"kind": "id"}, "group": {"kind": "category"}}


def _summ(x):
    x = pd.Series(x, dtype=float)
    return {"n": int(len(x)), "mean": x.mean(), "median": x.median(), "sd": x.std(), "skew": x.skew(),
            "p99": x.quantile(0.99), "max": x.max()}


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
    before = len(df)
    df = df.dropna(subset=[y])
    log.add(f"drop missing {y}", before, len(df))
    unit = prm.get("unit")
    if unit:
        before = len(df)
        df = df.groupby(unit, as_index=False)[y].agg(prm.get("agg", "sum"))
        log.add(f"aggregate to {unit} ({prm.get('agg', 'sum')})", before, len(df), "one row per unit")
        idc = unit
    else:
        idc = c.get("id")
    x = df[y].astype(float)
    q1, q3 = x.quantile([0.25, 0.75])
    iqr = q3 - q1
    mad = stats.median_abs_deviation(x)
    flags = pd.DataFrame(index=df.index)
    ks = prm.get("iqr_k", [1.5, 3])
    for k in ks:
        flags[f"iqr_{k}"] = (x < q1 - k * iqr) | (x > q3 + k * iqr)
    zt = prm.get("z", 3)
    flags[f"z_{zt}"] = ((x - x.mean()) / x.std()).abs() > zt
    rz = prm.get("robust_z", 3.5)
    mz = 0.6745 * (x - x.median()) / mad if mad > 0 else pd.Series(0.0, index=x.index)
    flags[f"robust_z_{rz}"] = mz.abs() > rz
    iso = prm.get("isolation_forest")
    if iso:
        from sklearn.ensemble import IsolationForest
        cols = iso["columns"]
        X = df[cols].astype(float).fillna(df[cols].median())
        flags["isolation_forest"] = IsolationForest(contamination=iso.get("contamination", 0.01), random_state=0).fit_predict(X) == -1
    counts = flags.sum().astype(int).to_dict()
    fl = df.join(flags)
    fl["robust_z"] = mz.round(2)
    fl[flags.any(axis=1)].sort_values(y, ascending=False).to_csv(out_path := output_dir(cfg, RECIPE) / "flagged.csv", index=False)
    out = out_path.parent

    # treatment comparison
    treat = {"keep all": _summ(x),
             "cap at P99": _summ(x.clip(upper=x.quantile(0.99))),
             "winsorise P1–P99": _summ(x.clip(x.quantile(0.01), x.quantile(0.99))),
             f"exclude robust z > {rz}": _summ(x[~flags[f"robust_z_{rz}"]]),
             "trimmed mean 10%": {**_summ(x), "mean": stats.trim_mean(x, 0.1)}}
    if (x > 0).all():
        lx = np.log(x)
        treat["log scale (geometric mean)"] = {**_summ(x), "mean": float(np.exp(lx.mean())), "skew": float(lx.skew())}
    tdf = pd.DataFrame(treat).T
    tdf.to_csv(out / "treatment_comparison.csv")

    # plots
    use_log = prm.get("log_scale", "auto")
    logp = (x > 0).all() and (use_log is True or (use_log == "auto" and x.skew() > 2))
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.4))
    ax[0].boxplot(x, vert=False, whis=1.5)
    ax[0].set_title(f"{y}: box plot (whiskers = 1.5 × IQR)")
    if logp:
        ax[0].set_xscale("log")
    ax[1].hist(np.log10(x) if logp else x, bins=60, color="#3b6ea5")
    ax[1].set_title(f"{y}: histogram" + (" (log10 scale)" if logp else ""))
    for k in ks:
        ub = q3 + k * iqr
        if ub > 0:
            ax[1].axvline(np.log10(ub) if logp else ub, color="#b5651d", ls="--", lw=1)
    plt.tight_layout()
    plt.savefig(out / "outliers.png", dpi=120)
    plt.close()

    metrics = {"n": int(len(x)), "q1": q1, "q3": q3, "iqr": iqr, "mad": mad, "mean": x.mean(), "median": x.median(),
               "sd": x.std(), "skew": x.skew(), "flag_counts": counts, "treatments": tdf.round(6).to_dict(orient="index")}
    write_run(out, RECIPE, cfg, data_hash(df), metrics, log, errors, warnings)
    L = [f"# Outlier scan: `{y}`" + (f" per `{unit}`" if unit else ""), "",
         f"**n = {len(x):,}** · mean {fmt(x.mean())} · median {fmt(x.median())} · SD {fmt(x.std())} · skew {x.skew():.2f} · "
         f"IQR {fmt(iqr)} (Q1 {fmt(q1)}, Q3 {fmt(q3)}) · MAD {fmt(mad)}", "",
         "## How many values each rule flags", "", "| Rule | Flagged | Threshold |", "| --- | --- | --- |"]
    for k in ks:
        L.append(f"| Tukey fence k = {k} | {counts[f'iqr_{k}']:,} | > {fmt(q3 + k * iqr)} or < {fmt(q1 - k * iqr)} |")
    L.append(f"| Plain z-score > {zt} | {counts[f'z_{zt}']:,} | uses mean and SD (both distorted by the outliers) |")
    L.append(f"| Robust z-score > {rz} | {counts[f'robust_z_{rz}']:,} | uses median and MAD |")
    if iso:
        L.append(f"| Isolation Forest | {counts['isolation_forest']:,} | contamination {iso.get('contamination', 0.01)} on {', '.join(iso['columns'])} |")
    L += ["", "## How each treatment changes the answer", "", "| Treatment | n | Mean | Median | SD | Skew |", "| --- | --- | --- | --- | --- | --- |"]
    for k, v in treat.items():
        L.append(f"| {k} | {v['n']:,} | {fmt(v['mean'])} | {fmt(v['median'])} | {fmt(v['sd'])} | {v['skew']:.2f} |")
    L += ["", "## How to read this", "",
          "- A flag is a question, not a verdict: **error** (fix or quarantine), **genuine extreme** (keep; maybe model separately), or **signal** (fraud, abuse — investigate).",
          "- On skewed data the plain z-score under-flags (the SD is inflated by the very values you are looking for) and Tukey's 1.5 × IQR over-flags. Prefer the robust z-score and look at the plot.",
          "- Report the treatment you chose and how much it moved the result.", "",
          "Files: `flagged.csv`, `treatment_comparison.csv`, `outliers.png`, `metrics.json`, `row_accounting.md`."]
    (out / "narrative.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:16]))
    return out
