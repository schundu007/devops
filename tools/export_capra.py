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


class ExportError(Exception):
    pass


# ───────────────────────────── README parsing ─────────────────────────────

def sections(readme: str) -> dict[int, str]:
    """Map section number -> body text, for '## N. Title' headings."""
    parts = re.split(r"^## (\d+)\.[^\n]*\n", readme, flags=re.M)
    return {int(parts[i]): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def title_of(readme: str) -> str:
    m = re.search(r"^# DC-[A-Z]+-\d+\s*·\s*(.+)$", readme, flags=re.M)
    if not m:
        raise ExportError("README has no '# DC-XXX-NN · Title' line")
    return m.group(1).strip()


def header_table(body: str) -> dict[str, str]:
    rows = {}
    for line in body.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] and not set(cells[0]) <= {"-", ":"}:
            rows[cells[0]] = "|".join(cells[1:]).strip()
    return rows


def bullets(body: str) -> list[str]:
    items = [l.strip()[2:].strip() for l in body.splitlines() if l.strip().startswith(("- ", "* "))]
    return items or [l.strip() for l in body.splitlines() if l.strip()]


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

def export_chip(folder: Path, matrix: dict[str, dict[str, str]]) -> dict[str, Any]:
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
        "freeAlt": re.sub(r"^Yes\s*\(P\)\.?\s*", "", premium) if meta["premium"] == "P" else "",
        "lc": int(meta["lc"]),
        "pattern": meta["pattern"],
        "subsystem": meta["subsystem"],
        "handbookId": None,
    }
    for n, name in ((2, "scenario"), (3, "why"), (11, "talkTrack"), (12, "levelUp"), (13, "related")):
        if n not in sec:
            raise ExportError(f"README section {n} missing")
    entry["devops"] = {"scenario": sec[2], "why": sec[3], "talkTrack": sec[11], "levelUp": sec[12], "related": sec[13]}

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
        "statement": sec[4],
        "examples": [{"args": e["args"], "output": expected[i], "explanation": e.get("explanation", ""),
                      **({"why": e["why"]} if "why" in e else {})} for i, e in enumerate(examples)],
        "constraints": bullets(sec[5]),
        "hints": numbered(sec[8]),
        "tests": [{"args": t["args"], "expected": expected[n_ex + i], **({"why": t["why"]} if "why" in t else {})}
                  for i, t in enumerate(tests)],
        "solutions": [{"name": s["name"], "description": s["description"], "code": {"python": code},
                       "complexity": {"time": s["time"], "space": s["space"]}, "keyPoints": s.get("keyPoints", []),
                       **({"slow": True} if s.get("slow") else {})} for s, code in zip(sols, codes)],
        "languages": ["python"],
        "starter": {"python": (folder / "starter.py").read_text()},
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
    if args.only:
        folders = [f for f in folders if any(f.name.startswith(o + "-") for o in args.only)]
    failures = 0
    exported = []
    for folder in folders:
        try:
            entry = export_chip(folder, matrix)
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
        index = [{k: v for k, v in e.items() if k not in ("devops", "problem")} for e in exported]
        (OUT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n")
        print(f"wrote {len(index)} chips + index.json to {OUT}")
    if failures:
        sys.exit(f"{failures} chip(s) failed")


if __name__ == "__main__":
    main()
