"""Shared helper: build an entity-level feature table from row-level data via a config spec."""
from __future__ import annotations

import numpy as np
import pandas as pd


def entity_table(df: pd.DataFrame, entity: str, aggregate: dict | None, share_of: str | None = None, log: list | None = None) -> pd.DataFrame:
    """aggregate: {output_name: [column, func]} (func: sum/mean/nunique/count/max/min/median); share_of: column whose
    level shares per entity are added as features; log: output names to log1p-transform."""
    if not aggregate:
        out = df.set_index(entity)
        return out.select_dtypes("number")
    out = df.groupby(entity).agg(**{k: (v[0], v[1]) for k, v in aggregate.items()})
    for c in out.columns:
        out[c] = out[c].astype(float)
    if share_of:
        sh = pd.crosstab(df[entity], df[share_of], normalize="index")
        sh.columns = [f"share_{c}" for c in sh.columns]
        out = out.join(sh)
    for c in log or []:
        if c in out:
            out[c] = np.log1p(out[c].clip(lower=0))
    return out
