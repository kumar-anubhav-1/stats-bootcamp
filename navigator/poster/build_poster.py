"""Generate the one-page Navigator poster (HTML; print to PDF at A2/A3 landscape) from trees.yaml.

python -m navigator.poster.build_poster   -> navigator/poster/poster.html
(PDF: open in a browser and print, or `python -m navigator.poster.build_poster --pdf` with Playwright installed.)
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
TREES = HERE.parent / "trees.yaml"


def leaf_lines(tree):
    nodes = tree["nodes"]
    out = []

    def walk(nid, depth, label, seen):
        n = nodes.get(nid)
        if n is None or nid in seen:
            out.append((depth, label, f"see {nid}", None))
            return
        seen = seen | {nid}
        if "q" in n:
            if label:
                out.append((depth, label, None, None))
            out.append((depth + (1 if label else 0), None, n["q"], "q"))
            for o in n["opts"]:
                walk(o["next"], depth + (2 if label else 1), o["label"], seen)
        else:
            out.append((depth, label, n["t"], n.get("fail", [""])[0] if n.get("fail") else ""))

    walk(tree["start"], 0, None, set())
    return out


def build() -> Path:
    t = yaml.safe_load(TREES.read_text())
    cards = []
    for tid, tr in t["trees"].items():
        rows = []
        for depth, label, text, extra in leaf_lines(tr):
            pad = depth * 9
            if extra == "q":
                rows.append(f'<div class="q" style="margin-left:{pad}px">{html.escape(text)}</div>')
            elif text and label:
                fb = f'<span class="fb">fallback: {html.escape(extra)}</span>' if extra and extra.strip('—– ') else ""
                rows.append(f'<div class="o" style="margin-left:{pad}px"><span class="lab">{html.escape(label)}</span> → '
                            f'<b>{html.escape(text)}</b> {fb}</div>')
            elif label:
                rows.append(f'<div class="o" style="margin-left:{pad}px"><span class="lab">{html.escape(label)}</span></div>')
        cards.append(f'<section><h2>{html.escape(tr["title"])}</h2>{"".join(rows)}</section>')
    master = "".join(f"<li>{html.escape(o['label'])} → <b>{html.escape(t['trees'][o['next']]['title'])}</b></li>" for o in t["master"]["opts"])
    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Statistics Navigator poster</title>
<style>
@page {{ size: A2 landscape; margin: 8mm; }}
body {{ font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 0; color: #1d2433; }}
header {{ display:flex; align-items:baseline; gap:16px; border-bottom:3px solid #3b6ea5; padding:4px 0 6px; margin-bottom:6px; }}
header h1 {{ font-size: 22px; margin:0; }} header p {{ margin:0; font-size:11px; color:#555; }}
.master {{ columns: 3; font-size: 10.5px; margin: 0 0 6px; padding-left: 16px; }}
main {{ columns: 4; column-gap: 10px; }}
section {{ break-inside: avoid; border:1px solid #d6dbe4; border-top:4px solid #b5651d; border-radius:4px; padding:4px 6px; margin:0 0 8px; }}
h2 {{ font-size: 14px; margin: 2px 0 4px; color:#3b6ea5; }}
.q {{ font-size: 11px; font-weight: 700; margin-top: 3px; }}
.o {{ font-size: 10.5px; line-height: 1.25; }}
.lab {{ color:#555; }} .fb {{ color:#8a4b12; font-size: 9.5px; }}
footer {{ font-size: 9px; color:#666; margin-top:4px; }}
</style></head><body>
<header><h1>Statistics Navigator</h1><p>Start from the business question → answer the data questions → technique · <span style="color:#8a4b12">fallback if an assumption fails</span>. Thresholds are rules of thumb.</p></header>
<ul class="master">{master}</ul>
<main>{''.join(cards)}</main>
<footer>Generated from navigator/trees.yaml · Statistics for Data Science Bootcamp · interactive version: Navigator page of the course site.</footer>
</body></html>"""
    out = HERE / "poster.html"
    out.write_text(page)
    return out


if __name__ == "__main__":
    p = build()
    print("wrote", p)
    if "--pdf" in sys.argv:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_page()
            pg.goto(p.as_uri())
            pg.pdf(path=str(HERE / "poster.pdf"), format="A2", landscape=True, print_background=True)
            b.close()
        print("wrote", HERE / "poster.pdf")
