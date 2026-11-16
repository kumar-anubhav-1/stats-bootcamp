---
description: Turn a successful one-off analysis into a reusable recipe
argument-hint: <path to the one-off analysis>
---
Turn the analysis in $ARGUMENTS into a new toolkit recipe that follows the pattern of `toolkit/rcp_two_group_test/`:
roles instead of column names, a `SCHEMA`, use of `toolkit.common.core` (schema check, filters, row accounting, output folder,
metrics.json), a plain-English `narrative.md`, a README, and one example config for each dataset. Show me the plan and the
README first; write code only after I approve. Then run it on both datasets and save a baseline.
