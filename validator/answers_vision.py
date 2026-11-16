"""Computed answers for Day 11 (computer vision): image classification of shelf windows, augmentation vs lighting drift,
out-of-stock gap detection (IoU, precision/recall, AP, on-shelf availability), cheque-digit reading (OCR), confidence routing,
annotator agreement. Keys v_."""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.datasets import load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, cohen_kappa_score, confusion_matrix, recall_score, precision_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from . import measures as M

warnings.filterwarnings("ignore")
WIN, STRIDE, R0, R1 = 16, 4, 4, 46
TRAIN = ["S01", "S02", "S04", "S05", "S06", "S08"]
TEST = ["S09", "S10"]


def _r(x, nd=3):
    return round(float(x), nd)


def windows(img):
    """All 16-pixel-wide windows of one shelf image, downsampled 2× → (n, 21*8*3) in [0, 1]."""
    out, xs = [], []
    for x in range(0, img.shape[1] - WIN + 1, STRIDE):
        w = img[R0:R1, x:x + WIN, :].astype(float) / 255
        out.append(w.reshape(21, 2, 8, 2, 3).mean(axis=(1, 3)).ravel())
        xs.append(x)
    return np.array(out), np.array(xs)


def labels_for(xs, gaps):
    """1 = window ≥ 75% covered by a gap, 0 = no gap overlap, -1 = ambiguous (excluded from training)."""
    lab = np.zeros(len(xs), int)
    for i, x in enumerate(xs):
        cov = sum(max(0, min(x + WIN, b) - max(x, a)) for a, b in gaps) / WIN
        lab[i] = 1 if cov >= 0.75 else (0 if cov == 0 else -1)
    return lab


def features(X):
    """Hand-crafted features: mean and spread of each colour, saturation, edge density."""
    P = X.reshape(-1, 21, 8, 3)
    mean = P.mean(axis=(1, 2))
    sd = P.std(axis=(1, 2))
    sat = (P.max(-1) - P.min(-1)).mean(axis=(1, 2))[:, None]
    gray = P.mean(-1)
    edge = (np.abs(np.diff(gray, axis=1)).mean(axis=(1, 2)) + np.abs(np.diff(gray, axis=2)).mean(axis=(1, 2)))[:, None]
    return np.hstack([mean, sd, sat, edge])


def intervals(xs, p, thr=0.5):
    """Merge consecutive windows with P(gap) > thr into predicted gap intervals with a confidence score."""
    out, cur = [], None
    for x, s in zip(xs, p):
        if s > thr:
            if cur and x <= cur[1]:
                cur = [cur[0], x + WIN, cur[2] + [s]]
            else:
                if cur:
                    out.append(cur)
                cur = [x, x + WIN, [s]]
        elif cur and x >= cur[1]:
            out.append(cur)
            cur = None
    if cur:
        out.append(cur)
    return [(a, b, float(np.mean(sc))) for a, b, sc in out]


def iou1d(a, b):
    inter = max(0, min(a[1], b[1]) - max(a[0], b[0]))
    union = max(a[1], b[1]) - min(a[0], b[0])
    return inter / union if union else 0.0


def evaluate_detection(preds, truths, thr=0.5):
    """preds: list per image of (x0,x1,score); truths: list per image of (x0,x1). Greedy matching at IoU ≥ thr."""
    scored, n_true = [], sum(len(t) for t in truths)
    for P, T in zip(preds, truths):
        used = set()
        for a, b, s in sorted(P, key=lambda z: -z[2]):
            best, bi = 0, None
            for j, t in enumerate(T):
                if j not in used and iou1d((a, b), t) > best:
                    best, bi = iou1d((a, b), t), j
            ok = best >= thr
            if ok:
                used.add(bi)
            scored.append((s, ok))
    scored.sort(key=lambda z: -z[0])
    tp = np.cumsum([o for _, o in scored])
    fp = np.cumsum([not o for _, o in scored])
    prec = tp / np.maximum(tp + fp, 1)
    rec = tp / max(n_true, 1)
    ap = sum((rec[i] - (rec[i - 1] if i else 0)) * prec[i] for i in range(len(scored))) if scored else 0
    return {"precision": float(prec[-1]) if len(prec) else 0, "recall": float(rec[-1]) if len(rec) else 0, "ap": float(ap),
            "n_pred": len(scored), "n_true": n_true}


def compute_vision(data=str(M.DATA)) -> dict:
    from datagen import vision as V
    a: dict = {}
    imgs, meta, gaps = V.load(M.Path(data) / "vision")
    gmap = {i: list(zip(g.x0, g.x1)) for i, g in gaps.groupby("image_id")}
    a["v_n_images"], a["v_n_gaps"] = int(len(meta)), int(len(gaps))
    a["v_shape"] = list(imgs.shape[1:])
    a["v_pixels_per_image"] = int(np.prod(imgs.shape[1:]))
    rows = []
    for i, m in meta.iterrows():
        X, xs = windows(imgs[i])
        y = labels_for(xs, gmap.get(i, []))
        rows.append((m.image_id, m.store_id, m.week, X, xs, y))

    def stack(sel):
        Xs, ys = [], []
        for r in rows:
            if sel(r):
                k = r[5] >= 0
                Xs.append(r[3][k])
                ys.append(r[5][k])
        return np.vstack(Xs), np.concatenate(ys)

    Xtr, ytr = stack(lambda r: r[1] in TRAIN)
    Xte, yte = stack(lambda r: r[1] in TEST)
    Xdim, ydim = stack(lambda r: r[1] == "S07" and r[2] >= 5)
    Xblur, yblur = stack(lambda r: r[1] == "S03")
    a["v_n_train_windows"], a["v_n_test_windows"] = int(len(ytr)), int(len(yte))
    a["v_gap_share"] = _r(100 * ytr.mean(), 1)
    a["v_features_pixels"], a["v_features_hand"] = int(Xtr.shape[1]), int(features(Xtr[:1]).shape[1])
    # brightness rule
    br = Xtr.reshape(-1, 21, 8, 3).mean(axis=(1, 2, 3))
    cands = np.linspace(br.min(), br.max(), 200)
    from sklearn.metrics import f1_score
    accs = [f1_score(ytr, (br < c).astype(int), zero_division=0) for c in cands]
    cut = cands[int(np.argmax(accs))]
    rule = lambda X: (X.reshape(-1, 21, 8, 3).mean(axis=(1, 2, 3)) < cut).astype(int)
    models = {"Brightness rule (dark window = gap)": None,
              "Logistic regression on hand-made features": ("feat", make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))),
              "Logistic regression on raw pixels": ("pix", make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.1))),
              "Small neural network on raw pixels": ("pix", make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(64,), alpha=1e-2, max_iter=400, random_state=0)))}
    res, fitted = {}, {}
    for nm, spec in models.items():
        if spec is None:
            f = rule
        else:
            kind, m = spec
            tf = features if kind == "feat" else (lambda X: X)
            m.fit(tf(Xtr), ytr)
            f = (lambda m_, tf_: (lambda X: m_.predict(tf_(X))))(m, tf)
            fitted[nm] = (m, tf)
        res[nm] = {"acc_test": _r(100 * accuracy_score(yte, f(Xte)), 1),
                   "rec_test": _r(100 * recall_score(yte, f(Xte), zero_division=0), 1),
                   "prec_test": _r(100 * precision_score(yte, f(Xte), zero_division=0), 1),
                   "acc_dim": _r(100 * accuracy_score(ydim, f(Xdim)), 1),
                   "rec_dim": _r(100 * recall_score(ydim, f(Xdim), zero_division=0), 1),
                   "rec_blur": _r(100 * recall_score(yblur, f(Xblur), zero_division=0), 1)}
    a["v_cls"] = res
    a["v_rule_cut"] = _r(cut, 3)
    # augmentation: random brightness 0.5–1.1 on training windows
    rng = np.random.default_rng(0)
    Xaug = np.clip(Xtr * rng.uniform(0.5, 1.1, (len(Xtr), 1)), 0, 1)
    aug = make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(64,), alpha=1e-2, max_iter=400, random_state=0)).fit(
        np.vstack([Xtr, Xaug]), np.concatenate([ytr, ytr]))
    a["v_aug"] = {"rec_test": _r(100 * recall_score(yte, aug.predict(Xte)), 1), "prec_test": _r(100 * precision_score(yte, aug.predict(Xte)), 1),
                  "rec_dim": _r(100 * recall_score(ydim, aug.predict(Xdim)), 1), "acc_dim": _r(100 * accuracy_score(ydim, aug.predict(Xdim)), 1),
                  "rec_blur": _r(100 * recall_score(yblur, aug.predict(Xblur)), 1)}
    # brightness drift statistic
    mb = meta.assign(brightness=[imgs[i].mean() / 255 for i in range(len(meta))])
    s7 = mb[mb.store_id == "S07"]
    a["v_bright_s7_before"], a["v_bright_s7_after"] = _r(s7[s7.week < 5].brightness.mean()), _r(s7[s7.week >= 5].brightness.mean())
    a["v_bright_by_store"] = mb.groupby("store_id").brightness.mean().round(3).to_dict()
    sharp = mb.assign(sharp=[np.abs(np.diff(imgs[i].mean(-1).astype(float), axis=1)).mean() for i in range(len(meta))])
    a["v_sharpness_by_store"] = sharp.groupby("store_id").sharp.mean().round(2).to_dict()
    # gap detection with the augmented pixel model
    det = {}
    for nm, stores, wk in (("test stores", TEST, 0), ("S07 dim weeks", ["S07"], 5)):
        P, T, osa_p, osa_t = [], [], [], []
        for r in rows:
            if r[1] in stores and r[2] >= wk:
                p = aug.predict_proba(r[3])[:, 1]
                iv = intervals(r[4], p)
                P.append(iv)
                T.append(gmap.get(r[0], []))
                osa_p.append(1 - sum(b - a for a, b, _ in iv) / 188)
                osa_t.append(1 - sum(b - a for a, b in gmap.get(r[0], [])) / 188)
        e = evaluate_detection(P, T, 0.5)
        e5 = evaluate_detection(P, T, 0.75)
        det[nm] = {"precision": _r(100 * e["precision"], 1), "recall": _r(100 * e["recall"], 1), "ap50": _r(e["ap"], 3),
                   "ap75": _r(e5["ap"], 3), "n_true": e["n_true"], "n_pred": e["n_pred"],
                   "osa_pred": _r(100 * np.mean(osa_p), 1), "osa_true": _r(100 * np.mean(osa_t), 1)}
    a["v_det"] = det
    # unaugmented model on dim store for comparison of detection
    m0, tf0 = fitted["Small neural network on raw pixels"]
    P, T = [], []
    for r in rows:
        if r[1] == "S07" and r[2] >= 5:
            P.append(intervals(r[4], m0.predict_proba(tf0(r[3]))[:, 1]))
            T.append(gmap.get(r[0], []))
    e = evaluate_detection(P, T, 0.5)
    a["v_det_dim_noaug"] = {"recall": _r(100 * e["recall"], 1), "ap50": _r(e["ap"], 3)}
    # example score traces for the chart: one clean test image and one dim S07 image with gaps
    ex = {}
    for nm, cond in (("test", lambda r: r[1] == "S09" and len(gmap.get(r[0], [])) >= 2),
                     ("dim", lambda r: r[1] == "S07" and r[2] >= 5 and len(gmap.get(r[0], [])) >= 1)):
        r = next(r for r in rows if cond(r))
        ex[nm] = {"image_id": int(r[0]), "x": [int(x + WIN / 2) for x in r[4]], "gaps": [list(map(int, g)) for g in gmap.get(r[0], [])],
                  "aug": [round(float(v), 3) for v in aug.predict_proba(r[3])[:, 1]],
                  "noaug": [round(float(v), 3) for v in m0.predict_proba(tf0(r[3]))[:, 1]]}
    a["v_examples"] = ex
    # annotators: A = truth, B = truth with ~8% flips on the test windows
    rngb = np.random.default_rng(7)
    flip = rngb.random(len(yte)) < 0.08
    yB = np.where(flip, 1 - yte, yte)
    a["v_agree_pct"] = _r(100 * (yB == yte).mean(), 1)
    a["v_kappa"] = _r(cohen_kappa_score(yte, yB), 3)
    a["v_kappa_expected_chance"] = _r(100 * (yte.mean() * yB.mean() + (1 - yte.mean()) * (1 - yB.mean())), 1)
    # train on noisy labels (8% flips on training labels)
    yn = np.where(np.random.default_rng(8).random(len(ytr)) < 0.08, 1 - ytr, ytr)
    mn = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, C=0.1)).fit(Xtr, yn)
    a["v_noisy_train_test_acc"] = _r(100 * accuracy_score(yte, mn.predict(Xte)), 1)

    # ---------------- cheque digits (OCR) ----------------
    dg = load_digits()
    Xd, yd = dg.data / 16.0, dg.target
    Xa, Xb, ya, yb = train_test_split(Xd, yd, test_size=0.5, random_state=0, stratify=yd)
    a["v_digits_n"], a["v_digits_pixels"] = int(len(yd)), int(Xd.shape[1])
    ocr = {"Logistic regression": LogisticRegression(max_iter=3000), "Support vector machine": SVC(gamma="scale", probability=True, random_state=0),
           "Small neural network": MLPClassifier(hidden_layer_sizes=(64,), alpha=1e-3, max_iter=800, random_state=0)}
    oacc, probs = {}, {}
    for nm, m in ocr.items():
        m.fit(Xa, ya)
        oacc[nm] = _r(100 * accuracy_score(yb, m.predict(Xb)), 1)
        probs[nm] = m.predict_proba(Xb)
    a["v_ocr_acc"] = oacc
    best = max(oacc, key=oacc.get)
    a["v_ocr_best"] = best
    pb = probs[best]
    pred = pb.argmax(1)
    cm = confusion_matrix(yb, pred)
    np.fill_diagonal(cm, 0)
    i, j = np.unravel_index(cm.argmax(), cm.shape)
    a["v_ocr_top_confusion"] = {"true": int(i), "read_as": int(j), "count": int(cm[i, j])}
    acc_digit = (pred == yb).mean()
    a["v_ocr_digit_acc"] = _r(100 * acc_digit, 2)
    # 6-digit cheque amounts
    rngc = np.random.default_rng(11)
    idx = rngc.integers(0, len(yb), (5000, 6))
    correct = (pred[idx] == yb[idx]).all(1)
    conf = pb.max(1)[idx].min(1)
    a["v_cheque_field_acc"] = _r(100 * correct.mean(), 1)
    a["v_cheque_field_acc_theory"] = _r(100 * acc_digit ** 6, 1)
    route = {}
    curve = []
    for t in np.round(np.linspace(0, 0.99, 34), 3):
        auto = conf >= t
        curve.append([float(t), _r(100 * auto.mean(), 1), _r(100 * (1 - correct[auto].mean()) if auto.any() else 0, 2)])
    a["v_route_curve"] = curve
    for t in (0.0, 0.5, 0.7, 0.8, 0.9, 0.95, 0.99):
        auto = conf >= t
        route[str(t)] = {"auto_pct": _r(100 * auto.mean(), 1), "error_pct": _r(100 * (1 - correct[auto].mean()) if auto.any() else 0, 2)}
    a["v_route"] = route
    ok = [float(t) for t, v in route.items() if v["error_pct"] <= 0.5]
    tsel = min(ok) if ok else 0.99
    a["v_route_threshold"] = tsel
    a["v_route_auto_at_thr"] = route[str(tsel)]["auto_pct"]
    # a smudged scanner batch
    Xs = np.clip(Xb + np.random.default_rng(3).normal(0, 0.25, Xb.shape), 0, 1)
    a["v_ocr_smudged_acc"] = _r(100 * accuracy_score(yb, ocr[best].predict(Xs)), 1)

    nn_ = a["v_cls"]["Small neural network on raw pixels"]
    checks = {"augmentation fixes dim store": a["v_aug"]["rec_dim"] > nn_["rec_dim"] + 30,
              "accuracy paradox in the dark": nn_["acc_dim"] > 85 and nn_["rec_dim"] < 50,
              "hand features break in the dark": a["v_cls"]["Logistic regression on hand-made features"]["acc_dim"] < 90,
              "detection works on test stores": det["test stores"]["recall"] > 70,
              "S07 dims": a["v_bright_s7_after"] < 0.7 * a["v_bright_s7_before"],
              "S03 blurry": a["v_sharpness_by_store"]["S03"] < 0.7 * np.median(list(a["v_sharpness_by_store"].values())),
              "kappa below agreement": a["v_kappa"] < a["v_agree_pct"] / 100,
              "cheque field acc < digit acc": a["v_cheque_field_acc"] < a["v_ocr_digit_acc"]}
    bad = [k for k, ok in checks.items() if not ok]
    if bad and __import__("os").environ.get("SB_NOGUARD"):
        print("GUARDS", bad)
    else:
        assert not bad, f"Vision guards failed: {bad}"
    return a
