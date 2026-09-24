"""Capra Playground export for DC-PLAT-07 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "busiest_backends", "params": ["k", "arrival", "load"], "types": {}, "ret": "value", "cmp": "exact"}

EXAMPLES = [
    {"args": {"k": 3, "arrival": [1, 2, 3, 4, 5], "load": [5, 2, 3, 3, 3]},
     "explanation": "Request 3 prefers backend 0 (busy) and skips to 1. Request 4 prefers 1 (busy), then 2 (busy), then 0 (busy): dropped. Backend 1 served 2.",
     "why": {"t": "Skip busy", "d": "Busy backends are skipped in order, wrapping around."}},
    {"args": {"k": 3, "arrival": [1, 2, 3], "load": [10, 12, 11]},
     "explanation": "Each backend served one request, so all three tie.",
     "why": {"t": "Tie", "d": "Every backend with the top count is returned."}},
]


def _large():
    rng = random.Random(1606)
    n, t = 3000, 0
    arrival, load = [], []
    for _ in range(n):
        t += rng.randint(1, 4)
        arrival.append(t)
        load.append(rng.randint(1, 60))
    return {"k": 17, "arrival": arrival, "load": load}


TESTS = [
    {"args": {"k": 1, "arrival": [1], "load": [1]}, "why": {"t": "Single backend", "d": "One backend, one request."}},
    {"args": {"k": 1, "arrival": [1, 2, 3], "load": [5, 1, 1]}, "why": {"t": "All dropped", "d": "While the only backend is busy, requests are dropped."}},
    {"args": {"k": 2, "arrival": [1, 3], "load": [2, 2]}, "why": {"t": "Free at arrival", "d": "A backend that finishes exactly at the arrival time is free."}},
    {"args": {"k": 4, "arrival": [1, 2, 3, 4, 5, 6, 7], "load": [100, 100, 100, 1, 1, 1, 1]},
     "why": {"t": "Hot backend", "d": "Three backends stay busy; the fourth takes every later request."}},
    {"args": {"k": 3, "arrival": [1, 2, 3, 4], "load": [1, 1, 1, 1]}, "why": {"t": "Plain round-robin", "d": "Nobody is ever busy: request i goes to i % k."}},
    {"args": {"k": 5, "arrival": [1, 2], "load": [1, 1]}, "why": {"t": "More backends than requests", "d": "Idle backends still count, with 0 served."}},
    {"args": _large(), "why": {"t": "Large input", "d": "3,000 requests over 17 backends."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Sorted idle list + busy heap (Optimal)",
     "description": "Keep a sorted list of idle backends and a min-heap of (free time, backend). Release finished backends, then binary-search the idle list for the first ID >= i % k, wrapping to the front.",
     "time": "O(n log n) plus O(k) list shifts", "space": "O(k)",
     "keyPoints": ["Finished at t counts as free at t", "bisect finds the next idle backend with wrap-around", "Drop the request when nobody is idle"]},
    {"name": "Check backends one by one", "slow": True,
     "description": "For each request, try backends i % k, i % k + 1, … until one is idle.",
     "time": "O(n · k)", "space": "O(k)",
     "keyPoints": ["Direct simulation", "10^10 steps at the limits"],
     "code": '''from __future__ import annotations


def busiest_backends(k: int, arrival: list[int], load: list[int]) -> list[int]:
    free_at = [0] * k
    served = [0] * k
    for i, (t, d) in enumerate(zip(arrival, load)):
        for step in range(k):
            b = (i + step) % k
            if free_at[b] <= t:
                free_at[b] = t + d
                served[b] += 1
                break
    top = max(served)
    return [b for b in range(k) if served[b] == top]
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Linear probe", "idea": "Try i % k, i % k + 1, … for each request.", "time": "O(n · k)", "space": "O(k)",
     "use": "Few backends."},
    {"name": "Sorted idle set + heap", "idea": "Binary-search the idle set; a heap releases finished backends.",
     "time": "O(n log k) with a balanced tree", "space": "O(k)", "use": "Large pools."},
]
