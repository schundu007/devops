"""Capra Playground export for DC-OBS-11 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "design", "fn": "EventCounter", "params": [], "types": {}, "ret": "value", "cmp": "exact"}


def ops(*calls):
    return {"ops": ["EventCounter"] + [c[0] for c in calls], "vals": [[]] + [list(c[1:]) for c in calls]}


def rec(name, *times):
    return [("record", name, t) for t in times]


EXAMPLES = [
    {"args": ops(*rec("deploy", 0, 60, 10), ("counts", "minute", "deploy", 0, 59), ("counts", "minute", "deploy", 0, 60)),
     "explanation": "[0, 59] holds 0 and 10. Extending to 60 opens a second bucket that holds only second 60.",
     "why": {"t": "Edge second", "d": "The first second of the next bucket starts a new bucket."}},
    {"args": ops(*rec("5xx", 100, 159, 160, 219, 220), ("counts", "minute", "5xx", 100, 220), ("counts", "minute", "5xx", 101, 218)),
     "explanation": "Buckets start at start, not at the clock: [100,159] [160,219] [220,220], then [101,160] [161,218].",
     "why": {"t": "Buckets move with start", "d": "Bucket edges are aligned to the query start."}},
    {"args": ops(("counts", "minute", "oom_kill", 0, 179)),
     "explanation": "An unknown name still gets one zero per bucket.",
     "why": {"t": "Unknown name", "d": "No events: every bucket is 0."}},
]


def _large():
    rng = random.Random(1348)
    calls = [("record", rng.choice(["req", "err"]), rng.randint(0, 86400 * 2)) for _ in range(1500)]
    calls += [("counts", "hour", "req", 0, 86400 * 2 - 1), ("counts", "day", "err", 0, 86400 * 2),
              ("counts", "minute", "req", 3600, 3600 * 3 - 1)]
    return ops(*calls)


TESTS = [
    {"args": ops(("counts", "day", "x", 0, 0)),
     "why": {"t": "Single-second range", "d": "start = end gives exactly one bucket."}},
    {"args": ops(*rec("x", 5), ("counts", "minute", "x", 5, 5)),
     "why": {"t": "Event on start = end", "d": "An event exactly on a one-second range is counted."}},
    {"args": ops(*rec("x", 30, 20, 10, 40), ("counts", "minute", "x", 0, 119)),
     "why": {"t": "Out-of-order records", "d": "Events may arrive in any time order."}},
    {"args": ops(*rec("x", 7, 7, 7), ("counts", "minute", "x", 0, 59)),
     "why": {"t": "Duplicates", "d": "Several events in the same second all count."}},
    {"args": ops(*rec("x", 3599, 3600, 7199, 7200), ("counts", "hour", "x", 0, 7200)),
     "why": {"t": "Hour edges", "d": "Hour buckets: [0,3599] [3600,7199] [7200,7200]."}},
    {"args": ops(*rec("x", 1, 500), ("counts", "minute", "x", 100, 200)),
     "why": {"t": "Events outside range", "d": "Events before start or after end are ignored."}},
    {"args": ops(*rec("a", 10), *rec("b", 10, 20), ("counts", "minute", "a", 0, 59), ("counts", "minute", "b", 0, 59)),
     "why": {"t": "Names are independent", "d": "Each event name has its own counts."}},
    {"args": ops(*rec("http_5xx", 0, 12, 61, 65, 70, 3500, 3601, 3605), ("counts", "hour", "http_5xx", 0, 7199),
                 ("counts", "minute", "http_5xx", 0, 179)),
     "why": {"t": "Zoom out", "d": "The same errors at 1-minute and 1-hour steps, as when a dashboard zooms out."}},
    {"args": _large(),
     "why": {"t": "Large input", "d": "1,500 events over two days, at three step sizes."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Sorted times + binary search (Optimal)",
     "description": "Keep each name's event times sorted with insort. A query binary searches [start, end] and drops each event in bucket (t - start) // size.",
     "time": "O(n) record worst case, O(log n + k + b) counts", "space": "O(total events)",
     "keyPoints": ["Align buckets to start, not to the clock", "Two bisects touch only events in range", "One zero per empty bucket"]},
    {"name": "Check every event", "slow": True,
     "description": "Keep an unsorted list per name and test every event on every query.",
     "time": "O(1) record, O(n + b) counts", "space": "O(total events)",
     "keyPoints": ["Simplest", "Every query scans the whole history"],
     "code": '''from __future__ import annotations

BUCKET_SECONDS = {"minute": 60, "hour": 3600, "day": 86400}


class EventCounter:
    def __init__(self) -> None:
        self._times: dict[str, list[int]] = {}

    def record(self, name: str, time: int) -> None:
        self._times.setdefault(name, []).append(time)

    def counts(self, step: str, name: str, start: int, end: int) -> list[int]:
        size = BUCKET_SECONDS[step]
        buckets = [0] * ((end - start) // size + 1)
        for t in self._times.get(name, []):
            if start <= t <= end:
                buckets[(t - start) // size] += 1
        return buckets
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Scan all events", "idea": "Check every event of the name against [start, end].",
     "time": "O(n) per query", "space": "O(n)", "use": "Short histories."},
    {"name": "Sorted times + bisect", "idea": "Binary search the range, then bucket only those events.",
     "time": "O(log n + k) per query", "space": "O(n)", "use": "Long histories, narrow queries."},
]
