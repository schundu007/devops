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
