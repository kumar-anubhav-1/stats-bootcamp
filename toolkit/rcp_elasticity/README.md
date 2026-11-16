# rcp_elasticity — own-price elasticity with fixed effects and promotion controls

**Navigator node:** `N-REG-LOGLOG` · **First used:** L8.4 · **Status:** working

Poisson (or log-log) regression of units on log(price ÷ list price) with item, store and week fixed effects and promotion/display
controls; excludes stock-out weeks; reports the elasticity with CI, the estimate without controls (bias check), price-change
simulations for units, revenue and margin (`cost_ratio`), and the constant-elasticity optimal price as a reference.
