# rcp_profile — profile any table

**Navigator node:** `N-DESC-PROFILE` · **First used:** L0.4 · **Status:** working

## What it does (plain English)

Looks at every column of a table and tells you what is in it: types, missing values, unique counts, ranges,
percentiles, skew, outliers and duplicates. It then lists **what needs your attention** in plain language.
It never changes your data.

## Roles (map them in the config `columns:` block)

| Role | Required | Meaning |
| --- | --- | --- |
| `id` | no | Row identifier, used to detect duplicate ids / wrong grain |
| `date` | no | Main date column |
| `target` | no | The outcome you care about; gets its own distribution plot |
| `group` | no | A segment column |

## Parameters

| Key | Default | Meaning |
| --- | --- | --- |
| `max_categories` | 15 | Top values shown per categorical column |
| `plots` | true | Write histogram/ECDF and missing-value plots |

## Outputs (dated folder under `outputs/rcp_profile/`)

`narrative.md` · `profile.csv` · `numeric_summary.csv` · `categorical_top.csv` · `quality_flags.csv` · `plots/` ·
`schema_report.md` · `row_accounting.md` · `metrics.json` · `run_manifest.json`

## Limits

Flags are prompts, not verdicts: a negative quantity may be a valid return. Profiling does not test *why* values are missing
(use `rcp_quality` for MCAR/MAR checks).

## Example prompt for Claude Code

> Run the profile recipe on `data/finance/accounts.parquet`. Copy `toolkit/configs/retail_profile_transactions.yaml`,
> change only the dataset path and column mapping (id = account_id, date = origination_date, target = balance_current),
> run it, and summarise the top five issues in plain English. Do not change the recipe code.
