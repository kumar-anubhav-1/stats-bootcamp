"""Meridian Bank: synthetic retail-lending and cards data with a planted Anomaly Register.

Applications are simulated first, decided by the bank's (old) application score,
then booked accounts get a latent risk that drives collections entry, cure,
default, churn and fraud. A monthly performance panel is built from the same
event timeline so vintage, roll-rate and survival analyses reconcile with the
account-level labels.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .common import ids, sigmoid, weighted_sample

REGIONS = ["R1", "R2", "R3", "R4"]
EMPLOYMENT = ["salaried", "self-employed", "contract", "retired", "student"]


@dataclass
class FinanceParams:
    seed: int = 20261115
    n_accounts: int = 25_000
    snapshot: str = "2026-10-31"
    first_orig: str = "2023-01-01"
    last_orig: str = "2025-09-30"
    drift_start: str = "2025-04-01"           # F11/F12 digital-partner vintages
    target_default: float = 0.040              # F03
    target_fraud: float = 0.007
    n_bad_age: int = 12                        # F01
    n_neg_income: int = 20
    income_missing: float = 0.04               # F02
    util_knot: float = 0.50                    # F04
    young_dti_or: float = 2.5                  # F05
    n_rings: int = 3                           # F07
    ring_size: int = 15
    ring_fraud_rate: float = 0.60
    n_structurers: int = 120                   # F08
    report_threshold: float = 10_000
    benford_branch: str = "BR07"               # F09
    benford_share: float = 0.70
    churn_censor_target: float = 0.70          # F13
    r4_share_b: float = 0.85                   # F15
    other_share_b: float = 0.25
    region_penalty: float = 60.0
    cure_champion: float = 0.35                # F16
    cure_challenger: float = 0.41
    challenger_share: float = 0.20
    n_policies: int = 8000                     # F17
    n_cat_claims: int = 3
    unverified_or: float = 1.6


def _months_between(a, b):
    return (b.year - a.year) * 12 + (b.month - a.month)


def generate(p: FinanceParams | None = None) -> dict:
    p = p or FinanceParams()
    rng = np.random.default_rng(p.seed + 1)
    truth: dict = {"params": p.__dict__.copy()}
    snap = pd.Timestamp(p.snapshot)

    # ---------------- applications ----------------
    n_app = int(p.n_accounts * 1.32)
    span = pd.date_range(p.first_orig, p.last_orig, freq="D")
    wts = np.linspace(0.7, 1.3, len(span))
    orig = span[rng.choice(len(span), n_app, p=wts / wts.sum())]
    drift = orig >= pd.Timestamp(p.drift_start)
    channel = np.where(drift & (rng.random(n_app) < 0.66), "partner",
                       rng.choice(["branch", "online"], n_app, p=[0.55, 0.45]))
    partner = channel == "partner"
    region = rng.choice(REGIONS, n_app, p=[0.28, 0.27, 0.25, 0.20])
    pgroup = np.where(rng.random(n_app) < np.where(region == "R4", p.r4_share_b, p.other_share_b), "B", "A")
    age = np.clip(np.round(rng.normal(41, 12, n_app) - 7 * partner), 18, 80).astype(int)
    emp = np.array([rng.choice(5, p=[0.03, 0.05, 0.12, 0.8, 0.0] if a >= 63 else
                               ([0.35, 0.05, 0.2, 0.0, 0.4] if a < 23 else [0.62, 0.17, 0.16, 0.02, 0.03]))
                    for a in age])
    emp_name = np.array(EMPLOYMENT)[emp]
    inc_med = np.array([54_000, 60_000, 42_000, 30_000, 14_000])[emp]
    hnw = rng.random(n_app) < 0.012                                           # F14 heavy tail
    income = np.round(np.where(hnw, rng.uniform(8, 20, n_app), 1.0) * inc_med * rng.lognormal(0, 0.45, n_app) * np.where(pgroup == "B", 0.88, 1.0), -2)
    bureau = np.clip(np.round(rng.normal(700, 65, n_app) - 30 * (pgroup == "B") - 60 * partner
                              + 0.6 * (age - 41)), 300, 900).astype(int)
    product = np.where(rng.random(n_app) < 0.6, "credit_card", "personal_loan")
    card = product == "credit_card"
    limit = np.where(card, income * 0.25 * rng.lognormal(0, 0.07, n_app), income * 0.40 * rng.lognormal(0, 0.09, n_app))
    limit = np.round(limit, -2)
    term = np.where(card, np.nan, rng.choice([12, 24, 36, 48, 60], n_app))
    util = np.clip(rng.beta(2.0, 2.6, n_app) + 0.12 * partner + 0.002 * (650 - bureau).clip(0) / 1.0, 0.0, 1.15)
    util = np.where(card, util, np.clip(rng.uniform(0.3, 1.0, n_app), 0, 1))
    dti = np.clip(rng.lognormal(np.log(0.28), 0.45, n_app) + 0.06 * partner, 0.02, 0.95)
    inq = rng.poisson(0.9 + 1.2 * partner + 0.004 * (700 - bureau).clip(0))
    delq = rng.poisson(np.clip(0.15 + 0.006 * (650 - bureau).clip(0), 0, 4))
    verified = rng.random(n_app) < np.where(partner, 0.55, 0.82)
    tenure_bank = np.clip(np.round(rng.exponential(48, n_app)), 0, 300).astype(int)
    digital = np.clip(rng.beta(2.5, 2.0, n_app) + 0.2 * partner, 0, 1).round(3)

    # old application scorecard (does not know about the later shock)
    old_logit = (-3.2 - 0.018 * (bureau - 700) + 1.6 * util + 1.4 * (dti - 0.3) + 0.18 * inq + 0.35 * delq)
    app_score = np.round(600 - (20 / np.log(2)) * (old_logit + 3.2)).astype(int)
    adj = app_score - p.region_penalty * (region == "R4")
    cutoff = np.quantile(adj, 0.17)
    approve = (adj >= cutoff) | (rng.random(n_app) < 0.02)
    approve &= ~(rng.random(n_app) < 0.01)
    a_idx = np.where(approve)[0]
    d_idx = np.where(~approve)[0]
    a_idx = np.sort(rng.choice(a_idx, p.n_accounts, replace=False))
    n_dec = int(round(p.n_accounts * len(d_idx) / approve.sum()))
    d_idx = np.sort(rng.choice(d_idx, n_dec, replace=False))
    reasons = np.where(bureau[d_idx] < 600, "low bureau score", np.where(dti[d_idx] > 0.5, "high DTI",
                       np.where(delq[d_idx] > 0, "recent delinquency", "score below cutoff")))
    declined = pd.DataFrame({
        "application_id": ids("APP", n_dec, 6), "application_date": orig[d_idx].date.astype(str),
        "age": age[d_idx], "income_annual": income[d_idx], "employment_type": emp_name[d_idx],
        "region": region[d_idx], "acquisition_channel": channel[d_idx], "product_type": product[d_idx],
        "requested_amount": limit[d_idx], "bureau_score": bureau[d_idx], "dti": dti[d_idx].round(3),
        "inquiries_6m": inq[d_idx], "delinq_2y": delq[d_idx], "app_score": app_score[d_idx],
        "protected_group": pgroup[d_idx], "decline_reason": reasons,
    })
    appr_rate = pd.Series(approve).groupby(pgroup).mean()
    truth["approval_rate_by_group_all_apps"] = appr_rate.round(4).to_dict()

    # ---------------- booked accounts ----------------
    A = p.n_accounts
    sel = lambda x: x[a_idx]
    age, emp_name, income, bureau, product, card, limit, term, util, dti, inq, delq, verified, tenure_bank, \
        digital, region, pgroup, channel, partner, app_score, hnw, orig = map(sel, (
            age, emp_name, income, bureau, product, card, limit, term, util, dti, inq, delq, verified,
            tenure_bank, digital, region, pgroup, channel, partner, app_score, hnw, orig))
    drift = orig >= pd.Timestamp(p.drift_start)
    branch = np.array([f"BR{(REGIONS.index(r) * 5 + rng.integers(1, 6)):02d}" for r in region])
    rate = np.round(np.clip(0.36 - 0.00045 * (bureau - 500) + rng.normal(0, 0.012, A), 0.07, 0.36) * np.where(card, 1.0, 0.7), 4)

    # latent risk (true model)
    u_term = np.where(util > p.util_knot, 4.2 * np.clip(util - p.util_knot, 0, None) ** 1.5, 0.0)          # F04
    young_hi = (age < 25) & (dti > 0.45)                                                     # F05
    shock = np.where(drift, 1.6 * np.maximum(util - 0.6, 0) + rng.normal(0, 1.2, A), 0.0)  # F12
    L = (-0.022 * (bureau - 700) + u_term + 1.5 * (dti - 0.3) + 0.15 * inq + 0.4 * delq
         + np.log(p.young_dti_or) * young_hi + np.log(p.unverified_or) * ~verified
         + 0.25 * (emp_name == "contract") + 0.3 * (emp_name == "student") - 0.004 * tenure_bank / 12
         + shock + rng.normal(0, 0.55, A))
    mob_max = np.minimum(24, np.array([_months_between(o, snap) for o in orig]))

    # collections entry (30 DPD) -> cure (strategy) -> roll to 90+ (default)
    lo, hi = -12.0, 4.0
    for _ in range(60):                       # calibrate intercept to the default target
        c = (lo + hi) / 2
        p_e = sigmoid(L + c)
        exp_def = (p_e * (1 - 0.362) * 0.72 * np.minimum(1, 10 / np.maximum(mob_max - 1, 1))).mean()
        lo, hi = (c, hi) if exp_def < p.target_default else (lo, c)
    enter = rng.random(A) < sigmoid(L + c)
    m_e = np.where(enter, rng.integers(2, np.maximum(mob_max, 3) + 1), 0)
    m_e = np.minimum(m_e, mob_max)
    strat = np.where(enter, np.where(rng.random(A) < p.challenger_share, "challenger", "champion"), "none")
    cured = np.zeros(A, bool)
    for s_, cr in (("champion", p.cure_champion), ("challenger", p.cure_challenger)):
        idx = np.where(strat == s_)[0]
        w = sigmoid(-0.6 * L[idx])
        cured[weighted_sample(rng, idx, int(round(cr * len(idx))), w)] = True
    roll = enter & ~cured & (rng.random(A) < 0.72)
    default_month = np.where(roll, m_e + 2, 0)
    default_12m = roll & (default_month <= 12) & (default_month <= mob_max)
    # top up / trim to hit target exactly via the riskiest non-entered accounts (keeps ranking)
    need = int(round(p.target_default * A)) - default_12m.sum()
    if need > 0:
        cand = np.where(~enter & (mob_max >= 12))[0]
        pick = cand[np.argsort(-(L[cand] + rng.normal(0, 0.7, len(cand))), kind="stable")][:need]
        enter[pick] = True
        m_e[pick] = rng.integers(2, 11, need)
        strat[pick] = np.where(rng.random(need) < p.challenger_share, "challenger", "champion")
        roll[pick] = True
        default_month[pick] = m_e[pick] + 2
        default_12m[pick] = True
    elif need < 0:
        cand = np.where(default_12m)[0]
        pick = rng.choice(cand, -need, replace=False)
        default_month[pick] = 13 + rng.integers(0, 6, -need)
        default_12m[pick] = False
    # re-impose exact cure rates after top-up
    for s_, cr in (("champion", p.cure_champion), ("challenger", p.cure_challenger)):
        idx = np.where(strat == s_)[0]
        k = int(round(cr * len(idx)))
        cur = idx[cured[idx]]
        if len(cur) > k:
            nd = cur[~roll[cur]]
            cured[rng.choice(nd, min(len(nd), len(cur) - k), replace=False)] = False
        elif len(cur) < k:
            cand = idx[~cured[idx] & ~roll[idx]]
            cured[rng.choice(cand, min(len(cand), k - len(cur)), replace=False)] = True

    # ---------------- monthly panel ----------------
    M = 24
    mob = np.arange(1, M + 1)[None, :]
    alive = mob <= mob_max[:, None]
    dpd = np.zeros((A, M), int)
    small = (rng.random((A, M)) < 0.025) & alive
    dpd[small] = rng.integers(1, 29, small.sum())
    e = enter
    rows_e = np.where(e)[0]
    for i in rows_e:
        m0 = m_e[i] - 1
        if m0 >= mob_max[i]:
            continue
        dpd[i, m0] = rng.integers(30, 59)
        if cured[i]:
            if m0 + 1 < M:
                dpd[i, m0 + 1] = 0 if rng.random() < 0.6 else rng.integers(1, 29)
            if m0 + 2 < M:
                dpd[i, m0 + 2] = 0
        elif roll[i]:
            for j in range(1, M - m0):
                dpd[i, m0 + j] = min(30 + 30 * j + rng.integers(0, 5), 210)
        else:
            if m0 + 1 < M:
                dpd[i, m0 + 1] = rng.integers(60, 89)
            for j in range(2, 4):
                if m0 + j < M:
                    dpd[i, m0 + j] = 0
    co_month = np.argmax(dpd >= 180, axis=1)
    has_co = (dpd >= 180).any(axis=1)
    after_co = has_co[:, None] & (np.arange(M)[None, :] > co_month[:, None])
    alive &= ~after_co
    status = np.where(dpd >= 180, "charged-off", "open")
    # churn (F13): monthly hazard, censored at snapshot or charge-off
    complaints = rng.poisson(0.25 + 0.5 * (L > 1.0))
    h = sigmoid(-3.85 + 0.55 * complaints - 1.1 * digital + 0.015 * (rate * 100 - 20) - 0.004 * tenure_bank / 12)
    ch_draw = rng.random((A, M)) < h[:, None]
    ch_draw &= alive & (dpd < 30)
    churned = ch_draw.any(axis=1)
    churn_m = np.where(churned, np.argmax(ch_draw, axis=1) + 1, 0)
    truth["churn_censored_share"] = float(1 - churned.mean())
    after_churn = churned[:, None] & (np.arange(M)[None, :] + 1 > churn_m[:, None])
    alive &= ~after_churn
    status = np.where(churned[:, None] & (np.arange(M)[None, :] + 1 == churn_m[:, None]), "closed", status)
    # balances
    u_path = np.clip(util[:, None] + np.cumsum(rng.normal(0, 0.04, (A, M)), axis=1) + 0.03 * (dpd > 0), 0, 1.2)
    amort = np.where(card[:, None], 1.0, 1 - np.clip(mob / np.nan_to_num(term, nan=36)[:, None], 0, 1))
    bal = np.where(card[:, None], limit[:, None] * u_path, limit[:, None] * amort)
    bal = np.round(np.where(status == "charged-off", 0, bal), 2)
    min_due = np.round(np.where(card[:, None], np.maximum(25, 0.03 * bal), limit[:, None] / np.nan_to_num(term, nan=36)[:, None] * (1 + rate[:, None] / 2)), 2)
    pay = np.round(np.where(dpd > 0, 0, min_due * rng.uniform(1.0, 2.5, (A, M))), 2)
    tx_level = rng.lognormal(np.log(1200), 0.9, A) * np.where(card, 1.0, 0.3)
    tx_cnt = rng.poisson(np.clip(tx_level / 60, 0.5, 80)[:, None] * rng.uniform(0.7, 1.3, (A, M)))
    tx_amt = np.round(tx_level[:, None] * rng.lognormal(0, 0.35, (A, M)), 2)
    cash_cnt = rng.poisson(0.8, (A, M))
    cash_max = np.where(cash_cnt > 0, np.round(rng.lognormal(np.log(400), 1.25, (A, M)), 2), 0.0)
    # structuring (F08)
    struct = rng.choice(np.where((mob_max >= 12))[0], p.n_structurers, replace=False)
    smask = np.zeros((A, M), bool)
    smask[struct] = rng.random((len(struct), M)) < 0.6
    smask &= alive
    cash_cnt[smask] = rng.integers(3, 9, smask.sum())
    cash_max[smask] = np.round(rng.uniform(0.90, 0.999, smask.sum()) * p.report_threshold, 2)

    ai, mi = np.nonzero(alive)
    cal_month = (pd.to_datetime(orig[ai]).to_period("M") + mi + 1).astype(str)
    bucket = pd.cut(dpd[ai, mi], [-1, 0, 29, 59, 89, 10_000], labels=["current", "1-29", "30-59", "60-89", "90+"]).astype(str)
    acct_id = ids("A", A, 6)
    panel = pd.DataFrame({
        "account_id": acct_id[ai], "month_on_book": mi + 1, "calendar_month": cal_month,
        "balance": bal[ai, mi], "payment": pay[ai, mi], "minimum_due": min_due[ai, mi],
        "dpd": dpd[ai, mi], "delinquency_bucket": bucket, "utilisation": np.round(np.where(card[ai], u_path[ai, mi], np.nan), 3),
        "txn_count": tx_cnt[ai, mi], "txn_amount": tx_amt[ai, mi],
        "cash_deposit_count": cash_cnt[ai, mi], "cash_deposit_max": cash_max[ai, mi], "status": status[ai, mi],
    })

    # ---------------- account-level fields ----------------
    max_dpd_12 = dpd[:, :12].max(axis=1)
    last3 = np.clip(mob_max - 3, 0, M - 3)
    tx_cnt3 = np.array([tx_cnt[i, last3[i]:last3[i] + 3].sum() for i in range(A)])
    tx_amt3 = np.round(np.array([tx_amt[i, last3[i]:last3[i] + 3].sum() for i in range(A)]), 2)
    bal_now = np.round(np.where(card, limit * u_path[np.arange(A), np.maximum(mob_max - 1, 0)], limit * 0.55), 2)
    bal_now[has_co] = 0
    recovery = np.where(has_co, np.round(limit * rng.uniform(0.05, 0.35, A), 2), 0.0)
    # fraud: rings (F07) + background
    ring_pool = np.where(~enter & (mob_max >= 12))[0]
    ring_acc = rng.choice(ring_pool, p.n_rings * p.ring_size, replace=False).reshape(p.n_rings, p.ring_size)
    fraud = np.zeros(A, bool)
    for r in ring_acc:
        fraud[rng.choice(r, int(round(p.ring_fraud_rate * len(r))), replace=False)] = True
    remaining = int(round(p.target_fraud * A)) - fraud.sum()
    fscore = 0.6 * inq + 1.2 * (tenure_bank < 6) + 0.8 * partner + rng.normal(0, 1, A)
    fscore[ring_acc.ravel()] = -np.inf
    fraud[np.argsort(-fscore, kind="stable")[: max(remaining, 0) * 3][rng.permutation(max(remaining, 0) * 3)[:max(remaining, 0)]]] = True
    # devices and addresses
    dev = ids("D", A, 6)
    addr = ids("AD", A, 6)
    hh = rng.choice(A, int(0.15 * A), replace=False)
    addr[hh[: len(hh) // 2]] = addr[hh[len(hh) // 2: 2 * (len(hh) // 2)]]
    for k, r in enumerate(ring_acc):
        dev[r] = rng.choice([f"DRING{k}a", f"DRING{k}b"], len(r))
        addr[r] = rng.choice([f"ADRING{k}a", f"ADRING{k}b"] if k < 1 else [f"ADRING{k}a"], len(r))
    second = rng.random(A) < 0.3
    links = pd.concat([
        pd.DataFrame({"account_id": acct_id, "link_type": "device", "link_id": dev}),
        pd.DataFrame({"account_id": acct_id[second], "link_type": "device", "link_id": ids("DX", second.sum(), 6)}),
        pd.DataFrame({"account_id": acct_id, "link_type": "address", "link_id": addr}),
    ]).reset_index(drop=True)
    links = links.iloc[rng.permutation(len(links))].reset_index(drop=True)
    # anonymise link ids so ring names do not leak the answer
    uniq = pd.Series(links.link_id.unique())
    mapping = dict(zip(uniq, ids("LK", len(uniq), 6)[rng.permutation(len(uniq))]))
    links["link_id"] = links.link_id.map(mapping)

    accounts = pd.DataFrame({
        "customer_id": ids("CU", A, 6), "account_id": acct_id, "age": age, "income_annual": income,
        "employment_type": emp_name, "region": region, "branch_id": branch, "acquisition_channel": channel,
        "tenure_months_with_bank": tenure_bank, "product_type": product,
        "limit_or_loan_amount": limit, "interest_rate": rate, "term_months": pd.array(np.where(card, pd.NA, term), dtype="Int64"),
        "utilisation": np.round(np.where(card, util, np.nan), 3), "dti": np.round(dti, 3), "bureau_score": bureau,
        "app_score": app_score, "inquiries_6m": inq, "delinq_2y": delq, "balance_current": bal_now,
        "txn_count_3m": tx_cnt3, "txn_amount_3m": tx_amt3, "digital_share": digital,
        "branch_visits_6m": rng.poisson(np.clip(4 * (1 - digital), 0.1, None)), "complaints_12m": complaints,
        "origination_date": orig.date.astype(str), "vintage": pd.PeriodIndex(orig, freq="Q").astype(str),
        "income_verified_flag": verified, "default_12m": default_12m, "max_dpd_12m": max_dpd_12,
        "churn_flag": churned, "churn_month": pd.array(np.where(churned, churn_m, pd.NA), dtype="Int64"),
        "months_observed": np.where(churned, churn_m, np.where(has_co, co_month + 1, mob_max)),
        "fraud_flag": fraud, "protected_group": pgroup, "strategy_group": strat,
        "cured_within_3m": pd.array(np.where(enter, cured, pd.NA), dtype="boolean"),
        "collections_flag": enter, "recovery_amount": recovery,
    })
    planted: dict = {}
    # F01 impossible values
    bad_a = rng.choice(A, p.n_bad_age, replace=False)
    accounts.loc[bad_a, "age"] = rng.choice([0, 7, 12, 130, 131, 150, 999], p.n_bad_age)
    neg = rng.choice(np.setdiff1d(np.arange(A), bad_a), p.n_neg_income, replace=False)
    accounts.loc[neg, "income_annual"] = -accounts.loc[neg, "income_annual"]
    planted["F01_age"] = acct_id[bad_a].tolist()
    planted["F01_income"] = acct_id[neg].tolist()
    # F02 income MNAR
    z = (L - L.mean()) / L.std()
    pm = np.exp(1.1 * z)
    pm = pm / pm.mean() * p.income_missing
    miss = (rng.random(A) < np.clip(pm, 0, 0.9)) & ~np.isin(np.arange(A), neg)
    accounts.loc[miss, "income_annual"] = np.nan
    planted["F02"] = acct_id[miss].tolist()
    # F09 Benford: fabricated txn amounts at one branch
    bb = np.where(branch == p.benford_branch)[0]
    fab = rng.choice(bb, int(round(p.benford_share * len(bb))), replace=False)
    mag = np.floor(np.log10(np.maximum(accounts.loc[fab, "txn_amount_3m"].values, 10)))
    accounts.loc[fab, "txn_amount_3m"] = np.round(rng.uniform(3, 10, len(fab)) * 10 ** mag, 0)
    planted["F09"] = acct_id[fab].tolist()
    planted["F07_rings"] = [acct_id[r].tolist() for r in ring_acc]
    planted["F08"] = acct_id[struct].tolist()
    truth["planted"] = planted
    truth["latent"] = pd.DataFrame({"account_id": acct_id, "latent_risk": np.round(L, 4), "drift_vintage": drift,
                                    "hnw": hnw, "true_young_high_dti": young_hi})

    # ---------------- insurance (F17) ----------------
    n = p.n_policies
    prodi = rng.choice(["motor", "home"], n, p=[0.65, 0.35])
    expo = np.round(rng.uniform(0.25, 1.0, n), 3)
    dab = rng.choice(["18-24", "25-34", "35-49", "50-64", "65+"], n, p=[0.1, 0.25, 0.32, 0.23, 0.1])
    vg = rng.integers(1, 6, n)
    ptype = rng.choice(["apartment", "villa", "townhouse"], n, p=[0.5, 0.2, 0.3])
    preg = rng.choice(REGIONS, n)
    si = np.round(np.where(prodi == "motor", rng.lognormal(np.log(25_000), 0.4, n), rng.lognormal(np.log(300_000), 0.5, n)), -2)
    f_age = pd.Series(dab).map({"18-24": 1.8, "25-34": 1.2, "35-49": 1.0, "50-64": 0.9, "65+": 1.1}).values
    lam = expo * np.where(prodi == "motor", 0.16 * f_age * (1 + 0.08 * (vg - 3)), 0.07) * rng.gamma(0.6, 1 / 0.6, n)
    nclaim = rng.poisson(lam)
    sev_mean = np.where(prodi == "motor", 2600 * (1 + 0.12 * (vg - 3)), 6500)
    pol_id = ids("P", n, 6)
    cl_pol = np.repeat(np.arange(n), nclaim)
    amt = np.round(rng.gamma(1.5, sev_mean[cl_pol] / 1.5), 2)
    cat = rng.choice(len(amt), p.n_cat_claims, replace=False)
    amt[cat] = np.round(rng.uniform(150_000, 400_000, p.n_cat_claims), 2)
    start = pd.Timestamp("2025-01-01")
    claims = pd.DataFrame({
        "claim_id": ids("CL", len(amt), 6), "policy_id": pol_id[cl_pol],
        "claim_date": (start + pd.to_timedelta((rng.random(len(amt)) * expo[cl_pol] * 365).astype(int), "D")).date.astype(str),
        "claim_amount": amt,
        "claim_type": np.where(prodi[cl_pol] == "motor", rng.choice(["collision", "theft", "glass"], len(amt), p=[0.7, 0.1, 0.2]),
                               rng.choice(["water", "fire", "theft"], len(amt), p=[0.6, 0.15, 0.25])),
    })
    premium = np.round(expo * np.where(prodi == "motor", 0.16 * f_age * (1 + 0.08 * (vg - 3)) * 2600, 0.07 * 6500) * 1.35, 2)
    policies = pd.DataFrame({
        "policy_id": pol_id, "customer_id": np.where(rng.random(n) < 0.4, rng.choice(accounts.customer_id.values, n), None),
        "product": prodi, "exposure_years": expo, "sum_insured": si,
        "driver_age_band": np.where(prodi == "motor", dab, None), "vehicle_group": pd.array(np.where(prodi == "motor", vg, pd.NA), dtype="Int64"),
        "property_type": np.where(prodi == "home", ptype, None), "region": preg, "premium": premium,
    })
    truth["planted"]["F17_catastrophic_claims"] = claims.claim_id.values[cat].tolist()

    return {"tables": {"accounts": accounts, "performance_monthly": panel, "applications_declined": declined,
                       "devices_addresses": links, "policies": policies, "claims": claims}, "truth": truth}
