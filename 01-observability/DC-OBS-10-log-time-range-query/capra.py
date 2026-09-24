"""Capra Playground export for DC-OBS-10 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "design", "fn": "LogStore", "params": [], "types": {}, "ret": "value", "cmp": "exact"}

LOGS = [(1, "2026:09:23:02:14:05"), (2, "2026:09:23:02:59:59"), (3, "2026:09:22:23:00:00"), (4, "2025:12:31:23:59:59")]


def ops(logs, *queries):
    return {"ops": ["LogStore"] + ["put"] * len(logs) + ["retrieve"] * len(queries),
            "vals": [[]] + [list(l) for l in logs] + [list(q) for q in queries]}


EXAMPLES = [
    {"args": ops(LOGS, ("2026:09:23:02:00:00", "2026:09:23:02:00:00", "Hour")),
     "explanation": "At hour detail, start and end both mean 02:xx on the 23rd, so both 02:14 and 02:59 match.",
     "why": {"t": "One hour", "d": "Start and end cut to the same hour."}},
    {"args": ops(LOGS, ("2026:09:22:23:59:59", "2026:09:23:00:00:00", "Day")),
     "explanation": "At day detail this means the 22nd through the 23rd. The 23:00 log on the 22nd is included even though it is earlier than 23:59:59.",
     "why": {"t": "Finer fields ignored", "d": "Fields below the granularity do not matter."}},
    {"args": ops(LOGS, ("2026:09:23:02:14:06", "2026:09:23:02:59:58", "Second")),
     "explanation": "Log 1 is one second before the start and log 2 is one second after the end.",
     "why": {"t": "Exact seconds", "d": "At second detail the bounds are exact and inclusive."}},
]


def _stamp(rng):
    return "{:04d}:{:02d}:{:02d}:{:02d}:{:02d}:{:02d}".format(
        rng.choice([2025, 2026]), rng.randint(1, 12), rng.randint(1, 28), rng.randint(0, 23), rng.randint(0, 59), rng.randint(0, 59))


def _large():
    rng = random.Random(635)
    logs = [(i, _stamp(rng)) for i in range(1, 401)]
    grans = ["Year", "Month", "Day", "Hour", "Minute", "Second"]
    queries = []
    for _ in range(40):
        a, b = sorted([_stamp(rng), _stamp(rng)])
        queries.append((a, b, rng.choice(grans)))
    return ops(logs, *queries)


TESTS = [
    {"args": ops([], ("2026:01:01:00:00:00", "2026:12:31:23:59:59", "Year")),
     "why": {"t": "No logs", "d": "An empty store returns []."}},
    {"args": ops([(7, "2026:05:05:05:05:05")], ("2026:05:05:05:05:05", "2026:05:05:05:05:05", "Second")),
     "why": {"t": "Single log, exact", "d": "start = end = the log's own timestamp."}},
    {"args": ops(LOGS, ("2025:01:01:00:00:00", "2026:01:01:00:00:00", "Year")),
     "why": {"t": "Whole years", "d": "At year detail both years are included in full."}},
    {"args": ops(LOGS, ("2026:09:23:02:14:59", "2026:09:23:02:14:00", "Minute")),
     "why": {"t": "Same minute, reversed seconds", "d": "Cut to minutes, start and end are equal even though start's seconds are larger."}},
    {"args": ops(LOGS, ("2025:12:31:23:59:59", "2026:01:01:00:00:00", "Second")),
     "why": {"t": "Year boundary", "d": "A range across New Year's midnight."}},
    {"args": ops([(10, "2026:09:23:02:14:05"), (11, "2026:09:23:02:14:05"), (9, "2026:09:23:02:14:05")],
                 ("2026:09:23:00:00:00", "2026:09:23:23:59:59", "Day")),
     "why": {"t": "Same timestamp", "d": "Several logs with one timestamp all match, returned in ascending ID order."}},
    {"args": ops(LOGS, ("2026:10:01:00:00:00", "2026:12:31:00:00:00", "Month")),
     "why": {"t": "No match", "d": "A range after every log returns []."}},
    {"args": ops([(101, "2026:09:22:23:58:10"), (102, "2026:09:23:00:01:30"), (103, "2026:09:23:00:07:00"), (104, "2026:09:23:01:00:00")],
                 ("2026:09:22:23:58:00", "2026:09:23:00:05:00", "Minute")),
     "why": {"t": "Incident across midnight", "d": "An incident window from 23:58 to 00:05 at minute detail."}},
    {"args": _large(),
     "why": {"t": "Large input", "d": "400 logs and 40 range queries at random granularities."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Sorted list + prefix bounds (Optimal)",
     "description": "Keep (timestamp, id) pairs sorted. Cut start and end to the granularity's prefix length, then two binary searches find the matching slice: prefix + '~' is an upper bound because '~' sorts above every digit.",
     "time": "O(n) put, O(log n + m log m) retrieve", "space": "O(n)",
     "keyPoints": ["Zero-padded fields: string order is time order", "A granularity is just a prefix length", "Two bisects instead of scanning every log"]},
    {"name": "Check every log", "slow": True,
     "description": "On each query, cut every stored timestamp and both bounds to the granularity and compare.",
     "time": "O(n) per retrieve", "space": "O(n)",
     "keyPoints": ["Simple and correct", "Scans every log on every query"],
     "code": '''from __future__ import annotations

_PREFIX_LEN = {"Year": 4, "Month": 7, "Day": 10, "Hour": 13, "Minute": 16, "Second": 19}


class LogStore:
    def __init__(self) -> None:
        self._logs: list[tuple[int, str]] = []

    def put(self, log_id: int, timestamp: str) -> None:
        self._logs.append((log_id, timestamp))

    def retrieve(self, start: str, end: str, granularity: str) -> list[int]:
        n = _PREFIX_LEN[granularity]
        return sorted(i for i, ts in self._logs if start[:n] <= ts[:n] <= end[:n])
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Scan every log", "idea": "Cut each timestamp to the granularity and compare with the cut bounds.",
     "time": "O(n) per query", "space": "O(n)", "use": "Small stores; the classic answer."},
    {"name": "Sorted index + prefix bounds", "idea": "Binary search the sorted timestamps with prefix-based lower and upper bounds.",
     "time": "O(log n + m log m) per query", "space": "O(n)", "use": "Many queries over a large store."},
]
