---
description: Run a toolkit recipe with a config, then explain the result
argument-hint: <config path> [audience]
---
Run the toolkit recipe defined in the config `$ARGUMENTS` using `python -m toolkit.run <config>`.

Before running: open the config, tell me the recipe, dataset, unit of analysis, column mapping and filters in plain English,
and state the assumptions the recipe will check. After running: read `narrative.md`, `schema_report.md` and
`row_accounting.md` in the output folder and explain the result for a business audience in at most 8 bullet points:
effect size with confidence interval, whether it is practically meaningful, assumption checks, rows removed, and what a
sceptical reviewer would ask next. Do not quote any number that is not in the output files.
