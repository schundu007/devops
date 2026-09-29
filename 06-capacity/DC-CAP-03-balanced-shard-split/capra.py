"""Capra Playground export for DC-CAP-03 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "min_busiest_worker_load", "params": ["loads", "workers"], "types": {}, "ret": "value", "cmp": "exact"}

EXAMPLES = [
    {"args": {"loads": [7, 2, 5, 10, 8], "workers": 2},
     "explanation": "[7,2,5] = 14 and [10,8] = 18. Every other split has a busier worker.",
     "why": {"t": "Five ranges", "d": "Two workers."}},
    {"args": {"loads": [1, 4, 4], "workers": 3},
     "explanation": "One range per worker: the hottest range, 4, sets the floor.",
     "why": {"t": "One per worker", "d": "The answer is max(loads)."}},
    {"args": {"loads": [42], "workers": 3},
     "explanation": "A single range cannot be split.",
     "why": {"t": "Single range", "d": "More workers than ranges."}},
]

_rng = random.Random(410)
_MID = [_rng.randint(0, 1000) for _ in range(60)]
_BIG = [_rng.randint(0, 10**6) for _ in range(3000)]

TESTS = [
    {"args": {"loads": [5, 5, 5, 5], "workers": 1}, "why": {"t": "One worker", "d": "Everything on one worker: sum(loads)."}},
    {"args": {"loads": [0, 0, 0], "workers": 2}, "why": {"t": "All zero", "d": "Idle ranges: 0."}},
    {"args": {"loads": [1, 2, 3, 4, 5], "workers": 50}, "why": {"t": "Workers exceed ranges", "d": "Using fewer workers than allowed is fine."}},
    {"args": {"loads": [10, 0, 0, 0, 10], "workers": 2}, "why": {"t": "Zeros in the middle", "d": "Zero-load ranges can go anywhere."}},
    {"args": {"loads": [1, 1, 1, 1, 100], "workers": 2}, "why": {"t": "Hot tail", "d": "One hot range dominates."}},
    {"args": {"loads": [300, 120, 80, 950, 60, 60, 400, 210], "workers": 3},
     "why": {"t": "Key-range rebalance", "d": "Requests per second per key range, split across 3 consumers."}},
    {"args": {"loads": _MID, "workers": 7}, "why": {"t": "Random", "d": "60 ranges, 7 workers."}},
    {"args": {"loads": _BIG, "workers": 50}, "why": {"t": "Large input", "d": "3,000 ranges with loads up to 10^6."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Binary search on the answer (Optimal)",
     "description": "The answer lies between the hottest range and the total. For a limit L, pack ranges greedily and count workers; binary search for the smallest L that needs at most `workers`.",
     "time": "O(n · log(sum − max))", "space": "O(1) extra",
     "keyPoints": ["Greedy packing is optimal for a fixed limit", "Feasibility is monotonic in L", "Search between max(loads) and sum(loads)"]},
    {"name": "DP over split points", "slow": True,
     "description": "best(i, k) is the best busiest-worker load for ranges i..n-1 with k workers; try every end point of the first block.",
     "time": "O(n² · k)", "space": "O(n · k)",
     "keyPoints": ["Independent of the greedy argument", "Fine for 100 ranges, too slow for 10^5"],
     "code": '''from __future__ import annotations

from functools import lru_cache
from itertools import accumulate


def min_busiest_worker_load(loads: list[int], workers: int) -> int:
    n = len(loads)
    pre = [0] + list(accumulate(loads))
    k_max = min(workers, n)
    INF = float("inf")
    # best[k][i]: ranges i..n-1 split into at most k blocks
    best = [[INF] * (n + 1) for _ in range(k_max + 1)]
    for k in range(k_max + 1):
        best[k][n] = 0
    for i in range(n):
        best[1][i] = pre[n] - pre[i]
    for k in range(2, k_max + 1):
        for i in range(n - 1, -1, -1):
            b = best[k - 1][i]
            for j in range(i + 1, n):
                first = pre[j] - pre[i]
                if first >= b:
                    break
                b = min(b, max(first, best[k - 1][j]))
            best[k][i] = b
    return int(best[k_max][0])
'''},
]

WAYS_TO_SOLVE = [
    {"name": "DP over split points", "idea": "Try every end of the first block, recurse on the rest.", "time": "O(n² · k)",
     "space": "O(n · k)", "use": "Small inputs; proves the answer independently."},
    {"name": "Binary search on the answer", "idea": "Greedy feasibility check for a limit L, binary search L.",
     "time": "O(n · log(sum − max))", "space": "O(1)", "use": "Large inputs; the standard answer."},
]

VARIANT_TITLE = "Contiguous shard split"
VARIANT_APPROACH = "Binary search on the answer · O(n · log(sum − max)) · O(1)"

_vr = random.Random(875)
_DRAIN_BIG = [_vr.randint(1, 1000) for _ in range(300)]
_SPREAD_BIG = _vr.sample(range(0, 20000), 250)

VARIANTS = [
    {
        "key": "drain-rate",
        "title": "Backlog drain rate",
        "approach": "Binary search on the rate · O(n · log max) · O(1)",
        "spec": {"kind": "fn", "fn": "min_drain_rate", "params": ["backlogs", "hours"], "ret": "value", "cmp": "exact"},
        "statement": """A consumer has to empty the backlog of every partition before a maintenance window closes.

### Input
- `backlogs[i]`: the number of messages waiting in partition `i`
- `hours`: the hours available

### Output
- The smallest integer `rate` that empties every partition within `hours` hours

### Rules
- Each hour the consumer picks **one** partition and drains up to `rate` messages from it
- If the partition has fewer than `rate` left, it finishes and the rest of that hour is idle""",
        "examples": [
            {"args": {"backlogs": [3, 6, 7, 11], "hours": 8},
             "explanation": "At rate 4 the partitions take 1 + 2 + 2 + 3 = 8 hours. Rate 3 needs 1 + 2 + 3 + 4 = 10.",
             "why": {"t": "Fits exactly", "d": "The smallest rate uses all 8 hours."}},
            {"args": {"backlogs": [30, 11, 23, 4, 20], "hours": 5},
             "explanation": "One hour per partition, so the rate must cover the largest backlog: 30.",
             "why": {"t": "One hour each", "d": "hours == len(backlogs) forces rate = max."}},
        ],
        "constraints": ["1 ≤ backlogs.length ≤ 10^4", "1 ≤ backlogs[i] ≤ 10^9", "backlogs.length ≤ hours ≤ 10^9"],
        "hints": [
            "If rate r works, every rate above r works too. That is what makes binary search possible.",
            "Hours needed at rate r: the sum of (b + r - 1) // r. Search r between 1 and max(backlogs).",
            "Start from max(1, ceil(sum / hours)): no smaller rate can ever work.",
        ],
        "tests": [
            {"args": {"backlogs": [1], "hours": 1}, "why": {"t": "Minimal", "d": "One message, one hour: rate 1."}},
            {"args": {"backlogs": [1000000000], "hours": 2}, "why": {"t": "Huge backlog", "d": "Half of 10^9 per hour; a linear scan from 1 would never finish."}},
            {"args": {"backlogs": [5, 5, 5], "hours": 1000}, "why": {"t": "Plenty of time", "d": "Rate 1 is enough when hours ≥ sum."}},
            {"args": {"backlogs": [7, 7, 7, 7], "hours": 4}, "why": {"t": "Ties", "d": "Equal backlogs, one hour each."}},
            {"args": {"backlogs": [9, 1, 1, 1], "hours": 6}, "why": {"t": "One hot partition", "d": "Three hours for the hot partition: rate 3."}},
            {"args": {"backlogs": [312, 845, 90, 77, 603], "hours": 11}, "why": {"t": "Nightly drain", "d": "Kafka partitions drained before a broker upgrade."}},
            {"args": {"backlogs": _DRAIN_BIG, "hours": 900}, "why": {"t": "Large input", "d": "300 partitions, 900 hours."}},
        ],
        "solutions": [
            {"name": "Binary search on the rate (Optimal)",
             "description": "The rate lies between ceil(sum / hours) and max(backlogs). Count the hours a rate needs and binary search for the smallest rate that fits.",
             "time": "O(n · log max)", "space": "O(1)",
             "keyPoints": ["Hours needed only fall as the rate rises", "Integer ceiling with (b + r - 1) // r", "Tight bounds keep the search short"],
             "code": '''def min_drain_rate(backlogs, hours):
    lo = max(1, (sum(backlogs) + hours - 1) // hours)
    hi = max(backlogs)
    while lo < hi:
        mid = (lo + hi) // 2
        if sum((b + mid - 1) // mid for b in backlogs) <= hours:
            hi = mid
        else:
            lo = mid + 1
    return lo
'''},
            {"name": "Try every rate upward", "slow": True,
             "description": "Start at the lower bound ceil(sum / hours) and try rates one by one until one fits.",
             "time": "O(n · max)", "space": "O(1)",
             "keyPoints": ["Easy to trust", "Fails when backlogs reach 10^9"],
             "code": '''def min_drain_rate(backlogs, hours):
    r = max(1, (sum(backlogs) + hours - 1) // hours)
    while sum((b + r - 1) // r for b in backlogs) > hours:
        r += 1
    return r
'''},
        ],
        "starter": '''def min_drain_rate(backlogs: list[int], hours: int) -> int:
    pass
''',
    },
    {
        "key": "replica-spread",
        "title": "Spread replicas along a rack row",
        "approach": "Binary search on the gap + greedy placement · O(n log n + n · log span) · O(n)",
        "spec": {"kind": "fn", "fn": "max_min_spacing", "params": ["positions", "replicas"], "ret": "value", "cmp": "exact"},
        "statement": """Place copies of a service along a data center row as far apart as possible, to survive a shared power or cooling fault.

### Input
- `positions`: the free slots, distinct integers in any order, measured in rack units from the end of the row
- `replicas`: the number of copies to place, each on a distinct slot

### Output
- The largest possible value of the **smallest** distance between any two placed replicas""",
        "examples": [
            {"args": {"positions": [1, 2, 3, 4, 7], "replicas": 3},
             "explanation": "Slots 1, 4 and 7 are 3 apart. No placement of three replicas keeps every pair 4 apart.",
             "why": {"t": "Three replicas", "d": "The ends plus a middle slot."}},
            {"args": {"positions": [40, 1, 22, 10], "replicas": 2},
             "explanation": "Two replicas go on the two ends: 40 − 1 = 39.",
             "why": {"t": "Unsorted input", "d": "Two replicas always take the extremes."}},
        ],
        "constraints": ["2 ≤ positions.length ≤ 10^5", "0 ≤ positions[i] ≤ 10^9, all distinct", "2 ≤ replicas ≤ positions.length"],
        "hints": [
            "Sort the slots first. For a fixed gap g, taking the leftmost slot and then the first slot at least g further on is never worse.",
            "If gap g fits, every smaller gap fits. Binary search for the largest g that fits.",
            "The answer is between 1 and (max − min) // (replicas − 1).",
        ],
        "tests": [
            {"args": {"positions": [0, 1], "replicas": 2}, "why": {"t": "Minimal", "d": "Two adjacent slots: gap 1."}},
            {"args": {"positions": [5, 3, 9, 1], "replicas": 4}, "why": {"t": "Every slot used", "d": "replicas == len: the smallest neighbor gap."}},
            {"args": {"positions": [0, 10, 20, 30, 40], "replicas": 3}, "why": {"t": "Even spacing", "d": "Every other slot: gap 20."}},
            {"args": {"positions": [0, 1, 2, 3, 100], "replicas": 2}, "why": {"t": "Outlier slot", "d": "The far slot sets the answer for two replicas."}},
            {"args": {"positions": [0, 1, 2, 3, 100], "replicas": 3}, "why": {"t": "Cluster plus outlier", "d": "Two in the cluster at distance 3, one far away."}},
            {"args": {"positions": [2, 7, 13, 21, 22, 34, 55, 56], "replicas": 4}, "why": {"t": "Irregular row", "d": "Gaps of different sizes."}},
            {"args": {"positions": _SPREAD_BIG, "replicas": 17}, "why": {"t": "Large input", "d": "250 slots across 20,000 units."}},
        ],
        "solutions": [
            {"name": "Binary search on the gap (Optimal)",
             "description": "Sort once. For a gap g, greedily count how many replicas fit; binary search for the largest g that still fits `replicas`.",
             "time": "O(n log n + n · log span)", "space": "O(n)",
             "keyPoints": ["Greedy from the left is optimal for a fixed gap", "Feasibility falls as the gap grows", "Search for the last feasible value, not the first"],
             "code": '''def max_min_spacing(positions, replicas):
    xs = sorted(positions)

    def fits(g):
        count, last = 1, xs[0]
        for x in xs[1:]:
            if x - last >= g:
                count += 1
                last = x
                if count == replicas:
                    return True
        return count >= replicas

    lo, hi = 1, (xs[-1] - xs[0]) // (replicas - 1)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if fits(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo
'''},
            {"name": "Try every gap downward", "slow": True,
             "description": "Start at the upper bound (max − min) // (replicas − 1) and lower the gap one unit at a time until the greedy placement fits.",
             "time": "O(n · span)", "space": "O(n)",
             "keyPoints": ["Same greedy check", "Linear in the row length, not its log"],
             "code": '''def max_min_spacing(positions, replicas):
    xs = sorted(positions)
    g = (xs[-1] - xs[0]) // (replicas - 1)
    while g > 1:
        count, last = 1, xs[0]
        for x in xs[1:]:
            if x - last >= g:
                count += 1
                last = x
        if count >= replicas:
            return g
        g -= 1
    return 1
'''},
        ],
        "starter": '''def max_min_spacing(positions: list[int], replicas: int) -> int:
    pass
''',
    },
]
