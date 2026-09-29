"""Capra Playground export for DC-OBS-12 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "design", "fn": "SampleTracker", "params": [], "types": {}, "ret": "value", "cmp": "exact"}


def ops(*calls):
    return {"ops": ["SampleTracker"] + [c[0] for c in calls], "vals": [[]] + [list(c[1:]) for c in calls]}


EXAMPLES = [
    {"args": ops(("update", 1, 10.0), ("update", 2, 5.0), ("current",), ("maximum",), ("update", 1, 3.0), ("maximum",)),
     "explanation": "The newest timestamp is 2, so current is 5. Correcting t=1 to 3 removes the 10, so the max drops to 5.",
     "why": {"t": "Correction lowers the peak", "d": "A stale maximum must not survive a correction."}},
    {"args": ops(("update", 100, 1.0), ("update", 50, 99.0), ("current",), ("maximum",)),
     "explanation": "50 is older than 100, so current does not change, but 99 is still the maximum.",
     "why": {"t": "Late sample", "d": "An old timestamp arrives after a newer one."}},
    {"args": ops(("update", 5, 1.0), ("update", 5, 8.0), ("current",), ("minimum",)),
     "explanation": "The newest timestamp itself was corrected: current and minimum both see 8.",
     "why": {"t": "Correct the newest", "d": "A correction at the newest timestamp."}},
]


def _large():
    rng = random.Random(2034)
    calls = []
    for _ in range(900):
        calls.append(("update", rng.randint(1, 200), float(rng.randint(-500, 500))))
        if rng.random() < 0.3:
            calls.append((rng.choice(["current", "maximum", "minimum"]),))
    return ops(*calls)


TESTS = [
    {"args": ops(("update", 1, 42.0), ("current",), ("maximum",), ("minimum",)),
     "why": {"t": "Single sample", "d": "One sample is the current, max and min."}},
    {"args": ops(("update", 1, 5.0), ("update", 1, 5.0), ("maximum",), ("minimum",)),
     "why": {"t": "Same correction twice", "d": "Re-sending the same value changes nothing."}},
    {"args": ops(("update", 1, 7.0), ("update", 2, 7.0), ("update", 1, 1.0), ("maximum",), ("minimum",)),
     "why": {"t": "Duplicate values", "d": "Two timestamps share a value; correcting one keeps the other."}},
    {"args": ops(("update", 3, -2.5), ("update", 1, -9.0), ("minimum",), ("update", 1, 0.0), ("minimum",)),
     "why": {"t": "Negative values", "d": "The minimum moves after a correction of a negative sample."}},
    {"args": ops(("update", 1, 1.0), ("update", 1, 2.0), ("update", 1, 3.0), ("update", 1, 0.5), ("maximum",), ("minimum",), ("current",)),
     "why": {"t": "Many corrections", "d": "Only the last correction of a timestamp counts."}},
    {"args": ops(("update", 10, 1.0), ("update", 20, 2.0), ("update", 15, 50.0), ("current",), ("maximum",), ("update", 15, 1.5), ("maximum",)),
     "why": {"t": "Late spike corrected", "d": "A late spike raises the max until it is corrected away."}},
    {"args": ops(("update", 1_700_000_000, 0.62), ("update", 1_700_000_015, 0.91), ("update", 1_700_000_030, 0.40),
                 ("update", 1_700_000_015, 0.58), ("current",), ("maximum",), ("minimum",)),
     "why": {"t": "Scrape correction", "d": "A mis-scraped 0.91 CPU reading is corrected to 0.58."}},
    {"args": _large(),
     "why": {"t": "Large input", "d": "900 updates over 200 timestamps with interleaved queries."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Hash map + two heaps, lazy deletion (Optimal)",
     "description": "A dict holds each timestamp's current value. Push every (value, timestamp) into a max-heap and a min-heap; when asked, pop tops whose value no longer matches the dict.",
     "time": "O(log n) update, O(log n) amortized max/min", "space": "O(updates)",
     "keyPoints": ["Never search a heap to delete", "A heap top is stale if the dict disagrees", "current is the value at the largest timestamp"]},
    {"name": "Scan the map", "slow": True,
     "description": "Keep only the dict and scan all current values for the max and min on every query.",
     "time": "O(1) update, O(n) max/min", "space": "O(n)",
     "keyPoints": ["No stale entries to reason about", "Every max/min query is a full scan"],
     "code": '''from __future__ import annotations


class SampleTracker:
    def __init__(self) -> None:
        self._value_at: dict[int, float] = {}
        self._latest = -1

    def update(self, timestamp: int, value: float) -> None:
        self._value_at[timestamp] = value
        self._latest = max(self._latest, timestamp)

    def current(self) -> float:
        return self._value_at[self._latest]

    def maximum(self) -> float:
        return max(self._value_at.values())

    def minimum(self) -> float:
        return min(self._value_at.values())
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Scan the map", "idea": "Recompute max and min from every current value.",
     "time": "O(n) per query", "space": "O(n)", "use": "Few samples or rare queries."},
    {"name": "Heaps + lazy deletion", "idea": "Push every update; discard stale tops only when they surface.",
     "time": "O(log n) amortized", "space": "O(updates)", "use": "Frequent queries on long, corrected series."},
]

VARIANT_TITLE = "Current, max and min"
VARIANT_APPROACH = "Hash map + two heaps, lazy deletion · O(log n) amortized · O(updates)"


def hops(*calls):
    return {"ops": ["HostLoad"] + [c[0] for c in calls], "vals": [[]] + [list(c[1:]) for c in calls]}


def _hosts_large():
    rng = random.Random(12)
    hosts = [f"node-{i:02d}" for i in range(40)]
    calls = []
    for _ in range(1200):
        r = rng.random()
        if r < 0.6:
            calls.append(("report", rng.choice(hosts), rng.randint(0, 100)))
        elif r < 0.75:
            calls.append(("retire", rng.choice(hosts)))
        else:
            calls.append(("hottest",))
    return hops(*calls)


def _spread_large():
    rng = random.Random(2034)
    return {"updates": [[rng.randint(1, 150), rng.randint(-1000, 1000)] for _ in range(1500)]}


VARIANTS = [
    {
        "key": "hottest-host",
        "title": "Hottest host in the fleet",
        "approach": "Hash map + max-heap, lazy deletion · O(log n) amortized · O(reports)",
        "spec": {"kind": "design", "fn": "HostLoad", "params": []},
        "statement": (
            "Track which host is hottest, so a scheduler can place the next batch job away from it.\n"
            "\n"
            "### Methods\n"
            "- `report(host, cpu)`: the host's CPU percent is now `cpu`, replacing any earlier report\n"
            "- `retire(host)`: forget the host\n"
            "- `hottest()`: the host with the highest current CPU; `None` if no host is known\n"
            "\n"
            "### Rules\n"
            "- A retired host that reports again is back\n"
            "- Retiring an unknown host does nothing\n"
            "- On a CPU tie, `hottest` returns the alphabetically smallest host"
        ),
        "examples": [
            {"args": hops(("report", "web-1", 90), ("report", "web-2", 40), ("hottest",), ("report", "web-1", 10), ("hottest",)),
             "explanation": "web-1 is hottest at 90. Its next report drops it to 10, so web-2 takes over.",
             "why": {"t": "Report lowers the peak", "d": "A replaced reading must not keep a host on top."}},
            {"args": hops(("report", "db-2", 70), ("report", "db-1", 70), ("hottest",), ("retire", "db-1"), ("hottest",)),
             "explanation": "Both run at 70, so db-1 wins alphabetically. After it is retired, db-2 is the hottest.",
             "why": {"t": "Tie · Retire", "d": "Ties break by name; retired hosts vanish."}},
        ],
        "constraints": ["0 ≤ cpu ≤ 100 (integer)", "Host names are non-empty strings", "At most 2000 calls"],
        "hints": [
            "Push (-cpu, host) on every report and never search the heap to delete.",
            "When asked, pop heap tops that no longer match the dict: the host was retired or re-reported with another value.",
            "An entry that matches the current value is valid, even if it was pushed long ago.",
        ],
        "tests": [
            {"args": hops(("hottest",)), "why": {"t": "Empty fleet", "d": "Nothing reported yet: None."}},
            {"args": hops(("report", "a", 0), ("hottest",), ("retire", "a"), ("hottest",)), "why": {"t": "Single host, zero CPU", "d": "0 is a real reading; after retire the fleet is empty."}},
            {"args": hops(("retire", "ghost"), ("report", "a", 5), ("hottest",)), "why": {"t": "Retire unknown", "d": "Retiring a host that never reported is a no-op."}},
            {"args": hops(("report", "a", 50), ("retire", "a"), ("report", "a", 50), ("hottest",)), "why": {"t": "Retire then return", "d": "A host that comes back with the same value is hottest again."}},
            {"args": hops(("report", "a", 90), ("report", "b", 80), ("report", "a", 80), ("hottest",), ("report", "b", 79), ("hottest",)),
             "why": {"t": "Ties after updates", "d": "Both drop to 80: a wins by name, then b falls behind."}},
            {"args": hops(("report", "x", 30), ("report", "x", 30), ("report", "x", 30), ("retire", "x"), ("hottest",)),
             "why": {"t": "Duplicate reports", "d": "Several heap entries for one host all go stale on retire."}},
            {"args": _hosts_large(), "why": {"t": "Large input", "d": "1,200 mixed calls over 40 hosts."}},
        ],
        "solutions": [
            {"name": "Dict + max-heap with lazy deletion (Optimal)",
             "description": "The dict holds each host's current CPU. Push (-cpu, host) on every report; hottest pops tops that the dict no longer agrees with.",
             "time": "O(log n) report, O(log n) amortized hottest", "space": "O(reports)",
             "keyPoints": ["(-cpu, host) orders by CPU, then name", "Stale if retired or re-reported", "Each pushed entry is popped at most once"],
             "code": '''import heapq


class HostLoad:
    def __init__(self):
        self.cpu = {}
        self.heap = []

    def report(self, host, cpu):
        self.cpu[host] = cpu
        heapq.heappush(self.heap, (-cpu, host))

    def retire(self, host):
        self.cpu.pop(host, None)

    def hottest(self):
        while self.heap and self.cpu.get(self.heap[0][1]) != -self.heap[0][0]:
            heapq.heappop(self.heap)
        return self.heap[0][1] if self.heap else None
'''},
            {"name": "Scan the dict", "slow": True,
             "description": "Keep only the dict and scan every host on each hottest call.",
             "time": "O(1) report, O(n) hottest", "space": "O(hosts)",
             "keyPoints": ["Nothing stale to reason about", "Full fleet scan per placement decision"],
             "code": '''class HostLoad:
    def __init__(self):
        self.cpu = {}

    def report(self, host, cpu):
        self.cpu[host] = cpu

    def retire(self, host):
        self.cpu.pop(host, None)

    def hottest(self):
        if not self.cpu:
            return None
        return min(self.cpu, key=lambda h: (-self.cpu[h], h))
'''},
        ],
        "starter": '''class HostLoad:
    def __init__(self):
        pass

    def report(self, host, cpu):
        pass

    def retire(self, host):
        pass

    def hottest(self):
        pass
''',
    },
    {
        "key": "spread",
        "title": "Spread after every correction",
        "approach": "Two heaps with lazy deletion · O(n log n) · O(n)",
        "spec": {"kind": "fn", "fn": "spread_after_each", "params": ["updates"]},
        "statement": (
            "Report the spread of a series (its maximum minus its minimum) after every update, for a flapping-sensor alert.\n"
            "\n"
            "### Input\n"
            "- `updates[i] = [timestamp, value]`, in arrival order\n"
            "\n"
            "### Output\n"
            "- The list of spreads, one per update: `max - min` over the current value of every timestamp seen so far, after applying that update\n"
            "\n"
            "### Rules\n"
            "- Samples can arrive late\n"
            "- A repeated timestamp is a **correction** that replaces the old value"
        ),
        "examples": [
            {"args": {"updates": [[1, 10], [2, 4], [3, 7], [1, 5]]},
             "explanation": "Spreads: 0, then 10 - 4 = 6, still 6, then correcting t=1 to 5 leaves {5, 4, 7}: 3.",
             "why": {"t": "Correction narrows", "d": "Replacing the old maximum must shrink the spread."}},
        ],
        "constraints": ["1 ≤ updates.length ≤ 2000", "0 ≤ timestamp ≤ 10⁹", "-10⁶ ≤ value ≤ 10⁶ (integer)"],
        "hints": [
            "You need the current max and min after every update, with values that can be replaced.",
            "Push into a max-heap and a min-heap; before reading a top, pop it while the dict says that timestamp now holds another value.",
        ],
        "tests": [
            {"args": {"updates": [[5, 3]]}, "why": {"t": "Single sample", "d": "One value: spread 0."}},
            {"args": {"updates": [[1, 2], [1, 2], [1, 2]]}, "why": {"t": "Same correction repeated", "d": "Re-sending one value never changes anything."}},
            {"args": {"updates": [[1, -5], [2, 5], [2, -5]]}, "why": {"t": "Negative values", "d": "Spread across zero, then collapsing to 0."}},
            {"args": {"updates": [[1, 8], [2, 8], [1, 0]]}, "why": {"t": "Duplicate values", "d": "Two timestamps share the max; correcting one keeps the other."}},
            {"args": {"updates": [[10, 1], [5, 100], [20, 2], [5, 1]]}, "why": {"t": "Late spike corrected", "d": "A late sample widens the spread until it is fixed."}},
            {"args": {"updates": [[1, 1], [2, 2], [3, 3], [4, 4], [1, 4], [2, 4], [3, 4]]}, "why": {"t": "Converging", "d": "Corrections pull every value to 4: spread falls to 0."}},
            {"args": _spread_large(), "why": {"t": "Large input", "d": "1,500 updates over 150 timestamps."}},
        ],
        "solutions": [
            {"name": "Two heaps, lazy deletion (Optimal)",
             "description": "Keep timestamp to value in a dict; push each update into a min-heap and a max-heap. Before reading each top, discard entries the dict no longer agrees with.",
             "time": "O(n log n)", "space": "O(n)",
             "keyPoints": ["A top is stale if its timestamp now holds another value", "Every entry is popped at most once", "Only read tops after cleaning them"],
             "code": '''import heapq


def spread_after_each(updates):
    cur = {}
    hi, lo = [], []
    out = []
    for t, v in updates:
        cur[t] = v
        heapq.heappush(hi, (-v, t))
        heapq.heappush(lo, (v, t))
        while cur[hi[0][1]] != -hi[0][0]:
            heapq.heappop(hi)
        while cur[lo[0][1]] != lo[0][0]:
            heapq.heappop(lo)
        out.append(-hi[0][0] - lo[0][0])
    return out
'''},
            {"name": "Recompute every time", "slow": True,
             "description": "Apply the update to the dict, then scan all current values for max and min.",
             "time": "O(n · distinct timestamps)", "space": "O(distinct timestamps)",
             "keyPoints": ["Trivially correct", "A full scan per update"],
             "code": '''def spread_after_each(updates):
    cur = {}
    out = []
    for t, v in updates:
        cur[t] = v
        vals = cur.values()
        out.append(max(vals) - min(vals))
    return out
'''},
        ],
        "starter": '''def spread_after_each(updates):
    """max - min of the current values after each update."""
    pass
''',
    },
]
