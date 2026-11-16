# rcp_drift

Population and concept drift between a reference window and a current window.

- **Navigator:** `N-MON-PSI` (L9.6)
- **Roles:** `period` (required), `target` (optional, binary), `score` (optional, numeric)
- **Params:** `reference`, `current` (pandas queries), `features` (list), `bins`, `thresholds`, `score_higher_is_riskier`
- **Outputs:** `drift_table.csv` (PSI, band, medians, missingness, unit-change flag), `drift.png`, `narrative.md`, `metrics.json`

Configs: `retail_drift_discount.yaml` (R19 logging change), `finance_drift_vintage.yaml` (F11 population drift, F12 performance decay).

Reuse: change `reference`/`current` and `features` to monitor any model or KPI feed; schedule monthly.
