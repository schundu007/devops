"""Capra Playground export for DC-SEC-10 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "design", "fn": "AllowList", "params": [], "types": {}, "ret": "value", "cmp": "exact"}


def ops(*calls):
    return {"ops": ["AllowList"] + [c[0] for c in calls], "vals": [[]] + [list(c[1:]) for c in calls]}


EXAMPLES = [
    {"args": ops(("add", 80, 444), ("remove", 100, 200), ("covers", 80, 100), ("covers", 150, 160), ("ranges",)),
     "explanation": "Removing 100-199 from the middle splits [80, 444) into [80, 100) and [200, 444).",
     "why": {"t": "Split in the middle", "d": "A remove inside one range must leave two pieces."}},
    {"args": ops(("add", 10, 20), ("add", 20, 30), ("ranges",), ("covers", 15, 25)),
     "explanation": "Touching ranges merge: [10, 20) and [20, 30) become [10, 30).",
     "why": {"t": "Touching ranges", "d": "Ranges that only touch are reported merged."}},
]


def _large():
    rng = random.Random(10)
    calls = []
    for _ in range(150):
        lo = rng.randint(0, 900)
        hi = lo + rng.randint(1, 60)
        calls.append((rng.choice(["add", "add", "remove"]), lo, hi))
        if rng.random() < 0.4:
            q = rng.randint(0, 950)
            calls.append(("covers", q, q + rng.randint(1, 20)))
    calls.append(("ranges",))
    return ops(*calls)


TESTS = [
    {"args": ops(("covers", 0, 1), ("ranges",)), "why": {"t": "Empty list", "d": "Nothing is allowed yet."}},
    {"args": ops(("add", 443, 444), ("covers", 443, 444), ("covers", 442, 444)),
     "why": {"t": "Single port", "d": "A one-value range, and a query one value wider."}},
    {"args": ops(("add", 100, 200), ("covers", 100, 200), ("covers", 100, 201), ("covers", 199, 200)),
     "why": {"t": "Half-open boundary", "d": "hi is excluded: [100, 200) does not cover 200."}},
    {"args": ops(("add", 0, 10), ("add", 20, 30), ("add", 5, 25), ("ranges",)),
     "why": {"t": "Bridge", "d": "One add overlaps two ranges and joins them."}},
    {"args": ops(("add", 0, 100), ("remove", 0, 100), ("ranges",), ("covers", 0, 1)),
     "why": {"t": "Remove everything", "d": "Removing the exact range leaves nothing."}},
    {"args": ops(("add", 10, 20), ("remove", 30, 40), ("remove", 0, 5), ("ranges",)),
     "why": {"t": "Remove outside", "d": "Removing ranges that do not overlap changes nothing."}},
    {"args": ops(("add", 0, 10), ("add", 20, 30), ("add", 40, 50), ("remove", 5, 45), ("ranges",)),
     "why": {"t": "Remove across several", "d": "Keep the left part of the first and the right part of the last."}},
    {"args": ops(("add", 0, 10), ("add", 20, 30), ("covers", 5, 25)),
     "why": {"t": "Gap inside the query", "d": "A query spanning a gap is not covered."}},
    {"args": ops(("add", 3000, 4000), ("add", 3500, 3600), ("ranges",)),
     "why": {"t": "Duplicate add", "d": "Adding a range already allowed changes nothing."}},
    {"args": _large(), "why": {"t": "Large input", "d": "About 200 random adds, removes and queries."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Sorted disjoint ranges (Optimal)",
     "description": "Keep ranges sorted, never overlapping and never touching. add replaces the block of ranges that overlap or touch with one spanning range. remove keeps only the left part of the first overlapping range and the right part of the last. covers checks the one range that starts at or before lo.",
     "time": "O(log n) covers; O(log n + k) add/remove", "space": "O(n)",
     "keyPoints": ["Half-open ranges make splits exact", "Merging touching ranges keeps covers a single lookup", "A remove can add at most one range"]},
    {"name": "Set of allowed values", "slow": True,
     "description": "Store every allowed value in a set. add and remove update each value; covers checks each value; ranges rebuilds runs from the sorted set.",
     "time": "O(hi - lo) per call", "space": "O(allowed values)",
     "keyPoints": ["Fine for 65,536 ports", "Hopeless for IPv4's 4 billion addresses"],
     "code": '''from __future__ import annotations


class AllowList:
    def __init__(self) -> None:
        self._on: set[int] = set()

    def add(self, lo: int, hi: int) -> None:
        self._on.update(range(lo, hi))

    def remove(self, lo: int, hi: int) -> None:
        self._on.difference_update(range(lo, hi))

    def covers(self, lo: int, hi: int) -> bool:
        return all(v in self._on for v in range(lo, hi))

    def ranges(self) -> list[tuple[int, int]]:
        out: list[tuple[int, int]] = []
        for v in sorted(self._on):
            if out and out[-1][1] == v:
                out[-1] = (out[-1][0], v + 1)
            else:
                out.append((v, v + 1))
        return out
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Set of values", "idea": "Track every allowed value individually.",
     "time": "O(range size) per call", "space": "O(values)", "use": "Tiny spaces such as ports."},
    {"name": "Sorted disjoint ranges", "idea": "Binary search a sorted list of merged, half-open ranges.",
     "time": "O(log n) query", "space": "O(ranges)", "use": "IP allow-lists and any large space."},
]
