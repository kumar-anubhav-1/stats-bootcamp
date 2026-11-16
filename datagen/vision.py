"""Computer-vision data for Day 11 (all synthetic, no real people or brands).

NorthStar shelf photos: each image is one shelf bay (48 × 192 pixels, RGB) from a store camera. Products are coloured packs with a
white price label; an out-of-stock "gap" shows the dark back panel. Labels give every gap's left/right pixel position.

Planted issues (instructor answer key in instructor/truth/vision/truth.json):
  V1  store S07's camera gets dimmer from week 5 (brightness × 0.55) — lighting drift
  V2  store S03's camera is out of focus (blurred images) — image-quality problem
  V3  annotator B mislabels ~8% of the windows they label — label noise
Meridian cheque digits come from scikit-learn's bundled handwritten-digits set (real handwriting, 8 × 8 pixels), loaded at analysis time.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

H, W = 48, 192
PALETTE = np.array([[0.80, 0.15, 0.15], [0.15, 0.45, 0.80], [0.95, 0.75, 0.10], [0.20, 0.60, 0.25],
                    [0.55, 0.25, 0.65], [0.95, 0.50, 0.15], [0.10, 0.65, 0.70], [0.85, 0.35, 0.55],
                    [0.16, 0.16, 0.22], [0.36, 0.24, 0.14], [0.30, 0.30, 0.32]])  # dark packs look like gaps to a brightness rule


@dataclass
class VisionParams:
    seed: int = 20261115
    n_stores: int = 10
    weeks: int = 8
    per_week: int = 5
    dim_store: str = "S07"
    dim_from_week: int = 5
    dim_factor: float = 0.55
    blur_store: str = "S03"
    noisy_annotator_rate: float = 0.08


def _blur(img):
    k = np.array([1, 4, 6, 4, 1], float)
    k /= k.sum()
    out = img.copy()
    for ax in (0, 1):
        pad = [(0, 0)] * 3
        pad[ax] = (2, 2)
        p = np.pad(out, pad, mode="edge")
        out = sum(k[i] * np.take(p, range(i, i + out.shape[ax]), axis=ax) for i in range(5))
    return out


def shelf(rng, oos_rate):
    img = np.ones((H, W, 3)) * np.array([0.86, 0.81, 0.70])
    img += rng.normal(0, 0.015, img.shape)
    img[44:, :, :] = np.array([0.35, 0.30, 0.25])  # shelf edge
    x, gaps, products = 2, [], []
    while x < W - 12:
        w = int(rng.integers(14, 25))
        x1 = min(x + w, W - 2)
        if rng.random() < oos_rate:
            img[6:44, x:x1, :] = np.array([0.48, 0.44, 0.40]) + rng.normal(0, 0.02, (38, x1 - x, 3))
            img[8:44:5, x + 2:x1:5, :] = 0.25  # pegboard holes in the back panel
            if rng.random() < 0.3:
                img[30:34, x + 2:x1 - 2, :] = 0.93  # a shelf-talker price tag left in the empty slot
            gaps.append((x, x1))
        else:
            h = int(rng.integers(26, 39))
            c = PALETTE[rng.integers(len(PALETTE))] * rng.uniform(0.85, 1.1)
            img[44 - h:44, x + 1:x1 - 1, :] = c
            if rng.random() < 0.7:
                img[44 - h // 2:44 - h // 2 + 4, x + 3:x1 - 3, :] = 0.97  # price label (30% of packs turned sideways: no label)
            if rng.random() < 0.25:
                img[44 - h:44, x + 1:x1 - 1, :] *= 0.6  # pushed-back pack in shadow
            products.append((x, x1))
        x = x1 + int(rng.integers(1, 3))
    ramp = np.linspace(rng.uniform(0.8, 1.0), rng.uniform(1.0, 1.15), W)[None, :, None]  # uneven lighting along the bay
    img = img * ramp + rng.normal(0, 0.03, img.shape)
    return np.clip(img, 0, 1), gaps, products


def generate(p: VisionParams = VisionParams()) -> dict:
    rng = np.random.default_rng(p.seed)
    stores = [f"S{i:02d}" for i in range(1, p.n_stores + 1)]
    oos = {s: float(rng.uniform(0.04, 0.16)) for s in stores}
    imgs, meta, gaps_rows = [], [], []
    k = 0
    for s in stores:
        for wk in range(1, p.weeks + 1):
            for j in range(p.per_week):
                img, gaps, prods = shelf(rng, oos[s])
                bright = rng.uniform(0.9, 1.1)
                dim = s == p.dim_store and wk >= p.dim_from_week
                if dim:
                    bright *= p.dim_factor
                img = np.clip(img * bright + (rng.normal(0, 0.05, img.shape) if dim else 0), 0, 1)  # dim camera: darker and noisier
                if s == p.blur_store:
                    img = _blur(_blur(img))
                imgs.append((img * 255).round().astype(np.uint8))
                meta.append({"image_id": k, "store_id": s, "week": wk, "n_products": len(prods), "n_gaps": len(gaps),
                             "gap_pixels": sum(b - a for a, b in gaps)})
                gaps_rows += [{"image_id": k, "x0": a, "x1": b} for a, b in gaps]
                k += 1
    meta = pd.DataFrame(meta)
    gaps_df = pd.DataFrame(gaps_rows)
    truth = {"V1": {"store": p.dim_store, "from_week": p.dim_from_week, "factor": p.dim_factor},
             "V2": {"store": p.blur_store}, "V3": {"annotator": "B", "error_rate": p.noisy_annotator_rate},
             "true_oos_rate": oos}
    return {"images": np.stack(imgs), "meta": meta, "gaps": gaps_df, "truth": truth}


def write(out: dict, folder: Path, truth_folder: Path | None = None) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(folder / "shelf_images.npz", images=out["images"])
    out["meta"].to_csv(folder / "shelf_images.csv", index=False)
    out["gaps"].to_csv(folder / "shelf_gaps.csv", index=False)
    (folder / "README.md").write_text(
        "# NorthStar shelf photos (synthetic)\n\n"
        "- `shelf_images.npz` — array `images`, shape (400, 48, 192, 3), uint8 RGB; one shelf bay per image.\n"
        "- `shelf_images.csv` — image_id, store_id, week, number of products and gaps, gap pixels.\n"
        "- `shelf_gaps.csv` — every out-of-stock gap: image_id, left pixel x0, right pixel x1 (exclusive).\n\n"
        "Meridian cheque digits: `sklearn.datasets.load_digits()` (bundled, real handwriting, 8 × 8 pixels).\n")
    if truth_folder:
        truth_folder.mkdir(parents=True, exist_ok=True)
        (truth_folder / "truth.json").write_text(json.dumps(out["truth"], indent=2))


def load(folder) -> tuple[np.ndarray, pd.DataFrame, pd.DataFrame]:
    folder = Path(folder)
    return (np.load(folder / "shelf_images.npz")["images"], pd.read_csv(folder / "shelf_images.csv"),
            pd.read_csv(folder / "shelf_gaps.csv"))
