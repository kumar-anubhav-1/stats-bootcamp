"""rcp_forecast: baselines + ETS / regression-with-seasonality / SARIMAX, rolling-origin backtest, WAPE / MASE / bias.

Navigator nodes N-FCST-SEASON, N-FCST-DRIVERS, N-FCST-INTERMITTENT. Roles: time (integer period, e.g. week), target,
exog (optional list of driver columns, averaged per period). Rows are summed per period (after filters) to one series.
Params: season_length 52 · horizon 8 · train_end (last training period) · origins [list] for the backtest ·
  models: [naive, seasonal_naive, moving_avg, holt_damped, regression_fourier, sarimax, croston, sba] · fourier_k 3 · log: true
"""
from __future__ import annotations

import warnings

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from toolkit.common.core import RowLog, SchemaError, apply_filters, data_hash, output_dir, read_dataset, schema_check, write_run

warnings.filterwarnings("ignore")
RECIPE = "rcp_forecast"
SCHEMA = {"time": {"required": True}, "target": {"required": True, "kind": "numeric"}}


def croston(y, h, alpha=0.1, sba=False):
    y = np.asarray(y, float)
    nz = np.where(y > 0)[0]
    if len(nz) == 0:
        return np.zeros(h)
    z, p, q = y[nz[0]], nz[0] + 1, 1
    for t in range(nz[0] + 1, len(y)):
        if y[t] > 0:
            z, p, q = alpha * y[t] + (1 - alpha) * z, alpha * q + (1 - alpha) * p, 1
        else:
            q += 1
    return np.full(h, z / p * ((1 - alpha / 2) if sba else 1))


def metrics(y, f, train, m=1):
    y, f, train = np.asarray(y, float), np.asarray(f, float), np.asarray(train, float)
    scale = np.mean(np.abs(train[m:] - train[:-m])) or 1.0
    return {"wape": float(np.abs(y - f).sum() / max(np.abs(y).sum(), 1e-9)), "mase": float(np.mean(np.abs(y - f)) / scale),
            "bias": float((f - y).sum() / max(y.sum(), 1e-9))}


def fit_forecast(name, ytr, t_tr, t_te, X_tr, X_te, m, K, use_log):
    h = len(t_te)
    if name == "naive":
        return np.full(h, ytr[-1])
    if name == "seasonal_naive":
        if len(ytr) < m:
            return np.full(h, ytr[-1])
        return np.array([ytr[len(ytr) - m + (i % m)] for i in range(h)])
    if name == "moving_avg":
        return np.full(h, ytr[-8:].mean())
    if name == "holt_damped":
        return ExponentialSmoothing(ytr, trend="add", damped_trend=True).fit().forecast(h)
    if name in ("croston", "sba"):
        return croston(ytr, h, sba=(name == "sba"))
    four = lambda t: np.column_stack([f(2 * np.pi * k * np.asarray(t, float) / m) for k in range(1, K + 1) for f in (np.sin, np.cos)])
    A_tr = np.column_stack([four(t_tr)] + ([X_tr] if X_tr is not None else []))
    A_te = np.column_stack([four(t_te)] + ([X_te] if X_te is not None else []))
    yy = np.log(np.clip(ytr, 1e-6, None)) if use_log else ytr
    if name == "regression_fourier":
        r = sm.OLS(yy, sm.add_constant(A_tr)).fit()
        f = r.predict(sm.add_constant(A_te, has_constant="add"))
    elif name == "sarimax":
        r = sm.tsa.SARIMAX(yy, exog=A_tr, order=(1, 0, 0), trend="c").fit(disp=False)
        f = r.forecast(h, exog=A_te)
    else:
        raise SchemaError(f"unknown model {name}")
    return np.exp(f) if use_log else f


def run(cfg: dict):
    log = RowLog()
    df = read_dataset(cfg)
    log.add("load", len(df), len(df), cfg["dataset"]["path"])
    errors, warnings_ = schema_check(df, cfg, SCHEMA)
    if errors:
        raise SchemaError("\n".join(errors))
    df = apply_filters(df, cfg, log)
    c, prm = cfg["columns"], cfg.get("params", {}) or {}
    t, y, ex = c["time"], c["target"], list(c.get("exog") or [])
    agg = {y: "sum", **{e: "mean" for e in ex}}
    for e in ex:
        if df[e].dtype == bool or str(df[e].dtype) == "boolean":
            df[e] = df[e].astype(float)
    s = df.groupby(t).agg(agg).sort_index()
    log.add(f"aggregate to one series per {t}", len(df), len(s))
    m, h, K = int(prm.get("season_length", 52)), int(prm.get("horizon", 8)), int(prm.get("fourier_k", 3))
    use_log = bool(prm.get("log", True)) and (s[y] > 0).all()
    train_end = prm.get("train_end", s.index[-h - 1])
    models = prm.get("models", ["naive", "seasonal_naive", "moving_avg", "holt_damped", "regression_fourier"])
    tv, yv = s.index.values, s[y].values.astype(float)
    Xv = s[ex].values.astype(float) if ex else None
    out = output_dir(cfg, RECIPE)
    tr, te = tv <= train_end, (tv > train_end) & (tv <= train_end + h)
    res, fcs = {}, {}
    for nm in models:
        f = fit_forecast(nm, yv[tr], tv[tr], tv[te], Xv[tr] if ex else None, Xv[te] if ex else None, m, K, use_log)
        fcs[nm], res[nm] = f, metrics(yv[te], f, yv[tr])
    bt_rows = []
    for o in prm.get("origins", [train_end]):
        trm, tem = tv <= o, (tv > o) & (tv <= o + h)
        if tem.sum() == 0:
            continue
        for nm in models:
            f = fit_forecast(nm, yv[trm], tv[trm], tv[tem], Xv[trm] if ex else None, Xv[tem] if ex else None, m, K, use_log)
            mt = metrics(yv[tem], f, yv[trm])
            bt_rows.append({"origin": int(o), "model": nm, **mt})
    bt = pd.DataFrame(bt_rows)
    bt.to_csv(out / "backtest.csv", index=False)
    summ = bt.groupby("model")[["wape", "mase", "bias"]].mean().sort_values("wape")
    pd.DataFrame({"period": tv[te], "actual": yv[te], **{k: v for k, v in fcs.items()}}).to_csv(out / "forecasts.csv", index=False)
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.plot(tv, yv, color="black", lw=1, label="actual")
    for nm, f in fcs.items():
        ax.plot(tv[te], f, lw=1.2, label=nm)
    ax.axvline(train_end, color="grey", ls=":")
    ax.legend(fontsize=7, ncol=3)
    ax.set_title(f"{y}: forecasts from period {train_end}")
    plt.tight_layout()
    plt.savefig(out / "forecast.png", dpi=110)
    plt.close()
    best = summ.index[0]
    metrics_out = {"train_end": int(train_end), "horizon": h, "season_length": m, "holdout": {k: v for k, v in res.items()},
                   "backtest_mean": summ.round(6).to_dict(orient="index"), "best_by_backtest": best,
                   "_tolerance": {"rtol": 0.02, "atol": 0.005}}
    write_run(out, RECIPE, cfg, data_hash(s), metrics_out, log, errors, warnings_)
    L = [f"# Forecast: `{y}` by `{t}`", "", f"{len(s)} periods · season length {m} · horizon {h} · drivers: {', '.join(ex) or 'none'} · log scale: {use_log}", "",
         f"## Hold-out (train ≤ {train_end})", "", "| Model | WAPE | MASE | Bias |", "| --- | --- | --- | --- |"]
    L += [f"| {k} | {v['wape']:.1%} | {v['mase']:.2f} | {v['bias']:+.1%} |" for k, v in sorted(res.items(), key=lambda kv: kv[1]["wape"])]
    L += ["", f"## Rolling-origin backtest (origins {', '.join(str(o) for o in prm.get('origins', [train_end]))})", "",
          "| Model | mean WAPE | mean MASE | mean bias |", "| --- | --- | --- | --- |"]
    L += [f"| {k} | {r.wape:.1%} | {r.mase:.2f} | {r.bias:+.1%} |" for k, r in summ.iterrows()]
    sn = summ.wape.get("seasonal_naive")
    L += ["", f"Best by backtest: **{best}**" + (f" — {(1 - summ.wape[best] / sn):.0%} lower WAPE than seasonal naive." if sn and best != "seasonal_naive" else "."),
          "", "## How to read this", "",
          "- Always beat the **seasonal naive** baseline before using anything fancier; MASE < 1 means better than a naive one-step forecast.",
          "- WAPE = total absolute error ÷ total actual (robust to zeros). Bias shows systematic over/under-forecasting — often the costlier error.",
          "- Judge models on several forecast origins (rolling backtest), not one hold-out window.",
          "- For intermittent items, MAE-based metrics reward forecasting zero; check bias and service levels (L7.4).", "",
          "Files: `forecasts.csv`, `backtest.csv`, `forecast.png`, `metrics.json`."]
    (out / "narrative.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:24]))
    return out
