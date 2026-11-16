# rcp_forecast — baselines, ETS, regression with seasonality, SARIMAX, rolling-origin backtest

**Navigator nodes:** `N-FCST-SEASON`, `N-FCST-DRIVERS`, `N-FCST-INTERMITTENT` · **First used:** L7.2 · **Status:** working

Aggregates rows to one series per period, fits the chosen models (naive, seasonal naive, moving average, damped Holt, log-linear
regression on Fourier terms + drivers, SARIMAX(1,0,0) with the same regressors, Croston, SBA), reports hold-out and rolling-origin
backtest WAPE, MASE and bias, and plots the forecasts.

| Role | Required | Meaning |
| --- | --- | --- |
| `time` | yes | integer period (week, month index) |
| `target` | yes | quantity to forecast (summed per period) |
| `exog` | no | drivers known in advance (holiday flag, temperature forecast, promotions) |

Params: `season_length`, `horizon`, `train_end`, `origins`, `models`, `fourier_k`, `log`. The dataset block accepts `joins`.

**Outputs:** `narrative.md`, `forecasts.csv`, `backtest.csv`, `forecast.png`, `metrics.json` (tolerance declared for fitted models).

**Limits:** drivers must be known at forecast time (use forecasts of temperature, planned promotions). One series per run — loop over
groups by changing the filter, or use the hierarchy guidance in L7.4.
