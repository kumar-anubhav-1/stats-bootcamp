"""Build the course site sources: render lesson templates and data files with computed numbers.

    python -m tools.build_site            # site_src/ -> docs/, quizzes/navigator/glossary -> docs/assets/data/
    mkdocs serve                          # preview
Every {{ a.<name> }} placeholder comes from validator.answers (computed from the generated data);
{{ reg.<ID> }} from the Anomaly Register. Fails loudly on undefined placeholders or invalid questions.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from collections import deque
from pathlib import Path

import jinja2
import markdown
import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC, DOCS = ROOT / "site_src", ROOT / "docs"
DATA_OUT = DOCS / "assets" / "data"
MD = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"])
CHOICE = {"mcq", "tf_reason", "spot_error", "scenario", "navigator", "ai_review", "multi"}
TYPES = CHOICE | {"numeric", "open"}


def md(s) -> str:
    MD.reset()
    return MD.convert(str(s).strip()) if s is not None else ""


class Num(float):
    """Float that prints without trailing noise in templates."""


def fmt_num(x, nd=None):
    if isinstance(x, bool) or x is None:
        return str(x)
    if isinstance(x, int):
        return f"{x:,}"
    if isinstance(x, float):
        if nd is not None:
            return f"{x:,.{nd}f}"
        if abs(x) >= 1000:
            return f"{x:,.0f}"
        if abs(x) < 0.001 and x != 0:
            return f"{x:.2g}"
        return f"{x:,.4f}".rstrip("0").rstrip(".")
    return str(x)


def lesson_catalogue() -> list[dict]:
    """Lessons from the module map, plus any lesson page in site_src not listed there (titles from the page heading)."""
    txt = (ROOT / "blueprint" / "04_MODULE_MAP.md").read_text()
    out, seen = [], set()
    for m in re.finditer(r"^\| \**(L\d+\.\d+)\** \| ([^|]+?) \|", txt, re.M):
        lid, title = m.group(1), re.sub(r"\*\*|\s*\(Step 2 reference lesson\)", "", m.group(2)).strip()
        d, n = lid[1:].split(".")
        page = SRC / f"day-{int(d):02d}" / f"L{d}-{n}.md"
        out.append({"id": lid, "title": title, "day": int(d), "url": f"day-{int(d):02d}/L{d}-{n}/" if page.exists() else None})
        seen.add(lid)
    for page in sorted(SRC.glob("day-*/L*-*.md")):
        d, n = page.stem[1:].split("-")
        lid = f"L{d}.{n}"
        if lid not in seen:
            head = page.read_text().splitlines()[0]
            out.append({"id": lid, "title": head.split("·", 1)[-1].strip(), "day": int(d), "url": f"day-{int(d):02d}/L{d}-{n}/"})
    out.sort(key=lambda x: (x["day"], int(x["id"].split(".")[1])))
    return out


def lesson_pages():
    """Per lesson page: id, day, title, Basic/Leader minutes (from the lesson-meta line)."""
    rows = []
    for page in sorted(SRC.glob("day-*/L*-*.md"), key=lambda p: (int(p.stem[1:].split("-")[0]), int(p.stem.split("-")[1]))):
        t = page.read_text()
        d, n = page.stem[1:].split("-")
        title = t.splitlines()[0].split("·", 1)[-1].strip()
        mb = re.search(r"Basic → Advanced (\d+) min", t)
        ml = re.search(r"Leader (\d+) min", t)
        rows.append({"id": f"L{d}.{n}", "day": int(d), "title": title, "url": f"../../day-{int(d):02d}/L{d}-{n}/",
                     "b": int(mb.group(1)) if mb else None, "l": int(ml.group(1)) if ml else None})
    return rows


def navigator_data(lessons):
    t = yaml.safe_load((ROOT / "navigator" / "trees.yaml").read_text())
    sc = yaml.safe_load((ROOT / "navigator" / "scenarios.yaml").read_text())
    nodes, starts, titles = {}, {}, {}
    for tid, tr in t["trees"].items():
        starts[tid] = tr["start"]
        titles[tid] = tr["title"]
        for nid, n in tr["nodes"].items():
            n = dict(n)
            n["tree"] = tid
            nodes[nid] = n
    for s in sc:
        for p in s["path"]:
            nodes[p].setdefault("scenarios", []).append(f"{s['id']} {s['text']}")
    # shortest path (node ids and option labels) from the master question to every node
    paths, labels = {}, {}
    q = deque()
    for o in t["master"]["opts"]:
        nid = starts.get(o["next"], o["next"])
        if nid not in paths:
            paths[nid], labels[nid] = [nid], [o["label"]]
            q.append(nid)
    while q:
        cur = q.popleft()
        for o in nodes[cur].get("opts", []):
            nid = starts.get(o["next"], o["next"])
            if nid not in paths:
                paths[nid], labels[nid] = paths[cur] + [nid], labels[cur] + [o["label"]]
                q.append(nid)
    lessons_map = {l["id"]: l["url"] for l in lessons if l["url"]}
    data = {"master": t["master"], "nodes": nodes, "starts": starts, "paths": paths, "lessons": lessons_map, "tree_titles": titles}
    return data, labels, sc


def build_questions(files, env, ctx) -> dict:
    bank = {}
    errors = []
    for f in files:
        raw = env.from_string(f.read_text()).render(**ctx)
        doc = yaml.safe_load(raw)
        for quiz in doc["quizzes"]:
            qid = quiz["id"]
            quiz.setdefault("pass_mark", 70)
            quiz.setdefault("track", "F")
            for q in quiz["questions"]:
                where = f"{f.name}:{qid}/{q.get('id')}"
                if q.get("type") not in TYPES:
                    errors.append(f"{where}: unknown type {q.get('type')}")
                    continue
                for k in ("id", "prompt", "difficulty"):
                    if k not in q:
                        errors.append(f"{where}: missing {k}")
                q.setdefault("track", quiz["track"])
                q.setdefault("lesson", quiz.get("lesson"))
                q["prompt_html"] = md(q["prompt"])
                q["prompt_text"] = re.sub(r"<[^>]+>", "", q["prompt_html"])
                q["explanation_html"] = md(q.get("explanation", ""))
                q["hint_html"] = md(q["hint"]) if q.get("hint") else ""
                if q["type"] in CHOICE:
                    opts = q.get("options", [])
                    nc = sum(bool(o.get("correct")) for o in opts)
                    if q["type"] != "multi" and nc != 1:
                        errors.append(f"{where}: needs exactly one correct option (has {nc})")
                    if q["type"] == "multi" and nc < 1:
                        errors.append(f"{where}: multi needs >= 1 correct option")
                    for o in opts:
                        if not o.get("why"):
                            errors.append(f"{where}: option {o.get('id')} has no explanation ('why')")
                        o["html"] = md(o["text"])
                        o["why_html"] = md(o.get("why", ""))
                elif q["type"] == "numeric":
                    try:
                        q["answer"] = float(q["answer"])
                    except Exception:
                        errors.append(f"{where}: numeric answer not a number: {q.get('answer')!r}")
                    if "tolerance_abs" in q:
                        q["tolerance_abs"] = float(q["tolerance_abs"])
                    for v in q.get("variants", []):
                        v["prompt_html"] = md(v.pop("prompt"))
                        v["answer"] = float(v["answer"])
                elif q["type"] == "open":
                    if not q.get("model"):
                        errors.append(f"{where}: open question needs a model answer")
                    q["model_html"] = md(q.get("model", ""))
                    q["rubric_html"] = md(q.get("rubric", ""))
            if qid in bank:
                errors.append(f"duplicate quiz id {qid}")
            bank[qid] = quiz
    if errors:
        raise SystemExit("Question bank errors:\n  " + "\n  ".join(errors))
    return bank


def main():
    sys.path.insert(0, str(ROOT))
    from validator import answers as A
    from validator import register as R

    print("computing answers from data ...")
    a = A.compute()
    (ROOT / "validator" / "answers.json").write_text(json.dumps(a, indent=2, default=str))
    reg_items = R.build()
    R.write(reg_items)
    reg = {i["id"]: i for i in reg_items}
    lessons = lesson_catalogue()
    nav, labels, scen = navigator_data(lessons)

    def here(node):
        n = nav["nodes"][node]
        crumbs = " › ".join(labels[node])
        return (f'<div class="you-are-here">📍 <b>You are here:</b> {crumbs} › '
                f'<a href="../../navigator/#{node}">{n.get("t") or n.get("q")}</a> <code>{node}</code></div>')

    def try_next(nodes):
        rows = []
        for nd in nodes:
            n = nav["nodes"][nd]
            rows.append(f"- **[{n.get('t') or n.get('q')}](../../navigator/#{nd})** — {n.get('use') or 'decision point: start the tree here'}")
        return '!!! tip "What else could I try?"\n' + "\n".join("    " + r for r in rows)

    env = jinja2.Environment(undefined=jinja2.StrictUndefined, keep_trailing_newline=True,
                             variable_start_string="{{", variable_end_string="}}")
    env.filters["n"] = fmt_num
    env.filters["signed"] = lambda x: f"{x:+g}"
    env.filters["pct"] = lambda x, nd=1: f"{x:.{nd}f}%"
    env.filters["kv"] = lambda d, unit="": " · ".join(f"{k} {fmt_num(v)}{unit}" for k, v in d.items())
    ctx = {"a": a, "reg": reg, "here": here, "try_next": try_next, "nav": nav}

    # exercises (rendered, then passed to lesson templates)
    ex = {}
    for f in sorted((ROOT / "exercises").rglob("*.yaml")):
        ex[f.stem] = yaml.safe_load(env.from_string(f.read_text()).render(**ctx))
    ctx["ex"] = ex

    def exercises(key, lesson=None):
        """Render exercise sets (retail and finance) for one lesson as collapsible blocks."""
        out = []
        for dom, title in (("retail", "Retail · NorthStar"), ("finance", "Finance · Meridian")):
            items = [e for e in ex[key][dom] if lesson is None or e.get("lesson") == lesson]
            if not items:
                continue
            out.append(f"### {title}\n")
            for e in items:
                out.append(f'??? example "{e["id"]} · {e["tier"]} · {e["title"]}"')
                out.append(f"    **Business framing:** {e['framing']}\n")
                out.append(f"    **Deliverable:** {e['deliverable']}\n")
                out.append('    ??? success "Expected finding and model answer"')
                out.append(f"        **Expected:** {e['expected']} *(tolerance: {e['tolerance']})*\n")
                out.append(f"        **Model answer:** {e['model']}\n")
                out.append(f"        **Common wrong answer:** {e['wrong']}\n")
                out.append(f"    **Leader drill:** {e['leader']}\n")
        return "\n".join(out)

    ctx["exercises"] = exercises

    def route(track):
        """Day-by-day route through every lesson for one path (no lesson restructuring: the path chooses tabs and emphasis)."""
        rows, out, day = lesson_pages(), [], None
        do = {"B": "Concept (Basic → Advanced tab) · prompt cards · learn-by-doing lab · Basic + Applied exercises · Basic → Advanced quiz",
              "L": "Refresh box · judgement points · output anatomy · Leader scenario matrix · Leader drills in exercises · Leader quiz"}[track]
        total = 0
        for r in rows:
            if r["day"] != day:
                day = r["day"]
                out += ["", f"### Day {day}", "", "| Lesson | Time |", "| --- | --- |"]
            mins = r["b"] if track == "B" else r["l"]
            total += mins or 0
            out.append(f"| [{r['id']} · {r['title']}]({r['url']}) | {str(mins) + ' min' if mins else '—'} |")
        return (f"**Total guided time on this path: about {total // 60} hours** (plus exercises, gates and optional evening labs).\n\n"
                f"!!! tip \"In every lesson\"\n    {do}\n" + "\n".join(out))

    ctx["route"] = route

    from tools import charts as CH
    built = set(CH.build())

    def chart(cid, caption=""):
        """Embed an interactive chart built by tools/charts*.py from the teaching data."""
        if cid not in built:
            raise SystemExit(f"unknown chart id: {cid}")
        cap = caption.replace('"', "&quot;")
        return f'<div class="sb-chart" data-chart="{cid}" data-caption="{cap}"></div>'

    ctx["chart"] = chart

    LAB_OVERRIDE = {
        "L0.1": ["Open the repository in Codespaces (or VS Code) and ask Claude Code: \"Explain this project in five bullet points and list the folders I will use most.\"",
                 "Ask it to run `make quick` and tell you, step by step, what each stage checked.",
                 "Change one thing: ask it to show the last three Git commits in plain English.",
                 "Explain it back: how would you prove to a colleague that your results are reproducible?"],
        "L0.2": ["Ask Claude Code: \"Before you compute anything, state your assumptions: what is one row of `transactions`, and which rows would you exclude from revenue?\"",
                 "Ask it to compute average basket value, then ask: \"How many rows did you drop and why?\"",
                 "Change one thing: give a deliberately vague prompt (\"analyse sales\") and compare the answer with an expert prompt.",
                 "Explain it back: which of the AI error-catalogue mistakes did you catch?"],
        "L0.3": ["Ask Claude Code to generate both datasets and print the validation report.",
                 "Ask: \"Do the row counts and hashes match MANIFEST.json? Show me.\"",
                 "Change one thing: regenerate with a different seed into a scratch folder and compare three headline numbers.",
                 "Explain it back: what does 'validated data' mean for a board report?"],
        "L0.4": ["Run `retail_profile.yaml` through Claude Code and open the narrative, schema report and row accounting.",
                 "Ask it to run the same config on the renamed variant and explain the schema error.",
                 "Change one thing: fix the column mapping in a copy of the config — not the recipe — and rerun with `--check-baseline`.",
                 "Explain it back: why is configuration safer than editing code?"],
        "L0.5": ["Ask Claude Code to list every column in `customers` and `accounts` that could identify a person, directly or in combination.",
                 "Ask it to create a pseudonymised copy (salted hash of IDs) in a scratch folder.",
                 "Change one thing: check k-anonymity on age band × postcode-like fields; generalise until k ≥ 5.",
                 "Explain it back: when may this data leave the secure environment?"],
        "L10.3": ["Pick five questions from the scenario atlas without looking at the answers.",
                  "For each, ask Claude Code: \"Which Navigator node would you use, what assumption would you check first, and what is the fallback?\"",
                  "Change one thing: alter the outcome type (e.g. revenue → converted yes/no) and see how the node changes.",
                  "Explain it back: teach one question to a partner using only the four coaching questions."],
    }
    WHOLE_LAB = {"L10.1", "L10.2", "L10.4"}

    def lab(lid):
        """Optional learn-by-doing vibe-coding lab: an industry task from the lesson's exercises, done by prompting Claude Code."""
        if lid in WHOLE_LAB:
            return '!!! tip "🛠 Learn by doing"\n    This whole lesson is a hands-on lab: every step is done by directing Claude Code on real data.'
        d, n = lid[1:].split(".")
        head = '??? tip "🛠 Learn by doing — optional vibe-coding lab (15–20 min)"\n'
        if lid in LAB_OVERRIDE:
            steps = LAB_OVERRIDE[lid]
            return head + "\n".join(f"    {i}. {s}" for i, s in enumerate(steps, 1))
        src = (SRC / f"day-{int(d):02d}" / f"L{d}-{n}.md").read_text()
        m = re.search(r"\*\*Reuse drill:\*\*\s*(.+)", src)
        twist = m.group(1).strip() if m else "Rerun the main prompt card on the other industry's dataset and compare."
        key = f"D{d}"
        pick = {}
        for dom in ("retail", "finance"):
            items = [e for e in ex.get(key, {}).get(dom, []) if e.get("lesson") == lid]
            items += [e for e in ex.get(f"L{d}-{n}", {}).get(dom, [])]  # lesson-specific exercise file (e.g. L3-4.yaml)
            items.sort(key=lambda e: {"Basic": 0, "Applied": 1, "Stretch": 2}.get(e.get("tier"), 3))
            if items:
                pick[dom] = items[0]
        out = [head, "    Work with Claude Code; you type plain English, it writes and runs the code. Try before you peek at any answer.\n"]
        for dom, lab_ in (("retail", "Retail · NorthStar"), ("finance", "Finance · Meridian")):
            if dom not in pick:
                continue
            e = pick[dom]
            out += [f"    **{lab_} — {e['title']}.** *{e['framing']}*\n",
                    f"    1. **Ask:** \"{e['deliverable']} Before running anything, state your assumptions and how many rows you will use.\"",
                    "    2. **Check:** does the output pass the sense checks (row counts, units, direction of effect)? Compare with "
                    f"the expected finding in exercise **{e['id']}** below.",
                    "    3. **Explain it back:** write two sentences for a manager — the number, its uncertainty and what to do.\n"]
        out += [f"    **Change one thing and watch what happens:** {twist}"]
        return "\n".join(out)

    ctx["lab"] = lab

    # pages (overwrite in place; stale files are removed at the end where permitted)
    written = set()
    for p in SRC.rglob("*"):
        rel = p.relative_to(SRC)
        out = DOCS / rel
        if p.is_dir():
            out.mkdir(parents=True, exist_ok=True)
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        written.add(out)
        if p.suffix == ".md":
            try:
                out.write_text(env.from_string(p.read_text()).render(**ctx))
            except jinja2.exceptions.UndefinedError as e:
                raise SystemExit(f"Undefined placeholder in {rel}: {e}")
        else:
            shutil.copy(p, out)

    DATA_OUT.mkdir(parents=True, exist_ok=True)
    bank = build_questions(sorted((ROOT / "quizzes" / "bank").rglob("*.yaml")), env, ctx)
    (DATA_OUT / "quizzes.json").write_text(json.dumps(bank, ensure_ascii=False))
    (DATA_OUT / "navigator.json").write_text(json.dumps(nav, ensure_ascii=False))
    (DATA_OUT / "lessons.json").write_text(json.dumps(lessons, ensure_ascii=False))
    sc_cfg = yaml.safe_load((ROOT / "quizzes" / "scorecard.yaml").read_text())
    (DATA_OUT / "scorecard.json").write_text(json.dumps(sc_cfg, ensure_ascii=False))

    # anomaly hunt (values from the register)
    hunt = yaml.safe_load((ROOT / "quizzes" / "anomaly_hunt.yaml").read_text())
    items = []
    for it in hunt["items"]:
        r = reg[it["id"]]
        v = float(it.get("value_override", r["measured"]))
        tol = it.get("tol_abs", abs(v) * it.get("tol_rel", 0.05))
        items.append({"id": it["id"], "domain": "Retail" if it["id"][0] == "R" else "Finance", "title": r["title"],
                      "clue_html": md(it["clue"]), "ask": it["ask"], "unlocks_in": r["lessons"], "node": r["hint_node"],
                      "hint": it.get("hint", ""), "lo": v - tol, "hi": v + tol})
    (DATA_OUT / "hunt.json").write_text(json.dumps({"items": items}, ensure_ascii=False))

    # navigator full listing (print / poster)
    lines = ["# Navigator: all decision trees", "", "Printable listing of every tree. The interactive version is on the [Navigator](index.md) page.", ""]
    lines += ["## Start: what is the business question?", ""] + [f"- {o['label']} → **{nav['tree_titles'][o['next']]}**" for o in nav["master"]["opts"]] + [""]
    for tid, title in nav["tree_titles"].items():
        lines += [f"## {title}", ""]
        for nid, n in nav["nodes"].items():
            if n["tree"] != tid:
                continue
            if "q" in n:
                lines.append(f"**{n['q']}** <small>`{nid}`</small>")
                lines += [f"- {o['label']} → `{nav['starts'].get(o['next'], o['next'])}`" for o in n["opts"]]
                lines.append("")
            else:
                lines.append(f"???+ note \"{n['t']} — `{nid}`\"")
                lines.append(f"    **Use when:** {n['use']}  ")
                lines.append(f"    **Check:** {'; '.join(n['check'])}  ")
                lines.append(f"    **If a check fails:** {'; '.join(n['fail'])}  ")
                lines.append(f"    **Alternatives:** {'; '.join(n['alt'])}  ")
                lines.append(f"    **Pitfalls:** {'; '.join(n['pit'])}  ")
                lines.append(f"    **Action:** {n['act']}  ")
                lines.append(f"    **Lessons:** {', '.join(n.get('lessons', []))}")
                lines.append("")
    (DOCS / "navigator" / "trees.md").write_text("\n".join(lines))
    sl = ["# Scenario atlas", "", "44 realistic situations mapped to the Navigator. Click a node to open it in the interactive map.", "",
          "| # | Industry | Situation | Navigator path | Lesson |", "| --- | --- | --- | --- | --- |"]
    for s in scen:
        path = " → ".join(f"[`{p}`](index.md#{p})" for p in s["path"])
        sl.append(f"| {s['id']} | {s['ind']} | {s['text']} | {path} | {s['lesson']} |")
    (DOCS / "navigator" / "scenarios.md").write_text("\n".join(sl) + "\n")

    # glossary
    g = yaml.safe_load((ROOT / "glossary" / "glossary.yaml").read_text())
    gl = ["# Glossary", "", f"{len(g)} terms. Use the search box (top right) to find any term. Ranges are typical values and rules of thumb, not laws.", ""]
    for letter in sorted({e["term"][0].upper() for e in g}):
        gl += [f"## {letter}", ""]
        for e in sorted([e for e in g if e["term"][0].upper() == letter], key=lambda e: e["term"].lower()):
            gl.append(f"**{e['term']}**" + (f" · `{e['symbol']}`" if e.get("symbol") else "") + f" — {e['plain']}  ")
            extra = []
            if e.get("use"):
                extra.append(f"*Typical use:* {e['use']}")
            if e.get("range"):
                extra.append(f"*Typical range:* {e['range']}")
            if e.get("watch"):
                extra.append(f"*Watch out:* {e['watch']}")
            if e.get("lessons"):
                extra.append("*Lessons:* " + ", ".join(e["lessons"]))
            gl.append("  ".join(extra) if extra else "")
            gl.append("")
    (DOCS / "glossary.md").write_text("\n".join(gl))

    # curriculum pages from the blueprint
    cur = DOCS / "curriculum"
    cur.mkdir(exist_ok=True)
    for src, dst in (("04_MODULE_MAP.md", "module-map.md"), ("01_CONCEPT_INVENTORY.md", "concepts.md")):
        (cur / dst).write_text((ROOT / "blueprint" / src).read_text())
    written |= {DATA_OUT / n for n in ("quizzes.json", "navigator.json", "lessons.json", "scorecard.json", "hunt.json")}
    written |= set((DATA_OUT / "charts").glob("*.json"))
    written |= {DOCS / "navigator" / "trees.md", DOCS / "navigator" / "scenarios.md", DOCS / "glossary.md",
                DOCS / "curriculum" / "module-map.md", DOCS / "curriculum" / "concepts.md"}
    for f in DOCS.rglob("*"):
        if f.is_file() and f not in written:
            try:
                f.unlink()
            except OSError:
                print(f"note: could not remove stale file {f.relative_to(ROOT)}")
    print(f"built: {sum(1 for _ in DOCS.rglob('*.md'))} pages, {len(bank)} quizzes "
          f"({sum(len(q['questions']) for q in bank.values())} questions), {len(items)} hunt items, {len(g)} glossary terms")


if __name__ == "__main__":
    main()
