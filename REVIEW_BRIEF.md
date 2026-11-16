# Independent review brief — Statistics for Data Science Bootcamp

**For:** an independent AI reviewer (prepared for Claude Fable 5.2), or a human expert reviewer
**Course owner:** Kumar Anubhav
**Built with:** Claude Opus 5.5 · **Repository:** this folder (`stats-bootcamp/`)

You are the second pair of eyes on a finished course. Your job is to **find what is wrong, unclear, inconsistent or missing**,
propose fixes, and only after the owner approves, make careful edits that keep the build green. You did not write this course;
that independence is the point. Be specific, be evidence-based, and say "no issue found" where that is the truth.

---

## 1. What the course is

- **Subject:** statistics, machine learning and AI for real business decisions, from descriptive statistics to deep learning,
  causal inference, monitoring and an optional computer-vision module.
- **Audience:** anyone — students, career-changers, analysts, managers. Assume **a graduate with decent maths and good logical
  sense, but no statistics background**. Plain English, every term defined at first use.
- **Two learning paths over the same lessons:**
  - **Basic → Advanced** — new to the subject; step-by-step, labs.
  - **Leader** — experienced decision-makers; fast refresh, judgement, reading outputs, coaching others.
- **Industry-first pedagogy:** every topic opens with a real problem at **NorthStar Markets** (grocery retail) or **Meridian Bank**
  (retail bank), never with a textbook definition.
- **Learning by doing:** learners never write code; they direct **Claude Code** in plain English. Each lesson has prompt cards and an
  optional "Learn by doing" lab.
- **Size:** Days 0–10 plus optional Day 11 (computer vision), 76 lessons, ~1,170 quiz questions, 30+ exercises per day,
  42 interactive charts, 7 mental-map pages, 20 reusable analysis recipes, 42 planted data issues (+3 in the vision module).

### Lesson template (every lesson follows it)

`here()` marker → objectives → 1 Business question (Retail / Finance tabs) → 2 Concept (Basic → Advanced / Leader tabs) →
3 Navigator → 4 Prompt cards (+ Learn-by-doing lab) → 5 Output anatomy → 6 Scenario matrix → 7 Planted traps and reuse drill →
8 Exercises → 9 Quiz → 10 Recap → instructor area.

### Where things live

| Path | What | May you edit it? |
| --- | --- | --- |
| `site_src/day-NN/LN-x.md` | lesson sources (Markdown + Jinja placeholders) | **yes — main review target** |
| `site_src/maps/*.md`, `site_src/start/*.md`, `site_src/index.md` | mental maps, start pages, home | yes |
| `quizzes/bank/*.yaml` | question bank | yes, with the YAML rules below |
| `exercises/day-NN/*.yaml` | exercises with expected answers | yes, with the YAML rules below |
| `glossary/glossary.yaml` | glossary | yes |
| `validator/answers*.py` | **computes every number** used in lessons, quizzes, exercises; ends with narrative "guards" | only to fix a genuine computational error; explain why |
| `tools/charts*.py` | interactive charts built from the data | only to fix a genuine error |
| `toolkit/` | analysis recipes + configs + baselines | no, unless a bug is proven (then re-save baselines and explain) |
| `datagen/` | synthetic data generators | **no** (changes every number in the course) |
| `docs/`, `site/` | **generated** — overwritten by the build | **never edit** |
| `instructor/` | answer keys, instructor pack (private) | review only; never copy answers into learner pages |
| `blueprint/` | the original approved design | read-only reference |

---

## 2. Ground rules — do not break these

1. **Never type a number into a lesson, quiz or exercise.** Numbers are placeholders like `{{ a.v_kappa }}` or
   `{{ a.d8_el_snacks }}`, rendered from `validator/answers*.py`. If a sentence needs a number that has no key, add the computation
   to the right `answers_*.py` and reference the new key. Never replace a placeholder with its current value.
2. **Jinja inside YAML:** any YAML string containing `{{` must be **double-quoted** and use **single quotes inside the Jinja**,
   e.g. `"Recall {{ a.v_det['test stores'].recall }}%"`. Never let YAML double up single quotes inside `{{ }}` (`''`) — the build
   renders raw text before parsing and will fail.
3. **Quiz schema:** types are `mcq`, `multi`, `numeric`, `scenario`, `open`, `tf_reason`, `spot_error`, `navigator`,
   `ai_review`. Every `mcq`/`scenario` has **exactly one** `correct: true` option and a `why` on **every** option (wrong answers
   teach). `numeric` needs `answer` + `tolerance_abs`; `open` needs `model` + `rubric`. Lesson quizzes need ≥ 8 questions
   (Basic → Advanced, id `LN.x-F`) and ≥ 5 (Leader, id `LN.x-L`).
4. **Exercise schema:** `id, lesson, tier (Basic|Applied|Stretch), title, framing, deliverable, expected, tolerance, model, wrong,
   leader`. Keep 15+ retail and 15+ finance per day.
5. **Keep the template, both tabs and both industries** in every lesson you touch. Do not delete the Leader layer or the
   finance/retail framing.
6. **Plain English** for the audience above; define a term the first time it appears; prefer a business example to an abstract one.
7. **Narrative guards:** each `answers_*.py` ends with `checks = {...}` asserting that the story told in the lesson matches the data.
   If you change a lesson's claim, update or add the guard. If a guard fails after your change, the lesson is now wrong — fix
   the lesson, not the guard.
8. **Verify after every batch:** run `make quick` (or `./build.sh --quick`); it must end with **✔ All checks passed**. Use `make`
   (full) before your final hand-over. The strict MkDocs build must show no warnings.
9. **Small, separate commits** per batch, with a clear message. Never rewrite history.
10. **Do not add new lessons, days or tools in Phase 2.** New topics are proposals only (Phase 3).

---

## 3. Phase 1 — Review (findings only, no edits)

Read the built site as a learner would (`make serve`, or open `site/index.html` after `make quick`) **and** the sources. Work
in this order, highest risk first:

1. Days 3–5 (inference, experiments, regression): statistical correctness matters most here.
2. Days 6 and 9 (ML, causal, survival, risk, fairness, monitoring, deep learning).
3. Day 11 (computer vision), Days 7–8, Days 1–2, Day 0, Day 10.
4. Mental maps (`site_src/maps/`), start pages, glossary, quiz banks end to end.

### Checklist (apply to every lesson)

| # | Category | Ask |
| --- | --- | --- |
| A | **Statistical correctness** | Is every definition, formula, assumption and interpretation correct? Any misreading of p-values, CIs, odds ratios, AUC, PSI, kappa, IoU, VaR/ES? |
| B | **Numbers ↔ narrative** | Does each sentence's claim match the rendered number (direction, size, "higher/lower", "significant")? Do tables agree with the text? |
| C | **Plain English** | Could a maths-literate graduate with no statistics follow it? Undefined jargon? Over-long sentences? |
| D | **Industry realism** | Are retail and banking scenarios, KPIs and rules of thumb credible to a practitioner? Any unrealistic or outdated practice? Are norms labelled as rules of thumb? |
| E | **Pedagogy** | Does the business question motivate the concept? Is the order logical? Are prerequisites right? Is the Leader layer genuinely about judgement? |
| F | **Quiz quality** | Exactly one defensible correct answer? Plausible distractors? Explanations correct? Ambiguous or trick questions? Numeric tolerances sensible? |
| G | **Exercise quality** | Deliverable clear? Expected answer matches the lesson? Model answer and common-wrong-answer useful? |
| H | **Charts and diagrams** | Does each chart show what its caption says? Are axis labels, titles and slider labels clear? Any misleading scale? Do Mermaid diagrams render and read well? |
| I | **Consistency** | Same term, symbol and number used the same way across lessons, maps, glossary and quizzes? Cross-references (`L6.4`, links) correct? |
| J | **Coverage vs brief** | Anything promised in `blueprint/` or the home page that is missing or thin? |
| K | **Responsible AI & ethics** | Fairness, privacy, data-safety and AI-governance advice correct and proportionate? |
| L | **Accessibility & UX** | Colour-only meaning, unreadable tables on mobile, broken interactivity, very long pages? |

### Severity

- **Critical** — factually wrong statistics, a number contradicting its text, a quiz keyed to a wrong answer, a build break.
- **Major** — misleading or confusing explanation, unrealistic industry practice, missing key concept for the lesson's objective.
- **Minor** — clarity, wording, formatting, small inconsistency.
- **Suggestion** — optional improvement.

### Output format (Phase 1 deliverable)

Create `review/FINDINGS.md` containing:

1. **Executive summary** (≤ 1 page): overall quality, top 10 issues, areas of strength, recommended fix effort.
2. **Findings table** — one row per issue:

| ID | Location (file + section / quiz id / chart id) | Category (A–L) | Severity | Finding | Evidence (quote or rendered number) | Suggested fix | Effort (S/M/L) |
| --- | --- | --- | --- | --- | --- | --- | --- |

3. **Per-day verdicts:** "ready", "ready after minor fixes" or "needs rework", with one line of reasoning.

Also write `review/findings.csv` with the same columns so the owner can sort and approve. **Stop after Phase 1 and wait for the
owner's approval list.**

---

## 4. Phase 2 — Approved fixes

Apply only the findings the owner marks as approved, in this order: Critical → Major → Minor.

- Work in batches of ≤ 1 day of content (or ≤ 15 findings). After each batch run `make quick`; commit with
  `Review fixes: <scope> (<finding IDs>)`.
- Keep a `review/CHANGELOG.md`: finding ID → files changed → what changed → how verified.
- If a fix needs a new number, add it to the right `validator/answers_*.py`, add or adjust a guard, and reference the key.
- If you discover that a planted data issue or a recipe behaves differently from what a lesson says, report it as a new finding
  rather than changing `datagen/` or `toolkit/`.
- Finish with a full `make` run and report its last lines.

---

## 5. Phase 3 — New-topic proposals (proposals only)

The owner wants to know what else is worth teaching. Propose **at most 10** additions, ranked. Judge each against these
criteria: real demand in retail/banking analytics today; fit with the audience and the two paths; builds on existing lessons;
can be taught with the course's synthetic data or a freely redistributable dataset; can be taught by directing Claude Code
without teaching coding; size (half-day, day, module).

For each proposal give:

| Field | Content |
| --- | --- |
| Topic and one-line pitch | |
| Business problem (retail and/or banking) | the industry question it answers |
| Why it matters now | evidence of industry use |
| Where it fits | new lesson, extension of an existing lesson (name it), or new optional module |
| Learning objectives (3–5) | |
| Data needed | existing data, a generator change, or a named open dataset (with licence) |
| Effort | S (≤ 1 lesson), M (2–4 lessons), L (module) |
| Risks / prerequisites | |

Seed list to **evaluate, not assume** (accept, reject or merge each, with a reason):

1. Text analytics / NLP module (complaints, reviews: classical text features → embeddings → LLM classification with evaluation), a
   sibling to the computer-vision module.
2. Recommender systems (market basket → collaborative filtering → embeddings), with offline/online evaluation.
3. Optimisation and operations research (linear programming for promotion budgets, assortment, staff rostering, collections
   capacity).
4. Bayesian hierarchical models (store- and branch-level effects, partial pooling) beyond L4.3.
5. Causal machine learning (double/debiased ML, heterogeneous treatment effects) beyond uplift in L9.1.
6. Geospatial analytics (store catchments, branch network, location-based risk).
7. Experimentation at scale (interference, switchback tests, multi-armed bandits, guardrail portfolios).
8. LLM evaluation and LLM-assisted analytics (evaluation sets, hallucination measurement, RAG quality metrics).
9. MLOps essentials (model registry, deployment patterns, CI for models) at an awareness level.
10. Climate/ESG risk and alternative data in credit — awareness.

Put proposals in `review/PROPOSALS.md`. Do not build any of them unless the owner approves a specific proposal.

---

## 6. Hand-over checklist

- [ ] `review/FINDINGS.md` and `review/findings.csv` (Phase 1)
- [ ] Owner's approval list received before any edit
- [ ] `review/CHANGELOG.md` and commits per batch (Phase 2)
- [ ] Final `make` passes; last lines pasted in the changelog
- [ ] `review/PROPOSALS.md` (Phase 3)
- [ ] No edits to `docs/`, `site/`, `datagen/`; no numbers typed in place of placeholders; no instructor answers in learner pages

## 7. Useful commands

```bash
make quick            # render + all checks, reuse existing data (~3 min)
make                  # full: regenerate data, tests, anomaly register, recipe checks, render, strict build
make serve            # build and preview the site at http://127.0.0.1:8000
python -m tools.build_site     # render only
SB_NOGUARD=1 python -c "from validator.answers import compute; compute()"   # list failing narrative guards instead of stopping
python quizzes/topup.py        # re-run quiz top-ups (idempotent)
```

Reading order for orientation: `README.md` → `site_src/index.md` → `site_src/maps/index.md` → `site_src/day-03/L3-4.md`
(the reference lesson) → `validator/answers_day3.py` → `quizzes/bank/day03_L3-4.yaml`.
