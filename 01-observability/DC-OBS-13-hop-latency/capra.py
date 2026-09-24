"""Capra Playground export for DC-OBS-13 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "design", "fn": "HopLatency", "params": [], "types": {}, "ret": "value", "cmp": "exact"}


def ops(*calls):
    return {"ops": ["HopLatency"] + [c[0] for c in calls], "vals": [[]] + [list(c[1:]) for c in calls]}


EXAMPLES = [
    {"args": ops(("enter", "r1", "gateway", 3), ("enter", "r2", "gateway", 8), ("exit", "r1", "orders", 15), ("exit", "r2", "orders", 20),
                 ("average", "gateway", "orders"), ("enter", "r3", "gateway", 21), ("exit", "r3", "orders", 39), ("average", "gateway", "orders")),
     "explanation": "(12 + 12) / 2 = 12, then (12 + 12 + 18) / 3 = 14.",
     "why": {"t": "Running average", "d": "The average updates as more hops complete."}},
    {"args": ops(("enter", "a", "x", 0), ("exit", "a", "y", 10), ("enter", "b", "y", 0), ("exit", "b", "x", 30),
                 ("average", "x", "y"), ("average", "y", "x")),
     "explanation": "x -> y and y -> x are different routes with their own averages.",
     "why": {"t": "Direction matters", "d": "A route is an ordered pair of services."}},
    {"args": ops(("enter", "done", "api", 0), ("exit", "done", "db", 7), ("enter", "stuck", "api", 1), ("average", "api", "db")),
     "explanation": "The stuck request never exits, so it is not part of the average.",
     "why": {"t": "Open hop ignored", "d": "Only completed hops count."}},
]


def _large():
    rng = random.Random(1396)
    services = ["gateway", "orders", "payments", "inventory"]
    calls, open_ids, t, n = [], [], 0, 0
    for _ in range(900):
        t += rng.randint(0, 3)
        if open_ids and rng.random() < 0.5:
            rid = open_ids.pop(rng.randrange(len(open_ids)))
            calls.append(("exit", rid, rng.choice(services), t + rng.randint(0, 40)))
        else:
            rid = f"req-{n}"
            n += 1
            open_ids.append(rid)
            calls.append(("enter", rid, rng.choice(services), t))
    done = {}
    starts = {}
    for c in calls:
        if c[0] == "enter":
            starts[c[1]] = c[2]
        else:
            done[(starts[c[1]], c[2])] = True
    calls += [("average", a, b) for a, b in sorted(done)]
    return ops(*calls)


TESTS = [
    {"args": ops(("enter", "r1", "a", 5), ("exit", "r1", "b", 5), ("average", "a", "b")),
     "why": {"t": "Zero duration", "d": "Entering and exiting in the same instant gives 0."}},
    {"args": ops(("enter", "r1", "a", 0), ("exit", "r1", "b", 1), ("enter", "r2", "a", 0), ("exit", "r2", "b", 2), ("average", "a", "b")),
     "why": {"t": "Fractional average", "d": "(1 + 2) / 2 = 1.5: the average is not rounded."}},
    {"args": ops(("enter", "r1", "a", 0), ("exit", "r1", "a", 9), ("average", "a", "a")),
     "why": {"t": "Same service", "d": "A hop can start and end at the same service."}},
    {"args": ops(("enter", "r1", "a", 0), ("exit", "r1", "b", 4), ("enter", "r1", "b", 10), ("exit", "r1", "c", 16),
                 ("average", "a", "b"), ("average", "b", "c")),
     "why": {"t": "Request ID reused", "d": "After a request exits, its ID can start a new hop."}},
    {"args": ops(("enter", "r1", "a", 0), ("enter", "r2", "a", 1), ("exit", "r2", "b", 11), ("exit", "r1", "b", 30), ("average", "a", "b")),
     "why": {"t": "Out-of-order exits", "d": "Hops overlap and finish in a different order than they started."}},
    {"args": ops(("enter", "r1", "a", 1_700_000_000), ("exit", "r1", "b", 1_700_000_250), ("average", "a", "b")),
     "why": {"t": "Epoch times", "d": "Large timestamps: only the difference matters."}},
    {"args": ops(("enter", "trace-9f1", "ingress-nginx", 1000), ("exit", "trace-9f1", "checkout-api", 1004),
                 ("enter", "trace-a22", "ingress-nginx", 1001), ("exit", "trace-a22", "checkout-api", 1013),
                 ("enter", "trace-9f1", "checkout-api", 1004), ("exit", "trace-9f1", "payments", 1110),
                 ("average", "ingress-nginx", "checkout-api"), ("average", "checkout-api", "payments")),
     "why": {"t": "Tracing spans", "d": "Two hops of one trace, like consecutive spans."}},
    {"args": _large(),
     "why": {"t": "Large input", "d": "About 900 enters and exits across four services."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Two hash maps (Optimal)",
     "description": "Map request ID to (service, time) while a hop is open. On exit, pop it and add the duration to a [total, count] pair for the (from, to) route. The average is total / count.",
     "time": "O(1) per call", "space": "O(R + P) open requests and routes",
     "keyPoints": ["Pop the open hop on exit so IDs can be reused", "Keep running totals, not every duration", "Key routes by the ordered pair (from, to)"]},
    {"name": "Store every hop", "slow": True,
     "description": "Keep a list of every completed (from, to, duration) and average the matching ones on each query.",
     "time": "O(1) enter/exit, O(h) average", "space": "O(h) completed hops",
     "keyPoints": ["Easy to reason about", "Memory and query time grow with traffic"],
     "code": '''from __future__ import annotations


class HopLatency:
    def __init__(self) -> None:
        self._open: dict[str, tuple[str, int]] = {}
        self._hops: list[tuple[str, str, int]] = []

    def enter(self, request_id: str, service: str, t: int) -> None:
        self._open[request_id] = (service, t)

    def exit(self, request_id: str, service: str, t: int) -> None:
        start_service, start_t = self._open.pop(request_id)
        self._hops.append((start_service, service, t - start_t))

    def average(self, from_service: str, to_service: str) -> float:
        d = [x for a, b, x in self._hops if a == from_service and b == to_service]
        return sum(d) / len(d)
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Store every hop", "idea": "Keep all completed durations and average the matching ones per query.",
     "time": "O(h) per average", "space": "O(h)", "use": "Small traces, or when you also need percentiles."},
    {"name": "Running totals per route", "idea": "Keep [total, count] per (from, to); average in O(1).",
     "time": "O(1) per call", "space": "O(routes + open requests)", "use": "Live dashboards over heavy traffic."},
]
