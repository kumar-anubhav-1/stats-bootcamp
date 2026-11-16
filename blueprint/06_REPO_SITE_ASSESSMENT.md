# 06. Repo, Site, Assessment and Build Plan

## 1. Repo tree

```
stats-bootcamp/
├── README.md                     # what it is, quick start (Codespaces / local), for companies and self-study
├── CLAUDE.md                     # learner rules for Claude Code (see 05 §4)
├── .claude/commands/             # slash commands per recipe + review, map-columns, regression-check
├── .vscode/                      # settings, recommended extensions (Claude Code, Python, Jupyter, YAML)
├── .devcontainer/                # Python 3.11, uv, deps pre-installed; Codespaces-ready
├── pyproject.toml                # pinned dependencies (instructor/CI use; learners never edit)
├── mkdocs.yml
├── docs/                         # the site
│   ├── index.md                  # track selector, how to use
│   ├── day-00/ … day-10/         # one .md per lesson; Foundation/Leader tabs inside each
│   ├── navigator/                # interactive map page (embeds navigator/widget)
│   ├── glossary.md               # rendered from glossary/glossary.yaml
│   ├── anomaly-hunt.md           # scoreboard page
│   ├── scorecard.md              # confidence scorecard
│   ├── assets/js/                # quiz.js, navigator.js, progress.js (vanilla JS, no build step)
│   └── assets/css/
├── navigator/
│   ├── trees.yaml                # single source for the poster, the site widget, and lesson markers
│   ├── scenarios.yaml            # 44 scenarios
│   └── poster/                   # generated SVG/PDF
├── data/
│   ├── retail/                   # generated parquet + csv, DATA_DICTIONARY.md, DATA_CARD.md
│   └── finance/
├── datagen/
│   ├── generate.py               # CLI: --domain --seed --variant
│   ├── retail/ finance/ transfer/
│   └── tests/                    # schema, reproducibility, one test per planted anomaly
├── validator/                    # recomputes every data-based answer from generated data
├── toolkit/
│   ├── common/                   # config loader, schema check, row accounting, output writer
│   ├── rcp_profile/ … rcp_drift/ # each: recipe.py, README.md, schema.yaml, examples/
│   └── configs/                  # example configs for both datasets and variants
├── quizzes/
│   ├── bank/day-XX/*.yaml        # question bank (structured, not hard-coded)
│   ├── diagnostic.yaml  final.yaml
│   └── schema.json               # question schema, validated in CI
├── exercises/day-XX/             # Foundation / Applied / Stretch sets per dataset
├── glossary/glossary.yaml
├── instructor/                   # excluded from the public site build
│   ├── anomaly_register.yaml     # answer key
│   ├── truth/                    # true demand, true PD, segment labels, anomaly row ids
│   ├── answer_keys/  rubrics/  facilitator_guide.md
│   └── exam/                     # held-out seeds 7001/7002, code-review exam
├── outputs/                      # learner outputs (git-ignored except examples)
└── .github/workflows/
    ├── data-and-tests.yml        # regenerate data, run anomaly tests, validator, quiz schema
    └── deploy-site.yml           # build MkDocs, deploy to GitHub Pages
```

**Instructor-content protection:** a public learner repo cannot hide files. Recommendation: two repos, `stats-bootcamp` (public or org-internal) and `stats-bootcamp-instructor` (private, holds `instructor/`, generator truth export and exam seeds), with CI in the private repo verifying the public one. Step 2 builds both folders in one workspace and splits at push time.

## 2. Site (MkDocs Material)

- **Track selector:** content tabs `Foundation | Leader` in every lesson; a site-wide toggle remembers the choice (localStorage) and opens the chosen tab by default.
- **Navigation:** Day → Lesson, with prev/next, "You are here" breadcrumb from lesson front matter, progress checkmarks.
- **Prompt cards:** admonition blocks with copy buttons (weak / better / expert).
- **Quizzes:** `quiz.js` loads YAML-converted JSON from the bank; instant feedback with explanations for every option, scoring, retry with numeric variants, per-track pass marks, progress saved locally, export/import of a progress file. Instructor view: upload cohort progress files → per-question statistics (difficulty, discrimination, common wrong option).
- **Navigator:** interactive widget plus downloadable poster.
- **Glossary:** searchable, auto-linked from lessons.
- **Mermaid** diagrams, MathJax for the one formula per lesson.
- **Deploy:** GitHub Actions → GitHub Pages. A private-Pages option for corporate cohorts.

## 3. Lesson template (12 sections, front matter drives the widgets)

```yaml
---
id: L3.4
title: Two-group comparison: promo lift and default-rate difference
time: {foundation: 120, leader: 60}
prerequisites: [L3.1, L3.3]
concepts: [C128, C129, C131, C133, C141, C142]
navigator: {you_are_here: N-TEST-2G, try_next: [N-TEST-PERM, N-BAYES-AB, N-REG-ANCOVA]}
anomalies: [R09, R07, F03]
recipe: rcp_two_group_test
---
```

Sections 1–12 exactly as in your master prompt (objectives & marker → business question → concept F/L → when to use/assumptions/fallbacks → prompt cards + recipe + verification → output anatomy → scenario matrix with norms → alternatives → planted trap + reuse drill → exercises → quiz + coaching cards + recap → instructor area).

## 4. Assessment design

### Question bank format

```yaml
- id: Q-L3.4-F-07
  type: numeric            # mcq | multi | true_false_reason | numeric | spot_error | scenario | navigator | ai_review
  track: F
  difficulty: 3            # 1-5
  lesson: L3.4
  concepts: [C129, C141]
  navigator_node: N-TEST-2G-MEAN
  anomaly: R09
  prompt: >
    Aggregate Hair Care units to store-week for weeks 70-77. What is the % lift
    (test vs control mean store-week units)?
  answer: {compute: validator.l3_4.hair_care_lift_pct, tolerance_abs: 1.5}
  explanation:
    correct: Store is the unit of randomisation, so compare store-level means.
    common_wrong:
      - answer_range: [20, 35]
        why: You analysed line level, which inflates n and mixes in display effects.
```

### Per lesson

- Foundation: 8–10 items (MCQ, multi-select, true/false with reason, numeric from data, spot the error).
- Leader: 5–8 scenario items (read output → interpret → decide; what would you ask the junior; which recommendation is wrong; alternative explanations), with rubric + model answer for open responses.
- Plus Navigator drills and AI-output review items in every day.
- Cross-track: either route may attempt the other's quiz (marked "refresh" or "stretch").

### Gates, exams, pass marks (proposed)

| Item | Foundation | Leader |
| --- | --- | --- |
| Lesson quiz | 70% to mark complete (unlimited retries with variants) | 70% |
| Day-end gate (quiz + data task) | 75%; below → remedial lesson links + extra practice set before next day | 75% |
| Pre-diagnostic | No pass mark; routes track and flags weak topics | Same |
| Transfer test | Rubric ≥ 3/5 on each criterion | Same + reuse review |
| Final exam (held-out seeds) | 75% | 75% |
| Code-review exam | — | Must find ≥ 5 of 7 planted flaws and make the right decision |
| Anomaly Hunt | ≥ 34 of 42 found and explained | ≥ 30 of 42 reviewed and decided |
| Completion | All gates + capstone + final exam passed | Same + code-review exam |

Learning gain = post-test minus diagnostic on the same blueprint (parallel forms).

### Mastery evidence

- **Exercises:** ≥ 15 per dataset per day in three tiers, each with business framing, deliverable, expected finding + tolerance, model answer, common wrong answers; Leader versions in "review and decide" form.
- **Anomaly Hunt scoreboard:** browser-side tracker; learner submits the finding (id guess + evidence number) and gets verification against tolerance; hints link to Navigator nodes.
- **Confidence scorecard:** competency matrix by concept group; self-rating before course and after each day; each rating links to evidence (exercise id, anomaly id, recipe run); chart shows self-rating vs demonstrated.
- **Explain-it-back** one-page readouts and **simulation briefs**, scored on a 5-criterion rubric: correctness, assumptions, interpretation, action, clarity.
- **Completion record:** auto-generated per learner from the progress file (skills, anomalies, scores, recipes reused).

## 5. CI

1. Regenerate data from seeds; check file hashes match committed manifest (reproducibility).
2. Run `datagen/tests`: one test per anomaly, inside tolerance.
3. Run `validator`: compute every `compute:` answer; fail if a quiz answer or exercise key changes unexpectedly.
4. Validate quiz YAML against `schema.json`; check every question has explanations and tags.
5. Run the two working recipes on both datasets and all variants (reuse smoke test).
6. Build MkDocs (strict mode: broken links fail) and deploy.

## 6. Step 2 build plan (after your approval)

1. Generators for retail, finance (+ insurance), variants, exam and transfer seeds; anomaly tests passing; register updated with measured magnitudes.
2. Data dictionaries and data cards.
3. Navigator v1: `trees.yaml` with all 13 trees, interactive widget, poster.
4. MkDocs site shell with track selector, quiz widget, progress, glossary page, Anomaly Hunt page.
5. Toolkit skeleton: `common/` + `rcp_profile` + `rcp_two_group_test` working on both datasets and variants; CLAUDE.md; slash commands.
6. Day 0 lessons (L0.1–L0.5) and diagnostic.
7. Reference lesson L3.4, full 12-section template, both tracks, with quizzes, exercises (15 per dataset), output anatomy and scenario matrix using numbers computed from the generated data.
8. CI workflows, local Git commits with clear messages.

Then pause for your quality review before Step 3 (Days 1–10, one day per pass).
