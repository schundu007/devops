"""Capra Playground export for DC-SEC-07 (see tools/export_capra.py).

Driver kind: compress() changes the list in place and returns only the new
length, so the driver returns both the length and the compacted prefix.
"""
import random

SPEC = {"kind": "driver", "fn": "compress", "params": ["buf"], "types": {}, "ret": "value", "cmp": "exact"}

DRIVER = '''
def __drive(args):
    buf = list(args["buf"])
    n = compress(buf)
    return {"length": n, "buf": buf[:n]}
'''


def case(text):
    return {"buf": list(text)}


EXAMPLES = [
    {"args": case("aabbccc"),
     "explanation": "Runs aa, bb, ccc become a2, b2, c3: 6 characters.",
     "why": {"t": "Several runs", "d": "Every run is longer than 1."}},
    {"args": case("a"),
     "explanation": "A run of 1 is written as the character alone.",
     "why": {"t": "Single character", "d": "No count for a run of length 1."}},
    {"args": case("a" + "b" * 12),
     "explanation": "a stays a, and twelve b's become b, 1, 2: 4 characters.",
     "why": {"t": "Two-digit count", "d": "A count of 10 or more takes several slots."}},
]


def _large():
    rng = random.Random(443)
    out = []
    for _ in range(300):
        out.append(rng.choice("EWID") * rng.randint(1, 12))
    return case("".join(out))


TESTS = [
    {"args": case(""), "why": {"t": "Empty", "d": "An empty buffer stays empty."}},
    {"args": case("abc"), "why": {"t": "All distinct", "d": "No runs longer than 1, so nothing changes."}},
    {"args": case("z" * 100), "why": {"t": "Three-digit count", "d": "A run of 100 becomes z, 1, 0, 0."}},
    {"args": case("1111222"), "why": {"t": "Digit characters", "d": "Runs of digit characters are still just characters."}},
    {"args": case("aaabaaa"), "why": {"t": "Same char, two runs", "d": "The same character in two separate runs."}},
    {"args": case("  ##  "), "why": {"t": "Spaces and symbols", "d": "Any printable character can form a run."}},
    {"args": case("IIIIIIIIWWEEEEEIIII"), "why": {"t": "Log levels", "d": "A stream of one-letter log levels (INFO, WARN, ERROR)."}},
    {"args": _large(), "why": {"t": "Large input", "d": "About 2,000 characters in 300 random runs."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Read and write pointers (Optimal)",
     "description": "A read pointer finds the end of each run; a write pointer writes the character and, for runs longer than 1, the digits of the count. The write pointer never passes the read pointer, so no input is lost.",
     "time": "O(n)", "space": "O(1) extra",
     "keyPoints": ["A run of length r writes at most r slots", "Write the count's digits, not one number", "Return the write pointer"]},
    {"name": "Build a new string", "slow": True,
     "description": "Group the runs with itertools.groupby, build the encoded string, and copy it back into the buffer.",
     "time": "O(n)", "space": "O(n) extra",
     "keyPoints": ["Same result, but it needs a second buffer", "The edge device doesn't have that memory"],
     "code": '''from __future__ import annotations

from itertools import groupby


def compress(buf: list[str]) -> int:
    out = []
    for ch, run in groupby(buf):
        k = len(list(run))
        out.append(ch)
        if k > 1:
            out.extend(str(k))
    buf[:len(out)] = out
    return len(out)
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Build a new string", "idea": "groupby into a new list, then copy back.",
     "time": "O(n)", "space": "O(n)", "use": "When memory doesn't matter."},
    {"name": "Two pointers in place", "idea": "Read runs ahead, write the compacted form behind.",
     "time": "O(n)", "space": "O(1)", "use": "Memory-tight log shippers and buffers."},
]

VARIANT_TITLE = "Run-length compaction"
VARIANT_APPROACH = "Read and write pointers · O(n) · O(1) extra"

_UNIQ_FAST = '''from __future__ import annotations


def uniq(lines: list[str]) -> int:
    write = 0
    for read in range(len(lines)):
        if write == 0 or lines[read] != lines[write - 1]:
            lines[write] = lines[read]
            write += 1
    return write
'''

_UNIQ_SLOW = '''from __future__ import annotations


def uniq(lines: list[str]) -> int:
    out: list[str] = []
    for line in lines:
        if not out or out[-1] != line:
            out.append(line)
    lines[:len(out)] = out
    return len(out)
'''

_CAP_FAST = '''from __future__ import annotations


def cap_runs(lines: list[str], k: int) -> int:
    write = 0
    run = 0
    for read in range(len(lines)):
        line = lines[read]
        if write > 0 and lines[write - 1] == line:
            run += 1
        else:
            run = 1
        if run <= k:
            lines[write] = line
            write += 1
    return write
'''

_CAP_SLOW = '''from __future__ import annotations

from itertools import groupby


def cap_runs(lines: list[str], k: int) -> int:
    out: list[str] = []
    for line, group in groupby(lines):
        out.extend([line] * min(k, len(list(group))))
    lines[:len(out)] = out
    return len(out)
'''

_UNIQ_DRIVER = '''
def __drive(args):
    lines = list(args["lines"])
    n = uniq(lines)
    return {"length": n, "lines": lines[:n]}
'''

_CAP_DRIVER = '''
def __drive(args):
    lines = list(args["lines"])
    n = cap_runs(lines, args["k"])
    return {"length": n, "lines": lines[:n]}
'''


def _log_lines(seed, runs):
    rng = random.Random(seed)
    msgs = ["GET /healthz 200", "conn reset by peer", "auth ok user=ci", "WARN disk 91%", "ERROR db timeout"]
    out = []
    for _ in range(runs):
        out += [rng.choice(msgs)] * rng.randint(1, 8)
    return out


VARIANTS = [
    {
        "key": "uniq-lines",
        "title": "Collapse repeated log lines (uniq)",
        "approach": "Read and write pointers · O(n) · O(1) extra",
        "spec": {"kind": "driver", "fn": "uniq", "params": ["lines"], "driver": _UNIQ_DRIVER},
        "statement": (
            "A crash-looping sidecar writes the same line thousands of times in a row, and the shipper's buffer is fixed size. "
            "Like `uniq`, keep only the **first line of each run** of identical consecutive lines.\n\n"
            "- change `lines` **in place** and return the new length `n`\n"
            "- `lines[:n]` must hold the kept lines in their original order\n"
            "- identical lines that are not next to each other are both kept"
        ),
        "examples": [
            {"args": {"lines": ["probe failed", "probe failed", "probe failed", "restarting", "probe failed"]},
             "explanation": "The first run of three becomes one line; the later probe failed starts a new run.",
             "why": {"t": "Runs, not duplicates", "d": "Only consecutive repeats collapse."}},
        ],
        "constraints": ["0 ≤ lines.length ≤ 2,000", "0 ≤ lines[i].length ≤ 100"],
        "hints": [
            "Compare each line with the last line you **kept**, not with the previous input line.",
            "The write pointer never passes the read pointer, so writing in place is safe.",
        ],
        "tests": [
            {"args": {"lines": []}, "why": {"t": "Empty", "d": "Nothing to keep."}},
            {"args": {"lines": ["only"]}, "why": {"t": "Single line", "d": "One line stays."}},
            {"args": {"lines": ["x"] * 50}, "why": {"t": "One long run", "d": "Fifty copies collapse to one."}},
            {"args": {"lines": ["a", "b", "c"]}, "why": {"t": "All distinct", "d": "Nothing changes."}},
            {"args": {"lines": ["", "", "a", "", ""]}, "why": {"t": "Empty lines", "d": "Blank lines form runs too."}},
            {"args": {"lines": ["a", "A", "a"]}, "why": {"t": "Case matters", "d": "Lines must match exactly to collapse."}},
            {"args": {"lines": _log_lines(701, 150)}, "why": {"t": "Larger input", "d": "About 700 lines in 150 runs."}},
        ],
        "solutions": [
            {"name": "Read and write pointers (Optimal)",
             "description": "Walk the list with a read index; copy a line to the write index only when it differs from the last kept line.",
             "time": "O(n)", "space": "O(1) extra",
             "keyPoints": ["Compare with lines[write - 1]", "Return the write pointer"],
             "code": _UNIQ_FAST},
            {"name": "Build a new list", "slow": True,
             "description": "Append each line that differs from the last appended one to a new list, then copy it back.",
             "time": "O(n)", "space": "O(n) extra",
             "keyPoints": ["Same result", "Needs a second buffer"],
             "code": _UNIQ_SLOW},
        ],
        "starter": "def uniq(lines: list[str]) -> int:\n    pass\n",
    },
    {
        "key": "cap-bursts",
        "title": "Keep at most k copies of a burst",
        "approach": "Read and write pointers with a run counter · O(n) · O(1) extra",
        "spec": {"kind": "driver", "fn": "cap_runs", "params": ["lines", "k"], "driver": _CAP_DRIVER},
        "statement": (
            "Collapsing a burst to one line hides how bad it was; the SOC wants the first `k` copies of every run as samples. "
            "In place, keep at most `k` consecutive copies of each run of identical lines and drop the rest.\n\n"
            "- return the new length `n`; `lines[:n]` holds the result in order\n"
            "- with `k = 1` this is `uniq`"
        ),
        "examples": [
            {"args": {"lines": ["401 /login"] * 5 + ["200 /login"] + ["401 /login"] * 2, "k": 2},
             "explanation": "The run of five keeps two; the later run of two keeps both.",
             "why": {"t": "Per-run cap", "d": "Each run is capped separately."}},
        ],
        "constraints": ["0 ≤ lines.length ≤ 2,000", "1 ≤ k ≤ 100"],
        "hints": [
            "Count the length of the current run as you read.",
            "Write the line only while that count is at most k.",
            "Checking `lines[write - k] == line` works for sorted input only; runs of other lines in between break it.",
        ],
        "tests": [
            {"args": {"lines": [], "k": 3}, "why": {"t": "Empty", "d": "Nothing to keep."}},
            {"args": {"lines": ["a", "a", "a"], "k": 1}, "why": {"t": "k = 1", "d": "Behaves like uniq."}},
            {"args": {"lines": ["a", "a", "a"], "k": 3}, "why": {"t": "k equals run", "d": "A run of exactly k is untouched."}},
            {"args": {"lines": ["a", "b", "a", "a", "a"], "k": 2}, "why": {"t": "Same line, other run", "d": "The earlier a must not count toward the later run."}},
            {"args": {"lines": ["x"] * 3 + ["y"] * 4 + ["x"] * 5, "k": 100}, "why": {"t": "Large k", "d": "Nothing is dropped."}},
            {"args": {"lines": ["", "", "", "z"], "k": 2}, "why": {"t": "Empty lines", "d": "Blank lines are capped too."}},
            {"args": {"lines": _log_lines(702, 200), "k": 3}, "why": {"t": "Larger input", "d": "About 900 lines in 200 runs."}},
        ],
        "solutions": [
            {"name": "Two pointers with a run counter (Optimal)",
             "description": "Track how long the current run is; copy a line to the write index only while the run length is at most k.",
             "time": "O(n)", "space": "O(1) extra",
             "keyPoints": ["Reset the counter when the line changes", "Compare with the last written line", "Write never passes read"],
             "code": _CAP_FAST},
            {"name": "Group and rebuild", "slow": True,
             "description": "Group the runs with itertools.groupby, keep min(k, run) copies of each in a new list, and copy it back.",
             "time": "O(n)", "space": "O(n) extra",
             "keyPoints": ["Clear and short", "Allocates a second buffer"],
             "code": _CAP_SLOW},
        ],
        "starter": "def cap_runs(lines: list[str], k: int) -> int:\n    pass\n",
    },
]
