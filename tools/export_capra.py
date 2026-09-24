"""Export every chip to Capra's Playground (DevOps tab) as JSON.

For each chip folder this reads:
  README.md    title, statement (section 4), constraints (5), hints (8) and the
               DevOps layer: scenario (2), why (3), talk track (11), level up (12),
               related (13)
  capra.py     NEW chips only: the runner spec and the case inputs (see below)
  starter.py   shown in Capra's editor
  solution.py  the reference solution; its outputs become the expected values
  handbook.json  REUSE chips only: marks the chip as a Capra Handbook problem

Expected values are computed by running the case inputs through the SAME
harness Capra sends to /api/run (built by the copilot repo's
apps/camora/scripts/devops-harness.ts) with solution.py. Every other solution in
capra.py must agree with them. A case that errors, or a size/time budget that is
exceeded, fails the export.

capra.py fields:
  SPEC          {"kind": "fn"|"design"|"driver", "fn", "params", "types", "ret", "cmp"}
  DRIVER        kind "driver" only: Python source defining __drive(args)
  EXAMPLES      [{"args": {...}, "explanation": str, "why": {"t", "d"}}]
  TESTS         [{"args": {...}, "why": {"t", "d"}}]
  SOLUTIONS     [{"name", "description", "time", "space", "keyPoints": [...],
                  "file": "solution.py"} | {..., "code": str, "slow": True}]
                The first entry must be file "solution.py".
  WAYS_TO_SOLVE optional [{"name", "idea", "time", "space", "use"}]
  FOLLOW_UP     optional str

    python3 tools/export_capra.py                     # export all, write JSON
    python3 tools/export_capra.py --only DC-OBS-01    # one chip
    python3 tools/export_capra.py --check             # verify, write nothing
"""
from __future__ import annotations

import argparse
import json
import os
import re
import runpy
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
COPILOT = Path(os.environ.get("CAPRA_REPO", Path.home() / "copilot"))
CAMORA = COPILOT / "apps" / "camora"
OUT = CAMORA / "src" / "data" / "capra" / "devops"
TSX = COPILOT / "node_modules" / ".bin" / "tsx"
MARK = "\x1eCASE"

MAX_CASES_BYTES = 150_000     # case inputs + expected outputs, as JSON
MAX_RUN_SECONDS = 3.0         # local run of every case; production allows 10 s
MAX_CASES = 45
MAX_JSON_DEPTH = 100        # Vite's JSON import fails near 128 levels of nesting

TRACKS = {
    "OBS": "Observability & SRE",
    "SEC": "Cloud Security & IAM",
    "PLAT": "Platform Engineering",
    "REL": "Release & CI/CD",
    "NET": "Networking & Resilience",
    "CAP": "Capacity & Cost",
    "OS": "OS & Automation",
}


# LeetCode's own name for each classic problem, shown next to the DevOps name
# so people can find a problem by the name they already know.
LC_TITLES = {
    981: "Time Based Key-Value Store", 362: "Design Hit Counter", 239: "Sliding Window Maximum",
    652: "Find Duplicate Subtrees", 1244: "Design A Leaderboard",
    1438: "Longest Continuous Subarray With Absolute Diff Less Than or Equal to Limit",
    224: "Basic Calculator", 295: "Find Median from Data Stream", 359: "Logger Rate Limiter",
    635: "Design Log Storage System", 1348: "Tweet Counts Per Frequency", 2034: "Stock Price Fluctuation",
    1396: "Design Underground System", 23: "Merge k Sorted Lists", 632: "Smallest Range Covering Elements from K Lists",
    1004: "Max Consecutive Ones III", 227: "Basic Calculator II", 71: "Simplify Path", 20: "Valid Parentheses",
    394: "Decode String", 820: "Short Encoding of Words", 56: "Merge Intervals", 1094: "Car Pooling",
    443: "String Compression", 44: "Wildcard Matching", 751: "IP to CIDR", 715: "Range Module",
    1233: "Remove Sub-Folders from the Filesystem", 841: "Keys and Rooms", 2092: "Find All People With Secret",
    721: "Accounts Merge", 1169: "Invalid Transactions",
    1604: "Alert Using Same Key-Card Three or More Times in a One Hour Period", 1032: "Stream of Characters",
    1797: "Design Authentication Manager", 722: "Remove Comments", 385: "Mini Parser", 210: "Course Schedule II",
    207: "Course Schedule", 253: "Meeting Rooms II", 621: "Task Scheduler", 433: "Minimum Genetic Mutation",
    146: "LRU Cache", 1606: "Find Servers That Handled Most Number of Requests", 1882: "Process Tasks Using Servers",
    2402: "Meeting Rooms III", 528: "Random Pick with Weight", 1845: "Seat Reservation Manager", 460: "LFU Cache",
    1188: "Design Bounded Blocking Queue", 1226: "The Dining Philosophers", 759: "Employee Free Time",
    278: "First Bad Version", 165: "Compare Version Numbers", 2050: "Parallel Courses III",
    1203: "Sort Items by Groups Respecting Dependencies", 2115: "Find All Possible Recipes from Given Supplies",
    1462: "Course Schedule IV", 802: "Find Eventual Safe States", 1146: "Snapshot Array",
    468: "Validate IP Address", 93: "Restore IP Addresses", 399: "Evaluate Division", 743: "Network Delay Time",
    208: "Implement Trie (Prefix Tree)", 1192: "Critical Connections in a Network",
    1319: "Number of Operations to Make Network Connected", 684: "Redundant Connection",
    1514: "Path with Maximum Probability", 787: "Cheapest Flights Within K Stops",
    1584: "Min Cost to Connect All Points", 994: "Rotting Oranges", 1971: "Find if Path Exists in Graph",
    875: "Koko Eating Bananas", 1011: "Capacity To Ship Packages Within D Days", 410: "Split Array Largest Sum",
    588: "Design In-Memory File System", 14: "Longest Common Prefix",
}


class ExportError(Exception):
    pass


# ───────────────────────────── README parsing ─────────────────────────────

def sections(readme: str) -> dict[int, str]:
    """Map section number -> body text, for '## N. Title' headings."""
    parts = re.split(r"^## (\d+)\.[^\n]*\n", readme, flags=re.M)
    return {int(parts[i]): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def kebab(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


CHIP_ID = re.compile(r"\bDC-[A-Z]+-\d{2}\b[ \t]*")


def name_refs(md: str, names: dict[str, str]) -> str:
    """Replace chip IDs (DC-OBS-12) in prose with the problem's name.

    When the name already follows the ID ("DC-OBS-12 Late & Corrected
    Samples"), the ID is simply dropped.
    """
    def rep(m: re.Match) -> str:
        cid = m.group(0).strip()
        name = names.get(cid, cid)
        after = md[m.end():]
        return "" if after.startswith(name) else name + (" " if m.group(0) != cid else "")
    return CHIP_ID.sub(rep, md)


def strip_ids(code: str) -> str:
    """Code shown in Capra's editor: drop chip IDs from docstrings and comments."""
    return CHIP_ID.sub("", code)


def title_of(readme: str) -> str:
    m = re.search(r"^# DC-[A-Z]+-\d+\s*·\s*(.+)$", readme, flags=re.M)
    if not m:
        raise ExportError("README has no '# DC-XXX-NN · Title' line")
    return m.group(1).replace("★", "").strip()


def header_table(body: str) -> dict[str, str]:
    rows = {}
    for line in body.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] and not set(cells[0]) <= {"-", ":"}:
            rows[cells[0]] = "|".join(cells[1:]).strip()
    return rows


def bullets(body: str) -> list[str]:
    """Top-level '- ' items, with wrapped continuation lines joined back on."""
    items: list[str] = []
    for line in body.splitlines():
        if line.strip().startswith(("- ", "* ")):
            items.append(line.strip()[2:].strip())
        elif items and line.strip() and line.startswith((" ", "\t")):
            items[-1] += " " + line.strip()
    return items or [l.strip() for l in unwrap(body).splitlines() if l.strip()]


BLOCK_START = re.compile(r"^\s*([-*+]|\d+\.)\s|^\s*(\||#|>|```)")


def unwrap(md: str) -> str:
    """Join hard-wrapped lines so Capra's markdown renderer keeps paragraphs whole.

    A line is joined onto the previous one unless either is blank, starts a
    list item, table row, heading, quote or code fence, or sits inside a fence.
    """
    out: list[str] = []
    in_code = False
    for line in md.split("\n"):
        if line.strip().startswith("```"):
            in_code = not in_code
            out.append(line)
            continue
        prev = out[-1] if out else ""
        if (not in_code and line.strip() and prev.strip() and not BLOCK_START.match(line)
                and not prev.strip().startswith(("|", "#", "```"))):
            out[-1] = prev.rstrip() + " " + line.strip()
        else:
            out.append(line)
    return "\n".join(out)


def clean_starter(src: str) -> str:
    """Drop the repo-only 'make try' instructions from a starter's docstring."""
    src = re.sub(r"[ \t]*Run your code against the tests:[ \t]*\n[ \t]*make try[^\n]*\n", "\n", src)
    return re.sub(r"\n{2,}(\"\"\")", r"\n\1", src, count=1)


def numbered(body: str) -> list[str]:
    items: list[str] = []
    for line in body.splitlines():
        m = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if m:
            items.append(m.group(1).strip())
        elif items and line.strip():
            items[-1] += " " + line.strip()
    return items


def master_matrix() -> dict[str, dict[str, str]]:
    readme = (ROOT / "README.md").read_text()
    table = readme.split("## Master matrix", 1)[1]
    rows: dict[str, dict[str, str]] = {}
    for line in table.splitlines():
        if not line.startswith("| DC-"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        rows[c[0]] = {"lc": c[1], "difficulty": c[2], "star": c[3], "premium": c[4],
                      "source": c[5], "pattern": c[6], "track": c[7], "subsystem": c[8]}
    return rows


# ─────────────────────────────── harness ───────────────────────────────

def run_harness(code: str, spec: dict[str, Any], cases: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], float]:
    payload = json.dumps({"code": code, "spec": spec, "cases": cases})
    harness = subprocess.run([str(TSX), "scripts/devops-harness.ts"], cwd=CAMORA, input=payload,
                             capture_output=True, text=True, check=True).stdout
    t0 = time.perf_counter()
    proc = subprocess.run([sys.executable, "-"], input=harness, capture_output=True, text=True, timeout=60)
    elapsed = time.perf_counter() - t0
    records = {}
    for line in proc.stdout.split("\n"):  # not splitlines(): it splits on the \x1e marker
        if line.startswith(MARK):
            rec = json.loads(line[len(MARK):])
            records[rec["i"]] = rec
    if len(records) != len(cases):
        raise ExportError(f"harness returned {len(records)}/{len(cases)} cases (exit {proc.returncode})\n{proc.stderr[-1500:]}")
    return [records[i] for i in range(len(cases))], elapsed


def json_depth(v: Any) -> int:
    if isinstance(v, dict):
        return 1 + max((json_depth(x) for x in v.values()), default=0)
    if isinstance(v, list):
        return 1 + max((json_depth(x) for x in v), default=0)
    return 0


def deep_equal(a: Any, b: Any) -> bool:
    """Mirror of top100Runner.ts deepEqual (numbers compare with 1e-5 relative tolerance)."""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
        return abs(a - b) <= 1e-5 * max(1, abs(b))
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(deep_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(deep_equal(a[k], b[k]) for k in a)
    return a == b


def judge(cmp: str, expected: Any, actual: Any) -> bool:
    key = lambda v: json.dumps(v, sort_keys=True)
    if cmp == "unordered":
        return isinstance(actual, list) and deep_equal(sorted(actual, key=key), sorted(expected, key=key))
    if cmp == "unorderedNested":
        norm = lambda arr: sorted([sorted(x, key=key) if isinstance(x, list) else x for x in arr], key=key)
        return isinstance(actual, list) and deep_equal(norm(actual), norm(expected))
    if cmp in ("exact", "float"):
        return deep_equal(actual, expected)
    raise ExportError(f"cmp {cmp!r} is not supported for DevOps problems; use a driver")


# ─────────────────────────────── export ───────────────────────────────

def export_chip(folder: Path, matrix: dict[str, dict[str, str]], names: dict[str, str]) -> dict[str, Any]:
    chip_id = re.match(r"(DC-[A-Z]+-\d+)", folder.name).group(1)
    readme = (folder / "README.md").read_text()
    sec = sections(readme)
    meta = matrix[chip_id]
    head = header_table(sec.get(1, ""))
    track_code = chip_id.split("-")[1]
    premium = head.get("Premium", "")
    entry: dict[str, Any] = {
        "id": chip_id,
        "slug": folder.name,
        "title": title_of(readme),
        "track": track_code,
        "trackName": TRACKS[track_code],
        "difficulty": meta["difficulty"],
        "star": meta["star"] == "★",
        "premium": meta["premium"] == "P",
        "freeAlt": name_refs(re.sub(r"^Yes\s*\(P\)\.?\s*", "", premium), names).replace("also chip ", "also here as ") if meta["premium"] == "P" else "",
        "lc": int(meta["lc"]),
        "classic": LC_TITLES[int(meta["lc"])],
        "urlSlug": kebab(title_of(readme)),
        "pattern": meta["pattern"],
        "subsystem": meta["subsystem"],
        "handbookId": None,
    }
    for n, name in ((2, "scenario"), (3, "why"), (11, "talkTrack"), (12, "levelUp"), (13, "related")):
        if n not in sec:
            raise ExportError(f"README section {n} missing")
    text = lambda md: name_refs(unwrap(md), names)
    entry["devops"] = {"scenario": text(sec[2]), "why": text(sec[3]), "talkTrack": text(sec[11]),
                       "levelUp": text(sec[12]), "related": text(sec[13])}
    entry["relatedIds"] = [r for r in dict.fromkeys(re.findall(r"\bDC-[A-Z]+-\d{2}\b", sec[13])) if r != chip_id and r in names]

    if (folder / "handbook.json").exists():
        m = re.search(r"Handbook #(\d+)", meta["source"])
        entry["handbookId"] = int(m.group(1))
        entry["problem"] = None
        return entry

    spec_file = folder / "capra.py"
    if not spec_file.exists():
        raise ExportError("capra.py missing")
    cfg = runpy.run_path(str(spec_file))
    spec = dict(cfg["SPEC"])
    if spec["kind"] == "driver":
        spec["driver"] = cfg["DRIVER"]
    spec.setdefault("types", {})
    spec.setdefault("ret", "value")
    spec.setdefault("cmp", "exact")
    examples, tests = cfg["EXAMPLES"], cfg["TESTS"]
    cases = [e["args"] for e in examples] + [t["args"] for t in tests]
    if not (2 <= len(examples) <= 4) or len(tests) < 6 or len(cases) > MAX_CASES:
        raise ExportError(f"need 2-4 examples, >= 6 tests, <= {MAX_CASES} cases (have {len(examples)}/{len(tests)})")

    sols = cfg["SOLUTIONS"]
    if sols[0].get("file") != "solution.py":
        raise ExportError('SOLUTIONS[0] must be {"file": "solution.py", ...}')
    codes = [(folder / s["file"]).read_text() if "file" in s else s["code"] for s in sols]

    records, elapsed = run_harness(codes[0], spec, cases)
    bad = [(i, r["err"]) for i, r in enumerate(records) if not r["ok"]]
    if bad:
        raise ExportError(f"reference solution failed case {bad[0][0]}: {bad[0][1]}")
    expected = [r["out"] for r in records]
    for s, code in zip(sols[1:], codes[1:]):
        other, _ = run_harness(code, spec, cases)
        for i, (r, e) in enumerate(zip(other, expected)):
            if not r["ok"] or not judge(spec["cmp"], e, r["out"]):
                raise ExportError(f"solution {s['name']!r} disagrees on case {i}: {r.get('err') or r['out']!r} != {e!r}")

    depth = json_depth({"cases": cases, "expected": expected})
    if depth > MAX_JSON_DEPTH:
        raise ExportError(f"cases nest {depth} levels deep (max {MAX_JSON_DEPTH}); Vite cannot import that")
    size = len(json.dumps({"cases": cases, "expected": expected}))
    if size > MAX_CASES_BYTES:
        raise ExportError(f"cases are {size} bytes (max {MAX_CASES_BYTES})")
    if elapsed > MAX_RUN_SECONDS:
        raise ExportError(f"cases took {elapsed:.2f}s (max {MAX_RUN_SECONDS}s)")

    n_ex = len(examples)
    problem: dict[str, Any] = {
        "spec": spec,
        "statement": name_refs(unwrap(sec[4]), names),
        "examples": [{"args": e["args"], "output": expected[i], "explanation": e.get("explanation", ""),
                      **({"why": e["why"]} if "why" in e else {})} for i, e in enumerate(examples)],
        "constraints": bullets(sec[5]),
        "hints": numbered(sec[8]),
        "tests": [{"args": t["args"], "expected": expected[n_ex + i], **({"why": t["why"]} if "why" in t else {})}
                  for i, t in enumerate(tests)],
        "solutions": [{"name": s["name"], "description": s["description"], "code": {"python": strip_ids(code)},
                       "complexity": {"time": s["time"], "space": s["space"]}, "keyPoints": s.get("keyPoints", []),
                       **({"slow": True} if s.get("slow") else {})} for s, code in zip(sols, codes)],
        "languages": ["python"],
        "starter": {"python": strip_ids(clean_starter((folder / "starter.py").read_text()))},
    }
    if len(problem["hints"]) < 3:
        raise ExportError("README section 8 needs 3 numbered hints")
    if cfg.get("WAYS_TO_SOLVE"):
        problem["waysToSolve"] = cfg["WAYS_TO_SOLVE"]
    if cfg.get("FOLLOW_UP"):
        problem["followUp"] = cfg["FOLLOW_UP"]
    entry["problem"] = problem
    entry["_stats"] = {"cases": len(cases), "bytes": size, "seconds": round(elapsed, 3)}
    return entry


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None, help="chip IDs to export")
    ap.add_argument("--check", action="store_true", help="verify only, write nothing")
    args = ap.parse_args()

    matrix = master_matrix()
    folders = sorted(p for p in ROOT.glob("0*/DC-*") if p.is_dir())
    names = {re.match(r"(DC-[A-Z]+-\d+)", f.name).group(1): title_of((f / "README.md").read_text()) for f in folders}
    slugs = [kebab(n) for n in names.values()]
    if len(set(slugs)) != len(slugs):
        sys.exit("two problems share a URL slug")
    if args.only:
        folders = [f for f in folders if any(f.name.startswith(o + "-") for o in args.only)]
    failures = 0
    exported = []
    for folder in folders:
        try:
            entry = export_chip(folder, matrix, names)
        except (ExportError, KeyError, subprocess.CalledProcessError) as e:
            failures += 1
            print(f"FAIL {folder.name}: {e}")
            continue
        stats = entry.pop("_stats", None)
        exported.append(entry)
        print(f"ok   {folder.name}" + (f"  ({stats['cases']} cases, {stats['bytes']} B, {stats['seconds']}s)" if stats else "  (handbook)"))
        if not args.check:
            (OUT / "chips").mkdir(parents=True, exist_ok=True)
            (OUT / "chips" / f"{entry['id']}.json").write_text(json.dumps(entry, ensure_ascii=False, indent=1) + "\n")

    if not args.check and not args.only and not failures:
        index = [{k: v for k, v in e.items() if k not in ("devops", "problem", "relatedIds")} for e in exported]
        (OUT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n")
        print(f"wrote {len(index)} chips + index.json to {OUT}")
    if failures:
        sys.exit(f"{failures} chip(s) failed")


if __name__ == "__main__":
    main()
