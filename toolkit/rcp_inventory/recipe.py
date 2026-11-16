"""rcp_inventory: ABC/XYZ classification and safety stock / reorder points at chosen service levels.

Navigator node N-OPT-INVENTORY. Roles: item (required), time (required), target (units, required), value (revenue, optional).
Params: lead_time 2 (periods) · service_levels [0.90, 0.95, 0.99] · abc [0.8, 0.95] · xyz [0.5, 1.0] (CV cut-offs) · top_n 15 ·
  newsvendor: {price, cost, salvage} (optional; single-period order quantity from the empirical demand distribution)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, output_dir, read_dataset, schema_check, write_run

RECIPE = "rcp_inventory"
SCHEMA = {"item": {"required": True}, "time": {"required": True}, "target": {"required": True, "kind": "numeric"}, "value": {"required": False}}


def run(cfg: dict):
    log = RowLog()
    df = read_dataset(cfg)
    log.add("load", len(df), len(df), cfg["dataset"]["path"])
    errors, warnings_ = schema_check(df, cfg, SCHEMA)
    if errors:
        raise SchemaError("\n".join(errors))
    df = apply_filters(df, cfg, log)
    c, prm = cfg["columns"], cfg.get("params", {}) or {}
    it, t, y, v = c["item"], c["time"], c["target"], c.get("value")
    d = df.groupby([it, t])[y].sum().unstack(fill_value=0)
    log.add("item × period demand matrix", len(df), d.size)
    mu, sd = d.mean(axis=1), d.std(axis=1, ddof=1)
    cv = (sd / mu.replace(0, np.nan)).fillna(np.inf)
    val = df.groupby(it)[v].sum() if v else (mu * len(d.columns))
    val = val.reindex(d.index).fillna(0).sort_values(ascending=False)
    a_cut, b_cut = prm.get("abc", [0.8, 0.95])
    cum = val.cumsum() / val.sum()
    abc = pd.Series(np.where(cum <= a_cut, "A", np.where(cum <= b_cut, "B", "C")), index=val.index)
    x_cut, y_cut = prm.get("xyz", [0.5, 1.0])
    xyz = pd.Series(np.where(cv <= x_cut, "X", np.where(cv <= y_cut, "Y", "Z")), index=cv.index).reindex(val.index)
    L_ = float(prm.get("lead_time", 2))
    sls = [float(s) for s in prm.get("service_levels", [0.9, 0.95, 0.99])]
    tab = pd.DataFrame({"abc": abc, "xyz": xyz, "mean": mu.reindex(val.index), "sd": sd.reindex(val.index), "cv": cv.reindex(val.index),
                        "dispersion": (sd ** 2 / mu.replace(0, np.nan)).reindex(val.index)})
    for s_ in sls:
        z = stats.norm.ppf(s_)
        tab[f"ss_{int(round(s_ * 1000))}"] = np.ceil(z * tab["sd"] * np.sqrt(L_))
        tab[f"rop_{int(round(s_ * 1000))}"] = np.ceil(tab["mean"] * L_ + z * tab["sd"] * np.sqrt(L_))
    tab["ss_poisson_950"] = np.ceil(stats.norm.ppf(0.95) * np.sqrt(tab["mean"]) * np.sqrt(L_))
    out = output_dir(cfg, RECIPE)
    tab.to_csv(out / "inventory_policy.csv")
    ct = pd.crosstab(tab.abc, tab.xyz)
    nv = prm.get("newsvendor")
    nvres = None
    if nv:
        p_, c_, s_ = float(nv["price"]), float(nv["cost"]), float(nv.get("salvage", 0))
        crit = (p_ - c_) / (p_ - s_)
        allv = d.values.ravel() if d.shape[0] == 1 else d.sum(axis=0).values
        nvres = {"critical_ratio": crit, "order_qty": float(np.quantile(allv, crit)), "mean_demand": float(allv.mean())}
    top = tab.head(int(prm.get("top_n", 15)))
    m = {"items": int(len(tab)), "abc_counts": tab.abc.value_counts().to_dict(), "abc_xyz": ct.to_dict(),
         "lead_time": L_, "service_levels": sls, "total_ss_by_level": {str(s_): float(tab[f"ss_{int(round(s_ * 1000))}"].sum()) for s_ in sls},
         "newsvendor": nvres}
    write_run(out, RECIPE, cfg, data_hash(d.reset_index()), m, log, errors, warnings_)
    keys = [int(round(s_ * 1000)) for s_ in sls]
    L = [f"# Inventory policy: `{y}` per `{it}`", "", f"{len(tab)} items · lead time {L_:g} periods · safety stock = z × σ × √L (normal approximation)", "",
         "## ABC (value) × XYZ (variability)", "", "| | " + " | ".join(ct.columns) + " |", "| --- | " + " | ".join("---" for _ in ct.columns) + " |"]
    L += [f"| {r} | " + " | ".join(str(int(ct.loc[r, col])) for col in ct.columns) + " |" for r in ct.index]
    L += ["", f"## Top {len(top)} items by value", "", "| Item | ABC/XYZ | Mean | SD | Var/mean | " + " | ".join(f"SS {k / 10:g}%" for k in keys) + " | SS 95% if Poisson |",
          "| --- | --- | --- | --- | --- | " + " | ".join("---" for _ in keys) + " | --- |"]
    for i, r in top.iterrows():
        L.append(f"| {i} | {r.abc}{r.xyz} | {r['mean']:.1f} | {r['sd']:.1f} | {r.dispersion:.1f} | " + " | ".join(f"{r[f'ss_{k}']:.0f}" for k in keys) + f" | {r.ss_poisson_950:.0f} |")
    L += ["", "Total safety stock (units): " + " · ".join(f"{s_:.0%}: {m['total_ss_by_level'][str(s_)]:,.0f}" for s_ in sls)]
    if nvres:
        L += ["", f"## Newsvendor", "", f"Critical ratio (p − c) ÷ (p − s) = {nvres['critical_ratio']:.3f} → order the {nvres['critical_ratio']:.0%} quantile of demand: **{nvres['order_qty']:.0f}** (mean {nvres['mean_demand']:.1f})."]
    L += ["", "## How to read this", "",
          "- Safety stock grows steeply with service level: the last few percentage points cost the most stock.",
          "- Use the real demand variability — a Poisson assumption (variance = mean) under-states it for over-dispersed demand.",
          "- AX items: tight, automated replenishment. CZ items: question whether to stock them at all (or make-to-order).",
          "- Censored demand (stock-outs) makes observed variability and means too low (L7.5).", "",
          "Files: `inventory_policy.csv`, `metrics.json`."]
    (out / "narrative.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:20]))
    return out
