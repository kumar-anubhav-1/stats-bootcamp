"""rcp_benford: first-digit (Benford) and rounding tests by group, compared with peers.

Navigator node N-ANOM-BENFORD. Roles: target (numeric amount, required), group (e.g. store_id / branch_id, required).
Params: min_n (default 300) groups with fewer positive values are skipped · round_to (default 0.5) last-digit rounding unit
Outputs per group: MAD vs Benford, Nigrini conformity band, chi-square p, share of rounded values, peer z-score of the MAD.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, fmt, output_dir, read_dataset, schema_check, write_run

RECIPE = "rcp_benford"
SCHEMA = {"target": {"required": True, "kind": "numeric"}, "group": {"required": True, "kind": "category"}}
BENFORD = np.log10(1 + 1 / np.arange(1, 10))


def first_digits(x):
    x = np.asarray(x, float)
    x = x[x > 0]
    return (x / 10 ** np.floor(np.log10(x))).astype(int)


def band(mad):
    # Nigrini's first-digit MAD bands (rules of thumb)
    return "close conformity" if mad < 0.006 else "acceptable" if mad < 0.012 else "marginal" if mad < 0.015 else "nonconformity"


def run(cfg: dict):
    log = RowLog()
    df = read_dataset(cfg)
    log.add("load", len(df), len(df), cfg["dataset"]["path"])
    errors, warnings = schema_check(df, cfg, SCHEMA)
    if errors:
        raise SchemaError("\n".join(errors))
    df = apply_filters(df, cfg, log)
    c, prm = cfg["columns"], cfg["params"]
    y, g = c["target"], c["group"]
    b = len(df)
    df = df[df[y] > 0]
    log.add(f"keep positive {y}", b, len(df), "Benford applies to positive amounts")
    unit = float(prm.get("round_to", 0.5))
    min_n = int(prm.get("min_n", 300))
    rows = []
    digits_all = first_digits(df[y])
    span = np.log10(df[y].quantile(0.99) / df[y].quantile(0.01))
    for key, sub in df.groupby(g):
        if len(sub) < min_n:
            continue
        d = first_digits(sub[y])
        obs = np.bincount(d, minlength=10)[1:10]
        p = obs / obs.sum()
        mad = float(np.abs(p - BENFORD).mean())
        chi_p = float(stats.chisquare(obs, BENFORD * obs.sum()).pvalue)
        rounded = float((np.round(sub[y].to_numpy() / unit, 6) % 1 == 0).mean())
        exp_mad = float(np.sqrt(2 / np.pi) * np.mean(np.sqrt(BENFORD * (1 - BENFORD) / obs.sum())))
        rows.append({"group": key, "n": int(obs.sum()), "mad": mad, "expected_mad_if_benford": exp_mad,
                     "excess_mad": mad - exp_mad, "band": band(mad), "chi2_p": chi_p,
                     "digit1_share": p[0], "rounded_share": rounded})
    res = pd.DataFrame(rows)
    if res.empty:
        raise SchemaError(f"No group has at least {min_n} positive values; lower params.min_n.")
    med = res.mad.median()
    em = res.excess_mad.median()
    res["mad_peer_z"] = (res.excess_mad - em) / max(1.4826 * np.median(np.abs(res.excess_mad - em)), 0.002)
    rmed = res.rounded_share.median()
    res["rounded_peer_ratio"] = res.rounded_share / max(rmed, 1e-9)
    res = res.sort_values("mad", ascending=False)
    out = output_dir(cfg, RECIPE)
    res.to_csv(out / "benford_by_group.csv", index=False)
    worst = res.iloc[0]
    wsub = df[df[g] == worst.group]
    wp = np.bincount(first_digits(wsub[y]), minlength=10)[1:10] / len(first_digits(wsub[y]))
    allp = np.bincount(digits_all, minlength=10)[1:10] / len(digits_all)
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    xs = np.arange(1, 10)
    ax.bar(xs - 0.2, wp, width=0.4, color="#b5651d", label=f"{worst.group}")
    ax.bar(xs + 0.2, allp, width=0.4, color="#3b6ea5", label="all groups")
    ax.plot(xs, BENFORD, "ko-", label="Benford")
    ax.set_xticks(xs)
    ax.set_xlabel("first digit")
    ax.legend()
    ax.set_title(f"First digits: most unusual {g} vs all")
    plt.tight_layout()
    plt.savefig(out / "benford.png", dpi=120)
    plt.close()
    metrics = {"groups": int(len(res)), "span_orders_of_magnitude": span, "peer_median_mad": med,
               "by_group": res.set_index("group")[["mad", "excess_mad", "chi2_p", "rounded_share", "mad_peer_z"]].round(6).to_dict(orient="index")}
    write_run(out, RECIPE, cfg, data_hash(df), metrics, log, errors, warnings)
    flagged = res[(res.mad_peer_z > 5) | (res.rounded_peer_ratio > 5)]
    L = [f"# Benford and rounding tests: `{y}` by `{g}`", "",
         f"{len(res)} groups with ≥ {min_n} positive values. Data span ≈ **{span:.1f} orders of magnitude** (P1–P99) — "
         + ("wide enough for Benford comparisons." if span >= 2 else "narrow: the data need not follow Benford even when genuine, so **compare groups with their peers**, not only with the theoretical curve."),
         "", f"Peer median MAD = {med:.4f}.", "",
         "| Group | n | MAD | Expected MAD at this n | Nigrini band | Peer z (excess MAD) | Rounded share | χ² p |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r_ in res.head(10).itertuples():
        L.append(f"| {r_.group} | {r_.n:,} | {r_.mad:.4f} | {r_.expected_mad_if_benford:.4f} | {r_.band} | {r_.mad_peer_z:.1f} | {r_.rounded_share:.1%} | {fmt(r_.chi2_p, 3)} |")
    L += ["", "## Flagged groups", ""]
    L += [f"- **{r_.group}**: MAD {r_.mad:.4f} (peer z {r_.mad_peer_z:.1f}), rounded share {r_.rounded_share:.1%} vs peer median {rmed:.1%}." for r_ in flagged.itertuples()] or ["- None."]
    L += ["", "## How to read this", "",
          "- Benford's law describes leading digits of many natural amounts spanning several orders of magnitude (digit 1 ≈ 30%).",
          "- **A deviation is a reason to look, not proof of fraud.** Prices, caps, thresholds and narrow ranges also break Benford.",
          "- Compare each unit with its **peers** (peer z) and add a **rounding test**: invented numbers are often round.",
          "- Small groups deviate more by chance: the *expected MAD* column shows the deviation a genuine Benford sample of that size would have; peer z uses the excess over it.",
          "- χ² p-values are tiny for large n even for trivial deviations — rank by MAD and peer z instead.", "",
          "Files: `benford_by_group.csv`, `benford.png`, `metrics.json`, `row_accounting.md`."]
    (out / "narrative.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:18]))
    return out
