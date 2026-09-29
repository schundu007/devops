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

VARIANT_TITLE = "Buckets from the query start"
VARIANT_APPROACH = "Sorted times + binary search · O(log n + k + b) per query · O(n)"

_rng_v = random.Random(635)
_ALIGNED_LARGE = {"times": [_rng_v.randint(0, 20000) for _ in range(1200)], "size": 300, "start": 1234, "end": 18765}
_BURST_LARGE = {"times": [_rng_v.randint(0, 50000) for _ in range(1500)] + [40000 + i for i in range(0, 60, 3)],
                "window": 60, "threshold": 12}

VARIANTS = [
    {
        "key": "clock-aligned",
        "title": "Clock-aligned buckets",
        "approach": "Sort + binary search, bucket by t // size · O(n log n + b) · O(n + b)",
        "spec": {"kind": "fn", "fn": "aligned_counts", "params": ["times", "size", "start", "end"], "cmp": "exact"},
        "statement": (
            "Dashboards such as Grafana align buckets to the clock, not to the query start.\n"
            "\n"
            "### Input\n"
            "- `times`: event seconds, in any order, duplicates allowed\n"
            "- `size`: the bucket size in seconds\n"
            "- `start`, `end`: the query range, **inclusive**\n"
            "\n"
            "### Output\n"
            "- `[bucketStart, count]` for **every** aligned bucket that overlaps the query, in order\n"
            "\n"
            "### Rules\n"
            "- With `size = 60` the buckets are `[0, 59]`, `[60, 119]`, … no matter where the query begins\n"
            "- Count only events inside `[start, end]`, so the first and last buckets may be partial\n"
            "- Empty buckets are listed with count 0"
        ),
        "examples": [
            {"args": {"times": [5, 59, 60, 61, 130], "size": 60, "start": 30, "end": 125},
             "explanation": "Buckets [0,59], [60,119], [120,179] overlap [30,125]. 5 is before start, 130 is after end.",
             "why": {"t": "Partial edges", "d": "The first and last buckets are clipped to the query."}},
            {"args": {"times": [], "size": 3600, "start": 0, "end": 7200},
             "explanation": "Three hour buckets, all empty.",
             "why": {"t": "No events", "d": "Empty buckets still appear."}},
        ],
        "constraints": ["0 ≤ len(times) ≤ 10^5", "0 ≤ times[i], start, end ≤ 10^9, start ≤ end",
                        "1 ≤ size ≤ 86400", "At most 10^4 buckets overlap the query"],
        "hints": [
            "The first bucket starts at `start // size * size`, the last at `end // size * size`.",
            "Sort the times once and use two binary searches to keep only events in `[start, end]`.",
            "Each kept event goes to index `t // size - start // size`.",
        ],
        "tests": [
            {"args": {"times": [7], "size": 10, "start": 7, "end": 7}, "why": {"t": "One-second query", "d": "A single second still maps to one aligned bucket."}},
            {"args": {"times": [59, 60], "size": 60, "start": 59, "end": 60}, "why": {"t": "Straddles an edge", "d": "Two seconds, two buckets."}},
            {"args": {"times": [120, 120, 120, 0], "size": 60, "start": 60, "end": 179}, "why": {"t": "Duplicates", "d": "Three events in one second; the one at 0 is outside."}},
            {"args": {"times": [300, 100, 200], "size": 100, "start": 0, "end": 299}, "why": {"t": "Unsorted input", "d": "Times arrive out of order; 300 is just past end."}},
            {"args": {"times": [86399, 86400], "size": 86400, "start": 0, "end": 86400}, "why": {"t": "Day buckets", "d": "The day edge at 86400 opens a new bucket."}},
            {"args": {"times": [1, 2, 3], "size": 1, "start": 0, "end": 4}, "why": {"t": "Size 1", "d": "Every second is its own bucket."}},
            {"args": _ALIGNED_LARGE, "why": {"t": "Large input", "d": "1,200 events and 60 five-minute buckets."}},
        ],
        "solutions": [
            {"name": "Sort + bisect (Optimal)",
             "description": "Sort the times, bisect the query range, and drop each event into bucket t // size relative to the first aligned bucket.",
             "time": "O(n log n + b)", "space": "O(n + b)",
             "keyPoints": ["Align with integer division, not with start", "Two bisects skip events outside the query", "Clip the edge buckets by filtering events, not buckets"],
             "code": '''from bisect import bisect_left, bisect_right


def aligned_counts(times, size, start, end):
    first = start // size
    counts = [0] * (end // size - first + 1)
    ts = sorted(times)
    for t in ts[bisect_left(ts, start):bisect_right(ts, end)]:
        counts[t // size - first] += 1
    return [[(first + i) * size, c] for i, c in enumerate(counts)]
'''},
            {"name": "Scan events per bucket", "slow": True,
             "description": "For every aligned bucket, scan all events and count the ones inside both the bucket and the query.",
             "time": "O(n · b)", "space": "O(b)",
             "keyPoints": ["Obvious correctness", "Rescans all events for every bucket"],
             "code": '''def aligned_counts(times, size, start, end):
    out = []
    b = start // size * size
    while b <= end:
        lo, hi = max(b, start), min(b + size - 1, end)
        out.append([b, sum(1 for t in times if lo <= t <= hi)])
        b += size
    return out
'''},
        ],
        "starter": '''def aligned_counts(times: list[int], size: int, start: int, end: int) -> list[list[int]]:
    pass
''',
    },
    {
        "key": "burst-alert",
        "title": "First burst alert",
        "approach": "Sort + two pointers · O(n log n) · O(n)",
        "spec": {"kind": "fn", "fn": "first_alert", "params": ["times", "window", "threshold"], "cmp": "exact"},
        "statement": (
            "Find the second a burst alert first fires.\n"
            "\n"
            "### Input\n"
            "- `times`: the error name's event seconds, in any order, duplicates allowed\n"
            "- `window`: the rolling window length in seconds\n"
            "- `threshold`: the event count that fires the alert\n"
            "\n"
            "### Output\n"
            "- The **earliest** second `t` at which the alert fires, or `-1` if it never does\n"
            "\n"
            "### Rules\n"
            "- The alert fires when at least `threshold` events fall in `[t - window + 1, t]` for some second `t`\n"
            "- Unlike fixed buckets, the window slides: a burst split across two buckets must still fire"
        ),
        "examples": [
            {"args": {"times": [50, 70, 65, 100, 110], "window": 60, "threshold": 3},
             "explanation": "At 70 the window [11, 70] holds 50, 65 and 70: three events. Fixed minute buckets would split them.",
             "why": {"t": "Burst across a bucket edge", "d": "The rolling window catches what fixed buckets miss."}},
            {"args": {"times": [0, 100, 200], "window": 60, "threshold": 2},
             "explanation": "No two events are within 60 seconds of each other.",
             "why": {"t": "Never fires", "d": "Spread-out events return -1."}},
        ],
        "constraints": ["0 ≤ len(times) ≤ 10^5", "0 ≤ times[i] ≤ 10^9", "1 ≤ window ≤ 10^6", "1 ≤ threshold ≤ 10^5"],
        "hints": [
            "The count in the window only goes up at an event, so the answer, if any, is an event time.",
            "Sort the times. Move a left pointer forward while it is older than `t - window + 1`.",
            "The window holds `right - left + 1` events; stop at the first time it reaches the threshold.",
        ],
        "tests": [
            {"args": {"times": [], "window": 10, "threshold": 1}, "why": {"t": "No events", "d": "Nothing can fire: -1."}},
            {"args": {"times": [42], "window": 1, "threshold": 1}, "why": {"t": "Threshold 1", "d": "The first event fires at once."}},
            {"args": {"times": [9, 9, 9], "window": 1, "threshold": 3}, "why": {"t": "Same second", "d": "Duplicates in one second count together."}},
            {"args": {"times": [0, 10], "window": 10, "threshold": 2}, "why": {"t": "Exactly window apart", "d": "[1, 10] no longer holds 0: -1."}},
            {"args": {"times": [0, 9], "window": 10, "threshold": 2}, "why": {"t": "Just inside", "d": "[0, 9] holds both."}},
            {"args": {"times": [30, 5, 20, 1, 25, 3], "window": 5, "threshold": 3}, "why": {"t": "Unsorted input", "d": "1, 3 and 5 fall in [1, 5]."}},
            {"args": _BURST_LARGE, "why": {"t": "Large input", "d": "1,500 random events plus a burst of 20 near 40,000."}},
        ],
        "solutions": [
            {"name": "Sort + two pointers (Optimal)",
             "description": "Sort once, then slide a window: advance the left pointer past events older than t - window + 1, and return t as soon as the window holds threshold events.",
             "time": "O(n log n)", "space": "O(n)",
             "keyPoints": ["Answer is always an event time", "Each pointer only moves forward", "Duplicates need no special case"],
             "code": '''def first_alert(times, window, threshold):
    ts = sorted(times)
    left = 0
    for right, t in enumerate(ts):
        while ts[left] < t - window + 1:
            left += 1
        if right - left + 1 >= threshold:
            return t
    return -1
'''},
            {"name": "Count around every time", "slow": True,
             "description": "For each distinct event time in increasing order, count all events in its window by scanning the whole list.",
             "time": "O(n²)", "space": "O(n)",
             "keyPoints": ["Direct translation of the rule", "Quadratic in the number of events"],
             "code": '''def first_alert(times, window, threshold):
    for t in sorted(set(times)):
        if sum(1 for x in times if t - window + 1 <= x <= t) >= threshold:
            return t
    return -1
'''},
        ],
        "starter": '''def first_alert(times: list[int], window: int, threshold: int) -> int:
    pass
''',
    },
]
