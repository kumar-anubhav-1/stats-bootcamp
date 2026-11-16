# rcp_inventory — ABC/XYZ classification, safety stock and reorder points

**Navigator node:** `N-OPT-INVENTORY` · **First used:** L7.6 · **Status:** working

Builds an item × period demand matrix, classifies items by value (ABC) and variability (XYZ), and computes safety stock and reorder
points at chosen service levels for a lead time (normal approximation, z·σ·√L), plus the Poisson-assumption safety stock for comparison
and an optional newsvendor order quantity.

| Role | Required | Meaning |
| --- | --- | --- |
| `item` | yes | SKU / product |
| `time` | yes | period |
| `target` | yes | units demanded |
| `value` | no | revenue for ABC (else mean × periods) |

Params: `lead_time`, `service_levels`, `abc`, `xyz`, `top_n`, `newsvendor: {price, cost, salvage}`.

**Outputs:** `narrative.md`, `inventory_policy.csv`, `metrics.json`.

**Limits:** cycle-service-level formula; stock-outs censor observed demand (uncensor first, L7.5); lumpy demand needs simulation.
