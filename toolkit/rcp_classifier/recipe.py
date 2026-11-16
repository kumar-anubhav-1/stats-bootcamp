"""rcp_classifier: baseline vs gradient boosting with honest validation, imbalance handling, evaluation and explanations.

Navigator nodes N-ML-GBM, N-ML-LEAK, N-ML-IMBALANCE, N-METRIC-*. Roles: target (0/1, required), features (list, required),
time (optional: column for an out-of-time split).
Params:
  split: random | time            time requires the `time` role and `cutoff` (train <= cutoff, test > cutoff)
  test_size: 0.3 · seed: 42
  models: [logistic, gbm]         also: random_forest
  class_weight: none | balanced
  leakage_auc: 0.95               warn when test AUC exceeds this (credit/fraud norms) and name the dominant feature
  capacity_k: [100, 500]          precision/recall in the top k scored cases (alert queues)
  cost_fn / cost_fp: numbers      expected-cost threshold (cost of a missed positive vs a false alarm)
  categorical: [cols]             one-hot encoded
Outputs: metrics by model (ROC-AUC, Gini, PR-AUC, KS, Brier, precision@k), lift by decile, calibration table, permutation importance,
threshold table, leakage warnings, narrative.
"""
from __future__ import annotations

import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score, roc_curve, precision_recall_curve
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, fmt, output_dir, read_dataset, schema_check, write_run

warnings.filterwarnings("ignore")
RECIPE = "rcp_classifier"
SCHEMA = {"target": {"required": True}, "time": {"required": False}}


def ks(y, s):
    o = np.argsort(-s)
    yy = y[o]
    return float(np.max(np.cumsum(yy) / yy.sum() - np.cumsum(1 - yy) / (1 - yy).sum()))


def run(cfg: dict):
    log = RowLog()
    df = read_dataset(cfg)
    log.add("load", len(df), len(df), cfg["dataset"]["path"])
    errors, warnings_ = schema_check(df, cfg, SCHEMA)
    if errors:
        raise SchemaError("\n".join(errors))
    df = apply_filters(df, cfg, log)
    c, prm = cfg["columns"], cfg.get("params", {}) or {}
    y_col, feats, tcol = c["target"], list(c.get("features") or []), c.get("time")
    miss = [f for f in feats if f not in df.columns]
    if miss:
        raise SchemaError(f"features not found: {miss}")
    vals = set(df[y_col].dropna().unique())
    if not vals <= {0, 1, True, False}:
        raise SchemaError(f"target `{y_col}` must be 0/1; found {sorted(vals)[:5]}")
    b = len(df)
    df = df.dropna(subset=[y_col])
    log.add("drop missing target", b, len(df))
    cats = [f for f in feats if f in (prm.get("categorical") or [])
            or not (pd.api.types.is_numeric_dtype(df[f]) or pd.api.types.is_bool_dtype(df[f]))]
    X = df[feats].copy()
    for col in X.columns:
        if pd.api.types.is_bool_dtype(X[col]) or str(X[col].dtype) in ("Int64", "Float64"):
            X[col] = X[col].astype(float)
    X = pd.get_dummies(X, columns=cats, drop_first=True, dtype=float)
    for col in X.columns:
        if X[col].isna().any():
            X[f"{col}_missing"] = X[col].isna().astype(float)
            X[col] = X[col].fillna(X[col].median())
    y = df[y_col].astype(int).to_numpy()
    seed = int(prm.get("seed", 42))
    if prm.get("split", "random") == "time":
        if not tcol:
            raise SchemaError("split: time needs a `time` role and params.cutoff")
        cut = prm["cutoff"]
        tr = (df[tcol].astype(str) <= str(cut)).to_numpy()
        Xtr, Xte, ytr, yte = X[tr], X[~tr], y[tr], y[~tr]
        split_txt = f"out-of-time: train `{tcol}` ≤ {cut} ({tr.sum():,}), test > {cut} ({(~tr).sum():,})"
    else:
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=float(prm.get("test_size", 0.3)), random_state=seed, stratify=y)
        split_txt = f"random stratified: train {len(ytr):,}, test {len(yte):,}"
    cw = None if prm.get("class_weight", "none") == "none" else "balanced"
    zoo = {"logistic": make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000, class_weight=cw)),
           "gbm": HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0,
                                                 class_weight=cw, random_state=seed),
           "random_forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=20, class_weight=cw, n_jobs=-1, random_state=seed)}
    out = output_dir(cfg, RECIPE)
    caps = [int(k) for k in prm.get("capacity_k", [100, 500])]
    res, preds = {}, {}
    for name in prm.get("models", ["logistic", "gbm"]):
        m = zoo[name].fit(Xtr, ytr)
        p = m.predict_proba(Xte)[:, 1]
        ptr = m.predict_proba(Xtr)[:, 1]
        o = np.argsort(-p)
        r = {"auc": roc_auc_score(yte, p), "train_auc": roc_auc_score(ytr, ptr), "pr_auc": average_precision_score(yte, p),
             "ks": ks(yte, p), "brier": brier_score_loss(yte, p), "mean_pred": float(p.mean()), "actual_rate": float(yte.mean())}
        r["gini"] = 2 * r["auc"] - 1
        for k in caps:
            k = min(k, len(p))
            r[f"precision_at_{k}"] = float(yte[o[:k]].mean())
            r[f"recall_at_{k}"] = float(yte[o[:k]].sum() / max(yte.sum(), 1))
        res[name], preds[name] = r, (m, p)
    best = max(res, key=lambda k: res[k]["auc"])
    m, p = preds[best]
    o = np.argsort(-p)
    dec = np.array_split(o, 10)
    lift = pd.DataFrame({"decile": range(1, 11), "n": [len(d) for d in dec], "rate": [yte[d].mean() for d in dec],
                         "lift": [yte[d].mean() / yte.mean() for d in dec],
                         "cum_capture": np.cumsum([yte[d].sum() for d in dec]) / yte.sum()})
    lift.to_csv(out / "lift_by_decile.csv", index=False)
    oc = np.argsort(p)
    cal = pd.DataFrame([{"predicted": p[d].mean(), "observed": yte[d].mean(), "n": len(d)} for d in np.array_split(oc, 10)])
    cal.to_csv(out / "calibration.csv", index=False)
    nimp = min(len(yte), 4000)
    pim = permutation_importance(m, Xte.iloc[:nimp], yte[:nimp], scoring="roc_auc", n_repeats=3, random_state=seed)
    imp = pd.Series(pim.importances_mean, index=X.columns).sort_values(ascending=False)
    imp.to_csv(out / "permutation_importance.csv", header=["auc_drop"])
    thr_rows = []
    cfn, cfp = prm.get("cost_fn"), prm.get("cost_fp")
    for t in (0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5):
        flag = p >= t
        tp, fp, fn = int((flag & (yte == 1)).sum()), int((flag & (yte == 0)).sum()), int((~flag & (yte == 1)).sum())
        row = {"threshold": t, "flagged_pct": flag.mean(), "precision": tp / max(tp + fp, 1), "recall": tp / max(yte.sum(), 1),
               "accuracy": float((flag.astype(int) == yte).mean())}
        if cfn is not None and cfp is not None:
            row["expected_cost"] = fn * float(cfn) + fp * float(cfp)
        thr_rows.append(row)
    thr = pd.DataFrame(thr_rows)
    thr.to_csv(out / "thresholds.csv", index=False)
    leak_thr = float(prm.get("leakage_auc", 0.95))
    leak = [f"Test AUC {res[k]['auc']:.3f} for {k} exceeds {leak_thr} — suspect leakage; dominant feature: `{imp.index[0]}`." for k in res if res[k]["auc"] > leak_thr]
    gaps = [f"{k}: train AUC {res[k]['train_auc']:.3f} vs test {res[k]['auc']:.3f} — overfitting." for k in res if res[k]["train_auc"] - res[k]["auc"] > 0.05]
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
    for k, (_, pp) in preds.items():
        f_, t_, _ = roc_curve(yte, pp)
        ax[0].plot(f_, t_, label=f"{k} ({res[k]['auc']:.3f})")
        pr, rc, _ = precision_recall_curve(yte, pp)
        ax[1].plot(rc, pr, label=f"{k} ({res[k]['pr_auc']:.3f})")
    ax[0].plot([0, 1], [0, 1], "k:")
    ax[0].set_title("ROC")
    ax[1].axhline(yte.mean(), color="k", ls=":")
    ax[1].set_title("Precision-recall")
    for a_ in ax:
        a_.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(out / "roc_pr.png", dpi=110)
    plt.close()
    metrics = {"split": split_txt, "best_model": best, "n_features": int(X.shape[1]),
               "models": {k: {kk: float(vv) for kk, vv in v.items()} for k, v in res.items()},
               "top_decile_lift": float(lift.lift.iloc[0]), "leakage_warnings": len(leak),
               "_tolerance": {"rtol": 0.05, "atol": 0.03}}
    write_run(out, RECIPE, cfg, data_hash(pd.concat([X, pd.Series(y, index=X.index, name="_y")], axis=1)), metrics, log, errors, warnings_)
    L = [f"# Classifier: `{y_col}`", "", f"Split: {split_txt} · event rate (test) {yte.mean():.2%} · {X.shape[1]} features" +
         (f" · class_weight={cw}" if cw else ""), ""]
    if leak:
        L += ["!!! danger \"Leakage alert\"", *[f"    {x}" for x in leak], ""]
    L += ["## Model comparison (test set)", "", "| Model | ROC-AUC | Gini | PR-AUC | KS | Brier | train AUC | " + " | ".join(f"precision@{k}" for k in caps) + " |",
          "| --- | --- | --- | --- | --- | --- | --- | " + " | ".join("---" for _ in caps) + " |"]
    for k, r in res.items():
        L.append(f"| {k} | {r['auc']:.3f} | {r['gini']:.3f} | {r['pr_auc']:.3f} | {r['ks']:.3f} | {r['brier']:.4f} | {r['train_auc']:.3f} | "
                 + " | ".join(f"{r[f'precision_at_{min(kk, len(p))}']:.1%}" for kk in caps) + " |")
    L += ["", f"Best by AUC: **{best}**. Mean predicted rate {res[best]['mean_pred']:.2%} vs actual {res[best]['actual_rate']:.2%}" +
          (" — **miscalibrated (recalibrate before using as a probability).**" if abs(res[best]['mean_pred'] - res[best]['actual_rate']) > 0.25 * res[best]['actual_rate'] else ".")]
    L += [f"- {g}" for g in gaps]
    L += ["", "## Lift by decile (best model)", "", "| Decile | Rate | Lift | Cumulative capture |", "| --- | --- | --- | --- |"]
    L += [f"| {int(r.decile)} | {r.rate:.2%} | {r.lift:.2f} | {r.cum_capture:.0%} |" for r in lift.itertuples()]
    L += ["", "## Calibration (deciles of predicted probability)", "", "| Predicted | Observed |", "| --- | --- |"]
    L += [f"| {r.predicted:.2%} | {r.observed:.2%} |" for r in cal.itertuples()]
    L += ["", "## Permutation importance (AUC drop when shuffled)", "", "| Feature | AUC drop |", "| --- | --- |"]
    L += [f"| {k} | {v:.4f} |" for k, v in imp.head(8).items()]
    L += ["", "## Thresholds", "", "| Threshold | Flagged | Precision | Recall | Accuracy" + (" | Expected cost |" if "expected_cost" in thr else " |"),
          "| --- | --- | --- | --- | ---" + (" | --- |" if "expected_cost" in thr else " |")]
    for r in thr.itertuples():
        L.append(f"| {r.threshold} | {r.flagged_pct:.1%} | {r.precision:.1%} | {r.recall:.1%} | {r.accuracy:.1%}" + (f" | {r.expected_cost:,.0f} |" if "expected_cost" in thr else " |"))
    if "expected_cost" in thr:
        bt = thr.loc[thr.expected_cost.idxmin()]
        L += ["", f"Lowest expected cost at threshold **{bt.threshold}** (cost of a miss {cfn}, of a false alarm {cfp})."]
    L += ["", "## How to read this", "",
          "- Compare against the logistic baseline; complexity must earn its keep on held-out (ideally out-of-time) data.",
          "- For rare events read PR-AUC and precision@k, not accuracy (a model that predicts 'no' for everyone is ~99% accurate).",
          "- AUC far above domain norms (credit > 0.9) usually means leakage — a post-outcome field.",
          "- Choose thresholds from costs or capacity, not 0.5. Check calibration before using scores as probabilities.", "",
          "Files: `lift_by_decile.csv`, `calibration.csv`, `permutation_importance.csv`, `thresholds.csv`, `roc_pr.png`, `metrics.json`."]
    (out / "narrative.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:22]))
    return out
