"""Fill the "From handbook" sections of a REUSE chip README from handbook.json.

The README template holds markers like <!-- HB:statement -->. This script swaps each
marker for the handbook's own text, so copied content is never retyped by hand.

    python3 tools/fill_handbook.py <chip-folder>/README.tmpl.md > <chip-folder>/README.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _args(args: dict) -> str:
    return ", ".join(f"{k} = {json.dumps(v)}" for k, v in args.items())


def statement(hb: dict) -> str:
    return hb["statement"]


def constraints(hb: dict) -> str:
    return "\n".join(f"- {c}" for c in hb["constraints"])


def examples(hb: dict) -> str:
    out = []
    for i, ex in enumerate(hb["examples"], 1):
        title = ex.get("why", {}).get("t", "")
        out.append(f"**Example {i}{' — ' + title if title else ''}**")
        out.append("```")
        out.append(f"Input:  {_args(ex['args'])}")
        out.append(f"Output: {json.dumps(ex['output'])}")
        out.append("```")
        if ex.get("explanation"):
            out.append(ex["explanation"])
        out.append("")
    return "\n".join(out).rstrip()


def hints(hb: dict) -> str:
    return "\n".join(f"{i}. {h}" for i, h in enumerate(hb["hints"], 1))


def follow_up(hb: dict) -> str:
    return hb.get("followUp") or "_(none in handbook)_"


def solutions(hb: dict) -> str:
    out = []
    for s in hb["solutions"]:
        out.append(f"#### {s['name']}")
        out.append(s["description"])
        out.append("")
        for kp in s.get("keyPoints", []):
            out.append(f"- {kp}")
        cx = s.get("complexity", {})
        out.append("")
        out.append(f"Time: {cx.get('time', '?')} · Space: {cx.get('space', '?')}")
        out.append("")
        out.append("```python")
        out.append(s["code"]["python"])
        out.append("```")
        out.append("")
    return "\n".join(out).rstrip()


def ways_to_solve(hb: dict) -> str:
    rows = hb.get("waysToSolve")
    if not rows:
        return "_(none in handbook)_"
    out = ["| Way | Idea | Time | Space | Use when |", "|---|---|---|---|---|"]
    for w in rows:
        out.append(f"| {w['name']} | {w['idea']} | {w['time']} | {w['space']} | {w['use']} |")
    return "\n".join(out)


def tests_summary(hb: dict) -> str:
    return f"{len(hb['tests'])} cases in `handbook.json` → `tests`, run unchanged by `test_chip.py`."


FILLERS = {
    "statement": statement,
    "constraints": constraints,
    "examples": examples,
    "hints": hints,
    "followUp": follow_up,
    "solutions": solutions,
    "waysToSolve": ways_to_solve,
    "tests": tests_summary,
}


def main(template_path: str) -> None:
    tmpl = Path(template_path)
    hb = json.loads((tmpl.parent / "handbook.json").read_text())
    text = tmpl.read_text()
    for key, fill in FILLERS.items():
        text = text.replace(f"<!-- HB:{key} -->", fill(hb))
    if "<!-- HB:" in text:
        sys.exit(f"unknown marker left in {template_path}")
    sys.stdout.write(text)


if __name__ == "__main__":
    main(sys.argv[1])
