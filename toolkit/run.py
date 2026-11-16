"""Run any toolkit recipe from its configuration file.

    python -m toolkit.run toolkit/configs/retail_promo_lift.yaml
    python -m toolkit.run <config> --save-baseline     # store metrics as the regression baseline
    python -m toolkit.run <config> --check-baseline    # re-run and confirm results are unchanged
    python -m toolkit.run --list                       # list available recipes
"""
from __future__ import annotations

import argparse
import importlib
import shutil
import sys
from pathlib import Path

from .common.core import ROOT, SchemaError, load_config, regression_check

RECIPES = {p.parent.name: f"toolkit.{p.parent.name}.recipe"
           for p in sorted((Path(__file__).parent).glob("rcp_*/recipe.py"))}  # every toolkit/rcp_*/recipe.py


def baseline_path(cfg_path: str) -> Path:
    return ROOT / "toolkit" / "baselines" / (Path(cfg_path).stem + ".metrics.json")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config", nargs="?")
    ap.add_argument("--save-baseline", action="store_true")
    ap.add_argument("--check-baseline", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    if a.list or not a.config:
        for k in RECIPES:
            print(k)
        return 0
    cfg = load_config(a.config)
    recipe = cfg.get("recipe")
    if recipe not in RECIPES:
        print(f"Unknown recipe `{recipe}`. Available: {', '.join(RECIPES)}")
        return 2
    mod = importlib.import_module(RECIPES[recipe])
    try:
        out = mod.run(cfg)
    except SchemaError as e:
        print(f"\nSCHEMA CHECK FAILED for {recipe}:\n{e}\n\nNothing was analysed. Fix the config `columns:` mapping or the data, then re-run.")
        return 3
    print(f"\nOutputs written to: {out}")
    bp = baseline_path(cfg["_config_path"])
    if a.save_baseline:
        bp.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(out / "metrics.json", bp)
        print(f"Baseline saved: {bp}")
    if a.check_baseline:
        if not bp.exists():
            print(f"No baseline at {bp}; run once with --save-baseline.")
            return 4
        diffs = regression_check(out, bp)
        if diffs:
            print("REGRESSION CHECK FAILED — results differ from baseline:")
            for d in diffs[:50]:
                print("  ", d)
            return 5
        print("Regression check passed: every metric matches the baseline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
