# Toolkit: reusable, configuration-driven analysis recipes

Every recipe asks for **roles** (target, group, date, cluster …) instead of column names. A small YAML config maps roles to the
columns of whatever dataset you use, so the same recipe runs on retail, finance, or a file you have never seen — by changing the
config only, never the code.

```bash
python -m toolkit.run toolkit/configs/retail_promo_lift.yaml                  # run
python -m toolkit.run toolkit/configs/retail_promo_lift.yaml --check-baseline # confirm results unchanged after edits
python -m toolkit.run --list
```

You will not type these yourself: ask Claude Code, e.g. *"Run the two-group test recipe with the retail promo-lift config and
explain the result to a category manager."* Slash commands in `.claude/commands/` do the same.

Every run writes a dated folder with `narrative.md`, tables, plots, `schema_report.md`, `row_accounting.md` (every row that was
removed and why), `metrics.json` and `run_manifest.json` (config, data hash, versions).

See `catalogue.yaml` for all 20 recipes and their status. Working now: **rcp_profile**, **rcp_two_group_test**.

## Golden rules for reuse

1. Read and explain a recipe before touching it.
2. Adapt by **config only**. If the logic must change, that is a new version: review the diff, re-run the regression check.
3. Never accept a result whose schema report has errors or unexplained row loss.
4. After any change, re-run the **original** config with `--check-baseline`.
