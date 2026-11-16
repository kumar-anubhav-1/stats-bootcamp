"""NorthStar Markets: synthetic CPG/retail data with a planted Anomaly Register.

Design (see blueprint/03):
  * A latent store x SKU x week demand intensity drives everything.
  * Full-chain weekly aggregates are drawn from that intensity (forecasting,
    experiments, elasticity, cannibalisation, stockouts, level shift).
  * A customer panel of ~25,000 transaction lines is sampled from the same
    intensity basket by basket (data quality, distributions, tests, baskets,
    segments, returns, Benford ...).
Every planted phenomenon is controlled by PARAMS so the exam generator can
shift magnitudes and locations.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .common import ids, sigmoid, weighted_sample

CATEGORIES = [
    "Fresh Produce", "Dairy", "Bakery", "Beverages", "Snacks", "Frozen",
    "Pantry", "Household", "Hair Care", "Personal Care", "Beer & Wine", "Electronics",
]
N_SKU = [45, 40, 30, 45, 50, 35, 45, 35, 25, 30, 25, 15]          # = 420
PRICE_MED = [3.0, 2.6, 2.2, 2.8, 2.4, 5.5, 3.0, 6.0, 6.5, 5.0, 9.0, 45.0]
ELASTICITY = [-0.9, -0.6, -0.8, -1.3, -1.8, -1.2, -1.0, -1.1, -1.4, -1.2, -1.5, -1.6]
CAT_VOLUME = [1.6, 1.3, 1.0, 1.2, 1.0, 0.7, 0.9, 0.6, 0.5, 0.5, 0.5, 0.15]
QTY_FACTOR = [1.0, 0.8, 0.6, 0.9, 0.7, 0.5, 0.6, 0.4, 0.2, 0.25, 0.8, 0.0]
SUBCATS = {
    "Fresh Produce": ["Fruit", "Vegetables", "Salad"],
    "Dairy": ["Milk", "Yogurt", "Cheese", "Butter"],
    "Bakery": ["Bread", "Cakes", "Pastries"],
    "Beverages": ["Soft Drinks", "Juice", "Water", "Coffee & Tea"],
    "Snacks": ["Chips", "Biscuits", "Chocolate", "Nuts"],
    "Frozen": ["Ice Cream", "Frozen Meals", "Frozen Veg"],
    "Pantry": ["Pasta", "Pasta Sauce", "Rice", "Oil", "Canned"],
    "Household": ["Laundry", "Cleaning", "Paper"],
    "Hair Care": ["Shampoo", "Conditioner", "Styling"],
    "Personal Care": ["Oral Care", "Skin Care", "Deodorant"],
    "Beer & Wine": ["Beer", "Wine"],
    "Electronics": ["Accessories", "Small Appliances", "Audio"],
}
BRANDS = {
    "Fresh Produce": ["FarmFresh", "GreenLeaf", "Orchard Co"],
    "Dairy": ["MilkWay", "Alpine", "CreamCo", "DailyDairy"],
    "Bakery": ["GoldenCrust", "Bakehouse", "Morning Oven"],
    "Beverages": ["FizzCo", "Aqua Pure", "Sunny Juice", "BrewMaster"],
    "Snacks": ["Crunchy", "ChocoJoy", "NutHouse", "SnackStar"],
    "Frozen": ["FrostBite", "IceDream", "ChefFrozen"],
    "Pantry": ["Bella Pasta", "Nonna", "RiceKing", "PureOil"],
    "Household": ["Sparkle", "CleanPro", "SoftTouch"],
    "Hair Care": ["Lustra", "SilkWave", "Herbia"],
    "Personal Care": ["SmileBright", "DermaSoft", "FreshDay"],
    "Beer & Wine": ["Harbour Lager", "Hilltop", "Vine & Co"],
    "Electronics": ["VoltX", "SoundWave", "HomeTech"],
}
SEGMENTS = ["Value Families", "Premium Singles", "Promo Hunters", "Convenience Top-up", "Bulk Business"]
SEG_CAT = np.array([
    [1.6, 1.8, 1.5, 0.8, 1.0, 1.5, 1.8, 2.0, 0.8, 0.8, 0.3, 0.4],
    [1.2, 0.6, 0.7, 0.9, 0.5, 0.6, 0.5, 0.4, 2.2, 2.4, 2.6, 2.0],
    [0.8, 1.0, 0.8, 1.5, 1.7, 1.3, 1.0, 1.3, 1.2, 1.0, 0.9, 0.7],
    [0.3, 0.5, 0.9, 1.8, 1.8, 0.3, 0.2, 0.2, 0.3, 0.5, 1.0, 0.4],
    [0.5, 0.8, 0.5, 2.0, 1.6, 0.8, 1.5, 2.0, 0.2, 0.2, 1.0, 0.2],
])
CAT_BASE_RATE = np.array([1.0, 0.8, 0.55, 0.7, 0.65, 0.4, 0.6, 0.35, 0.18, 0.22, 0.2, 0.05])
HOLIDAYS = {1: "Diwali", 4: "Black Friday", 8: "Christmas", 9: "New Year", 19: "Spring Festival",
            22: "Eid al-Fitr", 24: "Easter", 31: "Eid al-Adha", 43: "Back to School"}
REGIONS = ["North", "South", "East", "West"]
FORMATS = ["Hyper", "Super", "Express"]


@dataclass
class RetailParams:
    seed: int = 20261115
    start_date: str = "2024-11-04"
    n_weeks: int = 104
    n_stores: int = 40
    n_customers: int = 1500
    target_lines: int = 25_000
    n_duplicates: int = 150                 # R03
    n_negative_qty: int = 40                # R01
    n_price_100x: int = 25                  # R02
    temp_mcar: float = 0.03                 # R04
    age_missing_nonmember: float = 0.18     # R05
    age_missing_member: float = 0.02
    hh_missing_large: float = 0.50          # R06
    hh_missing_small: float = 0.05
    n_bulk: int = 25                        # R07
    bulk_revenue_share: float = 0.12
    shift_store: str = "S017"               # R08
    shift_week: int = 61
    shift_factor: float = 0.65
    exp_category: str = "Hair Care"         # R09
    exp_weeks: tuple = (70, 77)
    exp_lift: float = 1.12
    cannibal_weeks: tuple = (15, 16, 17, 40, 41, 42, 90, 91, 92)  # R10
    cannibal_factor: float = 0.80
    q4_month_factor: dict = field(default_factory=lambda: {10: 1.15, 11: 1.25, 12: 1.35, 1: 0.92, 2: 0.92})
    holiday_factor: float = 1.40            # R11
    stockout_rate: float = 0.04             # R12
    stockout_keep: float = 0.30
    promo_prob: dict = field(default_factory=lambda: {"Hyper": 0.02, "Super": 0.05, "Express": 0.45})  # R14
    promo_effect: float = 1.15              # R15
    display_effect: float = 1.10
    display_if_promo: float = 0.92
    display_if_not: float = 0.03
    delist_week: int = 52                   # R16
    delist_counts: dict = field(default_factory=lambda: {"Snacks": 18, "Frozen": 12})
    n_abusers: int = 30                     # R17
    abuser_stores: tuple = ("S005", "S012")
    abuser_return_rate: float = 0.45
    base_return_rate: float = 0.03
    fabricated_store: str = "S033"          # R18
    fabricated_share: float = 0.70
    drift_week: int = 80                    # R19
    online_share_before: float = 0.12
    online_share_after: float = 0.25
    loyalty_causal: float = 1.05            # R20
    member_spend_slope: float = 2.2
    pasta_sauce_q: float = 0.80             # R21
    beer_chips_q: float = 0.32
    long_tail_share: float = 0.25           # R22
    ab_users: int = 12_000                  # R24
    ab_control_conv: float = 0.100
    ab_treat_conv: float = 0.115
    ab_drop_prob: float = 0.275


def _week_month(start, n_weeks):
    wk_start = pd.date_range(start, periods=n_weeks, freq="7D")
    mid = wk_start + pd.Timedelta(days=3)
    return wk_start, mid.month.values


def generate(p: RetailParams | None = None) -> dict[str, pd.DataFrame]:
    p = p or RetailParams()
    # independent random stream per stage: a tiny floating-point difference in one stage
    # (e.g. across CPU architectures) cannot cascade into the others
    rngs = [np.random.default_rng(x) for x in np.random.SeedSequence(p.seed).spawn(8)]
    rng = rngs[0]
    W, S = p.n_weeks, p.n_stores
    weeks = np.arange(1, W + 1)
    wk_start, wk_month = _week_month(p.start_date, W)
    truth: dict = {"params": p.__dict__.copy()}

    # ---------------- stores ----------------
    fmt = np.array(["Hyper"] * 8 + ["Super"] * 18 + ["Express"] * 14)[:S]
    rng.shuffle(fmt)
    store_id = ids("S", S, 3)
    region = rng.choice(REGIONS, S)
    size_factor = np.select([fmt == "Hyper", fmt == "Super"], [2.5, 1.0], 0.5) * rng.lognormal(0, 0.15, S)
    sqm = np.round(np.select([fmt == "Hyper", fmt == "Super"], [9000, 2500], 450) * size_factor
                   / np.select([fmt == "Hyper", fmt == "Super"], [2.5, 1.0], 0.5), -1)
    exp_group = np.empty(S, dtype=object)
    for f in FORMATS:                                   # stratified randomisation
        idx = np.where(fmt == f)[0]
        rng.shuffle(idx)
        exp_group[idx[: len(idx) // 2]] = "test"
        exp_group[idx[len(idx) // 2:]] = "control"
    stores = pd.DataFrame({
        "store_id": store_id, "format": fmt, "region": region,
        "city_tier": rng.choice([1, 2, 3], S, p=[0.4, 0.35, 0.25]),
        "size_sqm": sqm.astype(int),
        "open_date": pd.to_datetime("2010-01-01") + pd.to_timedelta(rng.integers(0, 4500, S), "D"),
        "experiment_group": exp_group,
    })
    reg_idx = np.array([REGIONS.index(r) for r in region])

    # ---------------- products ----------------
    rows = []
    for k, cat in enumerate(CATEGORIES):
        n = N_SKU[k]
        subs = SUBCATS[cat]
        for j in range(n):
            rows.append({"category": cat, "cat_idx": k, "subcategory": subs[j % len(subs)],
                         "brand": BRANDS[cat][j % len(BRANDS[cat])]})
    prod = pd.DataFrame(rows)
    P = len(prod)
    prod.insert(0, "sku", ids("SKU", P, 4))
    cat_of = prod["cat_idx"].to_numpy()
    list_price = np.round(np.array(PRICE_MED)[cat_of] * rng.lognormal(0, 0.35, P), 2)
    private = rng.random(P) < 0.18
    prod.loc[private, "brand"] = "NorthStar Own"
    list_price[private] *= 0.75
    # special SKUs for cannibalisation (R10)
    hair = np.where((prod.category == "Hair Care") & (prod.subcategory == "Shampoo"))[0]
    sku_big, sku_small = hair[0], hair[1]
    prod.loc[[sku_big, sku_small], "brand"] = "Lustra"
    list_price[sku_big], list_price[sku_small] = 7.99, 4.49
    pack = np.round(rng.choice([100, 200, 250, 330, 400, 500, 750, 1000], P), 0)
    pack[sku_big], pack[sku_small] = 400, 200
    unit = np.where(np.isin(cat_of, [3, 10]), "ml", np.where(cat_of == 11, "unit", "g"))
    unit[[sku_big, sku_small]] = "ml"
    lus_other = np.where((prod.brand == "Lustra") & (prod.subcategory == "Shampoo"))[0]
    for i in lus_other:
        if i not in (sku_big, sku_small) and pack[i] in (200, 400):
            pack[i] = 750
    prod["pack_size"] = np.where(unit == "unit", 1, pack).astype(int)
    prod["pack_unit"] = unit
    prod["list_price"] = np.round(list_price, 2)
    nm = (prod.brand + " " + prod.subcategory + " " + np.where(unit == "unit", "", prod.pack_size.astype(str) + unit)).str.strip()
    dup_n = nm.groupby(nm).cumcount()
    prod.insert(1, "product_name", np.where(dup_n > 0, nm + " (v" + (dup_n + 1).astype(str) + ")", nm))
    prod["unit_cost"] = np.round(list_price * rng.uniform(0.55, 0.80, P), 2)
    prod["private_label_flag"] = prod["brand"].eq("NorthStar Own")
    # price tier within category
    tier_arr = np.zeros(P, int)                 # price tier within category (explicit, version-independent)
    for k in range(len(CATEGORIES)):
        ix = np.where(cat_of == k)[0]
        order = ix[np.lexsort((ix, list_price[ix]))]
        tier_arr[order] = (np.arange(len(ix)) * 3) // len(ix)
    prod["price_tier"] = tier_arr
    # long tail (R22) and delisting (R16)
    special = {sku_big, sku_small}
    base = np.array(CAT_VOLUME)[cat_of] * rng.lognormal(0.9, 0.6, P)
    elig = np.array([i for i in range(P) if i not in special])
    n_tail = int(round(p.long_tail_share * P))
    tail = rng.choice(elig, n_tail, replace=False)
    base[tail] = rng.uniform(0.004, 0.012, n_tail)
    prod["long_tail_flag"] = False
    prod.loc[tail, "long_tail_flag"] = True
    delisted = []
    for cat, n in p.delist_counts.items():
        cand = np.where((prod.category == cat) & ~prod.long_tail_flag)[0]
        weakest = cand[np.argsort(base[cand], kind="stable")][: max(n * 2, n)]
        chosen = rng.choice(weakest, n, replace=False)
        base[chosen] *= 0.4
        delisted.extend(chosen.tolist())
    delisted = np.array(sorted(delisted))
    prod["launch_week"] = 1
    prod["delist_week"] = pd.array([pd.NA] * P, dtype="Int64")
    prod.loc[delisted, "delist_week"] = p.delist_week
    base[sku_big], base[sku_small] = 4.0, 3.0

    # ---------------- calendar, weather, prices ----------------
    days = pd.date_range(p.start_date, periods=W * 7, freq="D")
    day_week = np.repeat(weeks, 7)
    hol_week = np.zeros(W, bool)
    hol_name = np.array([""] * W, dtype=object)
    for wk in weeks:
        nm = HOLIDAYS.get((wk - 1) % 52 + 1)
        if nm:
            hol_week[wk - 1], hol_name[wk - 1] = True, nm
    calendar = pd.DataFrame({
        "date": days, "week": day_week, "month": days.month, "quarter": days.quarter,
        "year": days.year, "day_of_week": days.day_name(),
        "holiday_flag": hol_week[day_week - 1], "holiday_name": hol_name[day_week - 1],
        "payday_flag": days.day.isin([25, 26, 27, 28]),
    })
    doy = days.dayofyear.values
    temp = np.zeros((4, len(days)))
    for r in range(4):
        noise = np.zeros(len(days))
        e = rng.normal(0, 1.6, len(days))
        for t in range(1, len(days)):
            noise[t] = 0.7 * noise[t - 1] + e[t]
        temp[r] = 22 + [-3, 3, 0, 1][r] + 9 * np.cos(2 * np.pi * (doy - 200) / 365) + noise
    temp = np.round(temp, 1)
    temp_week = temp.reshape(4, W, 7).mean(axis=2)                  # region x week
    log_idx = np.zeros((4, len(CATEGORIES), W))
    for t in range(1, W):
        log_idx[:, :, t] = 0.85 * log_idx[:, :, t - 1] + rng.normal(0, 0.045, (4, len(CATEGORIES)))
    price_idx = np.exp(np.clip(log_idx, -0.18, 0.18))
    cpi = np.zeros((4, W))
    for t in range(1, W):
        cpi[:, t] = 0.9 * cpi[:, t - 1] + rng.normal(0, 1.5, 4)
    cpi = np.round(100 + cpi, 1)

    # ---------------- cell-level design: promos, display, stockouts ----------------
    shape = (S, P, W)
    pp = np.array([p.promo_prob[f] for f in fmt])[:, None, None]
    promo = rng.random(shape) < pp
    promo[:, tail, :] = False
    ptype_codes = rng.choice(4, shape, p=[0.5, 0.25, 0.1, 0.15])   # TPR, multibuy, BOGO, coupon
    disc_by_type = np.stack([rng.uniform(0.10, 0.30, shape), rng.uniform(0.15, 0.33, shape),
                             np.full(shape, 0.5), rng.uniform(0.10, 0.20, shape)])
    disc = np.take_along_axis(disc_by_type, ptype_codes[None], 0)[0] * promo
    del disc_by_type
    cw = np.array(p.cannibal_weeks) - 1
    promo[:, sku_big, :] = False
    disc[:, sku_big, :] = 0
    promo[:, sku_big, cw] = True
    ptype_codes[:, sku_big, cw] = 0
    disc[:, sku_big, cw] = 0.25
    promo[:, sku_small, cw] = False
    disc[:, sku_small, cw] = 0
    display = np.where(promo, rng.random(shape) < p.display_if_promo, rng.random(shape) < p.display_if_not)
    stockout = rng.random(shape) < p.stockout_rate
    stockout[:, tail, :] = False

    # ---------------- latent intensity ----------------
    month_f = np.array([p.q4_month_factor.get(m, 1.0) for m in wk_month])
    season = month_f * np.where(hol_week, p.holiday_factor, 1.0)
    shift = np.ones((S, W))
    s_shift = list(store_id).index(p.shift_store)
    shift[s_shift, p.shift_week - 1:] = p.shift_factor
    common = size_factor[:, None] * season[None, :] * shift                        # S x W

    el = np.array(ELASTICITY)[cat_of]                                              # P
    idx_cell = price_idx[reg_idx][:, cat_of, :]                                    # S x P x W
    unit_price = np.round(list_price[None, :, None] * idx_cell * (1 - disc), 2)
    price_ratio = idx_cell * (1 - disc)
    specific = base[None, :, None] * price_ratio ** el[None, :, None]
    specific *= np.where(promo, p.promo_effect, 1.0) * np.where(display, p.display_effect, 1.0)
    temp_sens = np.isin(cat_of, [3, 5, 10])
    tf = 1 + 0.02 * (temp_week[reg_idx] - 22)                                       # S x W
    specific[:, temp_sens, :] *= tf[:, None, :]
    specific *= (cpi[reg_idx] / 100.0)[:, None, :] ** 0.8
    exp_sku = np.where(prod.category == p.exp_category)[0]
    test_stores = np.where(exp_group == "test")[0]
    e0, e1 = p.exp_weeks
    specific[np.ix_(test_stores, exp_sku, np.arange(e0 - 1, e1))] *= p.exp_lift
    specific[:, sku_small, cw] *= p.cannibal_factor
    # delisting with 50% demand transfer
    for cat in p.delist_counts:
        k = CATEGORIES.index(cat)
        d_in = delisted[cat_of[delisted] == k]
        keep = np.where((cat_of == k) & ~np.isin(np.arange(P), delisted))[0]
        transfer = 1 + 0.5 * base[d_in].sum() / base[keep].sum()
        specific[:, d_in, p.delist_week:] = 0.0
        specific[:, keep, p.delist_week:] *= transfer
    specific = np.round(specific, 9)          # quantise: removes last-digit differences between platforms
    true_lambda = common[:, None, :] * specific                                    # expected demand
    obs_lambda = true_lambda * np.where(stockout, p.stockout_keep, 1.0)

    # ---------------- full-chain aggregates ----------------
    g = rng.gamma(15, 1 / 15, shape)
    units = rng.poisson(obs_lambda * g).astype(np.int64)
    revenue = units * unit_price
    del g
    wk_sku = pd.DataFrame({
        "sku": np.repeat(prod.sku.values, W), "week": np.tile(weeks, P),
        "units": units.sum(0).ravel(), "revenue": np.round(revenue.sum(0).ravel(), 2),
        "promo_store_count": promo.sum(0).ravel(), "display_store_count": display.sum(0).ravel(),
        "stockout_store_count": stockout.sum(0).ravel(),
    })
    wk_sku["avg_shelf_price"] = np.round(unit_price.mean(0).ravel(), 3)
    wk_sku["avg_unit_price"] = np.round(np.where(wk_sku.units > 0, wk_sku.revenue / wk_sku.units.clip(lower=1),
                                                 np.nan), 3)
    # store x SKU x week price extract for elasticity work (R13): North region, top-20 SKUs
    ex_st = np.where(region == "North")[0]
    ex_sku = []
    for cat in ("Snacks", "Dairy"):
        k = CATEGORIES.index(cat)
        cand = np.where((cat_of == k) & ~prod.long_tail_flag.values & prod.delist_week.isna().values)[0]
        ex_sku.extend(cand[np.argsort(-base[cand], kind="stable")][:20].tolist())
    ex_sku = np.array(ex_sku)
    gs, gp, gw = np.meshgrid(ex_st, ex_sku, np.arange(W), indexing="ij")
    gs, gp, gw = gs.ravel(), gp.ravel(), gw.ravel()
    price_extract = pd.DataFrame({
        "store_id": store_id[gs], "sku": prod.sku.values[gp], "category": prod.category.values[gp],
        "week": gw + 1, "list_price": list_price[gp].round(2), "shelf_price": unit_price[gs, gp, gw],
        "promo_flag": promo[gs, gp, gw], "display_flag": display[gs, gp, gw],
        "stockout_flag": stockout[gs, gp, gw], "units": units[gs, gp, gw]})
    alive = ~((prod.delist_week.notna().values)[:, None] & (weeks[None, :] > p.delist_week))
    wk_sku = wk_sku[alive.ravel()].reset_index(drop=True)
    # store x category x week
    cat_onehot = np.eye(len(CATEGORIES))[cat_of]                                    # P x K
    u_sc = np.einsum("spw,pk->skw", units, cat_onehot)
    r_sc = np.einsum("spw,pk->skw", revenue, cat_onehot)
    pr_sc = np.einsum("spw,pk->skw", promo.astype(float), cat_onehot) / np.array(N_SKU)[None, :, None]
    so_sc = np.einsum("spw,pk->skw", stockout.astype(float), cat_onehot) / np.array(N_SKU)[None, :, None]
    K = len(CATEGORIES)
    wk_sc = pd.DataFrame({
        "store_id": np.repeat(store_id, K * W), "category": np.tile(np.repeat(CATEGORIES, W), S),
        "week": np.tile(weeks, S * K), "units": u_sc.ravel(), "revenue": np.round(r_sc.ravel(), 2),
        "promo_sku_share": np.round(pr_sc.ravel(), 3), "stockout_sku_share": np.round(so_sc.ravel(), 3),
    })
    wk_sc["experiment_group"] = np.repeat(exp_group, K * W)
    wk_store = wk_sc.groupby(["store_id", "week"], as_index=False)[["units", "revenue"]].sum()
    wk_store["revenue"] = wk_store.revenue.round(2)
    wk_store = wk_store.merge(stores[["store_id", "format", "region"]], on="store_id")
    wk_store["holiday_flag"] = hol_week[wk_store.week.values - 1]
    wk_store["avg_temperature_c"] = np.round(temp_week[reg_idx[wk_store.store_id.str[1:].astype(int).values - 1],
                                                       wk_store.week.values - 1], 1)
    wk_rc = wk_sc.merge(stores[["store_id", "region"]], on="store_id").groupby(
        ["region", "category", "week"], as_index=False)[["units", "revenue"]].sum()
    wk_rc["revenue"] = wk_rc.revenue.round(2)
    truth["true_demand_sku_week"] = pd.DataFrame({
        "sku": np.repeat(prod.sku.values, W), "week": np.tile(weeks, P),
        "true_expected_units": np.round(true_lambda.sum(0).ravel(), 3),
        "observed_expected_units": np.round(obs_lambda.sum(0).ravel(), 3)})

    # ---------------- customers ----------------
    rng = rngs[1]
    C = p.n_customers
    seg = rng.choice(4, C, p=[0.31, 0.21, 0.21, 0.27])
    bulk = rng.choice(C, p.n_bulk, replace=False)
    seg[bulk] = 4
    s_prop = rng.lognormal(0, 0.45, C)
    seg_mem = np.array([0.3, 0.2, 0.6, -0.6, -0.5])[seg]
    member = rng.random(C) < sigmoid(0.55 + p.member_spend_slope * np.log(s_prop) + seg_mem)
    home = np.empty(C, int)
    for sg_ in range(5):
        m_ = seg == sg_
        w_ = size_factor * np.where(fmt == "Express", 4.0 if sg_ == 3 else 1.0, 1.0)
        home[m_] = rng.choice(S, m_.sum(), p=w_ / w_.sum())
    abuser_pool = np.where(np.isin(store_id[home], p.abuser_stores) & np.isin(seg, [1, 3]))[0]
    if len(abuser_pool) < p.n_abusers:
        extra = rng.choice(np.where(np.isin(seg, [1, 3]))[0], p.n_abusers - len(abuser_pool), replace=False)
        home[extra] = rng.choice([list(store_id).index(x) for x in p.abuser_stores], len(extra))
        abuser_pool = np.concatenate([abuser_pool, extra])
    abusers = rng.choice(abuser_pool, p.n_abusers, replace=False)
    end_date = days[-1]
    joins_during = member & (rng.random(C) < 0.30)
    signup = np.where(joins_during, rng.integers(10 * 7, 90 * 7, C),
                      -rng.integers(30, 2500, C))                     # day offset from start
    signup_date = pd.to_datetime(p.start_date) + pd.to_timedelta(signup, "D")
    age_p = {0: [0.02, 0.25, 0.38, 0.25, 0.08, 0.02], 1: [0.25, 0.40, 0.18, 0.10, 0.05, 0.02],
             2: [0.08, 0.20, 0.25, 0.22, 0.15, 0.10], 3: [0.20, 0.30, 0.20, 0.15, 0.10, 0.05],
             4: [0.0, 0.15, 0.35, 0.35, 0.15, 0.0]}
    ages = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
    age_band = np.array([ages[rng.choice(6, p=age_p[s])] for s in seg], dtype=object)
    hh_mean = np.array([4.6, 1.4, 3.0, 2.0, 3.0])[seg]
    hh = np.clip(np.round(rng.normal(hh_mean, 1.0)), 1, 8).astype(int)
    spend_rank = pd.Series(s_prop).rank(pct=True).values
    loy_seg = np.where(~member, "none", np.where(spend_rank > 0.8, "gold", np.where(spend_rank > 0.45, "silver", "bronze")))
    first_seen = np.where(member, signup, -rng.integers(30, 2000, C))
    tenure = np.maximum(0, ((end_date - (pd.to_datetime(p.start_date) + pd.to_timedelta(first_seen, "D"))).days / 30.44)).round().astype(int)
    cust_id = ids("C", C, 5)
    # MAR (R05) and MNAR (R06) missingness
    age_miss = rng.random(C) < np.where(member, p.age_missing_member, p.age_missing_nonmember)
    hh_miss = rng.random(C) < np.where(hh >= 5, p.hh_missing_large, p.hh_missing_small)
    customers = pd.DataFrame({
        "customer_id": cust_id, "loyalty_flag": member, "loyalty_segment": loy_seg,
        "age_band": np.where(age_miss, None, age_band),
        "household_size": pd.array(np.where(hh_miss, pd.NA, hh), dtype="Int64"),
        "tenure_months": tenure, "home_store_id": store_id[home],
        "signup_date": pd.Series(signup_date).where(member, pd.NaT).values,
    })
    truth["customer_segments"] = pd.DataFrame({"customer_id": cust_id, "segment": np.array(SEGMENTS)[seg],
                                               "bulk": np.isin(np.arange(C), bulk),
                                               "return_abuser": np.isin(np.arange(C), abusers),
                                               "spend_propensity": np.round(s_prop, 4),
                                               "true_household_size": hh, "true_age_band": age_band})

    # ---------------- panel: baskets ----------------
    rng = rngs[2]
    rate = np.array([0.040, 0.026, 0.036, 0.030, 0.010])[seg] * s_prop ** 0.3
    traffic = season / season.mean()
    vis = rng.poisson(rate[:, None] * traffic[None, :] * 1.0)                      # C x W
    cust_i, week_i = np.nonzero(vis)
    reps = vis[cust_i, week_i]
    cust_i, week_i = np.repeat(cust_i, reps), np.repeat(week_i, reps)
    st = np.where(rng.random(len(cust_i)) < 0.9, home[cust_i], rng.choice(S, len(cust_i), p=size_factor / size_factor.sum()))
    keep = rng.random(len(st)) < shift[st, week_i]                                  # R08 in panel
    cust_i, week_i, st = cust_i[keep], week_i[keep], st[keep]
    dow_w = np.array([0.12, 0.12, 0.12, 0.13, 0.165, 0.17, 0.145])
    dow = rng.choice(7, len(st), p=dow_w / dow_w.sum())
    bdate = wk_start[week_i] + pd.to_timedelta(dow, "D")
    # category composition
    cat_spec = np.einsum("spw,pk->skw", specific, cat_onehot) / np.einsum("p,pk->k", base, cat_onehot)[None, :, None]
    seg_rates = CAT_BASE_RATE[None, :] * SEG_CAT[seg[cust_i]]
    ab_mask = np.isin(cust_i, abusers)
    seg_rates[ab_mask, 11] *= 6
    seg_rates[ab_mask, 9] *= 2
    cat_spec = np.round(cat_spec, 9)
    lam = seg_rates * (s_prop[cust_i] ** 0.85 * (hh[cust_i] / 3.0) ** 0.35)[:, None] * cat_spec[st, :, week_i]
    # calibrate basket count to hit target lines (approx. 4% returns, 1% basket-rule adds)
    exp_lines = lam.sum()
    target_sales = p.target_lines - p.n_duplicates
    keep_frac = min(1.0, target_sales * 1.02 / (exp_lines * (1 + p.base_return_rate + 0.02)))
    special_c = np.isin(cust_i, np.concatenate([bulk, abusers]))
    keepb = special_c | (rng.random(len(st)) < keep_frac)
    cust_i, week_i, st, dow, lam = cust_i[keepb], week_i[keepb], st[keepb], dow[keepb], lam[keepb]
    bdate = bdate[keepb]
    nB = len(st)
    counts = rng.poisson(lam)
    # channel and payment
    online_p = np.where(week_i + 1 >= p.drift_week, p.online_share_after, p.online_share_before)
    is_online = rng.random(nB) < online_p
    channel = np.where(is_online, rng.choice(["click-and-collect", "delivery"], nB, p=[0.45, 0.55]), "in-store")
    pay = np.where(is_online, rng.choice(["card", "wallet"], nB, p=[0.6, 0.4]),
                   rng.choice(["card", "cash", "wallet", "voucher"], nB, p=[0.52, 0.22, 0.20, 0.06]))
    order = np.lexsort((cust_i, bdate.values))
    cust_i, week_i, st, dow, counts, channel, pay = (a[order] for a in (cust_i, week_i, st, dow, counts, channel, pay))
    bdate = bdate[order]
    basket_id = ids("B", nB, 6)

    # ---------------- panel: lines ----------------
    rng = rngs[3]
    tier = prod.price_tier.to_numpy()
    tier_pref = np.array([[3.0, 1.0, 0.3], [0.3, 1.0, 4.0], [1.5, 1.0, 0.7], [1.0, 1.0, 1.0], [2.0, 1.0, 0.5]])
    skus_by_cat = [np.where(cat_of == k)[0] for k in range(K)]
    fb = np.select([fmt == "Hyper", fmt == "Super"], [2.8, 2.0], 1.2)
    qf = np.array(QTY_FACTOR)
    loyal_now = member[cust_i] & (bdate.values >= signup_date.values[cust_i])
    b_idx, c_idx = np.nonzero(counts)
    n_rep = counts[b_idx, c_idx]
    b_idx, c_idx = np.repeat(b_idx, n_rep), np.repeat(c_idx, n_rep)

    def choose(bi, k):
        s_, w_, sg = st[bi], week_i[bi], seg[cust_i[bi]]
        cand = skus_by_cat[k]
        wts = specific[s_, cand, w_] * tier_pref[sg, tier[cand]]
        if sg == 2:
            wts = wts * np.where(promo[s_, cand, w_], 4.0, 1.0)
        u = rng.random()                      # always exactly one draw per line
        tot = wts.sum()
        if tot <= 0:
            return cand[min(int(u * len(cand)), len(cand) - 1)]
        return cand[min(np.searchsorted(np.round(np.cumsum(wts) / tot, 9), u), len(cand) - 1)]

    line_sku = np.array([choose(b, k) for b, k in zip(b_idx, c_idx)], dtype=int)
    # basket rules (R21)
    sub = prod.subcategory.to_numpy()
    pasta, sauce = np.where(sub == "Pasta")[0], np.where(sub == "Pasta Sauce")[0]
    beer, chips = np.where(sub == "Beer")[0], np.where(sub == "Chips")[0]
    add_b, add_s = [], []
    by_b = pd.Series(line_sku).groupby(b_idx).agg(set)
    u_rule = rng.random((nB, 4))              # unconditional draws: (pasta?, sauce pick, beer?, chips pick)
    sp, ch = set(sauce.tolist()), set(chips.tolist())
    pa, be = set(pasta.tolist()), set(beer.tolist())
    for b, skus in by_b.items():
        if skus & pa and not skus & sp and u_rule[b, 0] < p.pasta_sauce_q:
            add_b.append(b)
            add_s.append(_choose_among(u_rule[b, 1], sauce, specific[st[b], sauce, week_i[b]]))
        if skus & be and not skus & ch and u_rule[b, 2] < p.beer_chips_q:
            add_b.append(b)
            add_s.append(_choose_among(u_rule[b, 3], chips, specific[st[b], chips, week_i[b]]))
    b_idx = np.concatenate([b_idx, np.array(add_b, int)])
    line_sku = np.concatenate([line_sku, np.array(add_s, int)])
    o = np.argsort(b_idx, kind="stable")
    b_idx, line_sku = b_idx[o], line_sku[o]
    nL = len(b_idx)
    ls, lw = st[b_idx], week_i[b_idx]
    l_promo = promo[ls, line_sku, lw]
    l_disp = display[ls, line_sku, lw]
    M = np.round((1 + (fb[ls] - 1) * qf[cat_of[line_sku]]) * np.where(l_promo, p.promo_effect, 1) \
        * np.where(l_disp, p.display_effect, 1) * np.where(loyal_now[b_idx], p.loyalty_causal, 1), 9)
    qty = 1 + rng.poisson(M - 1)
    l_price = unit_price[ls, line_sku, lw]
    # bulk buyers (R07): scale quantities to hit target revenue share
    l_cust = cust_i[b_idx]
    is_bulk = np.isin(l_cust, bulk)
    rev0 = qty * l_price
    kbar = p.bulk_revenue_share * rev0[~is_bulk].sum() / ((1 - p.bulk_revenue_share) * rev0[is_bulk].sum())
    cust_k = rng.uniform(0.5, 1.5, C)
    qty = np.where(is_bulk, np.maximum(1, np.round(qty * kbar * cust_k[l_cust])), qty).astype(int)
    truth["bulk_multiplier_mean"] = float(kbar)

    lines = pd.DataFrame({
        "basket_id": basket_id[b_idx], "date": bdate.values[b_idx], "week": lw + 1,
        "store_id": store_id[ls], "channel": channel[b_idx], "customer_id": cust_id[l_cust],
        "loyalty_flag": loyal_now[b_idx], "sku": prod.sku.values[line_sku],
        "list_price": prod.list_price.values[line_sku], "unit_price": l_price,
        "discount_pct": np.round(disc[ls, line_sku, lw] * 100, 1), "promo_flag": l_promo,
        "promo_type": np.where(l_promo, np.array(["TPR", "multibuy", "BOGO", "coupon"])[ptype_codes[ls, line_sku, lw]], "none"),
        "display_flag": l_disp, "quantity": qty, "unit_cost": prod.unit_cost.values[line_sku],
        "stockout_flag": stockout[ls, line_sku, lw], "return_flag": False, "payment_method": pay[b_idx],
    })
    lines["_cust"] = l_cust
    lines["_sku"] = line_sku

    # ---------------- returns (R17) ----------------
    rng = rngs[4]
    rr = np.full(nL, p.base_return_rate)
    rr[cat_of[line_sku] == 11] = 0.10
    ab_line = np.isin(l_cust, abusers)
    rr[ab_line] = np.where(cat_of[line_sku[ab_line]] >= 9, p.abuser_return_rate * 1.3, p.abuser_return_rate * 0.8)
    ret = rng.random(nL) < rr
    rdates = pd.to_datetime(lines.date.values) + pd.to_timedelta(rng.integers(1, 21, nL), "D")
    ret &= rdates <= end_date
    rl = lines[ret].copy()
    rl["date"] = rdates[ret]
    rl["week"] = ((rl.date - pd.Timestamp(p.start_date)).dt.days // 7 + 1).values
    rl["quantity"] = -rl.quantity
    rl["return_flag"] = True
    rl["promo_flag"] = False
    rl["display_flag"] = False
    lines["_has_return"] = ret
    rl["_has_return"] = True
    lines = pd.concat([lines, rl], ignore_index=True)

    # ---------------- trim to exact size ----------------
    target = p.target_lines - p.n_duplicates
    excess = len(lines) - target
    truth["trimmed_lines"] = int(excess)
    if excess > 0:
        droppable = np.where(~lines._has_return & ~lines.return_flag & ~np.isin(lines._cust, np.concatenate([bulk, abusers])))[0]
        drop = rng.choice(droppable, excess, replace=False)
        lines = lines.drop(index=drop).reset_index(drop=True)
    elif excess < 0:
        raise RuntimeError(f"Panel short by {-excess} lines; raise visit rates")

    # ---------------- enrich ----------------
    lines = lines.sort_values(["date", "basket_id", "return_flag"], kind="stable").reset_index(drop=True)
    lines.insert(0, "line_id", ids("L", len(lines), 7))
    tx = lines.basket_id.str.replace("B", "T", regex=False) + np.where(lines.return_flag, "R", "")
    lines.insert(2, "transaction_id", tx)
    li = lines._sku.to_numpy()
    for col in ["category", "brand", "pack_size", "pack_unit"]:
        lines[col] = prod[col].values[li]
    s_ix = lines.store_id.str[1:].astype(int).to_numpy() - 1
    lines["format"] = fmt[s_ix]
    lines["region"] = region[s_ix]
    lines["city_tier"] = stores.city_tier.values[s_ix]
    ci = lines._cust.to_numpy()
    lines["loyalty_segment"] = np.where(lines.loyalty_flag, loy_seg[ci], "none")
    lines["age_band"] = customers.age_band.values[ci]
    lines["household_size"] = customers.household_size.values[ci]
    lines["tenure_months"] = tenure[ci]
    lines["revenue"] = np.round(lines.quantity * lines.unit_price, 2)
    lines["margin"] = np.round(lines.revenue - lines.unit_cost * lines.quantity, 2)
    d_ix = ((pd.to_datetime(lines.date) - pd.Timestamp(p.start_date)).dt.days).to_numpy()
    temp_missing = rng.random(temp.shape) < p.temp_mcar          # R04 (region-day)
    t_day = np.where(temp_missing, np.nan, temp)
    lines["temperature_c"] = t_day[reg_idx[s_ix], d_ix]
    lines["holiday_flag"] = calendar.holiday_flag.values[d_ix]
    wk = lines.week.to_numpy() - 1
    lines["competitor_price_index"] = cpi[reg_idx[s_ix], wk]
    lines["experiment_group"] = np.where(lines.category == p.exp_category, exp_group[s_ix], "none")
    planted: dict[str, list] = {}
    rng = rngs[5]

    # R01 negative quantity entry errors
    sale = np.where(~lines.return_flag & ~np.isin(lines._cust, bulk))[0]
    r01 = rng.choice(sale, p.n_negative_qty, replace=False)
    lines.loc[r01, "quantity"] = -lines.loc[r01, "quantity"]
    lines.loc[r01, ["revenue", "margin"]] = -lines.loc[r01, ["revenue", "margin"]].abs()
    planted["R01"] = lines.line_id[r01].tolist()
    # R02 price 100x
    fab_s = lines.store_id.eq(p.fabricated_store).to_numpy()
    sale2 = np.setdiff1d(sale, np.concatenate([r01, np.where(fab_s)[0]]))
    r02 = rng.choice(sale2, p.n_price_100x, replace=False)
    lines.loc[r02, "unit_price"] = np.round(lines.loc[r02, "unit_price"] * 100, 2)
    lines.loc[r02, "revenue"] = np.round(lines.loc[r02, "unit_price"] * lines.loc[r02, "quantity"], 2)
    lines.loc[r02, "margin"] = np.round(lines.loc[r02, "revenue"] - lines.loc[r02, "unit_cost"] * lines.loc[r02, "quantity"], 2)
    planted["R02"] = lines.line_id[r02].tolist()
    # R18 fabricated store: rounded, uniform-first-digit revenues
    fab_rows = np.where(fab_s & ~lines.return_flag.to_numpy())[0]
    fab = rng.choice(fab_rows, int(round(p.fabricated_share * len(fab_rows))), replace=False)
    mag = np.floor(np.log10(lines.loc[fab, "revenue"].abs().clip(lower=1)))
    newrev = np.round(rng.uniform(3, 10, len(fab)) * 10 ** mag * 2) / 2
    lines.loc[fab, "revenue"] = newrev
    lines.loc[fab, "margin"] = np.round(newrev - lines.loc[fab, "unit_cost"] * lines.loc[fab, "quantity"], 2)
    planted["R18"] = lines.line_id[fab].tolist()
    # R19 drift: discount logged as fraction for online channel from drift week
    r19 = np.where((lines.week >= p.drift_week) & lines.channel.ne("in-store") & (lines.discount_pct > 0))[0]
    lines.loc[r19, "discount_pct"] = np.round(lines.loc[r19, "discount_pct"] / 100, 3)
    planted["R19"] = lines.line_id[r19].tolist()
    planted["R17_customers"] = cust_id[abusers].tolist()
    planted["R07_customers"] = cust_id[bulk].tolist()
    # R03 duplicates
    dup_src = rng.choice(len(lines), p.n_duplicates, replace=False)
    planted["R03"] = lines.line_id[dup_src].tolist()
    lines = pd.concat([lines, lines.iloc[dup_src]], ignore_index=True)
    lines = lines.sort_values(["date", "line_id"], kind="stable").reset_index(drop=True)

    cols = ["line_id", "basket_id", "transaction_id", "date", "week", "store_id", "format", "region", "city_tier",
            "channel", "customer_id", "loyalty_flag", "loyalty_segment", "age_band", "household_size",
            "tenure_months", "sku", "category", "brand", "pack_size", "pack_unit", "list_price", "unit_price",
            "discount_pct", "promo_flag", "promo_type", "display_flag", "quantity", "revenue", "unit_cost",
            "margin", "stockout_flag", "return_flag", "payment_method", "temperature_c", "holiday_flag",
            "competitor_price_index", "experiment_group"]
    transactions = lines[cols].copy()
    transactions["date"] = pd.to_datetime(transactions.date).dt.date.astype(str)

    # ---------------- e-coupon A/B test (R24) ----------------
    rng = rngs[6]
    n = p.ab_users
    arm = np.where(rng.permutation(n) < n // 2, "treatment", "control")
    ver = rng.choice(["3.1", "3.2", "3.3"], n, p=[0.3, 0.4, 0.3])
    pre = np.round(rng.gamma(2.0, 30.0, n), 2)
    base_logit = np.log(p.ab_control_conv / (1 - p.ab_control_conv)) + 0.55 * (np.log(pre) - np.log(pre).mean())
    shift_t = np.log(p.ab_treat_conv / (1 - p.ab_treat_conv)) - np.log(p.ab_control_conv / (1 - p.ab_control_conv))
    pr = sigmoid(base_logit + np.where(arm == "treatment", shift_t, 0))
    # recentre so the marginal rates match the targets
    for a, tgt in (("control", p.ab_control_conv), ("treatment", p.ab_treat_conv)):
        m = arm == a
        lo, hi = -3.0, 3.0
        for _ in range(50):
            mid = (lo + hi) / 2
            if sigmoid(base_logit[m] + (shift_t if a == "treatment" else 0) + mid).mean() > tgt:
                hi = mid
            else:
                lo = mid
        pr[m] = np.round(sigmoid(base_logit[m] + (shift_t if a == "treatment" else 0) + mid), 9)
    conv = np.zeros(n, bool)                       # exact marginal rates, covariate-weighted
    for a, tgt in (("control", p.ab_control_conv), ("treatment", p.ab_treat_conv)):
        idx_a = np.where(arm == a)[0]
        conv[weighted_sample(rng, idx_a, int(round(tgt * len(idx_a))), pr[idx_a])] = True
    rev14 = np.where(conv, np.round(rng.gamma(2.2, 18.0, n), 2), 0.0)
    ab = pd.DataFrame({
        "user_id": ids("U", n, 6), "assigned_arm": arm, "app_version": ver,
        "platform": rng.choice(["ios", "android"], n, p=[0.45, 0.55]),
        "assignment_date": (pd.Timestamp(p.start_date) + pd.to_timedelta(7 * 81 + rng.integers(0, 14, n), "D")).date.astype(str),
        "pre_period_spend_30d": pre, "converted_14d": conv, "revenue_14d": rev14,
    })
    truth["ab_full"] = ab.copy()
    drop = (ab.assigned_arm == "control") & (ab.app_version == "3.2") & ~ab.converted_14d & (rng.random(n) < p.ab_drop_prob)
    planted["R24_dropped_users"] = ab.user_id[drop].tolist()
    ab = ab[~drop].reset_index(drop=True)

    products_current = prod[prod.delist_week.isna()].drop(columns=["cat_idx", "price_tier"]).reset_index(drop=True)
    products_archive = prod[prod.delist_week.notna()].drop(columns=["cat_idx", "price_tier"]).reset_index(drop=True)
    truth["planted"] = planted
    truth["special_skus"] = {"cannibal_promoted": prod.sku[sku_big], "cannibal_victim": prod.sku[sku_small],
                             "delisted": prod.sku.values[delisted].tolist(),
                             "long_tail": prod.sku.values[tail].tolist()}
    truth["elasticity"] = dict(zip(CATEGORIES, ELASTICITY))

    tables = {
        "transactions": transactions, "products": products_current, "products_archive": products_archive,
        "stores": stores, "customers": customers, "calendar": calendar.assign(date=calendar.date.dt.date.astype(str)),
        "weekly_store": wk_store, "weekly_store_category": wk_sc, "weekly_region_category": wk_rc,
        "weekly_sku_chain": wk_sku, "price_elasticity_extract": price_extract, "ecoupon_ab": ab,
    }
    customers["signup_date"] = pd.to_datetime(customers.signup_date).dt.date.astype("string")
    return {"tables": tables, "truth": truth}


def _choose_among(u, cand, wts):
    tot = wts.sum()
    if tot <= 0:
        return cand[min(int(u * len(cand)), len(cand) - 1)]
    return cand[min(np.searchsorted(np.round(np.cumsum(wts) / tot, 9), u), len(cand) - 1)]
