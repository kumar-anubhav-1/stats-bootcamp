# rcp_quality — data-quality rules, duplicates and missing-data diagnosis

**Navigator nodes:** `N-DESC-QUALITY`, `N-DESC-MISSING` · **First used:** L1.2, L1.3 · **Status:** working

## What it does

Checks a table against rules you write in the config (no code), counts duplicates, and diagnoses missing values: how many,
whether missingness depends on other fields (tested at the unit where values go missing), and whether the outcome differs when a
value is missing (the MNAR signature). **It never changes the source data** — flagged rows go to `quarantine.csv`; an optional
cleaned copy is written to the output folder.

## Roles

| Role | Required | Meaning |
| --- | --- | --- |
| `id` | no | Row key (duplicate-id check, examples in the rule log) |
| `target` | no | Outcome compared between rows with and without each missing value |

## Parameters

| Key | Meaning |
| --- | --- |
| `rules` | list of `{name, flag, severity, why}`; `flag` is a pandas expression that is **true for bad rows**; severity `error` or `warning` |
| `missing_by` | columns to test missingness against (chi-square for categories, Mann-Whitney for numbers) |
| `missing_unit` | per column, the unit at which values go missing, e.g. `temperature_c: [region, date]`, `age_band: [customer_id]` |
| `reconcile` | `{column, expected_total, tolerance_pct}` |
| `write_clean` | write `clean.parquet` without rows failing `error` rules and without duplicate ids |

## Outputs

`narrative.md` · `rule_log.csv` · `quarantine.csv` · `missingness.csv` · `missingness_tests.csv` · `clean.parquet` (optional) ·
`schema_report.md` · `row_accounting.md` · `metrics.json`

## Limits

Tests can show data are *not* MCAR; they cannot prove MCAR or rule out MNAR. Rules encode business knowledge — review them with
the data owner (a rule that flags a third of the rows is usually a misunderstanding).

## Example prompt

> Run `toolkit/configs/retail_quality_transactions.yaml`. List each rule and what it protects against before running; afterwards
> report rows flagged per rule, where each warning is concentrated, and classify each missing column as consistent with MCAR, MAR or
> possibly MNAR. Do not delete anything.
