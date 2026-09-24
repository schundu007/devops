"""Capra Playground export for DC-CAP-02 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "min_nightly_capacity", "params": ["files", "nights"], "types": {}, "ret": "value", "cmp": "exact"}

EXAMPLES = [
    {"args": {"files": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "nights": 5},
     "explanation": "[1..5]=15, [6,7]=13, [8], [9], [10]. With 14 you would need 6 nights.",
     "why": {"t": "Ten files", "d": "The classic split."}},
    {"args": {"files": [3, 2, 2, 4, 1, 4], "nights": 3},
     "explanation": "[3,2] [2,4] [1,4]. Order is fixed, so the 1 cannot move earlier.",
     "why": {"t": "Order matters", "d": "Files must be copied in order."}},
    {"args": {"files": [500], "nights": 3},
     "explanation": "Capacity can never be smaller than the largest file.",
     "why": {"t": "Single file", "d": "The lower bound is max(files)."}},
]

_rng = random.Random(1011)
_BIG = [_rng.randint(1, 500) for _ in range(3000)]

TESTS = [
    {"args": {"files": [5, 5, 5, 5], "nights": 4}, "why": {"t": "One file per night", "d": "nights == len(files): the answer is max(files)."}},
    {"args": {"files": [5, 5, 5, 5], "nights": 1}, "why": {"t": "One night", "d": "Everything in one night: the answer is sum(files)."}},
    {"args": {"files": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], "nights": 3}, "why": {"t": "All equal", "d": "Ten 1 GB files over three nights: 4."}},
    {"args": {"files": [500, 1, 1, 1, 500], "nights": 2}, "why": {"t": "Big at both ends", "d": "The big files force a split point."}},
    {"args": {"files": [1, 2, 3, 1, 1], "nights": 4}, "why": {"t": "Boundary", "d": "The answer equals max(files) exactly."}},
    {"args": {"files": [120, 80, 300, 40, 40, 220, 90, 60], "nights": 3},
     "why": {"t": "Nightly DB dumps", "d": "Ordered dump sizes in GB, three-night migration window."}},
    {"args": {"files": _BIG, "nights": 7}, "why": {"t": "Large input", "d": "3,000 random files over 7 nights."}},
    {"args": {"files": _BIG, "nights": 3000}, "why": {"t": "Large, one per night", "d": "Every file gets its own night."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Binary search on capacity (Optimal)",
     "description": "The answer lies between max(files) and sum(files). For a candidate capacity, count nights greedily in order; binary search for the smallest capacity that fits the deadline.",
     "time": "O(n · log(sum − max))", "space": "O(1) extra",
     "keyPoints": ["Feasibility is monotonic: more capacity never needs more nights", "Greedy packing is optimal when order is fixed", "Search between max and sum"]},
    {"name": "Try every capacity", "slow": True,
     "description": "Start at max(files) and try each larger capacity until the greedy count fits the deadline.",
     "time": "O(n · (sum − max))", "space": "O(1)",
     "keyPoints": ["Same greedy check", "Linear instead of binary search over the range"],
     "code": '''from __future__ import annotations


def min_nightly_capacity(files: list[int], nights: int) -> int:
    def nights_needed(cap: int) -> int:
        used, count = 0, 1
        for size in files:
            if used + size > cap:
                count += 1
                used = 0
            used += size
        return count

    cap = max(files)
    while nights_needed(cap) > nights:
        cap += 1
    return cap
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Linear search", "idea": "Try capacities upward from max(files).", "time": "O(n · (sum − max))",
     "space": "O(1)", "use": "Small totals only."},
    {"name": "Binary search on the answer", "idea": "Greedy feasibility check plus binary search.", "time": "O(n · log(sum − max))",
     "space": "O(1)", "use": "The standard answer."},
]
