"""Shared helpers for the bootcamp data generators (instructor area)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

TEACHING_SEED = 20261115


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def weighted_sample(rng, idx, k: int, weights) -> np.ndarray:
    """Weighted sampling without replacement (exponential-keys method).

    Implemented explicitly so results are identical across NumPy versions
    (Generator.choice with p and replace=False is not guaranteed stable)."""
    idx = np.asarray(idx)
    w = np.round(np.asarray(weights, float), 12)
    keys = np.round(-np.log(rng.random(len(idx))) / np.maximum(w, 1e-300), 9)
    return idx[np.argsort(keys, kind="stable")[:k]]


def canonical_hash(df: pd.DataFrame) -> str:
    """Version-independent fingerprint: CSV text with fixed float formatting."""
    txt = df.to_csv(index=False, float_format="%.6g", na_rep="")
    return hashlib.sha256(txt.encode()).hexdigest()[:16]


def write_table(df: pd.DataFrame, folder: Path, name: str, csv: bool = True) -> dict:
    """Write parquet (+ csv) and return a manifest entry with row count and hash."""
    folder.mkdir(parents=True, exist_ok=True)
    df = df.reset_index(drop=True)
    pq = folder / f"{name}.parquet"
    df.to_parquet(pq, index=False)
    if csv:
        df.to_csv(folder / f"{name}.csv", index=False)
    digest = canonical_hash(df)
    return {"table": name, "rows": int(len(df)), "columns": int(df.shape[1]), "hash": digest}


def write_manifest(entries: list[dict], folder: Path, meta: dict) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "MANIFEST.json").write_text(json.dumps({"meta": meta, "tables": entries}, indent=2))


def ids(prefix: str, n: int, width: int, start: int = 1) -> np.ndarray:
    return np.array([f"{prefix}{i:0{width}d}" for i in range(start, start + n)])
