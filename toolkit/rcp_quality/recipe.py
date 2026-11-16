"""rcp_quality: rule-based data-quality checks, duplicate detection and missing-data diagnosis.

Navigator nodes N-DESC-QUALITY and N-DESC-MISSING. Never changes the source data: flagged rows are
written to a quarantine file, and an optional cleaned copy is written next to the outputs.

Roles (optional): id, target (outcome compared between missing / non-missing rows), date.
Params:
  rules: [{name, flag: "<pandas expression that is TRUE for bad rows>", severity: error|warning, why}]
  missing_by: [columns]          test whether missingness depends on these (chi-square / Mann-Whitney)
  missing_unit: {column: [unit columns]}   optional: also test each column's missingness at the unit where it
                                 goes missing (weather → [region, date]; demographics → [customer_id])
  reconcile: {column, expected_total, tolerance_pct}
  write_clean: false             write a copy without rows failing `error` rules and without duplicate ids
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, fmt, output_dir, read_dataset, schema_check, write_run

RECIPE = "rcp_quality"
SCHEMA = {"id": {"kind": "id"}, "target": {"kind": "any"}, "date": {"kind": "date"}}


def _miss_test(df, col, by):
    m = df[col].isna()
    x = df[by]
    if pd.api.types.is_numeric_dtype(x) and x.nunique() > 10:
        a, b = x[m].dropna(), x[~m].dropna()
        if len(a) < 2 or len(b) < 2:
            return None
        return {"by": by, "test": "Mann-Whitney", "p_value": float(stats.mannwhitneyu(a, b).pvalue),
                "detail": f"median {fmt(a.median())} when missing vs {fmt(b.median())} when present"}
    tab = pd.crosstab(x.fillna("<missing>"), m)
    if tab.shape[0] < 2 or tab.shape[1] < 2:
        return None
    p = float(stats.chi2_contingency(tab)[1])
    rates = m.groupby(x.fillna("<missing>")).mean().sort_values()
    return {"by": by, "test": "chi-square", "p_value": p,
            "detail": f"missing rate from {rates.iloc[0]:.1%} ({rates.index[0]}) to {rates.iloc[-1]:.1%} ({rates.index[-1]})"}


def run(cfg: dict):
    log = RowLog()
    df = read_dataset(cfg)
    log.add("load", len(df), len(df), cfg["dataset"]["path"])
    errors, warnings = schema_check(df, cfg, SCHEMA)
    if errors:
        raise SchemaError("\n".join(errors))
    df = apply_filters(df, cfg, log).reset_index(drop=True)
    c, prm = cfg["columns"], cfg["params"]
    out = output_dir(cfg, RECIPE)
    n = len(df)

    # 1. duplicates
    dup_rows = df.duplicated()
    dup_ids = df[c["id"]].duplicated() if c.get("id") in df.columns else pd.Series(False, index=df.index)
    # 2. rules
    rule_rows, flags = [], pd.DataFrame(index=df.index)
    for r in prm.get("rules", []):
        try:
            f = df.eval(r["flag"], engine="python").fillna(False).astype(bool)
        except Exception as e:
            raise SchemaError(f"Rule `{r['name']}` could not be evaluated: {e}. Rules use the dataset's own column names.")
        flags[r["name"]] = f
        ex = df.loc[f, c["id"]].head(5).tolist() if c.get("id") in df.columns else df.index[f][:5].tolist()
        rule_rows.append({"rule": r["name"], "severity": r.get("severity", "warning"), "rows_flagged": int(f.sum()),
                          "pct": round(100 * f.mean(), 3), "why": r.get("why", ""), "examples": ", ".join(map(str, ex))})
    rules = pd.DataFrame(rule_rows)
    if len(rules):
        rules.to_csv(out / "rule_log.csv", index=False)
    any_flag = flags.any(axis=1) if len(flags.columns) else pd.Series(False, index=df.index)
    q = df[any_flag | dup_ids].copy()
    if len(q):
        q.insert(0, "flags", [", ".join(flags.columns[flags.loc[i]]) + (", duplicate_id" if dup_ids[i] else "") for i in q.index])
        q.to_csv(out / "quarantine.csv", index=False)

    # 3. missing data
    miss_rows, tests = [], []
    tgt = c.get("target")
    for col in df.columns:
        rate = df[col].isna().mean()
        if rate == 0:
            continue
        row = {"column": col, "missing_rows": int(df[col].isna().sum()), "missing_pct": round(100 * rate, 2)}
        if tgt in df.columns and col != tgt and pd.api.types.is_numeric_dtype(df[tgt]):
            m = df[col].isna()
            row["target_mean_missing"] = df.loc[m, tgt].astype(float).mean()
            row["target_mean_present"] = df.loc[~m, tgt].astype(float).mean()
        miss_rows.append(row)
        for by in prm.get("missing_by", []):
            if by != col and by in df.columns:
                t = _miss_test(df, col, by)
                if t:
                    tests.append({"column": col, "level": "row", **t})
        unit = (prm.get("missing_unit") or {}).get(col)
        if unit and all(u in df.columns for u in unit):
            for by in prm.get("missing_by", []):
                if by == col or by not in df.columns:
                    continue
                allmiss = df[col].isna().groupby([df[u] for u in unit]).all().astype(bool)
                g = allmiss.rename("_m").reset_index()
                if by not in unit:
                    g = g.merge(df.groupby(unit)[by].first().reset_index(), on=unit)
                g[col] = np.where(g["_m"].to_numpy(dtype=bool), np.nan, 1.0)
                t = _miss_test(g, col, by)
                if t:
                    tests.append({"column": col, "level": "+".join(unit), **t})
    miss = pd.DataFrame(miss_rows)
    mt = pd.DataFrame(tests)
    if len(miss):
        miss.to_csv(out / "missingness.csv", index=False)
    if len(mt):
        mt.to_csv(out / "missingness_tests.csv", index=False)

    # 4. reconciliation
    rec = None
    if prm.get("reconcile"):
        rc = prm["reconcile"]
        tot = float(df[rc["column"]].sum())
        diff = 100 * (tot / rc["expected_total"] - 1)
        rec = {"column": rc["column"], "observed": tot, "expected": rc["expected_total"], "diff_pct": diff,
               "ok": abs(diff) <= rc.get("tolerance_pct", 0.5)}

    # 5. optional cleaned copy
    clean_n = None
    if prm.get("write_clean"):
        err_rules = [r["name"] for r in prm.get("rules", []) if r.get("severity") == "error"]
        bad = flags[err_rules].any(axis=1) if err_rules else pd.Series(False, index=df.index)
        before = len(df)
        cl = df[~bad]
        log.add("drop rows failing error rules", before, len(cl), ", ".join(err_rules))
        b2 = len(cl)
        cl = cl[~cl[c["id"]].duplicated()] if c.get("id") in cl.columns else cl.drop_duplicates()
        log.add("drop duplicate ids (keep first)", b2, len(cl))
        cl.to_parquet(out / "clean.parquet", index=False)
        clean_n = len(cl)

    metrics = {"rows": n, "duplicate_rows": int(dup_rows.sum()), "duplicate_ids": int(dup_ids.sum()),
               "rules": {r["rule"]: r["rows_flagged"] for r in rule_rows},
               "missing_pct": {r["column"]: r["missing_pct"] for r in miss_rows},
               "missing_tests": {f"{t['column']}|{t['by']}|{t['level']}": t["p_value"] for t in tests},
               "reconciliation": rec, "clean_rows": clean_n}
    write_run(out, RECIPE, cfg, data_hash(df), metrics, log, errors, warnings)

    L = [f"# Data-quality report: {cfg['dataset'].get('name', '')}", "",
         f"**{n:,} rows checked.** Fully duplicated rows: **{int(dup_rows.sum()):,}** · duplicated ids: **{int(dup_ids.sum()):,}**.", "",
         "## Rules", ""]
    if len(rules):
        L += ["| Rule | Severity | Rows flagged | Why it matters |", "| --- | --- | --- | --- |"]
        L += [f"| {r.rule} | {r.severity} | {r.rows_flagged:,} ({r.pct}%) | {r.why} |" for r in rules.itertuples()]
    else:
        L.append("No rules configured.")
    L += ["", "## Missing data", ""]
    if len(miss):
        L += ["| Column | Missing | Outcome when missing vs present |", "| --- | --- | --- |"]
        for r in miss_rows:
            o = (f"{fmt(r['target_mean_missing'])} vs {fmt(r['target_mean_present'])}" if "target_mean_missing" in r else "—")
            L.append(f"| {r['column']} | {r['missing_rows']:,} ({r['missing_pct']}%) | {o} |")
        if len(mt):
            L += ["", "**Does missingness depend on other fields?**", "", "| Column | Tested against | Level | p-value | Pattern |", "| --- | --- | --- | --- | --- |"]
            for t in tests:
                L.append(f"| {t['column']} | {t['by']} | {t['level']} | {fmt(t['p_value'], 3)} | {t['detail']} |")
            L += ["", "*Reading it:* p < 0.05 means missingness is related to that field → **not MCAR** (MAR if explained by observed "
                  "fields; MNAR is possible if rows with missing values also differ in outcome). A test can only rule MCAR *out*, never prove it. "
                  "Test at the unit where values go missing (e.g. region-day for weather): row-level tests on clustered data are falsely precise."]
    else:
        L.append("No missing values.")
    if rec:
        L += ["", "## Reconciliation", "", f"{rec['column']} total {fmt(rec['observed'])} vs expected {fmt(rec['expected'])} "
              f"({rec['diff_pct']:+.2f}%) → {'OK' if rec['ok'] else '**does not reconcile**'}"]
    L += ["", "## What to do next", "", "- Decide a treatment for each issue (correct, quarantine, keep with a flag) and write it down.",
          "- Nothing was deleted. Flagged rows are in `quarantine.csv`" + ("; a cleaned copy is in `clean.parquet`." if clean_n is not None else "."),
          "", "Files: `rule_log.csv`, `quarantine.csv`, `missingness.csv`, `missingness_tests.csv`, `schema_report.md`, `row_accounting.md`."]
    (out / "narrative.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:20]))
    return out
