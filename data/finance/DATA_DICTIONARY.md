# Data dictionary: finance

Generated from the data by `python -m datagen.docs`. Null % and examples are measured, not typed.

## accounts

One row per booked account at Meridian Bank (personal loans and credit cards), originated 2023-01 to 2025-09, observed to 2026-10-31.

Rows: 25,000 · Columns: 39

| Field | Type | Null % | Example | Description |
| --- | --- | --- | --- | --- |
| `customer_id` | text | 0.0 | CU012501 |  |
| `account_id` | text | 0.0 | A012501 |  |
| `age` | int64 | 0.0 | 35 |  |
| `income_annual` | float64 | 3.8 | 67300.0 | Stated annual income |
| `employment_type` | text | 0.0 | salaried | salaried, self-employed, contract, retired, student |
| `region` | text | 0.0 | R4 | R1-R4 |
| `branch_id` | text | 0.0 | BR20 | Booking branch |
| `acquisition_channel` | text | 0.0 | branch | branch, online, partner |
| `tenure_months_with_bank` | int64 | 0.0 | 8 | Months as a bank customer before this account |
| `product_type` | text | 0.0 | personal_loan | credit_card or personal_loan |
| `limit_or_loan_amount` | float64 | 0.0 | 27000.0 | Card limit or loan principal |
| `interest_rate` | float64 | 0.0 | 0.1719 | Annual rate (decimal) |
| `term_months` | Int64 | 60.4 | 12 | Loan term (blank for cards) |
| `utilisation` | float64 | 39.6 | 0.912 | Card balance / limit at origination (cards only) |
| `dti` | float64 | 0.0 | 0.368 | Debt-to-income ratio |
| `bureau_score` | int64 | 0.0 | 688 | Credit bureau score (300-900) |
| `app_score` | int64 | 0.0 | 575 | Bank's application score (higher = safer) |
| `inquiries_6m` | int64 | 0.0 | 0 | Credit inquiries in last 6 months |
| `delinq_2y` | int64 | 0.0 | 0 | Delinquencies in last 2 years |
| `balance_current` | float64 | 0.0 | 14850.0 | Balance at snapshot |
| `txn_count_3m` | int64 | 0.0 | 6 | Transactions, last 3 observed months |
| `txn_amount_3m` | float64 | 0.0 | 630.59 | Transaction value, last 3 observed months |
| `digital_share` | float64 | 0.0 | 0.817 | Share of interactions via app/web |
| `branch_visits_6m` | int64 | 0.0 | 0 | Branch visits, last 6 months |
| `complaints_12m` | int64 | 0.0 | 0 | Complaints, last 12 months |
| `origination_date` | text | 0.0 | 2025-07-10 | Account open date |
| `vintage` | text | 0.0 | 2025Q3 | Origination quarter |
| `income_verified_flag` | bool | 0.0 | False | Income was documented |
| `default_12m` | bool | 0.0 | False | Reached 90+ days past due within 12 months of origination |
| `max_dpd_12m` | int64 | 0.0 | 0 | Worst days past due in first 12 months |
| `churn_flag` | bool | 0.0 | False | Account closed by customer before snapshot |
| `churn_month` | Int64 | 71.9 | 17 | Month on book of closure |
| `months_observed` | int64 | 0.0 | 15 | Months observed until churn, charge-off or snapshot (survival time) |
| `fraud_flag` | bool | 0.0 | False | Confirmed fraud |
| `protected_group` | text | 0.0 | B | Protected characteristic (A/B) — for fairness monitoring only, never a model input |
| `strategy_group` | text | 0.0 | none | Collections strategy for accounts that reached 30 DPD: champion / challenger (80/20); none otherwise |
| `cured_within_3m` | boolean | 83.2 | False | Collections account returned to current within 3 months |
| `collections_flag` | bool | 0.0 | False | Account entered collections (recorded after the event) |
| `recovery_amount` | float64 | 0.0 | 0.0 | Amount recovered after charge-off |

## performance_monthly

Monthly performance panel: one row per account per month on book (max 24). Parquet only.

Rows: 454,364 · Columns: 14

| Field | Type | Null % | Example | Description |
| --- | --- | --- | --- | --- |
| `account_id` | text | 0.0 | A012520 |  |
| `month_on_book` | int64 | 0.0 | 8 |  |
| `calendar_month` | text | 0.0 | 2025-11 |  |
| `balance` | float64 | 0.0 | 5219.48 |  |
| `payment` | float64 | 0.0 | 384.47 |  |
| `minimum_due` | float64 | 0.0 | 156.58 |  |
| `dpd` | int64 | 0.0 | 0 | Days past due |
| `delinquency_bucket` | text | 0.0 | current | current, 1-29, 30-59, 60-89, 90+ |
| `utilisation` | float64 | 39.7 | 0.083 | Card balance / limit at origination (cards only) |
| `txn_count` | int64 | 0.0 | 19 |  |
| `txn_amount` | float64 | 0.0 | 1973.78 |  |
| `cash_deposit_count` | int64 | 0.0 | 0 | Cash deposits in month |
| `cash_deposit_max` | float64 | 0.0 | 0.0 | Largest single cash deposit |
| `status` | text | 0.0 | open | open, closed, charged-off |

## applications_declined

Applications declined in the same period (no performance data).

Rows: 5,240 · Columns: 16

| Field | Type | Null % | Example | Description |
| --- | --- | --- | --- | --- |
| `application_id` | text | 0.0 | APP002621 |  |
| `application_date` | text | 0.0 | 2023-03-01 |  |
| `age` | int64 | 0.0 | 27 |  |
| `income_annual` | float64 | 0.0 | 47300.0 | Stated annual income |
| `employment_type` | text | 0.0 | salaried | salaried, self-employed, contract, retired, student |
| `region` | text | 0.0 | R1 | R1-R4 |
| `acquisition_channel` | text | 0.0 | branch | branch, online, partner |
| `product_type` | text | 0.0 | personal_loan | credit_card or personal_loan |
| `requested_amount` | float64 | 0.0 | 21400.0 | Requested limit/principal |
| `bureau_score` | int64 | 0.0 | 482 | Credit bureau score (300-900) |
| `dti` | float64 | 0.0 | 0.388 | Debt-to-income ratio |
| `inquiries_6m` | int64 | 0.0 | 3 | Credit inquiries in last 6 months |
| `delinq_2y` | int64 | 0.0 | 2 | Delinquencies in last 2 years |
| `app_score` | int64 | 0.0 | 417 | Bank's application score (higher = safer) |
| `protected_group` | text | 0.0 | B | Protected characteristic (A/B) — for fairness monitoring only, never a model input |
| `decline_reason` | text | 0.0 | low bureau score | Primary decline reason |

## devices_addresses

Links between accounts and device ids / address ids (anonymised).

Rows: 57,615 · Columns: 3

| Field | Type | Null % | Example | Description |
| --- | --- | --- | --- | --- |
| `account_id` | text | 0.0 | A012067 |  |
| `link_type` | text | 0.0 | address | device or address |
| `link_id` | text | 0.0 | LK000406 | Anonymised device or address id |

## policies

Optional insurance book: one row per policy-year.

Rows: 8,000 · Columns: 10

| Field | Type | Null % | Example | Description |
| --- | --- | --- | --- | --- |
| `policy_id` | text | 0.0 | P004001 |  |
| `customer_id` | text | 61.2 | CU001438 |  |
| `product` | text | 0.0 | motor |  |
| `exposure_years` | float64 | 0.0 | 0.37 | Fraction of year insured |
| `sum_insured` | float64 | 0.0 | 16700.0 | Sum insured |
| `driver_age_band` | text | 35.6 | 25-34 |  |
| `vehicle_group` | Int64 | 35.6 | 2 | Motor risk group 1-5 |
| `property_type` | text | 64.4 | townhouse |  |
| `region` | text | 0.0 | R3 | R1-R4 |
| `premium` | float64 | 0.0 | 224.42 |  |

## claims

Claims on the policies.

Rows: 692 · Columns: 5

| Field | Type | Null % | Example | Description |
| --- | --- | --- | --- | --- |
| `claim_id` | text | 0.0 | CL000347 |  |
| `policy_id` | text | 0.0 | P003924 |  |
| `claim_date` | text | 0.0 | 2025-02-03 |  |
| `claim_amount` | float64 | 0.0 | 1511.82 | Incurred amount |
| `claim_type` | text | 0.0 | glass |  |
