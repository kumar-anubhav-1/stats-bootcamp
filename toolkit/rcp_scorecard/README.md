# rcp_scorecard — WoE/IV binning and points-based logistic scorecard

**Navigator node:** `N-ML-SCORECARD` · **First used:** L8.7 · **Status:** working

Bins features (edges or quantiles; missing as its own bin), computes WoE and IV, drops weak features (`min_iv`), fits a logistic model on
WoE and converts to points (`base_score` at `base_odds`, `pdo`), reports Gini and KS and (optionally) bad rate by vintage. Output
`woe_points.csv`. Booked-only data: performance of declined applicants is unknown (reject inference).
