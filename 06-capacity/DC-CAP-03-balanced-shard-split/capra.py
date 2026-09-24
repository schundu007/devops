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
