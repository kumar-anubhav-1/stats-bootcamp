# NorthStar shelf photos (synthetic)

- `shelf_images.npz` — array `images`, shape (400, 48, 192, 3), uint8 RGB; one shelf bay per image.
- `shelf_images.csv` — image_id, store_id, week, number of products and gaps, gap pixels.
- `shelf_gaps.csv` — every out-of-stock gap: image_id, left pixel x0, right pixel x1 (exclusive).

Meridian cheque digits: `sklearn.datasets.load_digits()` (bundled, real handwriting, 8 × 8 pixels).
