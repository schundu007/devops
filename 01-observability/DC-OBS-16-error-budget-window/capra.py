"""Capra Playground export for DC-OBS-16 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "longest_window", "params": ["checks", "budget"], "types": {}, "ret": "value", "cmp": "exact"}


def case(checks, budget):
    return {"checks": checks, "budget": budget}


EXAMPLES = [
    {"args": case([1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0], 2),
     "explanation": "The last 6 checks [0, 1, 1, 1, 1, 0] hold exactly 2 failures, and no longer run does.",
     "why": {"t": "Budget of 2", "d": "The best window uses the whole failure budget."}},
    {"args": case([0, 0, 0], 0),
     "explanation": "Every check failed and the budget is 0, so no window is allowed: the answer is 0.",
     "why": {"t": "All failed · Zero budget", "d": "No window fits, so the answer is 0."}},
    {"args": case([1, 0, 1, 1, 0, 1], 1),
     "explanation": "[1, 1, 0, 1] at the end, or [1, 0, 1, 1] at the start: 4 checks with one failure.",
     "why": {"t": "Two equal windows", "d": "Several windows share the best length."}},
]


def _large():
    rng = random.Random(1004)
    return case([0 if rng.random() < 0.15 else 1 for _ in range(3000)], 25)


TESTS = [
    {"args": case([], 0), "why": {"t": "Empty", "d": "No checks at all."}},
    {"args": case([1], 0), "why": {"t": "Single pass", "d": "One passing check."}},
    {"args": case([0], 1), "why": {"t": "Single failure", "d": "One failed check that the budget covers."}},
    {"args": case([1, 1, 1, 1], 0), "why": {"t": "All passed", "d": "No failures, so the whole list is the window."}},
    {"args": case([0, 1, 0, 1, 0], 5), "why": {"t": "Budget ≥ failures", "d": "The budget covers every failure."}},
    {"args": case([0, 1, 0, 1, 0, 1, 0], 1), "why": {"t": "Alternating", "d": "Pass and fail alternate; the window slides often."}},
    {"args": case([1] * 50 + [0] * 3 + [1] * 20 + [0] + [1] * 40, 2),
     "why": {"t": "Outage burst", "d": "A 3-check outage then one blip; the budget can't cover the burst."}},
    {"args": _large(), "why": {"t": "Large input", "d": "3,000 checks with about 15% failures."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Sliding window (Optimal)",
     "description": "Two pointers bound the window and a counter tracks its failures. Move the right edge every step; while failures exceed the budget, move the left edge.",
     "time": "O(n)", "space": "O(1)",
     "keyPoints": ["Each check enters and leaves the window at most once", "Shrink from the left only while over budget", "Record the length after every step"]},
    {"name": "Try every start", "slow": True,
     "description": "For every start, extend the window until the failures would exceed the budget, and keep the longest.",
     "time": "O(n²)", "space": "O(1)",
     "keyPoints": ["Simple, but re-scans overlapping windows", "Too slow for 30 days of 10-second probes"],
     "code": '''from __future__ import annotations


def longest_window(checks: list[int], budget: int) -> int:
    best = 0
    for start in range(len(checks)):
        failures = 0
        for end in range(start, len(checks)):
            failures += checks[end] == 0
            if failures > budget:
                break
            best = max(best, end - start + 1)
    return best
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Try every start", "idea": "Extend from each start until the budget breaks.",
     "time": "O(n²)", "space": "O(1)", "use": "Short lists; easiest to reason about."},
    {"name": "Sliding window", "idea": "Grow the right edge; shrink the left while failures > budget.",
     "time": "O(n)", "space": "O(1)", "use": "Long probe histories, e.g. 30 days of checks."},
]
