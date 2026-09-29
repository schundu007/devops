"""Capra Playground export for DC-OBS-01 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "design", "fn": "MetricStore", "params": [], "types": {}, "ret": "value", "cmp": "exact"}


def ops(*calls):
    """ops(("record", "cpu", 0.4, 1000), ("value_at", "cpu", 1005)) -> handbook design args."""
    return {"ops": ["MetricStore"] + [c[0] for c in calls], "vals": [[]] + [list(c[1:]) for c in calls]}


T0 = 1_700_000_000

EXAMPLES = [
    {"args": ops(("record", "cpu_usage", 0.42, 1000), ("record", "cpu_usage", 0.87, 1015),
                 ("value_at", "cpu_usage", 1010), ("value_at", "cpu_usage", 1015)),
     "explanation": "At 1010 the newest sample at or before it is the one at 1000. At 1015 the exact match counts.",
     "why": {"t": "Between samples · Exact match", "d": "A query between two samples, then one exactly on a sample."}},
    {"args": ops(("record", "cpu_usage", 0.5, 1000), ("value_at", "cpu_usage", 999), ("value_at", "mem_bytes", 1000)),
     "explanation": "Nothing was recorded that early, and mem_bytes was never recorded: both are None.",
     "why": {"t": "Too early · Unknown metric", "d": "Queries that have no answer return None."}},
    {"args": ops(("record", "queue_depth", 0.0, 1000), ("value_at", "queue_depth", 1005)),
     "explanation": "0.0 is a real reading (the queue was empty), not a missing value.",
     "why": {"t": "Zero value", "d": "A falsy value must not be confused with no data."}},
]


def _large():
    rng = random.Random(7)
    calls, t = [], T0
    for _ in range(600):
        t += rng.randint(1, 30)
        calls.append(("record", "cpu_usage", float(t % 97), t))
    for _ in range(300):
        calls.append(("value_at", "cpu_usage", rng.randint(T0 - 10, t + 10)))
    return ops(*calls)


TESTS = [
    {"args": ops(("value_at", "cpu_usage", T0)),
     "why": {"t": "Empty store", "d": "A query before anything was recorded."}},
    {"args": ops(("record", "cpu_usage", 0.5, T0), ("value_at", "cpu_usage", T0 - 1), ("value_at", "cpu_usage", T0)),
     "why": {"t": "Boundary", "d": "One second before the first sample, then exactly on it."}},
    {"args": ops(("record", "cpu_usage", 0.1, T0), ("record", "mem_bytes", 5e8, T0 + 30), ("record", "cpu_usage", 0.9, T0 + 60),
                 ("value_at", "mem_bytes", T0 + 59), ("value_at", "cpu_usage", T0 + 59), ("value_at", "mem_bytes", T0 + 29)),
     "why": {"t": "Independent metrics", "d": "Samples of one metric never answer a query for another."}},
    {"args": ops(("record", "cpu_usage", 0.3, T0), ("value_at", "cpu_usage", T0 + 10**6)),
     "why": {"t": "Long after", "d": "A query far after the last sample returns the last value."}},
    {"args": ops(*[("record", 'node_cpu{instance="10.0.3.17"}', float(i), T0 + 15 * i) for i in range(20)],
                 ("record", 'node_cpu{instance="10.0.3.17"}', 99.0, T0 + 720),
                 ("value_at", 'node_cpu{instance="10.0.3.17"}', T0 + 510),
                 ("value_at", 'node_cpu{instance="10.0.3.17"}', T0 + 720)),
     "why": {"t": "Scrape gap", "d": "A node reboot leaves a 7-minute gap; queries inside it see the last value before the gap."}},
    {"args": ops(("record", "cpu_usage", 1.0, 100), ("record", "cpu_usage", 2.0, 101), ("record", "cpu_usage", 3.0, 102),
                 ("value_at", "cpu_usage", 100), ("value_at", "cpu_usage", 101), ("value_at", "cpu_usage", 102), ("value_at", "cpu_usage", 103)),
     "why": {"t": "Consecutive seconds", "d": "Samples one second apart; every query lands exactly on one."}},
    {"args": _large(),
     "why": {"t": "Large input", "d": "600 samples and 300 queries at random times."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Hash map + binary search (Optimal)",
     "description": "Map each metric to parallel lists of times and values. Samples arrive in time order, so appending keeps the times sorted; a query is bisect_right(times, T) - 1.",
     "time": "O(1) record, O(log n) value_at", "space": "O(total samples)",
     "keyPoints": ["Arrival order is time order, so appends stay sorted", "bisect_right - 1 is the last sample at or before T", "Return None when the index is -1 or the metric is unknown"]},
    {"name": "Linear scan", "slow": True,
     "description": "Keep every sample and scan all of a metric's samples on each query, remembering the newest one at or before T.",
     "time": "O(1) record, O(n) value_at", "space": "O(total samples)",
     "keyPoints": ["Correct but scans the whole series", "Too slow when a dashboard asks thousands of times per refresh"],
     "code": '''from __future__ import annotations


class MetricStore:
    def __init__(self) -> None:
        self._samples: dict[str, list[tuple[int, float]]] = {}

    def record(self, metric: str, value: float, timestamp: int) -> None:
        self._samples.setdefault(metric, []).append((timestamp, value))

    def value_at(self, metric: str, timestamp: int) -> float | None:
        best = None
        for t, v in self._samples.get(metric, []):
            if t <= timestamp:
                best = v
        return best
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Linear scan", "idea": "Scan every sample of the metric and keep the newest one at or before T.",
     "time": "O(n) per query", "space": "O(total samples)", "use": "A handful of samples; simplest to explain."},
    {"name": "Binary search per metric", "idea": "Times arrive sorted, so bisect for the last time <= T.",
     "time": "O(log n) per query", "space": "O(total samples)", "use": "Real dashboards: many queries over long series."},
]

VARIANT_TITLE = "Value at a time"
VARIANT_APPROACH = "Hash map + binary search · O(log n) per query · O(samples)"


def lops(lookback, *calls):
    return {"ops": ["MetricStore"] + [c[0] for c in calls], "vals": [[lookback]] + [list(c[1:]) for c in calls]}


def _lookback_large():
    rng = random.Random(300)
    calls, t = [], T0
    for _ in range(500):
        t += rng.choice([15, 15, 15, 30, 400])
        calls.append(("record", rng.choice(["up", "cpu"]), float(rng.randint(0, 100)), t))
    for _ in range(300):
        calls.append(("value_at", rng.choice(["up", "cpu", "mem"]), rng.randint(T0 - 20, t + 400)))
    return lops(300, *calls)


def _range_large():
    rng = random.Random(1348)
    times, values, t = [], [], 0
    for _ in range(1500):
        t += rng.randint(5, 40)
        times.append(t)
        values.append(rng.randint(0, 999))
    return {"times": times, "values": values, "start": 0, "end": t + 50, "step": 60}


def rq(times, values, start, end, step, t, d):
    return {"args": {"times": times, "values": values, "start": start, "end": end, "step": step}, "why": {"t": t, "d": d}}


VARIANTS = [
    {
        "key": "lookback",
        "title": "Lookback window (stale series)",
        "approach": "Hash map + binary search, then an age check · O(log n) per query · O(samples)",
        "spec": {"kind": "design", "fn": "MetricStore", "params": []},
        "statement": (
            "A dashboard must not keep drawing a flat line for a target that stopped reporting. Like Prometheus's "
            "lookback delta, a sample only answers a query while it is fresh enough.\n\n"
            "Implement `MetricStore(lookback)`:\n\n"
            "- `record(metric, value, timestamp)`: store a sample. Samples of one metric arrive in increasing time order.\n"
            "- `value_at(metric, timestamp)`: the value of the newest sample at or before `timestamp`, **if** it is at most "
            "`lookback` seconds old (`timestamp - sample_time <= lookback`). Otherwise, or if there is no such sample, return `None`."
        ),
        "examples": [
            {"args": lops(300, ("record", "up", 1.0, 1000), ("value_at", "up", 1300), ("value_at", "up", 1301)),
             "explanation": "At 1300 the sample is exactly 300 s old and still counts. One second later it is stale.",
             "why": {"t": "Lookback edge", "d": "The age limit is inclusive."}},
            {"args": lops(60, ("record", "cpu", 0.5, 100), ("record", "cpu", 0.7, 500), ("value_at", "cpu", 400), ("value_at", "cpu", 520)),
             "explanation": "At 400 the newest sample (100) is 300 s old: None, even though the series continues later. At 520 the sample at 500 is fresh.",
             "why": {"t": "Gap in a series", "d": "A scrape gap shows as missing data, not the old value."}},
        ],
        "constraints": ["1 ≤ lookback ≤ 10⁴", "0 ≤ timestamp ≤ 2 · 10⁹", "Samples of one metric arrive in increasing time order", "At most 2000 calls"],
        "hints": [
            "Find the newest sample at or before the query exactly as before: bisect_right - 1.",
            "Only that one sample can answer. If it is too old, every earlier one is older still.",
        ],
        "tests": [
            {"args": lops(10, ("value_at", "x", 5)), "why": {"t": "Empty store", "d": "No samples at all."}},
            {"args": lops(10, ("record", "x", 0.0, 50), ("value_at", "x", 49), ("value_at", "x", 50), ("value_at", "x", 60), ("value_at", "x", 61)),
             "why": {"t": "Before, on, edge, after", "d": "Too early, exact match, exactly lookback old, one second past it."}},
            {"args": lops(1, ("record", "a", 1.0, 10), ("record", "a", 2.0, 11), ("value_at", "a", 12), ("value_at", "a", 13)),
             "why": {"t": "Lookback of one", "d": "The smallest window: a sample answers only in its own second and the next."}},
            {"args": lops(100, ("record", "a", 1.0, 10), ("record", "b", 9.0, 500), ("value_at", "a", 500), ("value_at", "b", 500)),
             "why": {"t": "Independent metrics", "d": "A fresh sample of b does not keep a alive."}},
            {"args": lops(30, ("record", "q", 0.0, 0), ("value_at", "q", 30), ("value_at", "q", 31)),
             "why": {"t": "Zero value at time 0", "d": "0.0 and timestamp 0 are real data, not missing."}},
            {"args": _lookback_large(), "why": {"t": "Large input", "d": "500 samples with scrape gaps and 300 queries."}},
        ],
        "solutions": [
            {"name": "Binary search + age check (Optimal)",
             "description": "Keep sorted times and values per metric. bisect_right - 1 finds the newest sample at or before the query; return it only if it is within lookback.",
             "time": "O(1) record, O(log n) value_at", "space": "O(samples)",
             "keyPoints": ["Only the newest sample can qualify", "The age check is inclusive", "Unknown metric or index -1 means None"],
             "code": '''from bisect import bisect_right


class MetricStore:
    def __init__(self, lookback):
        self.lookback = lookback
        self.series = {}

    def record(self, metric, value, timestamp):
        times, values = self.series.setdefault(metric, ([], []))
        times.append(timestamp)
        values.append(value)

    def value_at(self, metric, timestamp):
        if metric not in self.series:
            return None
        times, values = self.series[metric]
        i = bisect_right(times, timestamp) - 1
        if i < 0 or timestamp - times[i] > self.lookback:
            return None
        return values[i]
'''},
            {"name": "Scan the series", "slow": True,
             "description": "Walk every sample of the metric, keep the newest one at or before the query, then apply the age check.",
             "time": "O(n) value_at", "space": "O(samples)",
             "keyPoints": ["Simple", "Full scan on every dashboard query"],
             "code": '''class MetricStore:
    def __init__(self, lookback):
        self.lookback = lookback
        self.samples = {}

    def record(self, metric, value, timestamp):
        self.samples.setdefault(metric, []).append((timestamp, value))

    def value_at(self, metric, timestamp):
        best = None
        for t, v in self.samples.get(metric, []):
            if t <= timestamp:
                best = (t, v)
        if best is None or timestamp - best[0] > self.lookback:
            return None
        return best[1]
'''},
        ],
        "starter": '''class MetricStore:
    def __init__(self, lookback):
        pass

    def record(self, metric, value, timestamp):
        pass

    def value_at(self, metric, timestamp):
        pass
''',
    },
    {
        "key": "range-query",
        "title": "Range query at a fixed step",
        "approach": "Two pointers over samples and steps · O(n + s) · O(s)",
        "spec": {"kind": "fn", "fn": "range_query", "params": ["times", "values", "start", "end", "step"]},
        "statement": (
            "A graph panel does not ask for one instant; it asks for a whole range, evaluated every `step` seconds, "
            "the way a Prometheus range query does.\n\n"
            "`times` is strictly increasing and `values[i]` is the sample at `times[i]`. Evaluate the series at "
            "`start, start + step, start + 2·step, …` up to and including `end` when it lands on a step.\n\n"
            "At each instant, the value is the newest sample at or before it, or `None` if there is none yet. "
            "Return the list of values, one per instant."
        ),
        "examples": [
            {"args": {"times": [10, 25, 40], "values": [1, 2, 3], "start": 0, "end": 40, "step": 10},
             "explanation": "At 0 nothing exists yet. 10 and 20 see the sample at 10, 30 sees 25, and 40 hits a sample exactly.",
             "why": {"t": "Step between samples", "d": "Instants that land between samples repeat the last value."}},
        ],
        "constraints": ["0 ≤ times.length ≤ 10⁴", "times strictly increasing", "0 ≤ start ≤ end ≤ 10⁹", "1 ≤ step", "At most 10⁴ instants"],
        "hints": [
            "Both the samples and the instants are in increasing order.",
            "Keep one pointer into the samples. For each instant, advance it while the next sample is at or before the instant; it never moves back.",
            "A bisect per instant also works in O(s log n); the sweep avoids the log.",
        ],
        "tests": [
            rq([], [], 0, 30, 10, "No samples", "Every instant is None."),
            rq([5], [7], 5, 5, 1, "Single instant", "start == end gives exactly one value."),
            rq([0, 1, 2, 3], [4, 5, 6, 7], 0, 3, 1, "Step equals sample spacing", "Every instant lands exactly on a sample."),
            rq([100], [1], 0, 250, 100, "End between steps", "250 is not a step, so the last instant is 200."),
            rq([1, 2, 3, 50], [1, 2, 3, 4], 0, 60, 30, "Several samples per step", "Only the newest sample before each instant counts."),
            rq([10, 20], [0, 0], 0, 30, 15, "Zero values", "0 is data; None only before the first sample."),
            {"args": _range_large(), "why": {"t": "Large input", "d": "1,500 samples evaluated at about 500 instants."}},
        ],
        "solutions": [
            {"name": "Two-pointer sweep (Optimal)",
             "description": "Walk the instants in order with one pointer into the samples that only moves forward.",
             "time": "O(n + s)", "space": "O(s) for the output",
             "keyPoints": ["Both sequences are sorted", "The sample pointer never moves back", "None until the first sample"],
             "code": '''def range_query(times, values, start, end, step):
    out = []
    i = -1
    t = start
    while t <= end:
        while i + 1 < len(times) and times[i + 1] <= t:
            i += 1
        out.append(values[i] if i >= 0 else None)
        t += step
    return out
'''},
            {"name": "Scan per instant", "slow": True,
             "description": "For each instant, scan every sample and keep the newest one at or before it.",
             "time": "O(n · s)", "space": "O(s)",
             "keyPoints": ["Treats each instant as a fresh lookup", "Quadratic on long ranges"],
             "code": '''def range_query(times, values, start, end, step):
    out = []
    t = start
    while t <= end:
        best = None
        for ts, v in zip(times, values):
            if ts <= t:
                best = v
        out.append(best)
        t += step
    return out
'''},
        ],
        "starter": '''def range_query(times, values, start, end, step):
    """Value at start, start + step, ... up to end (None before the first sample)."""
    pass
''',
    },
]
