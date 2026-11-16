"""rcp_profile: profile any table and flag data-quality issues in plain English.

Roles (all optional): id, date, target, group. Params: max_categories (default 15), plots (default true).
Outputs: profile.csv, numeric_summary.csv, categorical_top.csv, quality_flags.csv, plots/, narrative.md
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, fmt, output_dir, read_dataset, schema_check, write_run

RECIPE = "rcp_profile"
SCHEMA = {"id": {"kind": "id"}, "date": {"kind": "date"}, "target": {"kind": "any"}, "group": {"kind": "category"}}


def run(cfg: dict):
    log = RowLog()
    df = read_dataset(cfg)
    log.add("load", len(df), len(df), cfg["dataset"]["path"])
    errors, warnings = schema_check(df, cfg, SCHEMA)
    if errors:
        raise SchemaError("\n".join(errors))
    df = apply_filters(df, cfg, log)
    out = output_dir(cfg, RECIPE)
    prm = cfg["params"]
    maxcat = int(prm.get("max_categories", 15))
    cols = cfg["columns"]

    rows, num_rows, cat_rows, flags = [], [], [], []
    n = len(df)
    for c in df.columns:
        s = df[c]
        r = {"column": c, "dtype": str(s.dtype), "non_null": int(s.notna().sum()), "null_pct": round(100 * s.isna().mean(), 2),
             "unique": int(s.nunique(dropna=True))}
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            x = s.dropna().astype(float)
            if len(x):
                q = x.quantile([0.01, 0.25, 0.5, 0.75, 0.99])
                iqr = q[0.75] - q[0.25]
                nr = {"column": c, "mean": x.mean(), "sd": x.std(), "min": x.min(), "p01": q[0.01], "p25": q[0.25],
                      "median": q[0.5], "p75": q[0.75], "p99": q[0.99], "max": x.max(), "skew": x.skew(),
                      "kurtosis": x.kurt(), "cv": x.std() / x.mean() if x.mean() else np.nan,
                      "n_negative": int((x < 0).sum()), "n_zero": int((x == 0).sum()),
                      "n_iqr_outliers": int(((x < q[0.25] - 3 * iqr) | (x > q[0.75] + 3 * iqr)).sum()) if iqr > 0 else 0}
                num_rows.append(nr)
                if x.max() > 0 and q[0.99] > 0 and x.max() / q[0.99] > 20:
                    flags.append((c, "extreme maximum", f"max {fmt(x.max())} is {x.max() / q[0.99]:,.0f}x the 99th percentile — unit error or genuine extreme?"))
                if (x < 0).any():
                    flags.append((c, "negative values", f"{(x < 0).sum():,} negative values — valid (returns, refunds) or entry errors?"))
                if abs(nr["skew"]) > 2:
                    flags.append((c, "heavy skew", f"skewness {nr['skew']:.1f}: prefer median/IQR, consider a log scale"))
        elif s.nunique(dropna=True) <= max(maxcat, 2) or pd.api.types.is_bool_dtype(s) or s.dtype == object or str(s.dtype) in ("str", "string", "category"):
            vc = s.value_counts(dropna=True).head(maxcat)
            for v, k in vc.items():
                cat_rows.append({"column": c, "value": v, "count": int(k), "pct": round(100 * k / max(n, 1), 2)})
            if s.nunique(dropna=True) > 0.95 * n and n > 100:
                r["note"] = "identifier-like"
        if r["null_pct"] > 0:
            flags.append((c, "missing values", f"{r['null_pct']}% missing — check whether missingness depends on other fields (MCAR/MAR/MNAR)"))
        if r["unique"] == 1:
            flags.append((c, "constant", "only one value — no information"))
        rows.append(r)

    dup_rows = int(df.duplicated().sum())
    if dup_rows:
        flags.append(("<all columns>", "duplicate rows", f"{dup_rows:,} fully duplicated rows"))
    if cols.get("id") in df.columns:
        d = int(df[cols["id"]].duplicated().sum())
        if d:
            flags.append((cols["id"], "duplicate ids", f"{d:,} repeated ids — duplicates or wrong grain"))

    prof = pd.DataFrame(rows)
    nums = pd.DataFrame(num_rows)
    cats = pd.DataFrame(cat_rows)
    order = {"duplicate rows": 0, "duplicate ids": 1, "extreme maximum": 2, "negative values": 3, "missing values": 4, "constant": 5, "heavy skew": 6}
    fl = pd.DataFrame(flags, columns=["column", "issue", "detail"])
    fl = fl.assign(_o=fl.issue.map(order)).sort_values("_o", kind="stable").drop(columns="_o").reset_index(drop=True)
    prof.to_csv(out / "profile.csv", index=False)
    nums.round(4).to_csv(out / "numeric_summary.csv", index=False)
    cats.to_csv(out / "categorical_top.csv", index=False)
    fl.to_csv(out / "quality_flags.csv", index=False)

    if prm.get("plots", True):
        pdir = out / "plots"
        pdir.mkdir(exist_ok=True)
        miss = prof.set_index("column").null_pct
        if miss.gt(0).any():
            ax = miss[miss > 0].sort_values().plot.barh(figsize=(7, max(2, 0.3 * miss.gt(0).sum())), color="#3b6ea5")
            ax.set_xlabel("% missing")
            ax.set_title("Missing values by column")
            plt.tight_layout()
            plt.savefig(pdir / "missing.png", dpi=110)
            plt.close()
        tgt = cols.get("target")
        for c in ([tgt] if tgt in df.columns else []) + [r["column"] for r in num_rows[:6] if r["column"] != tgt]:
            x = df[c].dropna().astype(float)
            if not len(x):
                continue
            fig, ax = plt.subplots(1, 2, figsize=(9, 3))
            ax[0].hist(x.clip(x.quantile(0.005), x.quantile(0.995)), bins=50, color="#3b6ea5")
            ax[0].set_title(f"{c}: histogram (0.5-99.5% range)")
            xs = np.sort(x.values)
            ax[1].plot(xs, np.arange(1, len(xs) + 1) / len(xs), color="#b5651d")
            ax[1].set_title(f"{c}: ECDF")
            if (x > 0).all() and x.skew() > 2:
                ax[1].set_xscale("log")
            plt.tight_layout()
            plt.savefig(pdir / f"dist_{c}.png", dpi=110)
            plt.close()

    metrics = {"rows": n, "columns": int(df.shape[1]), "duplicate_rows": dup_rows,
               "null_pct": prof.set_index("column").null_pct.to_dict(),
               "numeric_means": {r["column"]: r["mean"] for r in num_rows}, "n_flags": len(fl)}
    write_run(out, RECIPE, cfg, data_hash(df), metrics, log, errors, warnings)

    top = fl.head(12)
    narr = [f"# Data profile: {cfg['dataset'].get('name', 'dataset')}", "",
            f"**{n:,} rows × {df.shape[1]} columns** after filters. {dup_rows:,} fully duplicated rows.", "",
            "## What needs your attention", ""]
    narr += [f"- **{r.column}** — {r.issue}: {r.detail}" for r in top.itertuples()] or ["- No issues flagged."]
    if len(fl) > len(top):
        narr.append(f"- … {len(fl) - len(top)} more in `quality_flags.csv`.")
    narr += ["", "## How to read this", "",
             "- Flags are prompts for investigation, not verdicts. A negative quantity may be a valid return; a missing value may be meaningful.",
             "- Decide a rule for each issue, write it down, and count the rows it affects before changing anything.",
             "", "Files: `profile.csv`, `numeric_summary.csv`, `categorical_top.csv`, `quality_flags.csv`, `plots/`, `schema_report.md`, `row_accounting.md`."]
    (out / "narrative.md").write_text("\n".join(narr) + "\n")
    print("\n".join(narr[:14]))
    return out
