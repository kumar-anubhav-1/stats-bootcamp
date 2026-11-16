"""Computed answers for Day 10 capstones (Q4 promotion plan review; latest-vintage default rise). Keys d10_."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import measures as M


def _r(x, nd=3):
    return round(float(x), nd)


def compute_day10(data=str(M.DATA)) -> dict:
    a: dict = {}
    # ---------- retail capstone: Nov 4 – Dec 31, 2025 vs 2024 ----------
    tx = M.load("retail", "transactions", data).drop_duplicates("line_id")
    s = tx[~tx.return_flag & (tx.quantity > 0) & (tx.unit_price / tx.list_price < 20)].copy()
    s["date"] = pd.to_datetime(s.date)
    md = s.date.dt.strftime("%m-%d")
    win = (md >= "11-04") & (md <= "12-31")
    s = s[win].assign(year=s.date.dt.year)
    s = s[s.year.isin([2024, 2025])]
    s["disc_cost"] = (s.list_price - s.unit_price).clip(lower=0) * s.quantity
    g = s.groupby("year")
    rev, mar, units = g.revenue.sum(), g.margin.sum(), g.quantity.sum()
    a["d10_q4_rev"] = {str(k): _r(v, 0) for k, v in rev.items()}
    a["d10_q4_rev_growth"] = _r(100 * (rev[2025] / rev[2024] - 1), 1)
    a["d10_q4_units_growth"] = _r(100 * (units[2025] / units[2024] - 1), 1)
    a["d10_q4_margin_rate"] = {str(k): _r(100 * mar[k] / rev[k], 2) for k in rev.index}
    a["d10_q4_promo_share"] = {str(k): _r(100 * v, 1) for k, v in g.apply(lambda x: x.loc[x.promo_flag, "revenue"].sum() / x.revenue.sum()).items()}
    a["d10_q4_disc_cost"] = {str(k): _r(v, 0) for k, v in g.disc_cost.sum().items()}
    a["d10_q4_disc_growth"] = _r(100 * (a["d10_q4_disc_cost"]["2025"] / a["d10_q4_disc_cost"]["2024"] - 1), 1)
    p25 = s[s.year == 2025]
    a["d10_q4_margin_promo"] = _r(100 * p25[p25.promo_flag].margin.sum() / p25[p25.promo_flag].revenue.sum(), 1)
    a["d10_q4_margin_nonpromo"] = _r(100 * p25[~p25.promo_flag].margin.sum() / p25[~p25.promo_flag].revenue.sum(), 1)
    by_type = p25[p25.promo_flag].groupby("promo_type").agg(rev=("revenue", "sum"), cost=("disc_cost", "sum"), margin=("margin", "sum"))
    by_type["margin_rate"] = 100 * by_type.margin / by_type.rev
    by_type["cost_per_rev"] = by_type.cost / by_type.rev
    a["d10_q4_by_type"] = {k: {"revenue": _r(v.rev, 0), "discount_cost": _r(v.cost, 0), "margin_rate": _r(v.margin_rate, 1),
                               "cost_per_revenue": _r(v.cost_per_rev, 2)} for k, v in by_type.sort_values("rev", ascending=False).iterrows()}
    a["d10_q4_n_lines"] = {str(k): int(v) for k, v in g.size().items()}
    # ---------- finance capstone: latest vintage ----------
    acc = M.load("finance", "accounts", data)
    ref, late = acc[acc.vintage == "2025Q1"], acc[acc.vintage == "2025Q3"]
    a["d10_def_ref"], a["d10_def_late"] = _r(100 * ref.default_12m.mean(), 2), _r(100 * late.default_12m.mean(), 2)
    rr = ref.groupby("acquisition_channel").default_12m.mean()
    rl = late.groupby("acquisition_channel").default_12m.mean()
    ml = late.acquisition_channel.value_counts(normalize=True)
    mr = ref.acquisition_channel.value_counts(normalize=True)
    a["d10_rate_by_channel"] = {c: {"2025Q1": _r(100 * rr.get(c, np.nan), 2) if c in rr else None, "2025Q3": _r(100 * rl[c], 2)} for c in rl.index}
    a["d10_mix_late"] = {c: _r(100 * v, 1) for c, v in ml.items()}
    nonp = late[late.acquisition_channel != "partner"]
    cf = sum(mr[c] * rl[c] for c in mr.index)  # late within-channel rates at reference mix (no partner)
    a["d10_cf_no_partner"] = _r(100 * cf, 2)
    a["d10_rise_pp"] = _r(a["d10_def_late"] - a["d10_def_ref"], 2)
    a["d10_rise_from_mix_pp"] = _r(a["d10_def_late"] - a["d10_cf_no_partner"], 2)
    a["d10_rise_within_pp"] = _r(a["d10_cf_no_partner"] - a["d10_def_ref"], 2)
    a["d10_share_mix"] = int(round(100 * a["d10_rise_from_mix_pp"] / a["d10_rise_pp"]))
    a["d10_nonpartner_late"] = _r(100 * nonp.default_12m.mean(), 2)
    a["d10_bureau_med"] = {"2025Q1": _r(ref.bureau_score.median(), 0), "2025Q3 partner": _r(late[late.acquisition_channel == "partner"].bureau_score.median(), 0),
                           "2025Q3 other": _r(nonp.bureau_score.median(), 0)}
    checks = {
        "promo margin below non-promo": a["d10_q4_margin_promo"] < a["d10_q4_margin_nonpromo"],
        "default rose": a["d10_def_late"] > 2 * a["d10_def_ref"],
        "mix explains roughly half or more": 40 < a["d10_share_mix"] < 80 and a["d10_rise_within_pp"] > 0,
    }
    bad = [k for k, ok in checks.items() if not ok]
    if bad and __import__("os").environ.get("SB_NOGUARD"):
        print("GUARDS", bad)
    else:
        assert not bad, f"Day 10 narrative guards failed: {bad}"
    return a
