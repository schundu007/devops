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

VARIANT_TITLE = "Hop average latency"
VARIANT_APPROACH = "Open-hop map + running totals per route · O(1) per call · O(R + P)"


def ops_for(cls, ctor, *calls):
    return {"ops": [cls] + [c[0] for c in calls], "vals": [list(ctor)] + [list(c[1:]) for c in calls]}


def _slowest_large():
    rng = random.Random(13961)
    services = ["gateway", "orders", "payments", "inventory", "search"]
    calls, open_ids, t, n = [], [], 0, 0
    for _ in range(700):
        t += rng.randint(0, 3)
        r = rng.random()
        if open_ids and r < 0.45:
            rid = open_ids.pop(rng.randrange(len(open_ids)))
            calls.append(("exit", rid, rng.choice(services), t + rng.randint(0, 40)))
        elif r < 0.55:
            calls.append(("slowest",))
        else:
            rid = f"req-{n}"
            n += 1
            open_ids.append(rid)
            calls.append(("enter", rid, rng.choice(services), t))
    return ops_for("RouteStats", [], *calls)


def _stuck_large():
    rng = random.Random(13962)
    calls, open_ids, t, n = [], [], 0, 0
    for _ in range(900):
        t += rng.randint(0, 2)
        r = rng.random()
        if open_ids and r < 0.35:
            rid = open_ids.pop(rng.randrange(len(open_ids)))
            calls.append(("exit", rid, "db", t))
        elif r < 0.5:
            calls.append(("stuck", t))
        else:
            rid = f"r{n}"
            n += 1
            open_ids.append(rid)
            calls.append(("enter", rid, "api", t))
    return ops_for("HopWatch", [30], *calls)


_SLOWEST_TOTALS = '''from __future__ import annotations


class RouteStats:
    def __init__(self) -> None:
        self._open: dict[str, tuple[str, int]] = {}
        self._stats: dict[tuple[str, str], list[int]] = {}

    def enter(self, request_id: str, service: str, t: int) -> None:
        self._open[request_id] = (service, t)

    def exit(self, request_id: str, service: str, t: int) -> None:
        start_service, start_t = self._open.pop(request_id)
        stat = self._stats.setdefault((start_service, service), [0, 0])
        stat[0] += t - start_t
        stat[1] += 1

    def slowest(self) -> list[str] | None:
        best, best_total, best_count = None, 0, 1
        for route, (total, count) in self._stats.items():
            # compare total / count without floats: a/b > c/d  <=>  a*d > c*b
            if best is None or total * best_count > best_total * count or (
                    total * best_count == best_total * count and route < best):
                best, best_total, best_count = route, total, count
        return list(best) if best else None
'''

_SLOWEST_ALL = '''from __future__ import annotations


class RouteStats:
    def __init__(self) -> None:
        self._open: dict[str, tuple[str, int]] = {}
        self._hops: list[tuple[str, str, int]] = []

    def enter(self, request_id: str, service: str, t: int) -> None:
        self._open[request_id] = (service, t)

    def exit(self, request_id: str, service: str, t: int) -> None:
        start_service, start_t = self._open.pop(request_id)
        self._hops.append((start_service, service, t - start_t))

    def slowest(self) -> list[str] | None:
        routes = sorted({(a, b) for a, b, _ in self._hops})
        best, best_avg = None, None
        for route in routes:
            d = [x for a, b, x in self._hops if (a, b) == route]
            total, count = sum(d), len(d)
            if best is None or total * best_avg[1] > best_avg[0] * count:
                best, best_avg = route, (total, count)
        return list(best) if best else None
'''

_STUCK_QUEUE = '''from __future__ import annotations

from collections import deque


class HopWatch:
    def __init__(self, limit: int) -> None:
        self._limit = limit
        self._next = 0
        self._open: dict[str, int] = {}       # request id -> token of its open hop
        self._queue: deque = deque()          # (entry time, token), oldest first
        self._closed: set[int] = set()        # exited before becoming overdue
        self._overdue: set[int] = set()       # overdue and still open

    def enter(self, request_id: str, service: str, t: int) -> None:
        token = self._next
        self._next += 1
        self._open[request_id] = token
        self._queue.append((t, token))

    def exit(self, request_id: str, service: str, t: int) -> None:
        token = self._open.pop(request_id)
        if token in self._overdue:
            self._overdue.discard(token)
        else:
            self._closed.add(token)

    def stuck(self, now: int) -> int:
        while self._queue and now - self._queue[0][0] >= self._limit:
            _, token = self._queue.popleft()
            if token in self._closed:
                self._closed.discard(token)
            else:
                self._overdue.add(token)
        return len(self._overdue)
'''

_STUCK_SCAN = '''from __future__ import annotations


class HopWatch:
    def __init__(self, limit: int) -> None:
        self._limit = limit
        self._open: dict[str, int] = {}

    def enter(self, request_id: str, service: str, t: int) -> None:
        self._open[request_id] = t

    def exit(self, request_id: str, service: str, t: int) -> None:
        del self._open[request_id]

    def stuck(self, now: int) -> int:
        return sum(1 for t in self._open.values() if now - t >= self._limit)
'''

VARIANTS = [
    {
        "key": "slowest-route",
        "title": "Slowest route",
        "approach": "Running totals per route, scanned on query · O(1) per hop, O(P) per query · O(R + P)",
        "spec": {"kind": "design", "fn": "RouteStats", "params": [], "cmp": "exact"},
        "statement": "The on-call dashboard wants one number, not a lookup: **which route is slowest right now?** Build `RouteStats`:\n\n- `enter(request_id, service, t)` and `exit(request_id, service, t)` work exactly as in the main problem\n- `slowest()` returns `[from, to]` for the route with the highest average hop duration over its completed hops, or `null` if no hop has completed\n- on a tie in average, return the route that is smallest as a `(from, to)` pair of strings\n\nCompare averages exactly: `a / b > c / d` is `a · d > c · b`, which never suffers from float rounding.",
        "examples": [
            {"args": ops_for("RouteStats", [], ("slowest",), ("enter", "r1", "gateway", 0), ("exit", "r1", "orders", 12),
                             ("enter", "r2", "orders", 12), ("exit", "r2", "payments", 40), ("slowest",),
                             ("enter", "r3", "orders", 50), ("exit", "r3", "payments", 52), ("slowest",)),
             "explanation": "Nothing is complete at first. orders to payments averages 28, then (28 + 2) / 2 = 15, which is still above gateway to orders at 12.",
             "why": {"t": "Running averages", "d": "The answer tracks the averages as hops complete."}},
            {"args": ops_for("RouteStats", [], ("enter", "a", "x", 0), ("exit", "a", "y", 6), ("enter", "b", "b", 0), ("exit", "b", "c", 6), ("slowest",)),
             "explanation": "Both routes average 6. ('b', 'c') is smaller than ('x', 'y'), so it wins the tie.",
             "why": {"t": "Tie", "d": "Equal averages break by the (from, to) pair."}},
        ],
        "constraints": ["At most 5 · 10³ calls", "0 ≤ t ≤ 10⁹; every exit matches an open request", "At most 50 distinct routes"],
        "hints": [
            "Keep [total, count] per route exactly as in the main problem.",
            "On slowest(), scan the routes and compare averages by cross-multiplying instead of dividing.",
            "For a live leaderboard with many routes, a heap with lazy invalidation avoids the scan.",
        ],
        "tests": [
            {"args": ops_for("RouteStats", [], ("slowest",)), "why": {"t": "Nothing complete", "d": "No completed hop: null."}},
            {"args": ops_for("RouteStats", [], ("enter", "r", "a", 5), ("slowest",), ("exit", "r", "b", 5), ("slowest",)), "why": {"t": "Open hop · Zero duration", "d": "An open hop does not count; a 0-second hop does."}},
            {"args": ops_for("RouteStats", [], ("enter", "1", "a", 0), ("exit", "1", "b", 1), ("enter", "2", "a", 0), ("exit", "2", "b", 2),
                             ("enter", "3", "c", 0), ("exit", "3", "d", 3), ("enter", "4", "c", 0), ("exit", "4", "d", 0), ("slowest",)),
             "why": {"t": "Fractional tie", "d": "1.5 against 1.5: exact comparison finds the tie and picks (a, b)."}},
            {"args": ops_for("RouteStats", [], ("enter", "r", "a", 0), ("exit", "r", "a", 9), ("enter", "r", "a", 10), ("exit", "r", "b", 11), ("slowest",)),
             "why": {"t": "ID reused · Same service", "d": "A request ID starts a second hop; a route can loop to its own service."}},
            {"args": ops_for("RouteStats", [], ("enter", "1", "x", 0), ("exit", "1", "y", 100), ("enter", "2", "x", 0), ("exit", "2", "y", 0),
                             ("slowest",), ("enter", "3", "p", 0), ("exit", "3", "q", 51), ("slowest",)),
             "why": {"t": "Leader changes", "d": "A new route with a higher average takes over."}},
            {"args": _slowest_large(), "why": {"t": "Large input", "d": "About 700 calls over five services, with queries mixed in."}},
        ],
        "solutions": [
            {"name": "Running totals + scan routes (Optimal)",
             "description": "Update [total, count] per route on exit in O(1). slowest() scans the routes once, comparing averages by cross-multiplication and breaking ties by the route pair.",
             "time": "O(1) per hop, O(P) per query", "space": "O(R + P)",
             "keyPoints": ["Routes are far fewer than hops", "Cross-multiply instead of dividing", "Tie-break on the (from, to) pair"],
             "code": _SLOWEST_TOTALS},
            {"name": "Store every hop", "slow": True,
             "description": "Keep every completed hop. On each query, group hops by route, sum them, and pick the highest average.",
             "time": "O(h · P) per query", "space": "O(h)",
             "keyPoints": ["Recomputes from raw data each time", "Query time grows with traffic"],
             "code": _SLOWEST_ALL},
        ],
        "starter": '''from __future__ import annotations


class RouteStats:
    def __init__(self) -> None:
        pass

    def enter(self, request_id: str, service: str, t: int) -> None:
        pass

    def exit(self, request_id: str, service: str, t: int) -> None:
        pass

    def slowest(self) -> list[str] | None:
        """[from, to] of the route with the highest average, or None."""
        raise NotImplementedError
''',
    },
    {
        "key": "stuck-requests",
        "title": "Stuck request alarm",
        "approach": "Entry-ordered queue with lazy removal · O(1) amortized per call · O(R)",
        "spec": {"kind": "design", "fn": "HopWatch", "params": [], "cmp": "exact"},
        "statement": "Averages hide hangs: a request that never exits never shows up in them. Build `HopWatch(limit)` to page when hops are stuck:\n\n- `enter(request_id, service, t)` and `exit(request_id, service, t)` open and close a hop as before\n- `stuck(now)` returns how many hops are **still open** and have been open for at least `limit` seconds (`now - t >= limit`)\n\nAll calls arrive in time order: the `t` and `now` values never decrease. A request ID is never entered twice while its hop is open, and it may be reused after it exits.",
        "examples": [
            {"args": ops_for("HopWatch", [10], ("enter", "a", "api", 0), ("enter", "b", "api", 3), ("stuck", 9), ("stuck", 10),
                             ("exit", "a", "db", 11), ("stuck", 13), ("enter", "c", "api", 14), ("stuck", 30)),
             "explanation": "At 9 nothing has been open 10 seconds. At 10, a has. a exits at 11; at 13, b (open since 3) is stuck. At 30, b and c both are.",
             "why": {"t": "Threshold and exit", "d": "A hop becomes stuck at exactly limit seconds and stops counting when it exits."}},
        ],
        "constraints": ["1 ≤ limit ≤ 10⁶", "At most 10⁴ calls", "t and now never decrease across calls"],
        "hints": [
            "Hops enter in time order, so the oldest open hop is always at the front of a queue.",
            "When stuck(now) runs, move every hop with now - t >= limit from the queue into an 'overdue' set, unless it already exited.",
            "Give every hop a unique token, so an exit can find it in the overdue set even if its request ID is reused later.",
        ],
        "tests": [
            {"args": ops_for("HopWatch", [5], ("stuck", 100)), "why": {"t": "Nothing open", "d": "No hops: 0."}},
            {"args": ops_for("HopWatch", [1], ("enter", "a", "s", 7), ("stuck", 7), ("stuck", 8)), "why": {"t": "Limit of one", "d": "Not stuck at the same second, stuck one second later."}},
            {"args": ops_for("HopWatch", [5], ("enter", "a", "s", 0), ("exit", "a", "t", 2), ("stuck", 50)), "why": {"t": "Exited early", "d": "A hop that exits before the limit never counts."}},
            {"args": ops_for("HopWatch", [5], ("enter", "a", "s", 0), ("stuck", 6), ("exit", "a", "t", 7), ("enter", "a", "s", 8), ("stuck", 9), ("stuck", 13)),
             "why": {"t": "ID reused", "d": "The first hop of 'a' leaves the count on exit; its second hop counts on its own."}},
            {"args": ops_for("HopWatch", [3], ("enter", "a", "s", 1), ("enter", "b", "s", 1), ("enter", "c", "s", 1), ("exit", "b", "t", 2), ("stuck", 4), ("stuck", 4)),
             "why": {"t": "Same second", "d": "Several hops enter together; repeated queries at one time agree."}},
            {"args": ops_for("HopWatch", [10], ("enter", "a", "s", 0), ("stuck", 20), ("exit", "a", "t", 21), ("stuck", 21), ("stuck", 40)),
             "why": {"t": "Stuck then recovers", "d": "A late exit removes the hop from the stuck count."}},
            {"args": _stuck_large(), "why": {"t": "Large input", "d": "About 900 calls with a 30-second limit."}},
        ],
        "solutions": [
            {"name": "Queue with lazy removal (Optimal)",
             "description": "Queue hops by entry time with a unique token. stuck(now) pops every hop that has reached the limit into an overdue set, skipping tokens already exited. An exit removes its token from the overdue set, or marks it closed for the queue to skip.",
             "time": "O(1) amortized per call", "space": "O(R)",
             "keyPoints": ["Time order makes the queue front the oldest hop", "Tokens, not request IDs, because IDs are reused", "Each hop is popped once"],
             "code": _STUCK_QUEUE},
            {"name": "Scan open hops", "slow": True,
             "description": "Keep a map of open hops and, on every query, count those that have been open at least limit seconds.",
             "time": "O(R) per query", "space": "O(R)",
             "keyPoints": ["Trivially correct", "Every alarm check walks every open request"],
             "code": _STUCK_SCAN},
        ],
        "starter": '''from __future__ import annotations


class HopWatch:
    def __init__(self, limit: int) -> None:
        pass

    def enter(self, request_id: str, service: str, t: int) -> None:
        pass

    def exit(self, request_id: str, service: str, t: int) -> None:
        pass

    def stuck(self, now: int) -> int:
        """Open hops with now - entry time >= limit."""
        raise NotImplementedError
''',
    },
]
