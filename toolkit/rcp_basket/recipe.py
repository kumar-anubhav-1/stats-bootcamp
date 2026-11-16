"""rcp_basket: pairwise association rules (support, confidence, lift) with filters and a triviality flag.

Navigator node N-SEG-BASKET. Roles: basket (required), item (required; e.g. subcategory). Params: min_support 0.01 · min_lift 1.2 ·
top_n 15 · common_share 0.3 (consequents in more than this share of baskets are flagged 'trivial: popular item')
"""
from __future__ import annotations

from collections import Counter

import pandas as pd

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, output_dir, read_dataset, schema_check, write_run

RECIPE = "rcp_basket"
SCHEMA = {"basket": {"required": True}, "item": {"required": True}}


def run(cfg: dict):
    log = RowLog()
    df = read_dataset(cfg)
    log.add("load", len(df), len(df), cfg["dataset"]["path"])
    c, prm = cfg["columns"], cfg.get("params", {}) or {}
    bk, it = c["basket"], c["item"]
    if prm.get("item_map"):  # derive the item column from a lookup table (e.g. sku -> subcategory) before checking the schema
        from toolkit.common.core import ROOT
        mp = pd.concat([pd.read_parquet(ROOT / p) for p in prm["item_map"]["paths"]]).set_index(prm["item_map"]["key"])[prm["item_map"]["value"]]
        df = df.assign(**{it: df[prm["item_map"]["source"]].map(mp)})
    errors, warnings_ = schema_check(df, cfg, SCHEMA)
    if errors:
        raise SchemaError("\n".join(errors))
    df = apply_filters(df, cfg, log)
    df = df.dropna(subset=[it])
    sets = df.groupby(bk)[it].agg(lambda s: sorted(set(s)))
    nb = len(sets)
    log.add("baskets", len(df), nb)
    single = Counter(x for b in sets for x in b)
    pairs = Counter((x, y) for b in sets for i, x in enumerate(b) for y in b[i + 1:])
    ms, ml, cs = float(prm.get("min_support", 0.01)), float(prm.get("min_lift", 1.2)), float(prm.get("common_share", 0.3))
    rows = []
    for (x, y), nxy in pairs.items():
        sup = nxy / nb
        if sup < ms:
            continue
        for A, B in ((x, y), (y, x)):
            conf = nxy / single[A]
            lift = conf / (single[B] / nb)
            rows.append({"antecedent": A, "consequent": B, "support": sup, "confidence": conf, "lift": lift,
                         "consequent_share": single[B] / nb, "trivial": single[B] / nb > cs})
    r = pd.DataFrame(rows)
    if r.empty:
        raise SchemaError("No pair meets min_support; lower it.")
    r = r.assign(_l=r.lift.round(6), _c=r.confidence.round(6)).sort_values(["_l", "support", "_c"], ascending=False, kind="stable").drop(columns=["_l", "_c"])
    out = output_dir(cfg, RECIPE)
    r.to_csv(out / "rules.csv", index=False)
    good = r[(r.lift >= ml)]
    top = good.head(int(prm.get("top_n", 15)))
    m = {"baskets": nb, "items": len(single), "rules_after_support": int(len(r)), "rules_after_lift": int(len(good)),
         "top": top[["antecedent", "consequent", "support", "confidence", "lift"]].round(6).to_dict(orient="records")}
    write_run(out, RECIPE, cfg, data_hash(df[[bk, it]]), m, log, errors, warnings_)
    triv = r[r.trivial].sort_values("confidence", ascending=False).head(3)
    L = [f"# Association rules: `{it}` within `{bk}`", "", f"{nb:,} baskets · {len(single)} items · {len(r):,} rules with support ≥ {ms:.0%} · {len(good):,} with lift ≥ {ml}", "",
         "| Rule | Support | Confidence | Lift |", "| --- | --- | --- | --- |"]
    L += [f"| {x.antecedent} → {x.consequent} | {x.support:.1%} | {x.confidence:.1%} | {x.lift:.2f} |" for x in top.itertuples()]
    if len(triv):
        L += ["", "**High confidence, low insight** (consequent is in > {:.0%} of all baskets):".format(cs), ""]
        L += [f"- {x.antecedent} → {x.consequent}: confidence {x.confidence:.0%}, but lift only {x.lift:.2f}" for x in triv.itertuples()]
    L += ["", "## How to read this", "", "- **Support**: how often the pair occurs. **Confidence**: P(B | A). **Lift**: confidence ÷ P(B) — > 1 means bought together more than chance.",
          "- High confidence alone is misleading when B is popular; rank by lift with a support floor.",
          "- Rules are associations; test placement or bundling changes before rolling out.", "", "Files: `rules.csv`, `metrics.json`."]
    (out / "narrative.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:20]))
    return out
