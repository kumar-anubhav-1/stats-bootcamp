# rcp_changepoint — level shifts by binary segmentation, with a CUSUM monitor

**Navigator node:** `N-FCST-BREAK` · **First used:** L7.5 · **Status:** working

Finds sustained level shifts in a series (optionally one unit's share of the other units' total, which removes common seasonality),
reports segment means and % changes, and shows when a CUSUM monitor would have alarmed.

| Role | Required | Meaning |
| --- | --- | --- |
| `time` | yes | period |
| `target` | yes | value |
| `group` | no | unit column (with `params.unit`) |

Params: `unit`, `share_of_total`, `max_breaks`, `min_segment`, `penalty`, `cusum: {baseline_periods, k, h}`.

**Outputs:** `narrative.md`, `series.csv`, `changepoints.png`, `metrics.json`.

**Limits:** detects mean shifts, not variance or trend changes; find the business cause before modelling across a break.
