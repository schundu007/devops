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

VARIANT_TITLE = "Range by granularity"
VARIANT_APPROACH = "Sorted list + prefix bounds · O(log n + m log m) per query · O(n)"

_BUCKET_FAST = '''from bisect import bisect_left, bisect_right, insort


class EventCounter:
    def __init__(self) -> None:
        self._ts: list[int] = []

    def record(self, ts: int) -> None:
        insort(self._ts, ts)

    def counts(self, start: int, end: int, size: int) -> list[int]:
        out = []
        lo = start
        while lo <= end:
            hi = min(lo + size - 1, end)
            out.append(bisect_right(self._ts, hi) - bisect_left(self._ts, lo))
            lo += size
        return out
'''

_BUCKET_SLOW = '''class EventCounter:
    def __init__(self) -> None:
        self._ts: list[int] = []

    def record(self, ts: int) -> None:
        self._ts.append(ts)

    def counts(self, start: int, end: int, size: int) -> list[int]:
        if end < start:
            return []
        out = [0] * ((end - start) // size + 1)
        for t in self._ts:
            if start <= t <= end:
                out[(t - start) // size] += 1
        return out
'''

_RET_FAST = '''from bisect import bisect_left, bisect_right, insort

_PREFIX_LEN = {"Year": 4, "Month": 7, "Day": 10, "Hour": 13, "Minute": 16, "Second": 19}


class RetentionLogStore:
    def __init__(self) -> None:
        self._logs: list[tuple[str, int]] = []

    def put(self, log_id: int, timestamp: str) -> None:
        insort(self._logs, (timestamp, log_id))

    def retrieve(self, start: str, end: str, granularity: str) -> list[int]:
        n = _PREFIX_LEN[granularity]
        lo = bisect_left(self._logs, (start[:n],))
        hi = bisect_right(self._logs, (end[:n] + "~",))
        return sorted(i for _, i in self._logs[lo:hi])

    def purge(self, cutoff: str) -> int:
        k = bisect_left(self._logs, (cutoff,))
        del self._logs[:k]
        return k
'''

_RET_SLOW = '''_PREFIX_LEN = {"Year": 4, "Month": 7, "Day": 10, "Hour": 13, "Minute": 16, "Second": 19}


class RetentionLogStore:
    def __init__(self) -> None:
        self._logs: list[tuple[int, str]] = []

    def put(self, log_id: int, timestamp: str) -> None:
        self._logs.append((log_id, timestamp))

    def retrieve(self, start: str, end: str, granularity: str) -> list[int]:
        n = _PREFIX_LEN[granularity]
        return sorted(i for i, ts in self._logs if start[:n] <= ts[:n] <= end[:n])

    def purge(self, cutoff: str) -> int:
        keep = [(i, ts) for i, ts in self._logs if ts >= cutoff]
        gone = len(self._logs) - len(keep)
        self._logs = keep
        return gone
'''


def _bops(times, *queries):
    return {"ops": ["EventCounter"] + ["record"] * len(times) + ["counts"] * len(queries),
            "vals": [[]] + [[t] for t in times] + [list(q) for q in queries]}


def _rops(*steps):
    ops, vals = ["RetentionLogStore"], [[]]
    for s in steps:
        ops.append(s[0])
        vals.append(list(s[1:]))
    return {"ops": ops, "vals": vals}


def _bucket_large():
    rng = random.Random(1348)
    times = [rng.randint(0, 86399) for _ in range(500)]
    qs = []
    for _ in range(30):
        a = rng.randint(0, 80000)
        qs.append((a, a + rng.randint(0, 6000), rng.choice([60, 300, 3600])))
    return _bops(times, *qs)


def _ret_large():
    rng = random.Random(6350)
    steps = [("put", i, _stamp(rng)) for i in range(1, 301)]
    for _ in range(20):
        a, b = sorted([_stamp(rng), _stamp(rng)])
        steps.append(("retrieve", a, b, rng.choice(["Year", "Month", "Day", "Hour"])))
        steps.append(("purge", "2025:%02d:01:00:00:00" % rng.randint(1, 12)))
    return _rops(*steps)


VARIANTS = [
    {
        "key": "bucket-counts",
        "title": "Counts per time bucket",
        "approach": "Sorted timestamps + two bisects per bucket · O(n) record, O(b log n) query · O(n)",
        "spec": {"kind": "design", "fn": "EventCounter", "params": [], "cmp": "exact"},
        "statement": (
            "A dashboard panel plots error counts over a time range. Events arrive as integer timestamps "
            "(seconds). Implement `EventCounter`:\n\n"
            "- `record(ts)` stores one event at second `ts` (duplicates allowed)\n"
            "- `counts(start, end, size)` splits `[start, end]` into buckets `[start, start+size-1]`, "
            "`[start+size, start+2·size-1]`, ... with the last bucket cut at `end`, and returns the number of "
            "events in each bucket, in order\n\n"
            "Events outside `[start, end]` are not counted. A query with `end < start` returns `[]`."
        ),
        "examples": [
            {"args": _bops([0, 60, 10], (0, 59, 60), (0, 60, 60)),
             "explanation": "The first query is one bucket [0, 59] holding 0 and 10. The second adds a bucket [60, 60] holding 60.",
             "why": {"t": "Minute buckets", "d": "The last bucket is cut at end."}},
            {"args": _bops([5, 5, 5, 20], (0, 29, 10)),
             "explanation": "Buckets [0,9], [10,19], [20,29] hold 3, 0 and 1 events.",
             "why": {"t": "Empty bucket in the middle", "d": "A bucket with no events still appears as 0."}},
        ],
        "constraints": ["0 ≤ ts, start, end ≤ 10⁹", "1 ≤ size ≤ 10⁶", "at most 2,000 calls", "at most 10⁴ buckets per query"],
        "hints": [
            "Keep the timestamps sorted as they arrive, as in the main problem.",
            "Each bucket is a closed range [lo, hi]: bisect_right(hi) - bisect_left(lo) counts it.",
            "Generate bucket bounds by stepping lo by size until it passes end.",
        ],
        "tests": [
            {"args": _bops([], (0, 100, 50)), "why": {"t": "No events", "d": "Every bucket is 0."}},
            {"args": _bops([7], (8, 5, 1)), "why": {"t": "Reversed range", "d": "end < start returns []."}},
            {"args": _bops([10, 10, 10], (10, 10, 1)), "why": {"t": "Duplicates, one-second range", "d": "Three events in a single-second bucket."}},
            {"args": _bops([0, 9, 10, 19, 20], (0, 20, 10)), "why": {"t": "Bucket edges", "d": "Events on the first and last second of each bucket."}},
            {"args": _bops([100, 200], (0, 50, 1000)), "why": {"t": "Size larger than range", "d": "One bucket cut short at end; events after end are ignored."}},
            {"args": _bucket_large(), "why": {"t": "Large input", "d": "500 events over a day and 30 queries at 1 min, 5 min and 1 h."}},
        ],
        "solutions": [
            {"name": "Sorted list + bisect per bucket (Optimal)",
             "description": "insort keeps timestamps ordered; each bucket costs two binary searches.",
             "time": "O(n) record, O(b log n) counts", "space": "O(n)",
             "keyPoints": ["Closed ranges: bisect_left on lo, bisect_right on hi", "Query cost depends on buckets, not events", "The last bucket is clipped at end"],
             "code": _BUCKET_FAST},
            {"name": "Scan every event", "slow": True,
             "description": "On each query, walk every stored event and add it to bucket (t - start) // size.",
             "time": "O(1) record, O(n + b) counts", "space": "O(n)",
             "keyPoints": ["No ordering needed", "Every query touches every event"],
             "code": _BUCKET_SLOW},
        ],
        "starter": "class EventCounter:\n    def __init__(self) -> None:\n        pass\n\n    def record(self, ts: int) -> None:\n        pass\n\n    def counts(self, start: int, end: int, size: int) -> list[int]:\n        pass\n",
    },
    {
        "key": "retention-purge",
        "title": "Store with retention purge",
        "approach": "Sorted list, bisect + slice delete · O(log n + k) purge · O(n)",
        "spec": {"kind": "design", "fn": "RetentionLogStore", "params": [], "cmp": "exact"},
        "statement": (
            "The log store from the main problem now has a retention policy. Implement `RetentionLogStore`:\n\n"
            "- `put(id, timestamp)` and `retrieve(start, end, granularity)` behave exactly as in the main problem\n"
            "- `purge(cutoff)` deletes every log whose timestamp is strictly earlier than `cutoff` "
            "(a full `YYYY:MM:DD:hh:mm:ss` string) and returns how many were deleted\n\n"
            "Purged logs never come back in later `retrieve` calls. `retrieve` returns IDs in ascending order."
        ),
        "examples": [
            {"args": _rops(("put", 1, "2026:01:01:00:00:00"), ("put", 2, "2026:02:01:00:00:00"),
                           ("purge", "2026:02:01:00:00:00"), ("retrieve", "2026:01:01:00:00:00", "2026:12:31:00:00:00", "Year")),
             "explanation": "Log 1 is older than the cutoff and is purged; log 2 is exactly at the cutoff and stays.",
             "why": {"t": "Cutoff is exclusive", "d": "A log at the cutoff second is kept."}},
        ],
        "constraints": ["timestamps are zero-padded `YYYY:MM:DD:hh:mm:ss`", "granularity is Year, Month, Day, Hour, Minute or Second", "at most 2,000 calls"],
        "hints": [
            "Keep (timestamp, id) pairs sorted, as in the optimal main solution.",
            "All logs older than the cutoff form a prefix of the sorted list: bisect once and delete that slice.",
        ],
        "tests": [
            {"args": _rops(("purge", "2026:01:01:00:00:00")), "why": {"t": "Purge empty store", "d": "Nothing to delete: 0."}},
            {"args": _rops(("put", 5, "2026:03:03:03:03:03"), ("purge", "2020:01:01:00:00:00"),
                           ("retrieve", "2026:03:03:00:00:00", "2026:03:03:00:00:00", "Day")),
             "why": {"t": "Cutoff before everything", "d": "Purges nothing; the log is still found."}},
            {"args": _rops(("put", 1, "2026:01:01:00:00:00"), ("put", 2, "2026:01:01:00:00:00"), ("put", 3, "2026:01:01:00:00:01"),
                           ("purge", "2026:01:01:00:00:01"), ("retrieve", "2026:01:01:00:00:00", "2026:01:01:23:59:59", "Day")),
             "why": {"t": "Duplicate timestamps", "d": "Both logs at the same second go together."}},
            {"args": _rops(("put", 1, "2025:06:01:00:00:00"), ("purge", "2030:01:01:00:00:00"), ("purge", "2030:01:01:00:00:00"),
                           ("put", 2, "2025:06:01:00:00:00"), ("retrieve", "2025:01:01:00:00:00", "2025:12:31:00:00:00", "Year")),
             "why": {"t": "Purge twice, then put", "d": "A second purge finds nothing; a later put is visible."}},
            {"args": _rops(("put", 9, "2026:09:23:02:14:05"), ("put", 4, "2026:09:23:02:59:59"), ("purge", "2026:09:23:02:30:00"),
                           ("retrieve", "2026:09:23:02:00:00", "2026:09:23:02:00:00", "Hour")),
             "why": {"t": "Purge inside a range", "d": "An hour query sees only the half hour left."}},
            {"args": _ret_large(), "why": {"t": "Large input", "d": "300 logs with interleaved retrievals and purges."}},
        ],
        "solutions": [
            {"name": "Sorted list + prefix delete (Optimal)",
             "description": "Store (timestamp, id) sorted. Retrieval uses prefix bounds; purge bisects the cutoff and deletes the leading slice.",
             "time": "O(n) put, O(log n + m log m) retrieve, O(log n + k) purge", "space": "O(n)",
             "keyPoints": ["Expired logs are always a prefix", "(cutoff,) sorts before any (cutoff, id)", "Slice delete removes k logs at once"],
             "code": _RET_FAST},
            {"name": "Filter on every call", "slow": True,
             "description": "Keep logs unsorted; retrieve and purge both scan the whole list.",
             "time": "O(1) put, O(n) retrieve and purge", "space": "O(n)",
             "keyPoints": ["Straightforward", "Every call touches every log"],
             "code": _RET_SLOW},
        ],
        "starter": "class RetentionLogStore:\n    def __init__(self) -> None:\n        pass\n\n    def put(self, log_id: int, timestamp: str) -> None:\n        pass\n\n    def retrieve(self, start: str, end: str, granularity: str) -> list[int]:\n        pass\n\n    def purge(self, cutoff: str) -> int:\n        pass\n",
    },
]
