"""Capra Playground export for DC-OBS-12 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "design", "fn": "SampleTracker", "params": [], "types": {}, "ret": "value", "cmp": "exact"}


def ops(*calls):
    return {"ops": ["SampleTracker"] + [c[0] for c in calls], "vals": [[]] + [list(c[1:]) for c in calls]}


EXAMPLES = [
    {"args": ops(("update", 1, 10.0), ("update", 2, 5.0), ("current",), ("maximum",), ("update", 1, 3.0), ("maximum",)),
     "explanation": "The newest timestamp is 2, so current is 5. Correcting t=1 to 3 removes the 10, so the max drops to 5.",
     "why": {"t": "Correction lowers the peak", "d": "A stale maximum must not survive a correction."}},
    {"args": ops(("update", 100, 1.0), ("update", 50, 99.0), ("current",), ("maximum",)),
     "explanation": "50 is older than 100, so current does not change, but 99 is still the maximum.",
     "why": {"t": "Late sample", "d": "An old timestamp arrives after a newer one."}},
    {"args": ops(("update", 5, 1.0), ("update", 5, 8.0), ("current",), ("minimum",)),
     "explanation": "The newest timestamp itself was corrected: current and minimum both see 8.",
     "why": {"t": "Correct the newest", "d": "A correction at the newest timestamp."}},
]


def _large():
    rng = random.Random(2034)
    calls = []
    for _ in range(900):
        calls.append(("update", rng.randint(1, 200), float(rng.randint(-500, 500))))
        if rng.random() < 0.3:
            calls.append((rng.choice(["current", "maximum", "minimum"]),))
    return ops(*calls)


TESTS = [
    {"args": ops(("update", 1, 42.0), ("current",), ("maximum",), ("minimum",)),
     "why": {"t": "Single sample", "d": "One sample is the current, max and min."}},
    {"args": ops(("update", 1, 5.0), ("update", 1, 5.0), ("maximum",), ("minimum",)),
     "why": {"t": "Same correction twice", "d": "Re-sending the same value changes nothing."}},
    {"args": ops(("update", 1, 7.0), ("update", 2, 7.0), ("update", 1, 1.0), ("maximum",), ("minimum",)),
     "why": {"t": "Duplicate values", "d": "Two timestamps share a value; correcting one keeps the other."}},
    {"args": ops(("update", 3, -2.5), ("update", 1, -9.0), ("minimum",), ("update", 1, 0.0), ("minimum",)),
     "why": {"t": "Negative values", "d": "The minimum moves after a correction of a negative sample."}},
    {"args": ops(("update", 1, 1.0), ("update", 1, 2.0), ("update", 1, 3.0), ("update", 1, 0.5), ("maximum",), ("minimum",), ("current",)),
     "why": {"t": "Many corrections", "d": "Only the last correction of a timestamp counts."}},
    {"args": ops(("update", 10, 1.0), ("update", 20, 2.0), ("update", 15, 50.0), ("current",), ("maximum",), ("update", 15, 1.5), ("maximum",)),
     "why": {"t": "Late spike corrected", "d": "A late spike raises the max until it is corrected away."}},
    {"args": ops(("update", 1_700_000_000, 0.62), ("update", 1_700_000_015, 0.91), ("update", 1_700_000_030, 0.40),
                 ("update", 1_700_000_015, 0.58), ("current",), ("maximum",), ("minimum",)),
     "why": {"t": "Scrape correction", "d": "A mis-scraped 0.91 CPU reading is corrected to 0.58."}},
    {"args": _large(),
     "why": {"t": "Large input", "d": "900 updates over 200 timestamps with interleaved queries."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Hash map + two heaps, lazy deletion (Optimal)",
     "description": "A dict holds each timestamp's current value. Push every (value, timestamp) into a max-heap and a min-heap; when asked, pop tops whose value no longer matches the dict.",
     "time": "O(log n) update, O(log n) amortised max/min", "space": "O(updates)",
     "keyPoints": ["Never search a heap to delete", "A heap top is stale if the dict disagrees", "current is the value at the largest timestamp"]},
    {"name": "Scan the map", "slow": True,
     "description": "Keep only the dict and scan all current values for the max and min on every query.",
     "time": "O(1) update, O(n) max/min", "space": "O(n)",
     "keyPoints": ["No stale entries to reason about", "Every max/min query is a full scan"],
     "code": '''from __future__ import annotations


class SampleTracker:
    def __init__(self) -> None:
        self._value_at: dict[int, float] = {}
        self._latest = -1

    def update(self, timestamp: int, value: float) -> None:
        self._value_at[timestamp] = value
        self._latest = max(self._latest, timestamp)

    def current(self) -> float:
        return self._value_at[self._latest]

    def maximum(self) -> float:
        return max(self._value_at.values())

    def minimum(self) -> float:
        return min(self._value_at.values())
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Scan the map", "idea": "Recompute max and min from every current value.",
     "time": "O(n) per query", "space": "O(n)", "use": "Few samples or rare queries."},
    {"name": "Heaps + lazy deletion", "idea": "Push every update; discard stale tops only when they surface.",
     "time": "O(log n) amortised", "space": "O(updates)", "use": "Frequent queries on long, corrected series."},
]
