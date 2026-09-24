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
