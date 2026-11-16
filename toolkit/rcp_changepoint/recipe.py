"""rcp_changepoint: detect level shifts in a series (optionally one unit's share of the total) with binary segmentation and CUSUM.

Navigator node N-FCST-BREAK. Roles: time (required), target (required), group (optional).
Params:
  unit: S017            analyse this group value; with share_of_total: true the series is unit ÷ (all other units)
  share_of_total: true  removes common seasonality before looking for unit-specific breaks
  max_breaks: 2 · min_segment: 8 · penalty: 3.0 (× log n × variance, BIC-style) for adding a break
  cusum: {baseline_periods: 40, k: 0.5, h: 8}
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, output_dir, read_dataset, schema_check, write_run

RECIPE = "rcp_changepoint"
SCHEMA = {"time": {"required": True}, "target": {"required": True, "kind": "numeric"}, "group": {"required": False}}


def sse(x):
    return float(((x - x.mean()) ** 2).sum()) if len(x) else 0.0


def best_split(x, lo, hi, minseg):
    best, bk = np.inf, None
    for k in range(lo + minseg, hi - minseg + 1):
        v = sse(x[lo:k]) + sse(x[k:hi])
        if v < best:
            best, bk = v, k
    return bk, best


def run(cfg: dict):
    log = RowLog()
    df = read_dataset(cfg)
    log.add("load", len(df), len(df), cfg["dataset"]["path"])
    errors, warnings_ = schema_check(df, cfg, SCHEMA)
    if errors:
        raise SchemaError("\n".join(errors))
    df = apply_filters(df, cfg, log)
    c, prm = cfg["columns"], cfg.get("params", {}) or {}
    t, y, g = c["time"], c["target"], c.get("group")
    unit = prm.get("unit")
    if g and unit is not None:
        if unit not in set(df[g]):
            raise SchemaError(f"unit `{unit}` not found in `{g}`.")
        own = df[df[g] == unit].groupby(t)[y].sum()
        if prm.get("share_of_total", True):
            other = df[df[g] != unit].groupby(t)[y].sum()
            s = (own / other).dropna()
            label = f"{unit} share of other units' {y}"
        else:
            s, label = own, f"{unit} {y}"
    else:
        s, label = df.groupby(t)[y].sum(), f"total {y}"
    s = s.sort_index()
    x, tv = s.values.astype(float), s.index.values
    n = len(x)
    minseg, maxb, pen = int(prm.get("min_segment", 8)), int(prm.get("max_breaks", 2)), float(prm.get("penalty", 3.0))
    sigma2 = np.var(np.diff(x)) / 2 or 1e-12
    segs, breaks = [(0, n)], []
    for _ in range(maxb):
        cands = []
        for lo, hi in segs:
            if hi - lo >= 2 * minseg:
                k, v = best_split(x, lo, hi, minseg)
                if k is not None:
                    cands.append((sse(x[lo:hi]) - v, k, lo, hi))
        if not cands:
            break
        gain, k, lo, hi = max(cands)
        if gain < pen * np.log(n) * sigma2:
            break
        breaks.append(k)
        segs.remove((lo, hi))
        segs += [(lo, k), (k, hi)]
    breaks.sort()
    bounds = [0] + breaks + [n]
    levels = [{"from": tv[bounds[i]].item() if hasattr(tv[bounds[i]], "item") else tv[bounds[i]],
               "to": tv[bounds[i + 1] - 1].item() if hasattr(tv[bounds[i + 1] - 1], "item") else tv[bounds[i + 1] - 1],
               "mean": float(x[bounds[i]:bounds[i + 1]].mean())} for i in range(len(bounds) - 1)]
    cu = prm.get("cusum", {}) or {}
    nb, kk, hh = int(cu.get("baseline_periods", min(40, n // 2))), float(cu.get("k", 0.5)), float(cu.get("h", 8))
    mu0, sd0 = x[:nb].mean(), x[:nb].std(ddof=1) or 1e-12
    lo_c = np.zeros(n)
    hi_c = np.zeros(n)
    for i in range(1, n):
        z = (x[i] - mu0) / sd0
        lo_c[i] = min(0, lo_c[i - 1] + z + kk)
        hi_c[i] = max(0, hi_c[i - 1] + z - kk)
    alarm_idx = next((i for i in range(nb, n) if lo_c[i] < -hh or hi_c[i] > hh), None)
    alarm = tv[alarm_idx] if alarm_idx is not None else None
    out = output_dir(cfg, RECIPE)
    pd.DataFrame({"period": tv, "value": x, "cusum_low": lo_c, "cusum_high": hi_c}).to_csv(out / "series.csv", index=False)
    fig, ax = plt.subplots(figsize=(9, 3.4))
    ax.plot(tv, x, lw=1, color="black")
    for lv in levels:
        ax.hlines(lv["mean"], lv["from"], lv["to"], color="red")
    for b in breaks:
        ax.axvline(tv[b], color="red", ls=":")
    ax.set_title(label)
    plt.tight_layout()
    plt.savefig(out / "changepoints.png", dpi=110)
    plt.close()
    to_py = lambda v: v.item() if hasattr(v, "item") else v
    metrics = {"series": label, "n": n, "breaks": [to_py(tv[b]) for b in breaks], "levels": levels,
               "cusum_alarm": to_py(alarm) if alarm is not None else None}
    write_run(out, RECIPE, cfg, data_hash(s.to_frame()), metrics, log, errors, warnings_)
    L = [f"# Change-points: {label}", "", f"{n} periods. Binary segmentation (min segment {minseg}, penalty {pen} × log n × noise variance).", ""]
    if breaks:
        L += ["| Segment | From | To | Mean | Change vs previous |", "| --- | --- | --- | --- | --- |"]
        for i, lv in enumerate(levels):
            chg = "" if i == 0 else f"{lv['mean'] / levels[i - 1]['mean'] - 1:+.1%}"
            L.append(f"| {i + 1} | {lv['from']} | {lv['to']} | {lv['mean']:.4g} | {chg} |")
    else:
        L.append("No break exceeds the penalty — no evidence of a level shift.")
    L += ["", f"CUSUM (baseline first {nb} periods, k = {kk}, h = {hh}): " + (f"**first alarm at {alarm}**." if alarm is not None else "no alarm.")]
    L += ["", "## How to read this", "",
          "- A break is a sustained change in level; one-off spikes are outliers, not breaks.",
          "- Analysing a unit's **share of the total** removes seasonality and chain-wide shocks, isolating unit-specific breaks.",
          "- Binary segmentation finds *where*; CUSUM shows *how quickly a monitor would have noticed* (lower h = faster but more false alarms).",
          "- Always find the business cause (refit, competitor opening, data feed change) before modelling across a break.", "",
          "Files: `series.csv`, `changepoints.png`, `metrics.json`."]
    (out / "narrative.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:16]))
    return out
