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
