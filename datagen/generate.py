"""Generate bootcamp datasets.

Learner usage (via Claude Code):   python -m datagen.generate
Instructor usage:                  python -m datagen.generate --domain all --with-truth --exam --transfer

Outputs
  data/retail/*.parquet|csv, data/finance/*.parquet|csv, MANIFEST.json per folder
  data/<domain>/variants/   (renamed, weekly, period2, units) for reuse drills
  instructor/truth/...      (only with --with-truth)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import finance, retail, vision
from .common import TEACHING_SEED, write_manifest, write_table

ROOT = Path(__file__).resolve().parents[1]
CSV_SKIP = {"performance_monthly"}           # large: parquet only

RETAIL_RENAME = {
    "line_id": "row_ref", "basket_id": "receipt_no", "date": "txn_date", "store_id": "outlet_code",
    "customer_id": "shopper_id", "sku": "item_code", "category": "dept", "quantity": "units_sold",
    "unit_price": "selling_price", "list_price": "rrp", "revenue": "net_sales", "promo_flag": "on_deal",
    "discount_pct": "deal_depth", "return_flag": "is_refund", "experiment_group": "trial_arm",
}
FINANCE_RENAME = {
    "account_id": "acct_no", "customer_id": "cust_no", "income_annual": "gross_income", "bureau_score": "cb_score",
    "utilisation": "util_ratio", "dti": "debt_to_income", "default_12m": "bad_flag_12m", "vintage": "booking_qtr",
    "limit_or_loan_amount": "exposure_amt", "protected_group": "grp", "churn_flag": "attrited",
}


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.ndarray, tuple, set)):
        return list(o)
    return str(o)


def _write_domain(out: dict, folder: Path, meta: dict) -> list[dict]:
    entries = [write_table(df, folder, name, csv=name not in CSV_SKIP) for name, df in out["tables"].items()]
    write_manifest(entries, folder, meta)
    return entries


def _write_truth(out: dict, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    meta = {}
    for k, v in out["truth"].items():
        if isinstance(v, pd.DataFrame):
            v.to_parquet(folder / f"{k}.parquet", index=False)
        else:
            meta[k] = v
    (folder / "truth.json").write_text(json.dumps(meta, indent=2, default=_json_default))


def retail_variants(out: dict, folder: Path, seed: int) -> None:
    tx = out["tables"]["transactions"]
    folder.mkdir(parents=True, exist_ok=True)
    write_table(tx.rename(columns=RETAIL_RENAME), folder, "transactions_renamed")
    wk = (tx[~tx.return_flag].groupby(["store_id", "sku", "category", "week"], as_index=False)
          .agg(units=("quantity", "sum"), revenue=("revenue", "sum"), lines=("line_id", "count"),
               promo_lines=("promo_flag", "sum")))
    write_table(wk, folder, "transactions_weekly")
    units = tx.copy()
    for c in ["list_price", "unit_price", "revenue", "unit_cost", "margin"]:
        units[c] = (units[c] * 100).round().astype("int64")
    write_table(units, folder, "transactions_cents")
    p2 = retail.generate(retail.RetailParams(seed=seed + 11, start_date="2026-11-02"))["tables"]["transactions"]
    write_table(p2, folder, "transactions_period2")


def finance_variants(out: dict, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    write_table(out["tables"]["accounts"].rename(columns=FINANCE_RENAME), folder, "accounts_renamed")


def exam_params():
    """Held-out exam parameters live in the private instructor repository (instructor/exam_config.py)."""
    try:
        from instructor.exam_config import exam_params as _ep
    except ImportError:
        raise SystemExit("--exam needs instructor/exam_config.py (instructor-only; see PUSH_TO_GITHUB.md).")
    return _ep()


def _transfer():
    try:
        from instructor import transfer_gen
    except ImportError:
        raise SystemExit("--transfer needs instructor/transfer_gen.py (instructor-only; see PUSH_TO_GITHUB.md).")
    return transfer_gen


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--domain", choices=["retail", "finance", "all"], default="all")
    ap.add_argument("--seed", type=int, default=TEACHING_SEED)
    ap.add_argument("--out", default=str(ROOT / "data"))
    ap.add_argument("--no-variants", action="store_true")
    ap.add_argument("--with-truth", action="store_true", help="instructor: write the truth pack")
    ap.add_argument("--exam", action="store_true", help="instructor: held-out exam datasets")
    ap.add_argument("--transfer", action="store_true", help="instructor: Day-10 transfer dataset")
    a = ap.parse_args(argv)
    out_root = Path(a.out)
    truth_root = ROOT / "instructor" / "truth"
    report = {}
    if a.domain in ("retail", "all"):
        r = retail.generate(retail.RetailParams(seed=a.seed))
        report["retail"] = _write_domain(r, out_root / "retail", {"domain": "retail", "seed": a.seed})
        if not a.no_variants:
            retail_variants(r, out_root / "retail" / "variants", a.seed)
        if a.with_truth:
            _write_truth(r, truth_root / "retail")
    if a.domain in ("finance", "all"):
        f = finance.generate(finance.FinanceParams(seed=a.seed))
        report["finance"] = _write_domain(f, out_root / "finance", {"domain": "finance", "seed": a.seed})
        if not a.no_variants:
            finance_variants(f, out_root / "finance" / "variants")
        if a.with_truth:
            _write_truth(f, truth_root / "finance")
    if a.domain == "all":
        v = vision.generate()
        vision.write(v, out_root / "vision", truth_root / "vision" if a.with_truth else None)
        print(f"\nVISION  {len(v['meta'])} shelf images, {len(v['gaps'])} labelled gaps")
    if a.exam:
        rp, fp = exam_params()
        ex_root = ROOT / "instructor" / "exam"
        for nm, gen, prm in (("retail", retail.generate, rp), ("finance", finance.generate, fp)):
            o = gen(prm)
            _write_domain(o, ex_root / "data" / nm, {"domain": nm, "seed": prm.seed, "exam": True})
            _write_truth(o, ex_root / "truth" / nm)
    if a.transfer:
        tg = _transfer()
        t = tg.generate(tg.SEED)
        _write_domain(t, ROOT / "instructor" / "transfer" / "data", {"domain": "quick-commerce", "seed": tg.SEED})
        _write_truth(t, ROOT / "instructor" / "transfer" / "truth")
    for dom, entries in report.items():
        print(f"\n{dom.upper()}  (seed {a.seed})")
        for e in entries:
            print(f"  {e['table']:<28}{e['rows']:>9,} rows  {e['columns']:>3} cols  hash {e['hash']}")
    return report


if __name__ == "__main__":
    main()
