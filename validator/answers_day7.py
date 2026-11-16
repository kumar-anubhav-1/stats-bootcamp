"""Computed answers for Day 7 (time series and forecasting, change-points, censored demand, inventory). Keys d7_."""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import acf, adfuller, kpss

from . import measures as M

warnings.filterwarnings("ignore")


def _r(x, nd=3):
    return round(float(x), nd)


def wape(y, f):
    y, f = np.asarray(y, float), np.asarray(f, float)
    return float(np.abs(y - f).sum() / np.abs(y).sum())


def bias(y, f):
    y, f = np.asarray(y, float), np.asarray(f, float)
    return float((f - y).sum() / y.sum())


def mase(y, f, train, m=1):
    train = np.asarray(train, float)
    scale = np.mean(np.abs(train[m:] - train[:-m]))
    return float(np.mean(np.abs(np.asarray(y) - np.asarray(f))) / scale)


def fourier(weeks, period=52, K=3):
    w = np.asarray(weeks, float)
    return np.column_stack([f(2 * np.pi * k * w / period) for k in range(1, K + 1) for f in (np.sin, np.cos)])


def croston(y, h, alpha=0.1, sba=False):
    y = np.asarray(y, float)
    nz = np.where(y > 0)[0]
    if len(nz) == 0:
        return np.zeros(h)
    z, p = y[nz[0]], (nz[0] + 1)
    q = 1
    for t in range(nz[0] + 1, len(y)):
        if y[t] > 0:
            z = alpha * y[t] + (1 - alpha) * z
            p = alpha * q + (1 - alpha) * p
            q = 1
        else:
            q += 1
    f = z / p
    if sba:
        f *= (1 - alpha / 2)
    return np.full(h, f)


def ses_level(y, alpha=0.1, init_n=8):
    y = np.asarray(y, float)
    lvl = y[:init_n].mean()
    for v in y:
        lvl = alpha * v + (1 - alpha) * lvl
    return float(lvl)


def binseg_one(x, minseg=8):
    x = np.asarray(x, float)
    best, bk = np.inf, None
    for k in range(minseg, len(x) - minseg):
        sse = ((x[:k] - x[:k].mean()) ** 2).sum() + ((x[k:] - x[k:].mean()) ** 2).sum()
        if sse < best:
            best, bk = sse, k
    return bk


def compute_day7(data=str(M.DATA)) -> dict:
    a: dict = {}
    ws = M.load("retail", "weekly_store", data)
    sc = M.load("retail", "weekly_store_category", data)
    cal = M.load("retail", "calendar", data).drop_duplicates("week").set_index("week")
    chain = ws.groupby("week").units.sum()
    hol = cal.holiday_flag.reindex(chain.index).astype(int)
    a["d7_weeks"] = len(chain)

    # ================= L7.1 decomposition, stationarity, ACF =================
    stl = STL(chain.values, period=52, robust=True).fit()
    var_r, var_sr = np.var(stl.resid), np.var(stl.seasonal + stl.resid)
    var_tr = np.var(stl.trend + stl.resid)
    a["d7_seas_strength"] = _r(max(0, 1 - var_r / var_sr), 2)
    a["d7_trend_strength"] = _r(max(0, 1 - var_r / var_tr), 2)
    ac = acf(chain.values, nlags=53)
    a["d7_acf1"], a["d7_acf52"] = _r(ac[1], 2), _r(ac[52], 2)
    a["d7_adf_p"] = _r(adfuller(chain.values, autolag="AIC")[1], 3)
    a["d7_kpss_p"] = _r(kpss(chain.values, regression="c", nlags="auto")[1], 3)
    r11 = M.R11(data)
    a["d7_frisat_ratio"], a["d7_q4_ratio"], a["d7_hol_ratio"] = r11["measured"], r11["q4_vs_other"], r11["holiday_vs_non"]
    peak_w = int(chain.idxmax())
    a["d7_peak_week"], a["d7_peak_units"] = peak_w, int(chain.max())
    a["d7_peak_holiday"] = bool(hol.loc[peak_w])
    a["d7_mean_units"] = int(chain.mean())
    # finance monthly delinquency series (share of open accounts 30+ DPD by calendar month)
    pm = M.load("finance", "performance_monthly", data)
    dq = pm.groupby("calendar_month").agg(rate=("dpd", lambda x: (x >= 30).mean()), n=("dpd", "size"))
    dq = dq[dq.n >= 2000]
    a["d7_dq_months"] = len(dq)
    a["d7_dq_first"], a["d7_dq_last"] = _r(100 * dq.rate.iloc[0], 2), _r(100 * dq.rate.iloc[-1], 2)
    a["d7_dq_adf_p"] = _r(adfuller(dq.rate.values, autolag="AIC")[1], 3)
    a["d7_dq_adf_p_diff"] = _r(adfuller(np.diff(dq.rate.values), autolag="AIC")[1], 3)
    k = binseg_one(dq.rate.values, 4)
    a["d7_dq_break_month"] = dq.index[k]
    a["d7_dq_before"], a["d7_dq_after"] = _r(100 * dq.rate.values[:k].mean(), 2), _r(100 * dq.rate.values[k:].mean(), 2)

    # ================= L7.2 / L7.3 forecasting and backtesting =================
    bev = sc[sc.category == "Beverages"].groupby("week").units.sum()
    temp = ws.groupby("week").avg_temperature_c.mean()
    y = bev.values.astype(float)
    weeks = bev.index.values
    tr_end = 78
    tr, te = weeks <= tr_end, weeks > tr_end
    ytr, yte = y[tr], y[te]
    h = int(te.sum())
    fc = {}
    fc["naive"] = np.full(h, ytr[-1])
    fc["seasonal_naive"] = y[np.where(te)[0] - 52]
    fc["moving_avg_8"] = np.full(h, ytr[-8:].mean())
    fc["holt_damped"] = ExponentialSmoothing(ytr, trend="add", damped_trend=True).fit().forecast(h)
    X = np.column_stack([fourier(weeks, 52, 3), hol.reindex(bev.index).values, temp.reindex(bev.index).values])
    reg = sm.OLS(np.log(ytr), sm.add_constant(X[tr])).fit()
    fc["regression_fourier"] = np.exp(reg.predict(sm.add_constant(X[te], has_constant="add")))
    sar = sm.tsa.SARIMAX(np.log(ytr), exog=X[tr], order=(1, 0, 0), trend="c").fit(disp=False)
    fc["sarimax"] = np.exp(sar.forecast(h, exog=X[te]))
    res = {}
    for k_, f in fc.items():
        res[k_] = {"wape": _r(100 * wape(yte, f), 1), "mase": _r(mase(yte, f, ytr, 1), 2), "bias": _r(100 * bias(yte, f), 1)}
    a["d7_fc"] = res
    a["d7_fc_best"] = min(res, key=lambda k_: res[k_]["wape"])
    a["d7_bev_mean"] = int(y.mean())
    # rolling-origin backtest (origins 78, 86, 94; horizon 8) for seasonal naive vs regression
    bt = []
    for o in (78, 86, 94):
        trm, tem = weeks <= o, (weeks > o) & (weeks <= o + 8)
        ytr_o, yte_o = y[trm], y[tem]
        sn = y[np.where(tem)[0] - 52]
        rg = sm.OLS(np.log(ytr_o), sm.add_constant(X[trm])).fit()
        rf = np.exp(rg.predict(sm.add_constant(X[tem], has_constant="add")))
        bt.append({"origin": o, "snaive_wape": _r(100 * wape(yte_o, sn), 1), "reg_wape": _r(100 * wape(yte_o, rf), 1)})
    a["d7_backtest"] = bt
    a["d7_bt_mean_snaive"] = _r(np.mean([b["snaive_wape"] for b in bt]), 1)
    a["d7_bt_mean_reg"] = _r(np.mean([b["reg_wape"] for b in bt]), 1)
    # WAPE by level: chain vs store-level for the same regression approach (store forecasts from chain shares)
    st = sc[sc.category == "Beverages"].pivot(index="week", columns="store_id", values="units").astype(float)
    share = st[st.index <= tr_end].sum() / st[st.index <= tr_end].sum().sum()
    store_fc = np.outer(fc["regression_fourier"], share.values)
    a["d7_wape_chain"] = res["regression_fourier"]["wape"]
    a["d7_wape_store"] = _r(100 * np.abs(st[st.index > tr_end].values - store_fc).sum() / st[st.index > tr_end].values.sum(), 1)
    # finance: monthly total balance forecast
    bal = pm.groupby("calendar_month").balance.sum()
    bal = bal[pm.groupby("calendar_month").size() >= 2000]
    btr, bte = bal.values[:-6], bal.values[-6:]
    hb = ExponentialSmoothing(btr, trend="add", damped_trend=True).fit().forecast(6)
    a["d7_bal_wape_holt"] = _r(100 * wape(bte, hb), 1)
    a["d7_bal_wape_naive"] = _r(100 * wape(bte, np.full(6, btr[-1])), 1)
    a["d7_bal_bias_naive"] = _r(100 * bias(bte, np.full(6, btr[-1])), 1)

    # ================= L7.4 intermittent and hierarchical =================
    sk = M.load("retail", "weekly_sku_chain", data)
    g = sk.groupby("sku").units
    adi = g.apply(lambda u: len(u) / max((u > 0).sum(), 1))
    cv2 = g.apply(lambda u: (u[u > 0].std() / u[u > 0].mean()) ** 2 if (u > 0).sum() > 1 else 0)
    cls = np.where(adi <= 1.32, np.where(cv2 <= 0.49, "smooth", "erratic"), np.where(cv2 <= 0.49, "intermittent", "lumpy"))
    vc = pd.Series(cls).value_counts(normalize=True)
    a["d7_sku_n"] = int(len(adi))
    a["d7_sbc"] = {k_: _r(100 * vc.get(k_, 0), 1) for k_ in ["smooth", "erratic", "intermittent", "lumpy"]}
    a["d7_adi_share"] = _r(100 * M.R22(data)["measured"], 1)
    inter = adi[adi > 1.32].index
    piv = sk[sk.sku.isin(inter)].pivot(index="week", columns="sku", values="units").fillna(0).sort_index()
    errs = {"ses": [], "croston": [], "sba": [], "zero": []}
    for s_ in piv.columns:
        u = piv[s_].values
        utr, ute = u[:78], u[78:]
        if utr.sum() == 0:
            continue
        scale = np.mean(np.abs(np.diff(utr))) or 1.0
        f_ses = np.full(len(ute), ses_level(utr))
        for nm, f_ in [("ses", f_ses), ("croston", croston(utr, len(ute))), ("sba", croston(utr, len(ute), sba=True)), ("zero", np.zeros(len(ute)))]:
            errs[nm].append(np.mean(np.abs(ute - f_)) / scale)
    a["d7_int_mase"] = {k_: _r(np.mean(v), 3) for k_, v in errs.items()}
    a["d7_int_n"] = len(errs["ses"])
    # bias of each method on intermittent SKUs (total forecast vs total actual)
    tot_act = piv.iloc[78:].values.sum()
    tot = {}
    for nm in ["ses", "croston", "sba"]:
        s_tot = 0
        for s_ in piv.columns:
            u = piv[s_].values
            utr = u[:78]
            if utr.sum() == 0:
                continue
            if nm == "ses":
                f0 = ses_level(utr)
            else:
                f0 = croston(utr, 1, sba=(nm == "sba"))[0]
            s_tot += f0 * 26
        tot[nm] = _r(100 * (s_tot - tot_act) / tot_act, 1)
    a["d7_int_bias"] = tot
    # hierarchy: region x category (Beverages) -> total
    rc = M.load("retail", "weekly_region_category", data)
    rb = rc[rc.category == "Beverages"].pivot(index="week", columns="region", values="units").astype(float)
    regs = list(rb.columns)
    bu, td_tot, reg_fc = {}, None, {}
    for r_ in regs:
        yr = rb[r_].values
        mdl = sm.OLS(np.log(yr[:78]), sm.add_constant(X[:78])).fit()
        reg_fc[r_] = np.exp(mdl.predict(sm.add_constant(X[78:], has_constant="add")))
    bu_total = np.sum([reg_fc[r_] for r_ in regs], axis=0)
    tot_series = rb.sum(axis=1).values
    mt = sm.OLS(np.log(tot_series[:78]), sm.add_constant(X[:78])).fit()
    td_total = np.exp(mt.predict(sm.add_constant(X[78:], has_constant="add")))
    shares = rb.iloc[:78].sum() / rb.iloc[:78].sum().sum()
    td_reg = {r_: td_total * shares[r_] for r_ in regs}
    act_reg = {r_: rb[r_].values[78:] for r_ in regs}
    a["d7_h_total_wape_bu"] = _r(100 * wape(tot_series[78:], bu_total), 1)
    a["d7_h_total_wape_td"] = _r(100 * wape(tot_series[78:], td_total), 1)
    a["d7_h_reg_wape_bu"] = _r(100 * np.mean([wape(act_reg[r_], reg_fc[r_]) for r_ in regs]), 1)
    a["d7_h_reg_wape_td"] = _r(100 * np.mean([wape(act_reg[r_], td_reg[r_]) for r_ in regs]), 1)
    a["d7_h_incoherence_pct"] = _r(100 * np.mean(np.abs(bu_total - td_total) / td_total), 1)

    # ================= L7.5 change-points and censored demand =================
    r08 = M.R08(data)
    a["d7_cp_week"], a["d7_cp_ratio"] = r08["measured"], r08["level_ratio"]
    s17 = ws[ws.store_id == "S017"].set_index("week").revenue
    oth = ws[ws.store_id != "S017"].groupby("week").revenue.sum()
    share = (s17 / oth).values
    mu0 = share[:40].mean()
    sd0 = share[:40].std(ddof=1)
    cus = np.minimum.accumulate(np.minimum(0, np.cumsum((share - mu0) / sd0 + 0.5)))  # lower CUSUM, k = 0.5
    lc = np.zeros(len(share))
    for t in range(1, len(share)):
        lc[t] = min(0, lc[t - 1] + (share[t] - mu0) / sd0 + 0.5)
    H = 8.0  # decision interval (in SDs); k = 0.5
    a["d7_cusum_h"] = H
    alarm = int(np.argmax(lc < -H)) + 1 if (lc < -H).any() else None
    a["d7_cusum_alarm_week"] = alarm
    a["d7_cusum_alarm_h5"] = int(np.argmax(lc < -5)) + 1 if (lc < -5).any() else None
    a["d7_cusum_delay"] = (alarm - a["d7_cp_week"]) if alarm else None
    a["d7_s17_share_before"], a["d7_s17_share_after"] = _r(100 * share[:a["d7_cp_week"] - 1].mean(), 2), _r(100 * share[a["d7_cp_week"] - 1:].mean(), 2)
    # naive single-series view: S017 revenue alone (seasonality hides the break?)
    r12 = M.R12(data)
    a["d7_censor_loss_pct"] = _r(100 * r12["measured"], 1)
    a["d7_stockout_cell_pct"] = _r(100 * r12["stockout_cell_share"], 1)
    truth_p = M.ROOT / "instructor" / "truth" / "retail" / "true_demand_sku_week.parquet"
    if truth_p.exists():
        td = pd.read_parquet(truth_p)
        skx = sk.merge(td, on=["sku", "week"], how="inner") if "sku" in td.columns else None
    else:
        skx = None
    sk2 = sk.copy()
    instock = 40 - sk2.stockout_store_count
    sk2["uncensored"] = np.where((sk2.stockout_store_count > 0) & (instock > 0), sk2.units * 40 / instock.clip(lower=1), sk2.units)
    a["d7_uncensor_uplift_pct"] = _r(100 * (sk2.uncensored.sum() / sk2.units.sum() - 1), 1)
    if skx is not None and "true_expected_units" in skx.columns:
        tot_true = skx.true_expected_units.sum()
        a["d7_naive_vs_true_pct"] = _r(100 * (skx.units.sum() / tot_true - 1), 1)
        sk3 = sk2.merge(td, on=["sku", "week"], how="inner")
        a["d7_uncens_vs_true_pct"] = _r(100 * (sk3.uncensored.sum() / sk3.true_expected_units.sum() - 1), 1)
    else:
        a["d7_naive_vs_true_pct"] = _r(-100 * r12["measured"], 1)
        a["d7_uncens_vs_true_pct"] = None

    # ================= L7.6 inventory =================
    rev = sk.groupby("sku").revenue.sum().sort_values(ascending=False)
    cum = rev.cumsum() / rev.sum()
    abc = np.where(cum <= 0.8, "A", np.where(cum <= 0.95, "B", "C"))
    abc = pd.Series(abc, index=rev.index)
    dm = sk.pivot_table(index="sku", columns="week", values="units", aggfunc="sum", fill_value=0)  # as rcp_inventory
    cvw = (dm.std(axis=1, ddof=1) / dm.mean(axis=1).replace(0, np.nan)).reindex(rev.index)
    xyz = pd.Series(np.where(cvw <= 0.5, "X", np.where(cvw <= 1.0, "Y", "Z")), index=rev.index)
    a["d7_abc_counts"] = abc.value_counts().reindex(["A", "B", "C"]).fillna(0).astype(int).to_dict()
    a["d7_abc_a_share_sku"] = _r(100 * (abc == "A").mean(), 1)
    ct = pd.crosstab(abc, xyz)
    a["d7_ax"] = int(ct.loc["A", "X"]) if "X" in ct.columns else 0
    a["d7_cz"] = int(ct.loc["C", "Z"]) if "Z" in ct.columns else 0
    # safety stock for a top SKU at one store: weekly demand from store-level extract
    pe = M.load("retail", "price_elasticity_extract", data)
    top = rev.index[0]
    top_name = M.load("retail", "products", data).set_index("sku").product_name.get(top, top)
    a["d7_top_sku"], a["d7_top_sku_name"] = top, str(top_name)
    d = sk[sk.sku == top].set_index("week").units.astype(float)
    mu, sd = d.mean(), d.std(ddof=1)
    L = 2
    a["d7_ss_mu"], a["d7_ss_sd"] = _r(mu, 1), _r(sd, 1)
    a["d7_ss"] = {str(sl): int(np.ceil(stats.norm.ppf(sl / 100) * sd * np.sqrt(L))) for sl in (90, 95, 98, 99, 99.5)}
    a["d7_rop_95"] = int(np.ceil(mu * L + stats.norm.ppf(0.95) * sd * np.sqrt(L)))
    a["d7_ss_ratio_99_vs_95"] = _r(a["d7_ss"]["99"] / a["d7_ss"]["95"], 2)
    # Poisson vs actual variance: safety stock understatement
    a["d7_ss_poisson_95"] = int(np.ceil(stats.norm.ppf(0.95) * np.sqrt(mu) * np.sqrt(L)))
    # newsvendor: bakery item price 3.0, cost 1.2, salvage 0.3 -> critical ratio
    p_, c_, s_ = 3.0, 1.2, 0.3
    crit = (p_ - c_) / (p_ - s_)
    a["d7_nv_crit"] = _r(crit, 3)
    bak = sc[(sc.category == "Bakery") & (sc.store_id == "S001")].units.astype(float)
    a["d7_nv_mu"], a["d7_nv_sd"] = _r(bak.mean(), 1), _r(bak.std(ddof=1), 1)
    a["d7_nv_q"] = int(np.ceil(bak.quantile(crit)))
    a["d7_nv_q_normal"] = int(np.ceil(bak.mean() + stats.norm.ppf(crit) * bak.std(ddof=1)))
    # finance: collections capacity — monthly new 30+ DPD entries
    pm2 = pm.sort_values(["account_id", "month_on_book"])
    pm2["prev"] = pm2.groupby("account_id").dpd.shift(1).fillna(0)
    entries = pm2[(pm2.dpd >= 30) & (pm2.prev < 30)].groupby("calendar_month").size()
    entries = entries.reindex(dq.index).fillna(0)
    last12 = entries.iloc[-12:]
    a["d7_coll_mean"], a["d7_coll_sd"] = _r(last12.mean(), 0), _r(last12.std(ddof=1), 0)
    a["d7_coll_cap95"] = int(np.ceil(last12.mean() + 1.645 * last12.std(ddof=1)))
    a["d7_coll_trend_ratio"] = _r(entries.iloc[-6:].mean() / entries.iloc[-18:-12].mean(), 2)

    checks = {
        "snaive wins at origin 86": a["d7_backtest"][1]["snaive_wape"] < a["d7_backtest"][1]["reg_wape"],
        "snaive halves naive": res["seasonal_naive"]["wape"] < 0.6 * res["naive"]["wape"],
        "chain stationary both tests": a["d7_adf_p"] < 0.05 and a["d7_kpss_p"] > 0.05,
        "holt under-forecasts": res["holt_damped"]["bias"] < -3,
        "reg wins on average": a["d7_bt_mean_reg"] < a["d7_bt_mean_snaive"],
        "uncensoring over-corrects slightly": a["d7_uncens_vs_true_pct"] is None or 0 < a["d7_uncens_vs_true_pct"] < 3,
        "cusum h5 alarms early": a["d7_cusum_alarm_h5"] is not None and a["d7_cusum_alarm_h5"] < a["d7_cp_week"],
        "seasonality strong": a["d7_seas_strength"] > 0.5,
        "acf52 positive": a["d7_acf52"] > 0.3,
        "peak is holiday": a["d7_peak_holiday"],
        "dq non-stationary": a["d7_dq_adf_p"] > 0.05,
        "dq break in 2025 or later": str(a["d7_dq_break_month"]) >= "2025-06",
        "regression/sarimax beats naive": min(res["regression_fourier"]["wape"], res["sarimax"]["wape"]) < res["naive"]["wape"],
        "seasonal naive beats naive": res["seasonal_naive"]["wape"] < res["naive"]["wape"],
        "store WAPE > chain": a["d7_wape_store"] > a["d7_wape_chain"] + 5,
        "adi share ≈ 25%": 15 < a["d7_adi_share"] < 40,
        "SBA ≤ Croston bias": abs(a["d7_int_bias"]["sba"]) <= abs(a["d7_int_bias"]["croston"]) + 1,
        "cp week ≈ 61": abs(a["d7_cp_week"] - 61) <= 1,
        "cusum alarms after break": a["d7_cusum_alarm_week"] is not None and a["d7_cusum_alarm_week"] >= a["d7_cp_week"],
        "naive demand low": a["d7_naive_vs_true_pct"] < -1,
        "uncensoring closer": a["d7_uncens_vs_true_pct"] is None or abs(a["d7_uncens_vs_true_pct"]) < abs(a["d7_naive_vs_true_pct"]),
        "99% SS > 95% SS by >30%": a["d7_ss_ratio_99_vs_95"] > 1.3,
        "poisson SS understates": a["d7_ss_poisson_95"] < a["d7_ss"]["95"],
        "A is minority of SKUs": a["d7_abc_a_share_sku"] < 50,
        "zero forecast wins MASE on intermittent": a["d7_int_mase"]["zero"] < min(a["d7_int_mase"]["ses"], a["d7_int_mase"]["croston"]),
        "top-down better at region level": a["d7_h_reg_wape_td"] < a["d7_h_reg_wape_bu"],
    }
    bad = [k_ for k_, ok in checks.items() if not ok]
    if bad and __import__("os").environ.get("SB_NOGUARD"):
        print("GUARDS", bad)
    else:
        assert not bad, f"Day 7 narrative guards failed: {bad}"
    return a
