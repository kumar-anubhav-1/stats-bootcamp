"""Shared machinery for every toolkit recipe: config, column mapping, filters,
schema check, row accounting, output folder, regression check.

Recipes never hard-code dataset column names; they ask for ROLES (target, group,
date, ...) and the config maps roles to the columns of whatever dataset is used.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import platform
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]


class SchemaError(Exception):
    """Raised when a dataset cannot be used by a recipe; message is written for humans."""


@dataclass
class RowLog:
    steps: list = field(default_factory=list)

    def add(self, step: str, before: int, after: int, note: str = ""):
        self.steps.append({"step": step, "rows_before": before, "rows_after": after,
                           "rows_removed": before - after, "note": note})

    def table(self) -> pd.DataFrame:
        return pd.DataFrame(self.steps)

    def markdown(self) -> str:
        lines = ["| Step | Rows before | Rows after | Removed | Note |", "| --- | --- | --- | --- | --- |"]
        for s in self.steps:
            lines.append(f"| {s['step']} | {s['rows_before']:,} | {s['rows_after']:,} | {s['rows_removed']:,} | {s['note']} |")
        return "\n".join(lines)


def load_config(path: str | Path) -> dict:
    path = Path(path)
    if not path.is_absolute() and not path.exists():
        path = ROOT / path
    cfg = yaml.safe_load(path.read_text())
    cfg["_config_path"] = str(path)
    cfg.setdefault("columns", {})
    cfg.setdefault("filters", [])
    cfg.setdefault("params", {})
    cfg.setdefault("output", {})
    return cfg


def _read_file(path) -> pd.DataFrame:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    if not p.exists():
        raise SchemaError(f"Dataset file not found: {p}. Did you run `python -m datagen.generate`?")
    if p.suffix == ".parquet":
        return pd.read_parquet(p)
    if p.suffix in (".csv", ".gz"):
        return pd.read_csv(p)
    if p.suffix in (".xlsx", ".xls"):
        return pd.read_excel(p)
    raise SchemaError(f"Unsupported file type {p.suffix}; use parquet, csv or xlsx.")


def read_dataset(cfg: dict) -> pd.DataFrame:
    """Read the dataset; optional `dataset.joins: [{path, keys: [cols], columns: [cols]} | {path, keys, count_as: name}]`
    left-joins extra tables (or counts their rows per key)."""
    df = _read_file(cfg["dataset"]["path"])
    for j in cfg["dataset"].get("joins", []) or []:
        other = _read_file(j["path"])
        key = j.get("keys", j.get("on", j.get(True)))  # YAML 1.1 reads an unquoted `on:` as True
        on = list(key) if isinstance(key, (list, tuple)) else [key]
        if j.get("count_as"):  # count rows per key in the joined table (e.g. claims per policy); 0 when absent
            cnt = other.groupby(on).size().rename(j["count_as"]).reset_index()
            df = df.merge(cnt, on=on, how="left")
            df[j["count_as"]] = df[j["count_as"]].fillna(0).astype(int)
            continue
        cols = on + [c for c in (j.get("columns") or other.columns) if c not in on]
        missing = [c for c in cols if c not in other.columns]
        if missing:
            raise SchemaError(f"Join file {j['path']} lacks columns {missing}.")
        dup = [c for c in cols if c in df.columns and c not in on]
        df = df.merge(other[cols].drop_duplicates(on), on=on, how="left", suffixes=("", "_j"))
        if dup:
            df = df.drop(columns=[f"{c}_j" for c in dup if f"{c}_j" in df.columns])
    return df


SYNONYMS = {
    "quantity": ["units", "qty", "units_sold", "volume"], "revenue": ["sales", "net_sales", "amount", "value"],
    "store": ["outlet", "shop", "branch", "dark_store"], "customer": ["shopper", "client", "cust", "member"],
    "line": ["row", "item", "ref"], "date": ["dt", "day", "ts", "time"], "sku": ["item", "product", "article"],
    "price": ["rrp", "selling", "amt"], "experiment": ["trial", "arm", "variant", "test"], "promo": ["deal", "offer"],
    "category": ["dept", "department", "class"], "account": ["acct"], "default": ["bad"], "income": ["salary", "gross"],
    "basket": ["receipt", "order", "ticket"], "return": ["refund"],
}


def suggest(col: str, columns) -> list[str]:
    """Suggest dataset columns that may correspond to a missing one (string similarity + business synonyms)."""
    import difflib
    cands = set(difflib.get_close_matches(col, list(columns), n=3, cutoff=0.5))
    toks = col.lower().replace("_id", "").split("_")
    for t in toks:
        for key, syns in SYNONYMS.items():
            if t.startswith(key) or key.startswith(t):
                for c in columns:
                    if any(sy in c.lower() for sy in syns + [key]):
                        cands.add(c)
    return sorted(cands)[:4]


def schema_check(df: pd.DataFrame, cfg: dict, schema: dict) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). schema = {role: {required: bool, kind: numeric|binary|category|date|id|any}}."""
    errors, warnings = [], []
    cols = cfg["columns"]
    for role, spec in schema.items():
        col = cols.get(role)
        if col is None:
            if spec.get("required"):
                guess = [c for c in df.columns if role in c.lower()][:3]
                errors.append(f"Role `{role}` is required but not mapped in `columns:`. "
                              f"Columns that might fit: {guess or 'none found'}.")
            continue
        if col not in df.columns:
            close = suggest(col, df.columns)
            errors.append(f"Role `{role}` is mapped to `{col}`, which is not in the dataset. "
                          + (f"Possible matches: {', '.join(close)}." if close else f"Available columns: {', '.join(df.columns[:12])} ..."))
            continue
        s = df[col]
        kind = spec.get("kind", "any")
        if kind == "numeric" and not (pd.api.types.is_numeric_dtype(s) or pd.api.types.is_bool_dtype(s)):
            errors.append(f"Role `{role}` (`{col}`) must be numeric but is {s.dtype}.")
        if kind == "date":
            try:
                pd.to_datetime(s.dropna().head(100))
            except Exception:
                errors.append(f"Role `{role}` (`{col}`) should be a date but cannot be parsed.")
        null = s.isna().mean()
        if null > 0:
            warnings.append(f"`{col}` ({role}) has {null:.1%} missing values; rows with missing {role} will be excluded and counted.")
        if kind == "numeric" and pd.api.types.is_numeric_dtype(s) and s.notna().any():
            med, mx = s.abs().median(), s.abs().max()
            if med > 0 and mx / med > 1000:
                warnings.append(f"`{col}` max is {mx / med:,.0f}x its median: check for unit errors or extreme outliers.")
            if (s < 0).any() and spec.get("non_negative"):
                warnings.append(f"`{col}` has {(s < 0).sum():,} negative values but {role} should be non-negative.")
    idc = cols.get("id")
    if idc in df.columns:
        d = df[idc].duplicated().sum()
        if d:
            warnings.append(f"`{idc}` (id) has {d:,} duplicated values: possible duplicate rows or a different grain than declared.")
    return errors, warnings


def apply_filters(df: pd.DataFrame, cfg: dict, log: RowLog) -> pd.DataFrame:
    for f in cfg["filters"]:
        before = len(df)
        try:
            df = df.query(f, engine="python")
        except Exception as e:
            raise SchemaError(f"Filter `{f}` failed: {e}. Filters use the dataset's own column names.")
        log.add(f"filter: {f}", before, len(df))
    return df


def output_dir(cfg: dict, recipe: str) -> Path:
    tmpl = cfg["output"].get("folder", "outputs/{recipe}/{date}_{dataset}")
    name = tmpl.format(recipe=recipe, date=dt.date.today().isoformat(), dataset=cfg["dataset"].get("name", "data"))
    p = Path(name)
    if not p.is_absolute():
        p = ROOT / p
    p.mkdir(parents=True, exist_ok=True)
    return p


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if (o is None or math.isnan(o)) else round(float(o), 6)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def write_run(out: Path, recipe: str, cfg: dict, df_hash: str, metrics: dict, log: RowLog,
              errors: list, warnings: list) -> None:
    (out / "metrics.json").write_text(json.dumps(_clean(metrics), indent=2, default=str))
    (out / "row_accounting.md").write_text(log.markdown() + "\n")
    rep = [f"# Schema report: {recipe}", "", f"Dataset: `{cfg['dataset']['path']}`", "",
           "## Column mapping", "", "| Role | Column |", "| --- | --- |"]
    rep += [f"| {k} | `{v}` |" for k, v in cfg["columns"].items()]
    rep += ["", "## Errors", ""] + ([f"- {e}" for e in errors] or ["None"])
    rep += ["", "## Warnings", ""] + ([f"- {w}" for w in warnings] or ["None"])
    rep += ["", "## Row accounting", "", log.markdown()]
    (out / "schema_report.md").write_text("\n".join(rep) + "\n")
    manifest = {"recipe": recipe, "run_at": dt.datetime.now().isoformat(timespec="seconds"),
                "config": {k: v for k, v in cfg.items() if not k.startswith("_")},
                "config_file": cfg.get("_config_path"), "data_hash": df_hash,
                "python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__}
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str))


def data_hash(df: pd.DataFrame) -> str:
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=False).values.tobytes()).hexdigest()[:16]


def regression_check(out: Path, baseline: Path, rtol: float = 1e-6) -> list[str]:
    """Compare metrics.json in `out` with a saved baseline; return list of differences."""
    new = json.loads((out / "metrics.json").read_text())
    old = json.loads(Path(baseline).read_text())
    tol = old.get("_tolerance", {})  # ML recipes declare a tolerance: fitted models differ slightly across library versions
    rtol = float(tol.get("rtol", rtol))
    atol = float(tol.get("atol", 1e-9))
    new.pop("_tolerance", None)
    old = {k: v for k, v in old.items() if k != "_tolerance"}
    diffs = []

    def walk(a, b, path=""):
        if isinstance(a, dict) and isinstance(b, dict):
            for k in set(a) | set(b):
                if k not in a or k not in b:
                    diffs.append(f"{path}/{k}: present in only one run")
                else:
                    walk(a[k], b[k], f"{path}/{k}")
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
            if not math.isclose(a, b, rel_tol=rtol, abs_tol=atol):
                diffs.append(f"{path}: {b} -> {a}")
        elif a != b:
            diffs.append(f"{path}: {b!r} -> {a!r}")

    walk(new, old)
    return diffs


def fmt(x, nd=3):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    if isinstance(x, (int, np.integer)):
        return f"{x:,}"
    if abs(x) >= 1000:
        return f"{x:,.0f}"
    if abs(x) >= 100:
        return f"{x:,.1f}"
    return f"{x:.{nd}g}" if abs(x) < 0.001 and x != 0 else f"{x:,.{nd}f}"


def md_table(df: pd.DataFrame, index: bool = True, nd: int = 4) -> str:
    """Markdown table without the optional `tabulate` dependency."""
    d = df.reset_index() if index else df
    def cell(v):
        if isinstance(v, (float, np.floating)):
            return "" if np.isnan(v) else (f"{v:.{nd}g}" if abs(v) < 1e-3 and v != 0 else f"{v:,.{nd}f}".rstrip("0").rstrip("."))
        return str(v)
    head = "| " + " | ".join(str(c) for c in d.columns) + " |"
    sep = "| " + " | ".join("---" for _ in d.columns) + " |"
    body = ["| " + " | ".join(cell(v) for v in row) + " |" for row in d.itertuples(index=False)]
    return "\n".join([head, sep] + body)
