# Statistics for Data Science Bootcamp

A rigorous two-week statistics, machine-learning and AI bootcamp for anyone — with two learning paths: **Basic → Advanced** (new to the subject) and **Leader** (experienced decision-makers). Learners do all analysis by
instructing **Claude Code in VS Code** in plain English — no coding is taught. Built on two synthetic 25,000-row datasets
(retail and banking) with **42 planted issues** that learners find, explain and fix.

> **Status: complete** — Days 0–10 plus an optional Day 11 computer-vision module (76 lessons, 1,100+ quiz questions, 30+ exercises per day), 42 interactive charts (sliders and
> rotatable 3-D), mental maps for every section, an optional learn-by-doing lab in every lesson, 20 working recipes, Navigator (13 trees),
> instructor pack and push-to-GitHub checklist. Recipes: `rcp_profile`, `rcp_quality`, `rcp_outliers`, `rcp_two_group_test`, `rcp_distribution_fit`, `rcp_benford`, `rcp_multi_group_test`, `rcp_power`, `rcp_ab_test`, `rcp_regression`, `rcp_classifier`, `rcp_forecast`, `rcp_changepoint`, `rcp_inventory`, `rcp_cluster`, `rcp_basket`, `rcp_elasticity`, `rcp_anomaly_scan`, `rcp_scorecard`, `rcp_drift`. See `blueprint/` for the approved design.

## Quick start

**Codespaces (recommended):** Code → Codespaces → Create. The dev container installs everything and generates the data.

**Local:**

```bash
pip install -e .                       # Python 3.10+
python -m datagen.generate             # both datasets (seed 20261115), ~15 s
python -m toolkit.run toolkit/configs/retail_promo_lift.yaml
python -m tools.build_site && mkdocs serve   # course site at http://127.0.0.1:8000
```

**Everything in one command** (regenerate data → tests → anomaly register → recipe regression checks → render → strict build):

```bash
./build.sh            # or: make
./build.sh --quick    # reuse existing data/
./build.sh --serve    # then preview the site
```

Learners will not type these — they ask Claude Code (rules in `CLAUDE.md`, slash commands in `.claude/commands/`).

## Repository map

| Path | What |
| --- | --- |
| `blueprint/` | Approved Step 1 design: concept inventory (296), Navigator design, datasets and Anomaly Register, module map, toolkit, repo/site |
| `datagen/` | Seeded generators (retail, finance, transfer-test), variants, held-out exam seeds; `tests/` prove every planted anomaly |
| `data/` | Generated data (git-ignored) + `DATA_DICTIONARY.md`, `DATA_CARD.md`, `MANIFEST.json` |
| `validator/` | `measures.py` (measures all 42 phenomena), `register.py` (answer key), `answers.py` (every number used in lessons/quizzes) |
| `toolkit/` | Configuration-driven recipes: 20 working recipes (complete); `configs/`, `baselines/` |
| `navigator/` | `trees.yaml` (13 trees, 79 technique cards), `scenarios.yaml` (44), poster generator and PDFs |
| `site_src/` | Lesson and page templates (numbers are placeholders filled from the data) |
| `quizzes/` | Question bank (YAML), Anomaly Hunt clues, scorecard competencies |
| `exercises/` | Exercise sets with computed expected answers |
| `glossary/` | Glossary source |
| `docs/` | Generated site sources (`python -m tools.build_site`) — do not edit by hand |
| `instructor/` | Anomaly answer key; **instructor-only** (private repo): `pack/` (facilitator guide, rubrics, code-review exam, keys), `exam_config.py`, `transfer_gen.py`; generated truth/exam/transfer data (git-ignored) |
| `templates/` | Pre-registration template (L3.7) |
| `tools/` | `build_site.py` (renders the site from data), `instructor_pack.py` (answer keys), `split_repos.sh` (public/private split) |
| `.github/workflows/` | CI: regenerate data, prove anomalies, regression-check recipes, validate quizzes, build and deploy the site |

## How numbers stay honest

Every number in a lesson, quiz or exercise is a placeholder (e.g. `{{ a.l34_hc_lift_pct }}`) rendered from
`validator/answers.py`, which computes it from the generated data. CI fails if any planted anomaly drifts outside its tolerance band
(`python -m pytest`), if a recipe's results change unexpectedly (`--check-baseline`), or if a question lacks explanations.

## Instructor material

Start with `instructor/pack/README.md` (facilitator guide, rubrics, code-review exam and key, completion record). `make instructor`
generates the held-out exam data (seeds 7001/7002), the Day-10 transfer dataset and their answer keys. Before publishing, follow
**[`PUSH_TO_GITHUB.md`](PUSH_TO_GITHUB.md)**: `tools/split_repos.sh` produces a public learner repo without any instructor material and a
private instructor repo.

## Independent review

`REVIEW_BRIEF.md` is a ready-to-use brief for a second-model (or human expert) review: rules that keep the computed numbers and
build intact, a findings checklist and format, a safe fix process, and a framework for proposing new topics.

## Course at a glance

| Day | Theme | Recipes introduced |
| --- | --- | --- |
| 0 | Workbench, vibe-coding playbook, build and validate the data | `rcp_profile` |
| 1 | Data quality, missingness, descriptive statistics | `rcp_quality`, `rcp_outliers` |
| 2 | Probability, distributions, Benford, Monte Carlo | `rcp_distribution_fit`, `rcp_benford` |
| 3 | Inference: CIs, tests, power, multiple testing | `rcp_two_group_test`, `rcp_multi_group_test`, `rcp_power` |
| 4 | Experiments: SRM, CUPED, sequential, Bayesian, DAGs | `rcp_ab_test` |
| 5 | Regression, GLMs, Part A/B capstone | `rcp_regression` |
| 6 | Machine learning, validation, leakage, metrics | `rcp_classifier` |
| 7 | Time series, forecasting, inventory | `rcp_forecast`, `rcp_changepoint`, `rcp_inventory` |
| 8 | Segmentation, pricing, anomaly, fraud, credit risk | `rcp_cluster`, `rcp_basket`, `rcp_elasticity`, `rcp_anomaly_scan`, `rcp_scorecard` |
| 9 | Causal methods, survival, AI, risk, fairness, monitoring, storytelling | `rcp_drift` |
| 10 | Transfer test, capstone, Navigator sprint, final exams | — |

## Licence and data

© 2026 Kumar Anubhav. Licensed under **[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)** — you may share and adapt
the course with credit, but not for commercial purposes. See [`LICENSE`](LICENSE). All data is synthetic; course text is original.
