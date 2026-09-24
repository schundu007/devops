"""Capra Playground export for DC-REL-02 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "compare_versions", "params": ["a", "b"], "types": {}, "ret": "value", "cmp": "exact"}


def case(a, b):
    return {"a": a, "b": b}


EXAMPLES = [
    {"args": case("1.27.10", "1.27.9"),
     "explanation": "Compare part by part as numbers: 10 > 9, so a is newer. A plain string compare gets this wrong ('1' < '9').",
     "why": {"t": "Multi-digit part", "d": "The classic string-compare trap."}},
    {"args": case("1.0", "1.0.0"),
     "explanation": "A missing part counts as 0, so 1.0 and 1.0.0 are the same release.",
     "why": {"t": "Different lengths", "d": "Trailing zero parts do not change the version."}},
    {"args": case("2.01", "2.1"),
     "explanation": "Leading zeros are ignored: 01 and 1 are both 1.",
     "why": {"t": "Leading zeros", "d": "Parts compare as integers, not strings."}},
]


def _large():
    rng = random.Random(165)
    parts = [str(rng.randint(0, 999)) for _ in range(400)]
    b = parts[:]
    b[-1] = str(int(b[-1]) + 1)
    return case(".".join(parts), ".".join(b))


TESTS = [
    {"args": case("1", "1"), "why": {"t": "Single part · equal", "d": "One-part versions that match."}},
    {"args": case("0.1", "1.1"), "why": {"t": "First part decides", "d": "Older major version."}},
    {"args": case("1.2", "1.10"), "why": {"t": "Minor 2 vs 10", "d": "Numeric compare on the second part."}},
    {"args": case("1.0.1", "1"), "why": {"t": "Longer is newer", "d": "Extra non-zero part makes a newer version."}},
    {"args": case("1.0.0.0.0", "1"), "why": {"t": "Many trailing zeros", "d": "All trailing parts are zero."}},
    {"args": case("7.5.2.4", "7.5.3"), "why": {"t": "Decided before the end", "d": "Part 3 differs before the longer list runs out."}},
    {"args": case("1.001", "1.01"), "why": {"t": "Leading zeros both sides", "d": "001 and 01 are both 1."}},
    {"args": case("1.28.0", "1.27.15"), "why": {"t": "Kubernetes upgrade check", "d": "Is the cluster's 1.28.0 newer than the fixed-in version 1.27.15?"}},
    {"args": case("3.10.2", "3.9.18"), "why": {"t": "Python CVE check", "d": "Installed 3.10.2 vs fixed-in 3.9.18."}},
    {"args": _large(), "why": {"t": "Large input", "d": "400-part versions that differ only in the last part."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Split and compare as integers (Optimal)",
     "description": "Split both versions on dots. Walk the longer list; a missing part counts as 0. Compare each pair as integers and return at the first difference.",
     "time": "O(len(a) + len(b))", "space": "O(len(a) + len(b))",
     "keyPoints": ["int() drops leading zeros", "A missing part is 0", "Return at the first differing part"]},
    {"name": "Pad and compare tuples",
     "description": "Turn each version into a list of integers, pad the shorter one with zeros, then let Python compare the two lists.",
     "time": "O(len(a) + len(b))", "space": "O(len(a) + len(b))",
     "keyPoints": ["Python compares lists element by element", "Padding makes 1.0 equal 1.0.0"],
     "code": '''from __future__ import annotations


def compare_versions(a: str, b: str) -> int:
    x = [int(p) for p in a.split(".")]
    y = [int(p) for p in b.split(".")]
    width = max(len(x), len(y))
    x += [0] * (width - len(x))
    y += [0] * (width - len(y))
    return (x > y) - (x < y)
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Split and compare", "idea": "Split on dots and compare part by part as integers, treating a missing part as 0.",
     "time": "O(n)", "space": "O(n)", "use": "The standard answer; easy to explain."},
    {"name": "Pad and compare lists", "idea": "Convert to integer lists, pad with zeros, compare the lists.",
     "time": "O(n)", "space": "O(n)", "use": "Shortest code in languages with list comparison."},
    {"name": "Two pointers, no split", "idea": "Scan both strings, building one number at a time up to the next dot.",
     "time": "O(n)", "space": "O(1)", "use": "When memory matters or versions are huge."},
]
