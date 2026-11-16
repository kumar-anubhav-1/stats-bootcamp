"""rcp_power: sample size, minimum detectable effect and power curves — planned from your own data.

Navigator node N-EXP-POWER. Roles: target (required), cluster (optional), group (optional; restrict SD to the control arm).
Params:
  design: means | proportions | cluster_means          default: proportions if target is 0/1, else means
  baseline: {period_col, pre: [a, b], post: [c, d]}   outcome = post/pre per cluster (as in rcp_two_group_test)
  control_label: e.g. control                           estimate SD/rate from this arm only
  sd_method: pooled_within (with group + control_label): outcome scaled to the control mean, SD pooled within arms
             (use when an earlier test exists — the treatment effect must not inflate the SD)
  effects: [0.05, 0.10, ...]   relative lifts (means) or absolute differences in rate (proportions)
  alpha: 0.05 · power: 0.8 · ratio: 1.0 (n_treatment / n_control) · sides: 2
  icc / cluster_size: for cluster_means when rows within clusters are analysed (design effect)
  n_available: per arm — reports achieved power and MDE for the sample you actually have
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, output_dir, read_dataset, schema_check, write_run

RECIPE = "rcp_power"
SCHEMA = {"target": {"required": True, "kind": "numeric"}, "cluster": {"required": False}, "group": {"required": False}}


def n_means(delta, sd, alpha, power, ratio=1.0, sides=2):
    za, zb = stats.norm.ppf(1 - alpha / sides), stats.norm.ppf(power)
    n_c = (za + zb) ** 2 * sd ** 2 * (1 + 1 / ratio) / delta ** 2
    # small-sample t correction (one iteration)
    df = max(2, n_c * (1 + ratio) - 2)
    ta, tb = stats.t.ppf(1 - alpha / sides, df), stats.t.ppf(power, df)
    return float((ta + tb) ** 2 * sd ** 2 * (1 + 1 / ratio) / delta ** 2)


def n_props(p0, p1, alpha, power, ratio=1.0, sides=2):
    h = abs(2 * np.arcsin(np.sqrt(p1)) - 2 * np.arcsin(np.sqrt(p0)))
    za, zb = stats.norm.ppf(1 - alpha / sides), stats.norm.ppf(power)
    return float((za + zb) ** 2 * (1 + 1 / ratio) / h ** 2)


def power_props(p0, p1, n_c, alpha, ratio=1.0, sides=2):
    h = abs(2 * np.arcsin(np.sqrt(p1)) - 2 * np.arcsin(np.sqrt(p0)))
    return float(stats.norm.cdf(h / np.sqrt((1 + 1 / ratio) / n_c) - stats.norm.ppf(1 - alpha / sides)))


def power_means(delta, sd, n_c, alpha, ratio=1.0, sides=2):
    return float(stats.norm.cdf(abs(delta) / (sd * np.sqrt((1 + 1 / ratio) / n_c)) - stats.norm.ppf(1 - alpha / sides)))


def run(cfg: dict):
    log = RowLog()
    df = read_dataset(cfg)
    log.add("load", len(df), len(df), cfg["dataset"]["path"])
    errors, warnings = schema_check(df, cfg, SCHEMA)
    if errors:
        raise SchemaError("\n".join(errors))
    df = apply_filters(df, cfg, log)
    c, prm = cfg["columns"], cfg.get("params", {}) or {}
    y, cl, gcol = c["target"], c.get("cluster"), c.get("group")
    alpha, pw, ratio, sides = float(prm.get("alpha", 0.05)), float(prm.get("power", 0.8)), float(prm.get("ratio", 1.0)), int(prm.get("sides", 2))
    base = prm.get("baseline")
    if base:
        if not cl:
            raise SchemaError("params.baseline needs a `cluster` role (e.g. store_id).")
        pc = base["period_col"]
        pre = df[df[pc].between(*base["pre"])].groupby(cl)[y].mean()
        post = df[df[pc].between(*base["post"])].groupby(cl)[y].mean()
        x = (post / pre).rename(y).to_frame()
        if gcol:
            x[gcol] = df.groupby(cl)[gcol].first()
        b = len(df)
        df = x.reset_index()
        log.add(f"growth index per {cl}", b, len(df), "post-period mean ÷ own pre-period mean")
    if gcol and prm.get("control_label") is not None and prm.get("sd_method") == "pooled_within":
        cm = df.loc[df[gcol] == prm["control_label"], y].mean()
        df[y] = df[y] / cm
        sds = df.groupby(gcol)[y].var(ddof=1)
        pooled_sd = float(np.sqrt(sds.mean()))
        log.add("scale to control mean; pool SD within arms", len(df), len(df), "relative scale: 1.00 = control average")
    elif gcol and prm.get("control_label") is not None:
        b = len(df)
        df = df[df[gcol] == prm["control_label"]]
        log.add(f"keep control arm ({prm['control_label']})", b, len(df), "variance estimated where no treatment acted")
    vals = df[y].dropna()
    design = prm.get("design") or ("proportions" if set(vals.unique()) <= {0, 1, True, False} else "means")
    out = output_dir(cfg, RECIPE)
    rows = []
    if design == "proportions":
        p0 = float(vals.astype(float).mean())
        effects = prm.get("effects", [0.01, 0.02, 0.03, 0.05])
        for e in effects:
            n_c = n_props(p0, p0 + e, alpha, pw, ratio, sides)
            rows.append({"effect": e, "effect_label": f"+{100 * e:.1f} pp", "n_control": int(np.ceil(n_c)),
                         "n_treatment": int(np.ceil(n_c * ratio)), "n_total": int(np.ceil(n_c) + np.ceil(n_c * ratio))})
        stat = {"baseline_rate": p0}
    else:
        if prm.get("sd_method") == "pooled_within" and gcol:
            mean, sd = 1.0, pooled_sd
        else:
            mean, sd = float(vals.mean()), float(vals.std(ddof=1))
        deff = 1.0
        if design == "cluster_means" and prm.get("icc") is not None:
            deff = 1 + (float(prm.get("cluster_size", 1)) - 1) * float(prm["icc"])
        effects = prm.get("effects", [0.05, 0.10, 0.15, 0.20])
        for e in effects:
            delta = e * mean
            n_c = n_means(delta, sd, alpha, pw, ratio, sides) * deff
            rows.append({"effect": e, "effect_label": f"+{100 * e:.0f}%", "n_control": int(np.ceil(n_c)),
                         "n_treatment": int(np.ceil(n_c * ratio)), "n_total": int(np.ceil(n_c) + np.ceil(n_c * ratio))})
        stat = {"mean": mean, "sd": sd, "cv": sd / mean if mean else None, "design_effect": deff, "n_units_for_sd": int(len(vals))}
    tab = pd.DataFrame(rows)
    tab.to_csv(out / "sample_size.csv", index=False)
    metrics = {"design": design, "alpha": alpha, "power": pw, "ratio": ratio, **stat, "table": tab.set_index("effect_label").to_dict(orient="index")}
    navail = prm.get("n_available")
    if navail:
        n_c = float(navail)
        if design == "proportions":
            ach = {r.effect_label: power_props(p0, p0 + r.effect, n_c, alpha, ratio, sides) for r in tab.itertuples()}
            grid = np.linspace(0.001, 0.3, 3000)
            mde = next((e for e in grid if power_props(p0, p0 + e, n_c, alpha, ratio, sides) >= pw), None)
            mde_txt = f"{100 * mde:.1f} pp" if mde else "n/a"
        else:
            ach = {r.effect_label: power_means(r.effect * mean, sd * np.sqrt(deff), n_c, alpha, ratio, sides) for r in tab.itertuples()}
            mde = (stats.norm.ppf(1 - alpha / sides) + stats.norm.ppf(pw)) * sd * np.sqrt(deff) * np.sqrt((1 + 1 / ratio) / n_c) / mean
            mde_txt = f"{100 * mde:.1f}%"
        metrics.update({"n_available_control": n_c, "achieved_power": ach, "mde_at_n_available": mde})
    # curve
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ns = np.linspace(5, max(tab.n_control.max() * 1.3, 20), 200)
    for r in tab.itertuples():
        if design == "proportions":
            pv = [power_props(p0, p0 + r.effect, n, alpha, ratio, sides) for n in ns]
        else:
            pv = [power_means(r.effect * mean, sd * np.sqrt(deff), n, alpha, ratio, sides) for n in ns]
        ax.plot(ns, pv, label=r.effect_label)
    ax.axhline(pw, color="grey", ls="--")
    ax.set_xlabel("units in control arm")
    ax.set_ylabel("power")
    ax.set_ylim(0, 1)
    ax.legend(title="effect")
    ax.set_title("Power curves")
    plt.tight_layout()
    plt.savefig(out / "power_curve.png", dpi=120)
    plt.close()
    unit = cl or "row"
    L = [f"# Power and sample size for `{y}`", "", f"Design: **{design}** · α = {alpha} ({sides}-sided) · power = {pw:.0%} · ratio treatment:control = {ratio:g} · unit = **{unit}**", ""]
    if design == "proportions":
        L.append(f"Baseline rate (from data): **{100 * p0:.2f}%**.")
    else:
        L.append(f"From data: mean {mean:.3f}, SD {sd:.3f} (CV {sd / mean:.2f}), estimated on {len(vals)} units." + (f" Design effect {deff:.1f}." if deff > 1 else ""))
    L += ["", "| Effect to detect | Control | Treatment | Total |", "| --- | --- | --- | --- |"]
    L += [f"| {r.effect_label} | {r.n_control:,} | {r.n_treatment:,} | {r.n_total:,} |" for r in tab.itertuples()]
    if navail:
        L += ["", f"## With the sample you have ({int(n_c):,} control units)", "", f"Minimum detectable effect at {pw:.0%} power: **{mde_txt}**.", "",
              "| Effect | Achieved power |", "| --- | --- |"] + [f"| {k} | {v:.0%} |" for k, v in ach.items()]
    L += ["", "## How to read this", "",
          "- Halving the effect you want to detect roughly **quadruples** the sample needed.",
          "- Unequal splits (e.g. 80/20) need more units in total than 50/50 for the same power.",
          "- A non-significant result from an under-powered test is *not* evidence of no effect — report the MDE.",
          "- Plan at the unit of randomisation (stores, branches). Rows inside a unit add far less information (design effect).", "",
          "Files: `sample_size.csv`, `power_curve.png`, `metrics.json`."]
    write_run(out, RECIPE, cfg, data_hash(df), metrics, log, errors, warnings)
    (out / "narrative.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:20]))
    return out
