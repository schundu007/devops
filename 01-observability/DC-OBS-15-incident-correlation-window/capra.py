"""Capra Playground export for DC-OBS-15 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "tightest_window", "params": ["error_times"], "types": {}, "ret": "value", "cmp": "exact"}


def case(times):
    return {"error_times": times}


EXAMPLES = [
    {"args": case([[4, 10, 15, 24, 26], [0, 9, 12, 20], [5, 18, 22, 30]]),
     "explanation": "[20, 24] holds 24 (service 0), 20 (service 1) and 22 (service 2). No narrower window covers all three.",
     "why": {"t": "Three services", "d": "The classic case: one error from every service inside the narrowest window."}},
    {"args": case([[1, 2, 3], [1, 2, 3], [1, 2, 3]]),
     "explanation": "All services failed at second 1, so a zero-width window [1, 1] works. It is the earliest of the ties.",
     "why": {"t": "Same second · Ties", "d": "Several zero-width windows; the earliest one wins."}},
    {"args": case([[5, 9]]),
     "explanation": "With one service, any single error is a window of width 0. The earliest is [5, 5].",
     "why": {"t": "Single service", "d": "Only one list, so the answer is its first error."}},
]


def _large():
    rng = random.Random(632)
    return case([sorted(rng.sample(range(-100_000, 100_000), 40)) for _ in range(12)])


TESTS = [
    {"args": case([[7]]),
     "why": {"t": "Single error", "d": "One service with one error time."}},
    {"args": case([[10], [30]]),
     "why": {"t": "One error each", "d": "Each service failed once, so the window spans both."}},
    {"args": case([[1, 5], [3, 7]]),
     "why": {"t": "Tie on width", "d": "[1, 3] and [3, 5] are both width 2; the one starting earlier wins."}},
    {"args": case([[-50, -10, 0], [-20, 40], [-15, 100]]),
     "why": {"t": "Negative times", "d": "Times before the reference point are allowed."}},
    {"args": case([[1, 100], [1, 100], [100]]),
     "why": {"t": "Late single error", "d": "One service only failed late, which pulls the window to [100, 100]."}},
    {"args": case([[1000, 1004, 1030], [1002, 1003], [900, 1001, 1200], [1003, 1050]]),
     "why": {"t": "Incident correlation", "d": "api, db, cache and queue errors; the 4-second window points at one shared cause."}},
    {"args": case([[i] for i in range(0, 200, 5)]),
     "why": {"t": "Many services", "d": "40 services with one error each; the window must cover them all."}},
    {"args": _large(),
     "why": {"t": "Large input", "d": "12 services with 40 random error times each."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Min-heap + sliding window (Optimal)",
     "description": "Put the first error of every service in a min-heap and track the largest head. The heap top and that largest head form a window holding one error per service. Pop the smallest, advance that service, and stop when a service runs out.",
     "time": "O(n log k)", "space": "O(k)",
     "keyPoints": ["The window is [smallest head, largest head]", "Only the smallest head can move the window forward", "Stop when the popped service has no later error"]},
    {"name": "Try every start", "slow": True,
     "description": "For every error time as a start, take each service's first error at or after it; the window ends at the largest of those.",
     "time": "O(n · k log m)", "space": "O(n)",
     "keyPoints": ["Every optimal window starts at some error time", "A binary search per service finds its first error at or after the start"],
     "code": '''from __future__ import annotations

from bisect import bisect_left


def tightest_window(error_times: list[list[int]]) -> list[int]:
    best = None
    for start in sorted({t for times in error_times for t in times}):
        end = start
        for times in error_times:
            i = bisect_left(times, start)
            if i == len(times):
                end = None
                break
            end = max(end, times[i])
        if end is None:
            continue
        if best is None or end - start < best[1] - best[0]:
            best = [start, end]
    return best
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Try every start", "idea": "For each error time, find each service's first error at or after it with binary search.",
     "time": "O(n · k log m)", "space": "O(n)", "use": "Few services and short lists; easy to explain."},
    {"name": "Min-heap of heads", "idea": "Keep one pointer per service in a min-heap and slide the smallest forward.",
     "time": "O(n log k)", "space": "O(k)", "use": "Many services and long error lists."},
]
