# rcp_benford — first-digit and rounding tests by group

**Navigator node:** `N-ANOM-BENFORD` · **First used:** L2.6 · **Status:** working

For each group (store, branch, employee) compares the first-digit distribution of an amount with Benford's law and with peer groups,
adjusts for sample size (smaller groups deviate more by chance), and adds a rounding test (share of values that are whole multiples of
`round_to`). Flags groups whose excess deviation or rounding is far beyond their peers.

| Role | Required | Meaning |
| --- | --- | --- |
| `target` | yes | positive amount |
| `group` | yes | unit to compare (store_id, branch_id, …) |

| Param | Default | Meaning |
| --- | --- | --- |
| `min_n` | 300 | skip smaller groups |
| `round_to` | 0.5 | rounding unit for the last-digit test |

**Outputs:** `narrative.md`, `benford_by_group.csv` (MAD, expected MAD at that n, Nigrini band, peer z, rounding share, χ² p),
`benford.png`, `metrics.json`.

**Limits:** a deviation is a reason to look, not proof. Data spanning fewer than ~2 orders of magnitude (prices, capped amounts) need
not follow Benford — rely on peer comparison there. Nigrini's MAD bands are rules of thumb.
