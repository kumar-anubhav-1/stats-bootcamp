---
description: Map an unfamiliar dataset's columns to a recipe's roles and flag mismatches
argument-hint: <data file> <recipe>
---
I want to use the recipe and file given here: $ARGUMENTS.

1. Read the recipe README in `toolkit/<recipe>/README.md` and list its roles.
2. Profile the file (types, units, grain, nulls, ranges) without changing it.
3. Propose a mapping from roles to columns in a table with a confidence level and reason for each.
4. Flag every mismatch: wrong type, different units (e.g. cents vs units), different grain, missing values, renamed or ambiguous fields, duplicated keys.
5. Write a new config file next to the closest example config, changing only `dataset` and `columns`/`filters`. Show it to me before running.
