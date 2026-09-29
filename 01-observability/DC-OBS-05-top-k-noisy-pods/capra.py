"""Capra Playground export for DC-OBS-05 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "design", "fn": "NoisyBoard", "params": [], "types": {}, "ret": "value", "cmp": "exact"}


def ops(*calls):
    return {"ops": ["NoisyBoard"] + [c[0] for c in calls], "vals": [[]] + [list(c[1:]) for c in calls]}


EXAMPLES = [
    {"args": ops(("add", "checkout-7d9f4-x2kqp", 900), ("add", "search-5c8b7-q1wzt", 300), ("add", "cart-6f5d2-m8hvn", 600),
                 ("top", 2), ("top_total", 2)),
     "explanation": "checkout (900) and cart (600) are the two largest; their sum is 1500.",
     "why": {"t": "Ranking", "d": "The basic top-k and its total."}},
    {"args": ops(("add", "api-key-7f3a", 25), ("add", "api-key-91bc", 20), ("reset", "api-key-7f3a"), ("top", 5)),
     "explanation": "The reset key is gone from the board; asking for 5 returns only what exists.",
     "why": {"t": "Reset · k larger than board", "d": "A reset key disappears, and k larger than the board returns everything."}},
    {"args": ops(("top", 3), ("add", "pod-c", 7), ("add", "pod-a", 7), ("add", "pod-b", 7), ("top", 2)),
     "explanation": "An empty board returns []. Equal totals are ordered by key, A to Z.",
     "why": {"t": "Empty board · Ties", "d": "Nothing to rank, then a three-way tie broken by key."}},
]


def _large():
    rng = random.Random(1244)
    pods = [f"pod-{i:03d}" for i in range(150)]
    calls = []
    for _ in range(700):
        r = rng.random()
        if r < 0.85:
            calls.append(("add", rng.choice(pods), rng.randint(1, 500)))
        elif r < 0.93:
            calls.append(("reset", rng.choice(pods)))
        else:
            calls.append(("top", rng.randint(1, 8)))
    calls += [("top", 10), ("top_total", 10)]
    return ops(*calls)


TESTS = [
    {"args": ops(("top_total", 3)),
     "why": {"t": "Empty total", "d": "The total of an empty board is 0."}},
    {"args": ops(("add", "pod-a", 5), ("top", 1), ("top_total", 1)),
     "why": {"t": "Single key", "d": "One key is its own top 1."}},
    {"args": ops(("add", "pod-a", 5), ("add", "pod-a", 7), ("add", "pod-b", 11), ("top", 2)),
     "why": {"t": "Accumulate", "d": "Repeated adds sum into one total; 12 beats 11."}},
    {"args": ops(("reset", "never-seen"), ("add", "pod-a", 1), ("reset", "pod-a"), ("reset", "pod-a"), ("top", 1)),
     "why": {"t": "Reset unknown or twice", "d": "Resetting a missing key is a no-op."}},
    {"args": ops(("add", "pod-a", 3), ("reset", "pod-a"), ("add", "pod-a", 2), ("top", 1)),
     "why": {"t": "Reset then re-add", "d": "A key starts again from 0 after a reset."}},
    {"args": ops(("add", "b", 10), ("add", "a", 10), ("add", "c", 9), ("top", 2), ("top", 3)),
     "why": {"t": "Tie at the cut", "d": "The tie-break decides which of two equal totals makes the top k."}},
    {"args": ops(("add", "ratelimit:key-4f1c", 4200), ("add", "ratelimit:key-0a9e", 3900), ("add", "ratelimit:key-77d2", 150),
                 ("add", "ratelimit:key-0a9e", 600), ("top", 2), ("top_total", 2)),
     "why": {"t": "Rate-limit board", "d": "API keys hitting rate limits; a late burst moves key-0a9e to first place."}},
    {"args": _large(),
     "why": {"t": "Large input", "d": "700 random adds, resets and top-k queries over 150 pods."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Hash map + size-k heap (Optimal)",
     "description": "Keep a dict of running totals. top(k) takes the k smallest (-total, key) pairs with heapq.nsmallest, which keeps a heap of size k and handles the tie-break.",
     "time": "O(1) add/reset, O(n log k) top", "space": "O(n)",
     "keyPoints": ["Totals live in one dict; add and reset are O(1)", "nsmallest on (-total, key) sorts by total desc, then key asc", "A heap of size k beats sorting all n keys"]},
    {"name": "Sort every time", "slow": True,
     "description": "Sort all keys by (-total, key) on each top call and take the first k.",
     "time": "O(n log n) per top", "space": "O(n)",
     "keyPoints": ["Simplest correct answer", "Wasteful when n is large and k is small"],
     "code": '''from __future__ import annotations


class NoisyBoard:
    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    def add(self, key: str, amount: int) -> None:
        self._counts[key] = self._counts.get(key, 0) + amount

    def reset(self, key: str) -> None:
        self._counts.pop(key, None)

    def top(self, k: int) -> list[tuple[str, int]]:
        return sorted(self._counts.items(), key=lambda kv: (-kv[1], kv[0]))[:k]

    def top_total(self, k: int) -> int:
        return sum(total for _, total in self.top(k))
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Sort all keys", "idea": "Sort every (key, total) by total descending on each query.",
     "time": "O(n log n) per query", "space": "O(n)", "use": "Few keys or rare queries."},
    {"name": "Heap of size k", "idea": "heapq.nsmallest(k, ...) keeps only k candidates while scanning.",
     "time": "O(n log k) per query", "space": "O(n + k)", "use": "Many keys, small k: a live dashboard."},
]

VARIANT_TITLE = "Noisy-pod leaderboard"
VARIANT_APPROACH = "Hash map + size-k heap · O(1) add, O(n log k) top · O(n)"


def _sig_large():
    rng = random.Random(692)
    sigs = [f"E{c:02d}:{w}" for c in range(40) for w in ("timeout", "oom", "refused")]
    return [rng.choice(sigs[: rng.randint(10, len(sigs))]) for _ in range(900)]


def _kth_large():
    rng = random.Random(703)
    calls = [("KthLoudest", 5)] + [("add", rng.randint(1, 5000)) for _ in range(600)]
    return {"ops": [c[0] for c in calls], "vals": [[c[1]] for c in calls]}


def kops(k, *values):
    return {"ops": ["KthLoudest"] + ["add"] * len(values), "vals": [[k]] + [[v] for v in values]}


VARIANTS = [
    {
        "key": "top-error-signatures",
        "title": "Top error signatures",
        "approach": "Counter + heap of size k · O(n + u log k) · O(u)",
        "spec": {"kind": "fn", "fn": "top_signatures", "params": ["lines", "k"]},
        "statement": (
            "An incident bot posts the most common error signatures from the last deploy's logs. Each entry of "
            "`lines` is one normalized signature, such as `\"E503:upstream\"`.\n\n"
            "Return the `k` most frequent signatures as `[signature, count]` pairs, most frequent first. Break ties "
            "by signature in ascending order. If there are fewer than `k` distinct signatures, return them all."
        ),
        "examples": [
            {"args": {"lines": ["oom", "timeout", "oom", "refused", "timeout", "oom"], "k": 2},
             "explanation": "oom appears 3 times and timeout 2 times; refused (1) misses the cut.",
             "why": {"t": "Ranking", "d": "Plain frequency ranking."}},
            {"args": {"lines": ["b", "a", "c", "a", "b", "c"], "k": 2},
             "explanation": "All three appear twice, so the two alphabetically first win: a, b.",
             "why": {"t": "Tie at the cut", "d": "The tie-break decides who makes the top k."}},
        ],
        "constraints": ["0 ≤ len(lines) ≤ 10^5", "1 ≤ k ≤ 10^4", "Signatures are non-empty strings"],
        "hints": [
            "Count first with a dictionary; ranking is a separate step.",
            "Rank by the key (-count, signature) so one ordering handles both rules.",
            "heapq.nsmallest(k, ...) keeps only k candidates while scanning the counts.",
        ],
        "tests": [
            {"args": {"lines": [], "k": 3}, "why": {"t": "No logs", "d": "Nothing to rank: []."}},
            {"args": {"lines": ["E1"], "k": 1}, "why": {"t": "Single line", "d": "One signature is its own top 1."}},
            {"args": {"lines": ["x", "y", "x"], "k": 10}, "why": {"t": "k larger than distinct", "d": "Returns every signature."}},
            {"args": {"lines": ["z", "z", "y", "y", "x"], "k": 1}, "why": {"t": "Tie at the top", "d": "y beats z on name."}},
            {"args": {"lines": ["E503:upstream"] * 4 + ["E500:panic"] * 4 + ["E429:ratelimit"] * 5, "k": 3},
             "why": {"t": "Deploy triage", "d": "Rate limiting leads, then a tie resolved by name."}},
            {"args": {"lines": _sig_large(), "k": 7}, "why": {"t": "Large input", "d": "900 lines over 120 signatures."}},
        ],
        "solutions": [
            {"name": "Counter + nsmallest (Optimal)",
             "description": "Count every signature, then take the k smallest (-count, signature) pairs with a size-k heap.",
             "time": "O(n + u log k)", "space": "O(u)",
             "keyPoints": ["Counting is linear in the log lines", "One sort key covers count and tie-break", "Heap of size k beats sorting u signatures"],
             "code": '''import heapq
from collections import Counter


def top_signatures(lines, k):
    counts = Counter(lines)
    best = heapq.nsmallest(k, ((-c, s) for s, c in counts.items()))
    return [[s, -c] for c, s in best]
'''},
            {"name": "Count by scanning, then sort", "slow": True,
             "description": "For each distinct signature, count it with a full pass over the lines, then sort all of them.",
             "time": "O(n · u + u log u)", "space": "O(u)",
             "keyPoints": ["No hash-map counting", "Quadratic when there are many distinct signatures"],
             "code": '''def top_signatures(lines, k):
    distinct = sorted(set(lines))
    ranked = sorted(([s, lines.count(s)] for s in distinct), key=lambda p: (-p[1], p[0]))
    return ranked[:k]
'''},
        ],
        "starter": '''def top_signatures(lines: list[str], k: int) -> list[list]:
    """The k most frequent signatures as [signature, count], ties by name."""
    raise NotImplementedError
''',
    },
    {
        "key": "kth-loudest-threshold",
        "title": "Paging threshold: k-th loudest",
        "approach": "Min-heap of the k largest · O(log k) per add · O(k)",
        "spec": {"kind": "design", "fn": "KthLoudest", "params": []},
        "statement": (
            "An alerting rule pages only when a pod's error rate is among the `k` worst seen so far. The threshold is "
            "the **k-th largest** rate reported to date.\n\n"
            "Build `KthLoudest(k)` with one method:\n\n"
            "- `add(rate)`: record a new rate and return the current k-th largest rate, counting duplicates. If fewer "
            "than `k` rates have been recorded, return `-1`."
        ),
        "examples": [
            {"args": kops(3, 4, 5, 8, 2, 10, 9),
             "explanation": "After 4, 5 there are only two rates: -1, -1. Then 4 (of 8,5,4), 4, 5 (of 10,8,5), 8 (of 10,9,8).",
             "why": {"t": "Threshold rises", "d": "Small rates stop mattering once k larger ones exist."}},
        ],
        "constraints": ["1 ≤ k ≤ 10^4", "0 ≤ rate ≤ 10^6", "Up to 10^5 add calls"],
        "hints": [
            "Only the k largest rates can ever be the answer again.",
            "Keep them in a min-heap of size k: its top is the k-th largest.",
            "When the heap is full, a new rate replaces the top only if it is larger.",
        ],
        "tests": [
            {"args": kops(1, 7), "why": {"t": "k = 1", "d": "The threshold is the maximum."}},
            {"args": kops(2, 5), "why": {"t": "Not enough rates", "d": "One rate with k = 2 returns -1."}},
            {"args": kops(2, 3, 3, 3, 1), "why": {"t": "Duplicates", "d": "Equal rates count separately."}},
            {"args": kops(3, 9, 8, 7, 6, 5, 4), "why": {"t": "Falling rates", "d": "Smaller rates never change the threshold."}},
            {"args": kops(2, 0, 0, 1000000, 0), "why": {"t": "Boundaries", "d": "Zero and the largest allowed rate."}},
            {"args": _kth_large(), "why": {"t": "Large input", "d": "600 random rates with k = 5."}},
        ],
        "solutions": [
            {"name": "Size-k min-heap (Optimal)",
             "description": "Push each rate; if the heap grows past k, pop the smallest. With k items, the top is the k-th largest.",
             "time": "O(log k) per add", "space": "O(k)",
             "keyPoints": ["The heap holds only the k largest rates", "heappushpop keeps it at size k", "Return -1 until k rates have arrived"],
             "code": '''import heapq


class KthLoudest:
    def __init__(self, k):
        self.k = k
        self.heap = []

    def add(self, rate):
        if len(self.heap) < self.k:
            heapq.heappush(self.heap, rate)
        elif rate > self.heap[0]:
            heapq.heapreplace(self.heap, rate)
        return self.heap[0] if len(self.heap) == self.k else -1
'''},
            {"name": "Keep a sorted list", "slow": True,
             "description": "Insert every rate into a sorted list and read the element k from the end.",
             "time": "O(n) per add", "space": "O(n)",
             "keyPoints": ["Keeps every rate forever", "Insertion shifts the list on each add"],
             "code": '''import bisect


class KthLoudest:
    def __init__(self, k):
        self.k = k
        self.rates = []

    def add(self, rate):
        bisect.insort(self.rates, rate)
        return self.rates[-self.k] if len(self.rates) >= self.k else -1
'''},
        ],
        "starter": '''class KthLoudest:
    def __init__(self, k: int) -> None:
        pass

    def add(self, rate: int) -> int:
        """Record rate; return the k-th largest so far, or -1."""
        raise NotImplementedError
''',
    },
]
