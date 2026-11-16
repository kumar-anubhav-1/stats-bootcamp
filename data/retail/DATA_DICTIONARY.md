# Data dictionary: retail

Generated from the data by `python -m datagen.docs`. Null % and examples are measured, not typed.

## transactions

One row per transaction line from the NorthStar customer panel (~1,500 identified shoppers). Returns are separate lines with negative quantity and return_flag = True.

Rows: 25,000 · Columns: 38

| Field | Type | Null % | Example | Description |
| --- | --- | --- | --- | --- |
| `line_id` | text | 0.0 | L0012418 | Line identifier (should be unique) |
| `basket_id` | text | 0.0 | B001578 | Shopping basket (one visit) |
| `transaction_id` | text | 0.0 | T001578 | Payment transaction; returns carry an 'R' suffix and reference the original basket |
| `date` | text | 0.0 | 2025-11-02 | Transaction date (ISO) |
| `week` | int64 | 0.0 | 52 | Week number 1-104 (week 1 starts 2024-11-04) |
| `store_id` | text | 0.0 | S006 | Store code |
| `format` | text | 0.0 | Super | Store format: Hyper, Super, Express |
| `region` | text | 0.0 | West | North/South/East/West |
| `city_tier` | int64 | 0.0 | 3 | 1 = metro, 3 = small town |
| `channel` | text | 0.0 | delivery | in-store, click-and-collect, delivery |
| `customer_id` | text | 0.0 | C00233 | Shopper id |
| `loyalty_flag` | bool | 0.0 | False | Shopper was a loyalty member at the time of the basket |
| `loyalty_segment` | text | 0.0 | none | bronze/silver/gold for members, none otherwise |
| `age_band` | text | 5.4 | 25-34 | Shopper age band |
| `household_size` | Int64 | 17.9 | 3 | People in household (self-reported) |
| `tenure_months` | int64 | 0.0 | 47 | Months since first relationship |
| `sku` | text | 0.0 | SKU0150 | Product code |
| `category` | text | 0.0 | Beverages | One of 12 categories |
| `brand` | text | 0.0 | NorthStar Own | Brand |
| `pack_size` | int64 | 0.0 | 250 | Pack size |
| `pack_unit` | text | 0.0 | ml | g, ml or unit |
| `list_price` | float64 | 0.0 | 1.61 | Regular shelf price before any discount |
| `unit_price` | float64 | 0.0 | 1.69 | Price paid per unit |
| `discount_pct` | float64 | 0.0 | 0.0 | Discount depth in percent (0-100) |
| `promo_flag` | bool | 0.0 | False | Line was on a price promotion |
| `promo_type` | text | 0.0 | none | none, TPR, multibuy, BOGO, coupon |
| `display_flag` | bool | 0.0 | False | Product was on secondary display |
| `quantity` | int64 | 0.0 | 2 | Units (negative for returns) |
| `revenue` | float64 | 0.0 | 3.38 | Line revenue = quantity x unit_price |
| `unit_cost` | float64 | 0.0 | 0.93 | Cost per unit |
| `margin` | float64 | 0.0 | 1.52 | revenue - unit_cost x quantity |
| `stockout_flag` | bool | 0.0 | False | SKU was out of stock in that store-week (partial availability) |
| `return_flag` | bool | 0.0 | False | Line is a return |
| `payment_method` | text | 0.0 | wallet | card, cash, wallet, voucher |
| `temperature_c` | float64 | 2.4 | 22.0 | Daily mean temperature in the store's region |
| `holiday_flag` | bool | 0.0 | False | Date falls in a holiday week |
| `competitor_price_index` | float64 | 0.0 | 95.4 | Competitor price level in region-week (100 = parity) |
| `experiment_group` | text | 0.0 | none | For Hair Care lines: the store's arm in the store-level feature-promotion test (test/control); 'none' otherwise |

## products

Current SKU master (active range as of today). Delisted SKUs are in products_archive.

Rows: 390 · Columns: 13

| Field | Type | Null % | Example | Description |
| --- | --- | --- | --- | --- |
| `sku` | text | 0.0 | SKU0214 | Product code |
| `product_name` | text | 0.0 | FrostBite Ice Cream 200g | Readable product name |
| `category` | text | 0.0 | Frozen | One of 12 categories |
| `subcategory` | text | 0.0 | Ice Cream | Subcategory |
| `brand` | text | 0.0 | FrostBite | Brand |
| `pack_size` | int64 | 0.0 | 200 | Pack size |
| `pack_unit` | text | 0.0 | g | g, ml or unit |
| `list_price` | float64 | 0.0 | 8.89 | Regular shelf price before any discount |
| `unit_cost` | float64 | 0.0 | 5.02 | Cost per unit |
| `private_label_flag` | bool | 0.0 | False | NorthStar own brand |
| `long_tail_flag` | bool | 0.0 | False | Low-volume specialty SKU |
| `launch_week` | int64 | 0.0 | 1 | First week on sale |
| `delist_week` | Int64 | 100.0 |  | Week the SKU was delisted (blank if active) |

## products_archive

SKUs delisted during the period (same columns as products).

Rows: 30 · Columns: 13

| Field | Type | Null % | Example | Description |
| --- | --- | --- | --- | --- |
| `sku` | text | 0.0 | SKU0204 | Product code |
| `product_name` | text | 0.0 | SnackStar Nuts 1000g |  |
| `category` | text | 0.0 | Snacks | One of 12 categories |
| `subcategory` | text | 0.0 | Nuts |  |
| `brand` | text | 0.0 | SnackStar | Brand |
| `pack_size` | int64 | 0.0 | 1000 | Pack size |
| `pack_unit` | text | 0.0 | g | g, ml or unit |
| `list_price` | float64 | 0.0 | 2.14 | Regular shelf price before any discount |
| `unit_cost` | float64 | 0.0 | 1.55 | Cost per unit |
| `private_label_flag` | bool | 0.0 | False |  |
| `long_tail_flag` | bool | 0.0 | False |  |
| `launch_week` | int64 | 0.0 | 1 |  |
| `delist_week` | Int64 | 0.0 | 52 |  |

## stores

Store master.

Rows: 40 · Columns: 7

| Field | Type | Null % | Example | Description |
| --- | --- | --- | --- | --- |
| `store_id` | text | 0.0 | S021 | Store code |
| `format` | text | 0.0 | Express | Store format: Hyper, Super, Express |
| `region` | text | 0.0 | North | North/South/East/West |
| `city_tier` | int64 | 0.0 | 1 | 1 = metro, 3 = small town |
| `size_sqm` | int64 | 0.0 | 490 | Selling area (m2) |
| `open_date` | datetime | 0.0 | 2012-07-31 00:00:00 | Store opening date |
| `experiment_group` | text | 0.0 | test | Arm in the Hair Care feature-promotion test (weeks 70-77), randomised within format |

## customers

Shopper master for the panel.

Rows: 1,500 · Columns: 8

| Field | Type | Null % | Example | Description |
| --- | --- | --- | --- | --- |
| `customer_id` | text | 0.0 | C00751 | Shopper id |
| `loyalty_flag` | bool | 0.0 | True | Shopper was a loyalty member at the time of the basket |
| `loyalty_segment` | text | 0.0 | gold | bronze/silver/gold for members, none otherwise |
| `age_band` | text | 8.5 | 35-44 | Shopper age band |
| `household_size` | Int64 | 13.5 | 5 | People in household (self-reported) |
| `tenure_months` | int64 | 0.0 | 10 | Months since first relationship |
| `home_store_id` | text | 0.0 | S033 | Most-visited store |
| `signup_date` | text | 36.6 | 2018-03-04 | Loyalty sign-up date (blank for non-members) |

## calendar

Daily calendar.

Rows: 728 · Columns: 9

| Field | Type | Null % | Example | Description |
| --- | --- | --- | --- | --- |
| `date` | text | 0.0 | 2025-11-03 | Transaction date (ISO) |
| `week` | int64 | 0.0 | 53 | Week number 1-104 (week 1 starts 2024-11-04) |
| `month` | int32 | 0.0 | 11 |  |
| `quarter` | int32 | 0.0 | 4 |  |
| `year` | int32 | 0.0 | 2025 |  |
| `day_of_week` | text | 0.0 | Monday |  |
| `holiday_flag` | bool | 0.0 | True | Date falls in a holiday week |
| `holiday_name` | text | 0.0 | Diwali |  |
| `payday_flag` | bool | 0.0 | False | Day 25-28 of month |

## weekly_store

Full-chain weekly sales by store (all customers, not just the panel).

Rows: 4,160 · Columns: 8

| Field | Type | Null % | Example | Description |
| --- | --- | --- | --- | --- |
| `store_id` | text | 0.0 | S021 | Store code |
| `week` | int64 | 0.0 | 1 | Week number 1-104 (week 1 starts 2024-11-04) |
| `units` | float64 | 0.0 | 970.0 |  |
| `revenue` | float64 | 0.0 | 3045.6 | Line revenue = quantity x unit_price |
| `format` | text | 0.0 | Express | Store format: Hyper, Super, Express |
| `region` | text | 0.0 | North | North/South/East/West |
| `holiday_flag` | bool | 0.0 | True | Date falls in a holiday week |
| `avg_temperature_c` | float64 | 0.0 | 16.5 | Weekly mean temperature |

## weekly_store_category

Full-chain weekly sales by store and category.

Rows: 49,920 · Columns: 8

| Field | Type | Null % | Example | Description |
| --- | --- | --- | --- | --- |
| `store_id` | text | 0.0 | S021 | Store code |
| `category` | text | 0.0 | Fresh Produce | One of 12 categories |
| `week` | int64 | 0.0 | 1 | Week number 1-104 (week 1 starts 2024-11-04) |
| `units` | float64 | 0.0 | 205.0 |  |
| `revenue` | float64 | 0.0 | 540.95 | Line revenue = quantity x unit_price |
| `promo_sku_share` | float64 | 0.0 | 0.4 | Share of the category's SKUs on promotion |
| `stockout_sku_share` | float64 | 0.0 | 0.044 | Share of the category's SKUs out of stock |
| `experiment_group` | text | 0.0 | test | For Hair Care lines: the store's arm in the store-level feature-promotion test (test/control); 'none' otherwise |

## weekly_region_category

Full-chain weekly sales by region and category (forecasting).

Rows: 4,992 · Columns: 5

| Field | Type | Null % | Example | Description |
| --- | --- | --- | --- | --- |
| `region` | text | 0.0 | South | North/South/East/West |
| `category` | text | 0.0 | Bakery | One of 12 categories |
| `week` | int64 | 0.0 | 1 | Week number 1-104 (week 1 starts 2024-11-04) |
| `units` | float64 | 0.0 | 2125.0 |  |
| `revenue` | float64 | 0.0 | 4750.53 | Line revenue = quantity x unit_price |

## weekly_sku_chain

Full-chain weekly sales by SKU (all 40 stores).

Rows: 42,120 · Columns: 9

| Field | Type | Null % | Example | Description |
| --- | --- | --- | --- | --- |
| `sku` | text | 0.0 | SKU0212 | Product code |
| `week` | int64 | 0.0 | 53 | Week number 1-104 (week 1 starts 2024-11-04) |
| `units` | int64 | 0.0 | 259 |  |
| `revenue` | float64 | 0.0 | 1242.51 | Line revenue = quantity x unit_price |
| `promo_store_count` | int64 | 0.0 | 8 | Stores running a promotion on the SKU |
| `display_store_count` | int64 | 0.0 | 10 | Stores with the SKU on display |
| `stockout_store_count` | int64 | 0.0 | 3 | Stores out of stock |
| `avg_shelf_price` | float64 | 0.0 | 4.745 | Simple average shelf price across stores |
| `avg_unit_price` | float64 | 17.3 | 2.095 | Revenue / units |

## price_elasticity_extract

Store x SKU x week extract for the top-20 Snacks and Dairy SKUs in the North region (pricing work).

Rows: 26,208 · Columns: 10

| Field | Type | Null % | Example | Description |
| --- | --- | --- | --- | --- |
| `store_id` | text | 0.0 | S020 | Store code |
| `sku` | text | 0.0 | SKU0050 | Product code |
| `category` | text | 0.0 | Dairy | One of 12 categories |
| `week` | int64 | 0.0 | 1 | Week number 1-104 (week 1 starts 2024-11-04) |
| `list_price` | float64 | 0.0 | 1.98 | Regular shelf price before any discount |
| `shelf_price` | float64 | 0.0 | 1.98 | Price charged that week |
| `promo_flag` | bool | 0.0 | False | Line was on a price promotion |
| `display_flag` | bool | 0.0 | False | Product was on secondary display |
| `stockout_flag` | bool | 0.0 | False | SKU was out of stock in that store-week (partial availability) |
| `units` | int64 | 0.0 | 21 |  |

## ecoupon_ab

Online e-coupon A/B test: one row per app user logged in the experiment.

Rows: 11,421 · Columns: 8

| Field | Type | Null % | Example | Description |
| --- | --- | --- | --- | --- |
| `user_id` | text | 0.0 | U005993 |  |
| `assigned_arm` | text | 0.0 | treatment | control or treatment (planned 50/50) |
| `app_version` | text | 0.0 | 3.3 | App version at assignment |
| `platform` | text | 0.0 | ios |  |
| `assignment_date` | text | 0.0 | 2026-05-25 |  |
| `pre_period_spend_30d` | float64 | 0.0 | 85.1 | Spend in the 30 days before assignment |
| `converted_14d` | bool | 0.0 | False | Purchased within 14 days |
| `revenue_14d` | float64 | 0.0 | 0.0 | Revenue within 14 days |
