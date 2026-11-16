"""rcp_elasticity: own-price elasticity from store-SKU-week data with fixed effects and promotion controls; price simulations.

Navigator node N-REG-LOGLOG. Roles: units, price, ref_price (list price), item, store, time (all required).
Params: controls [promo_flag, display_flag] · family poisson | loglog · cost_ratio (unit cost ÷ list price) for margin simulations ·
  price_changes [-0.10, -0.05, 0.05, 0.10] · exclude_stockouts: stockout_flag
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, output_dir, read_dataset, schema_check, write_run

warnings.filterwarnings("ignore")
RECIPE = "rcp_elasticity"
SCHEMA = {k: {"required": True} for k in ("units", "price", "ref_price", "item", "store", "time")}


def run(cfg: dict):
    log = RowLog()
    df = read_dataset(cfg)
    log.add("load", len(df), len(df), cfg["dataset"]["path"])
    errors, warnings_ = schema_check(df, cfg, SCHEMA)
    if errors:
        raise SchemaError("\n".join(errors))
    df = apply_filters(df, cfg, log)
    c, prm = cfg["columns"], cfg.get("params", {}) or {}
    so = prm.get("exclude_stockouts")
    if so:
        b = len(df)
        df = df[~df[so].astype(bool)]
        log.add(f"drop {so} rows", b, len(df), "censored demand")
    df = df.copy()
    df["_lp"] = np.log(df[c["price"]] / df[c["ref_price"]])
    ctr = [x for x in (prm.get("controls") or []) if x in df.columns]
    for x in ctr:
        df[x] = df[x].astype(float)
    fe = f"C({c['item']}) + C({c['store']}) + C({c['time']})"
    rhs = " + ".join(["_lp"] + ctr + [fe])
    fam = prm.get("family", "poisson")
    if fam == "poisson":
        m = smf.glm(f"{c['units']} ~ {rhs}", df, family=sm.families.Poisson()).fit(cov_type="HC1")
    else:
        d2 = df[df[c["units"]] > 0].copy()
        d2["_lu"] = np.log(d2[c["units"]])
        m = smf.ols(f"_lu ~ {rhs}", d2).fit(cov_type="HC1")
    e, se = float(m.params["_lp"]), float(m.bse["_lp"])
    m0 = smf.glm(f"{c['units']} ~ _lp + {fe}", df, family=sm.families.Poisson()).fit() if ctr and fam == "poisson" else None
    cr = prm.get("cost_ratio")
    sims = []
    for dp in prm.get("price_changes", [-0.10, -0.05, 0.05, 0.10]):
        q = (1 + dp) ** e
        row = {"price_change": dp, "units_change": q - 1, "revenue_change": q * (1 + dp) - 1}
        if cr is not None:
            row["margin_change"] = q * ((1 + dp) - cr) / (1 - cr) - 1
        sims.append(row)
    sim = pd.DataFrame(sims)
    out = output_dir(cfg, RECIPE)
    sim.to_csv(out / "price_simulation.csv", index=False)
    met = {"elasticity": e, "se": se, "ci": [e - 1.96 * se, e + 1.96 * se], "n": int(m.nobs), "family": fam,
           "elasticity_without_controls": float(m0.params["_lp"]) if m0 is not None else None,
           "promo_effect": {x: float(np.exp(m.params[x]) - 1) for x in ctr}, "_tolerance": {"rtol": 0.01, "atol": 0.005}}
    if cr is not None and e < -1:
        met["optimal_price_over_cost"] = e / (1 + e)
        met["optimal_vs_list"] = e / (1 + e) * cr - 1
    write_run(out, RECIPE, cfg, data_hash(df[[c["units"], "_lp"]]), met, log, errors, warnings_)
    L = [f"# Price elasticity of `{c['units']}`", "", f"{int(m.nobs):,} store-item-weeks · model: {fam} with item, store and week fixed effects" + (f" + {', '.join(ctr)}" if ctr else ""), "",
         f"**Elasticity {e:.2f}** (95% CI {e - 1.96 * se:.2f} to {e + 1.96 * se:.2f}): a 1% price rise changes units by {e:.2f}%. " +
         ("Elastic (|e| > 1): price cuts raise revenue." if e < -1 else "Inelastic (|e| < 1): price rises raise revenue and margin.")]
    if m0 is not None:
        L += ["", f"Without promotion/display controls: {met['elasticity_without_controls']:.2f} — promotions move price and volume together, so omitting them biases the estimate."]
    if ctr:
        L += ["", "Promotion controls: " + ", ".join(f"{k} {v:+.0%}" for k, v in met["promo_effect"].items())]
    L += ["", "| Price change | Units | Revenue" + (" | Margin |" if cr is not None else " |"), "| --- | --- | ---" + (" | --- |" if cr is not None else " |")]
    L += [f"| {r.price_change:+.0%} | {r.units_change:+.1%} | {r.revenue_change:+.1%}" + (f" | {r.margin_change:+.1%} |" if cr is not None else " |") for r in sim.itertuples()]
    if "optimal_price_over_cost" in met:
        L += ["", f"Constant-elasticity optimal price = cost × e/(1+e) = **{met['optimal_price_over_cost']:.2f} × cost** ({met['optimal_vs_list']:+.0%} vs list) — an upper reference, not a recommendation (competition, image, cross-effects)."]
    L += ["", "## How to read this", "", "- Fixed effects compare each item-store with itself over weeks; promotion controls separate promo lift from the price effect.",
          "- Exclude stock-out weeks (censored demand). Elasticities are local — extrapolate cautiously.", "", "Files: `price_simulation.csv`, `metrics.json`."]
    (out / "narrative.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:20]))
    return out
