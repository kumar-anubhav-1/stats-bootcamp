"""Interactive charts for Day 11 (computer vision). Registered into tools.charts.REG on import."""
from __future__ import annotations

import numpy as np

from tools.charts import BLUE, GREEN, GREY, ORANGE, RED, ROOT, L, buttons, chart, r, slider
from tools.charts_ml import answers


def _imgs():
    from datagen import vision as V
    return V.load(ROOT / "data" / "vision")


def _rgb(img):
    return img.astype(int).tolist()


def _gap_shapes(gaps, y0=4, y1=46, color=RED):
    return [{"type": "rect", "x0": a, "x1": b, "y0": y0, "y1": y1, "line": {"color": color, "width": 2}} for a, b in gaps]


@chart
def c_cv_shelves():
    imgs, meta, gaps = _imgs()
    gm = {i: list(zip(g.x0, g.x1)) for i, g in gaps.groupby("image_id")}
    pick = []
    for nm, q in (("normal camera (store S09)", (meta.store_id == "S09")), ("dim camera (S07, week 6)", (meta.store_id == "S07") & (meta.week == 6)),
                  ("blurry camera (S03)", meta.store_id == "S03")):
        cand = meta[q & (meta.n_gaps >= 1)]
        pick.append((nm, int(cand.image_id.iloc[0])))
    data, shapes, titles = [], [], []
    for i, (nm, k) in enumerate(pick):
        data.append({"type": "image", "z": _rgb(imgs[k]), "visible": i == 0, "name": nm})
        shapes.append(_gap_shapes(gm.get(k, [])))
        titles.append(f"Shelf photo — {nm}. Red boxes = labelled out-of-stock gaps")
    lay = L(titles[0], "pixel column (x)", "pixel row (y)", height=330, shapes=shapes[0])
    lay["updatemenus"] = [{"type": "buttons", "direction": "right", "x": 0, "y": 1.3, "xanchor": "left", "buttons": [
        {"method": "update", "label": nm.split(" (")[0], "args": [{"visible": [j == i for j in range(len(pick))]}, {"title.text": titles[i], "shapes": shapes[i]}]}
        for i, (nm, _) in enumerate(pick)]}]
    return {"data": data, "layout": lay}


@chart
def c_cv_pixels():
    imgs, meta, gaps = _imgs()
    img = imgs[int(meta[(meta.store_id == "S09") & (meta.n_gaps >= 1)].image_id.iloc[0])]
    crop = img[20:36, 0:24, :]
    data = [{"type": "image", "z": _rgb(crop), "visible": True, "name": "colour"}]
    names = ["Red channel", "Green channel", "Blue channel"]
    for c in range(3):
        data.append({"type": "heatmap", "z": crop[:, :, c].tolist(), "text": crop[:, :, c].tolist(), "texttemplate": "%{text}",
                     "colorscale": [[0, "black"], [1, ["red", "green", "blue"][c]]], "zmin": 0, "zmax": 255, "showscale": False,
                     "visible": False, "name": names[c], "textfont": {"size": 8}})
    titles = ["A 16 × 24-pixel corner of a shelf photo, in colour", *[f"{n}: every pixel is a number from 0 (dark) to 255 (bright)" for n in names]]
    lay = L(titles[0], "pixel column", "pixel row", height=420, yaxis={"autorange": "reversed"})
    lay["updatemenus"] = buttons(["colour", "red", "green", "blue"], [[j == i for j in range(4)] for i in range(4)], titles, y=1.22)
    return {"data": data, "layout": lay}


@chart
def c_cv_convolution():
    imgs, meta, _ = _imgs()
    g = imgs[int(meta[(meta.store_id == "S09") & (meta.n_gaps >= 1)].image_id.iloc[0])].mean(-1)
    K = {"original": np.array([[0, 0, 0], [0, 1, 0], [0, 0, 0]]), "blur (average)": np.ones((3, 3)) / 9,
         "vertical edges": np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]), "horizontal edges": np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]]),
         "sharpen": np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])}
    P = np.pad(g, 1, mode="edge")
    data, titles = [], []
    for i, (nm, k) in enumerate(K.items()):
        out = sum(k[a, b] * P[a:a + g.shape[0], b:b + g.shape[1]] for a in range(3) for b in range(3))
        if "edges" in nm:
            out = np.abs(out)
        data.append({"type": "heatmap", "z": [r(row, 1) for row in out], "colorscale": "Greys", "reversescale": True, "showscale": False,
                     "visible": i == 0, "name": nm})
        titles.append(f"Filter: {nm} — kernel {k.round(2).tolist()}")
    vis = [[j == i for j in range(len(K))] for i in range(len(K))]
    lay = L(titles[0], "pixel column", "pixel row", height=330, yaxis={"autorange": "reversed"})
    lay["sliders"] = slider(list(K), vis, "filter: ", titles)
    return {"data": data, "layout": lay}


@chart
def c_cv_iou():
    true = (80, 104)
    shifts = list(range(-24, 25, 4))
    data = [{"type": "scatter", "x": [true[0], true[1], true[1], true[0], true[0]], "y": [0, 0, 1, 1, 0], "fill": "toself",
             "fillcolor": "rgba(31,122,77,0.25)", "line": {"color": GREEN}, "name": "labelled gap (truth)"}]
    titles = []
    for i, s in enumerate(shifts):
        p = (true[0] + s - 2, true[1] + s + 2)
        inter = max(0, min(p[1], true[1]) - max(p[0], true[0]))
        union = max(p[1], true[1]) - min(p[0], true[0])
        iou = inter / union
        data.append({"type": "scatter", "x": [p[0], p[1], p[1], p[0], p[0]], "y": [0.1, 0.1, 0.9, 0.9, 0.1], "fill": "toself",
                     "fillcolor": "rgba(192,57,43,0.25)", "line": {"color": RED}, "name": "predicted gap", "visible": i == len(shifts) // 2})
        titles.append(f"IoU = overlap ÷ union = {inter} ÷ {union} = {iou:.2f} → " + ("counts as a hit at IoU ≥ 0.5" if iou >= 0.5 else "a miss (and a false alarm)"))
    vis = [[True] + [j == i for j in range(len(shifts))] for i in range(len(shifts))]
    lay = L(titles[len(shifts) // 2], "pixel column", None, height=320, yaxis={"visible": False, "range": [-0.2, 1.2]}, xaxis={"range": [40, 150], "title": {"text": "pixel column"}})
    lay["sliders"] = slider([f"{s:+d}px" for s in shifts], vis, "shift the prediction: ", titles, active=len(shifts) // 2)
    return {"data": data, "layout": lay}


@chart
def c_cv_scores():
    ex = answers().get("v_examples", {})
    if not ex:
        return {"data": [], "layout": L("run the build to compute examples")}
    data, shapes, titles, vis = [], [], [], []
    views = [("test", "aug", "Clean store: P(gap) along the shelf — peaks sit on the labelled gaps"),
             ("dim", "noaug", "Dim store, network trained without augmentation: the gaps are missed"),
             ("dim", "aug", "Dim store, network trained with brightness augmentation: gaps found again")]
    for i, (k, m, t) in enumerate(views):
        e = ex[k]
        data.append({"type": "scatter", "x": e["x"], "y": e[m], "mode": "lines+markers", "line": {"color": BLUE}, "visible": i == 0, "name": "P(gap) per window"})
        shapes.append([{"type": "rect", "x0": a, "x1": b, "y0": 0, "y1": 1, "fillcolor": "rgba(192,57,43,0.15)", "line": {"width": 0}} for a, b in e["gaps"]]
                      + [{"type": "line", "x0": 0, "x1": 192, "y0": 0.5, "y1": 0.5, "line": {"color": GREY, "dash": "dash"}}])
        titles.append(t)
    lay = L(titles[0], "pixel column (window centre)", "model's probability of 'gap'", shapes=shapes[0], yaxis={"range": [-0.05, 1.05]})
    lay["updatemenus"] = [{"type": "buttons", "direction": "right", "x": 0, "y": 1.22, "xanchor": "left", "buttons": [
        {"method": "update", "label": lab, "args": [{"visible": [j == i for j in range(3)]}, {"title.text": titles[i], "shapes": shapes[i]}]}
        for i, lab in enumerate(["clean store", "dim, no augmentation", "dim, with augmentation"])]}]
    return {"data": data, "layout": lay}


@chart
def c_cv_drift():
    imgs, meta, _ = _imgs()
    m = meta.assign(b=[imgs[i].mean() / 255 for i in range(len(meta))])
    wk = m.groupby(["store_id", "week"]).b.mean().reset_index()
    data = []
    for s, g in wk.groupby("store_id"):
        data.append({"type": "scatter", "x": g.week.tolist(), "y": r(g.b, 3), "name": s, "mode": "lines+markers",
                     "line": {"width": 4 if s == "S07" else 1.5, "color": RED if s == "S07" else GREY}})
    return {"data": data, "layout": L("Average image brightness by store and week: one camera goes dim from week 5", "week", "mean brightness (0–1)")}


@chart
def c_cv_digits():
    from sklearn.datasets import load_digits
    from sklearn.model_selection import train_test_split
    from sklearn.svm import SVC
    d = load_digits()
    Xa, Xb, ya, yb, ia, ib = train_test_split(d.data / 16, d.target, np.arange(len(d.target)), test_size=0.5, random_state=0, stratify=d.target)
    m = SVC(gamma="scale", random_state=0).fit(Xa, ya)
    p = m.predict(Xb)
    wrong = np.where(p != yb)[0][:12]
    right = np.arange(12)

    def mosaic(idx):
        tiles = [np.pad(d.images[ib[k]], 1, constant_values=0) for k in idx]
        return np.hstack(tiles), [f"{yb[k]}→{p[k]}" for k in idx]

    data, ticks = [], []
    for i, (nm, idx) in enumerate((("read correctly", right), ("misread", wrong))):
        z, lab = mosaic(idx)
        data.append({"type": "heatmap", "z": z[::-1].tolist(), "colorscale": "Greys", "reversescale": True, "showscale": False, "visible": i == 0, "name": nm,
                     "hoverinfo": "skip"})
        ticks.append(lab)
    centers = [10 * k + 5 for k in range(12)]
    titles = ["Handwritten cheque digits (8 × 8 pixels) read correctly — labels show true → read",
              "Handwritten cheque digits misread by the model — labels show true → read"]
    lay = L(titles[0], "true → read", None, height=300, yaxis={"visible": False, "scaleanchor": "x"},
            xaxis={"tickvals": centers, "ticktext": ticks[0], "title": {"text": "true → read"}})
    lay["updatemenus"] = [{"type": "buttons", "direction": "right", "buttons": [
        {"method": "update", "label": nm, "args": [{"visible": [j == i for j in range(2)]}, {"title.text": titles[i], "xaxis.ticktext": ticks[i]}]}
        for i, nm in enumerate(["read correctly", "misread"])]}]
    return {"data": data, "layout": lay}


@chart
def c_cv_confidence():
    c = answers().get("v_route_curve", [])
    t = [x[0] for x in c]
    return {"data": [{"type": "scatter", "x": t, "y": [x[1] for x in c], "name": "% of cheques read automatically", "line": {"color": BLUE, "width": 3}},
                     {"type": "scatter", "x": t, "y": [x[2] for x in c], "name": "% of automatic reads with a wrong amount", "yaxis": "y2",
                      "line": {"color": RED, "width": 3}}],
            "layout": L("Confidence threshold for 6-digit cheque amounts: raise it → fewer errors, more sent to people",
                        "minimum confidence required to auto-process", "% automated",
                        yaxis2={"overlaying": "y", "side": "right", "title": {"text": "% wrong among automated"}})}


@chart
def c_cv_map():
    """Computer-vision task ladder as a chart: input → output, with retail / banking examples (hover)."""
    tasks = [("Image classification", 1, "one label per image", "Is this shelf slot empty?  ·  Is this a cheque, an ID card or a bill?"),
             ("Object detection", 2, "boxes around objects", "Find every gap and every pack on the shelf  ·  Locate the signature and amount on a cheque"),
             ("Segmentation", 3, "a label for every pixel", "Exact shelf area per brand (share of shelf)  ·  Isolate a damaged region on a claim photo"),
             ("OCR / document AI", 3, "text and fields from images", "Read price labels and receipts  ·  Read cheque amounts, KYC documents"),
             ("Image generation", 4, "new images", "Product imagery and planogram mock-ups  ·  Synthetic documents to test fraud checks")]
    return {"data": [{"type": "scatter", "mode": "markers+text", "x": [t[1] for t in tasks], "y": [5 - i for i in range(len(tasks))],
                      "text": [f"<b>{t[0]}</b> — {t[2]}" for t in tasks], "textposition": "middle right", "marker": {"size": 18, "color": [BLUE, GREEN, ORANGE, ORANGE, RED]},
                      "customdata": [t[3] for t in tasks], "hovertemplate": "%{customdata}<extra></extra>"}],
            "layout": L("Computer-vision tasks, from simplest to most complex — hover for a retail · banking example", "complexity →", None,
                        height=380, xaxis={"range": [0.5, 7.5], "title": {"text": "complexity →"}}, yaxis={"visible": False}, showlegend=False)}
