"""Capra Playground export for DC-PLAT-10 (see tools/export_capra.py).

The router must draw its randomness from the injected rng. The driver passes a
scripted rng that hands out preset tickets, so every case is deterministic, and
it checks that each pick draws exactly one ticket over the total weight.
"""
import random

SPEC = {"kind": "driver", "fn": "WeightedRouter", "params": ["weights", "tickets", "report"], "types": {}, "ret": "value", "cmp": "exact"}

DRIVER = '''
class _ScriptedRng:
    def __init__(self, tickets):
        self._tickets = list(tickets)
        self.stops = []

    def randrange(self, stop):
        self.stops.append(stop)
        if not self._tickets:
            raise RuntimeError("pick() drew more random numbers than picks were made")
        return self._tickets.pop(0)


def __drive(args):
    weights, tickets = args["weights"], args["tickets"]
    rng = _ScriptedRng(tickets)
    try:
        router = WeightedRouter(weights, rng)
    except ValueError:
        return "ValueError"
    picks = [router.pick() for _ in range(len(tickets))]
    total = sum(weights)
    if rng.stops != [total] * len(tickets):
        return "each pick must call rng.randrange(%d) exactly once" % total
    if args["report"] == "counts":
        counts = [0] * len(weights)
        for p in picks:
            counts[p] += 1
        return counts
    return picks
'''

EXAMPLES = [
    {"args": {"weights": [90, 10], "tickets": [0, 8, 89, 90, 99], "report": "picks"},
     "explanation": "Backend 0 owns tickets 0-89 and backend 1 owns 90-99, so tickets 89 and 90 fall on either side of the boundary.",
     "why": {"t": "Ticket boundaries", "d": "The last ticket of one backend and the first of the next."}},
    {"args": {"weights": [5, 0, 5], "tickets": list(range(10)), "report": "picks"},
     "explanation": "Backend 1 has weight 0 (drained), so it owns no tickets and is never picked.",
     "why": {"t": "Drained backend", "d": "A zero weight must never receive traffic."}},
]

_rng = random.Random(7)
_W = [_rng.randint(0, 50) for _ in range(300)] + [1]
_T = sum(_W)

TESTS = [
    {"args": {"weights": [7], "tickets": [0, 3, 6], "report": "picks"},
     "why": {"t": "Single backend", "d": "With one backend every ticket goes to it."}},
    {"args": {"weights": [], "tickets": [], "report": "picks"},
     "why": {"t": "Empty list", "d": "No backends at all is rejected with ValueError."}},
    {"args": {"weights": [0, 0], "tickets": [], "report": "picks"},
     "why": {"t": "All drained", "d": "A total weight of 0 is rejected with ValueError."}},
    {"args": {"weights": [3, -1], "tickets": [], "report": "picks"},
     "why": {"t": "Negative weight", "d": "A negative weight is rejected with ValueError."}},
    {"args": {"weights": [0, 0, 4], "tickets": [0, 3], "report": "picks"},
     "why": {"t": "Leading zeros", "d": "Drained backends at the front are skipped."}},
    {"args": {"weights": [95, 5], "tickets": list(range(100)), "report": "counts"},
     "why": {"t": "Canary 5%", "d": "Every ticket drawn once: the traffic split must equal the weights exactly."}},
    {"args": {"weights": [75, 25], "tickets": list(range(100)), "report": "counts"},
     "why": {"t": "Canary 25%", "d": "An Argo-Rollouts-style step: 25% of tickets go to the canary."}},
    {"args": {"weights": _W, "tickets": [_rng.randrange(_T) for _ in range(400)] + [0, _T - 1], "report": "picks"},
     "why": {"t": "Large input", "d": "301 backends (many drained) and 402 tickets, including the first and last."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Prefix sums + binary search (Optimal)",
     "description": "Build running totals of the weights once. Each pick draws one ticket in [0, total) and returns bisect_right(prefix, ticket), the first backend whose range ends after the ticket.",
     "time": "O(n) build, O(log n) per pick", "space": "O(n)",
     "keyPoints": ["Backend i owns tickets [prefix[i-1], prefix[i])", "bisect_right skips zero-weight backends", "Draw exactly one ticket per pick from the injected rng"]},
    {"name": "Walk the backends", "slow": True,
     "description": "Draw one ticket, then subtract weights backend by backend until the ticket falls inside one.",
     "time": "O(n) per pick", "space": "O(n)",
     "keyPoints": ["No precomputation", "Too slow for thousands of weighted endpoints at high request rates"],
     "code": '''from __future__ import annotations

import random


class WeightedRouter:
    def __init__(self, weights: list[int], rng: random.Random | None = None) -> None:
        if not weights or any(w < 0 for w in weights) or sum(weights) == 0:
            raise ValueError("bad weights")
        self._weights = list(weights)
        self._total = sum(weights)
        self._rng = rng if rng is not None else random.Random()

    def pick(self) -> int:
        ticket = self._rng.randrange(self._total)
        for i, w in enumerate(self._weights):
            if ticket < w:
                return i
            ticket -= w
        raise AssertionError("unreachable")
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Walk the backends", "idea": "Subtract weights one by one until the ticket fits.",
     "time": "O(n) per pick", "space": "O(1) extra", "use": "A handful of backends (stable + canary)."},
    {"name": "Prefix sums + binary search", "idea": "Precompute running totals; binary search the ticket.",
     "time": "O(log n) per pick", "space": "O(n)", "use": "Many weighted endpoints and high request rates."},
]
