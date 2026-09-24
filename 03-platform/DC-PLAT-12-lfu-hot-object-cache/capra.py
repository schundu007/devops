"""Capra Playground export for DC-PLAT-12 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "design", "fn": "LFUCache", "params": [], "types": {}, "ret": "value", "cmp": "exact"}


def ops(capacity, *calls):
    return {"ops": ["LFUCache"] + [c[0] for c in calls], "vals": [[capacity]] + [list(c[1:]) for c in calls]}


EXAMPLES = [
    {"args": ops(2, ("put", "a", "1"), ("put", "b", "2"), ("get", "a"), ("put", "c", "3"), ("get", "b"), ("get", "a"), ("get", "c")),
     "explanation": "a was read once, so it has 2 uses and b has 1. Adding c evicts b, the least frequently used.",
     "why": {"t": "Evict least frequent", "d": "The key with the fewest uses leaves first."}},
    {"args": ops(2, ("put", "a", "1"), ("put", "b", "2"), ("put", "c", "3"), ("get", "a"), ("get", "b"), ("get", "c")),
     "explanation": "a and b both have 1 use. On a tie the one touched longest ago, a, is evicted.",
     "why": {"t": "Tie → least recent", "d": "Among equal counts, the oldest touch is evicted."}},
]


def _large():
    rng = random.Random(460)
    keys = [f"obj-{i}" for i in range(40)]
    calls = []
    for i in range(700):
        k = keys[min(int(rng.expovariate(0.15)), 39)]  # a few hot objects, a long cold tail
        calls.append(("get", k) if rng.random() < 0.6 else ("put", k, f"v{i}"))
    return ops(10, *calls)


TESTS = [
    {"args": ops(0, ("put", "a", "1"), ("get", "a")),
     "why": {"t": "Capacity 0", "d": "A zero-size cache stores nothing."}},
    {"args": ops(1, ("put", "a", "1"), ("get", "a"), ("put", "b", "2"), ("get", "a"), ("get", "b")),
     "why": {"t": "Capacity 1", "d": "Every new key evicts the only one, whatever its count."}},
    {"args": ops(2, ("get", "missing")),
     "why": {"t": "Miss", "d": "A missing key returns None."}},
    {"args": ops(2, ("put", "a", "1"), ("put", "a", "9"), ("put", "b", "2"), ("put", "c", "3"), ("get", "a"), ("get", "b"), ("get", "c")),
     "why": {"t": "Update counts as use", "d": "Updating a key's value also counts as a use, so a survives."}},
    {"args": ops(3, ("put", "a", "1"), ("get", "a"), ("get", "a"), ("put", "b", "2"), ("put", "c", "3"), ("put", "d", "4"), ("get", "b"), ("get", "c"), ("get", "d"), ("get", "a")),
     "why": {"t": "New key is least frequent", "d": "After an eviction, the new key starts at 1 use; min frequency resets to 1."}},
    {"args": ops(2, ("put", "x", "1"), ("get", "x"), ("put", "y", "2"), ("get", "y"), ("put", "z", "3"), ("get", "x"), ("get", "y"), ("get", "z")),
     "why": {"t": "Tie at higher count", "d": "x and y both have 2 uses; x was touched longer ago and is evicted."}},
    {"args": ops(3, ("put", "/img/logo.png", "L"), ("put", "/css/app.css", "C"), *[("get", "/img/logo.png")] * 3,
                 ("put", "/tmp/a", "A"), ("put", "/tmp/b", "B"), ("get", "/img/logo.png"), ("get", "/css/app.css"), ("get", "/tmp/a"), ("get", "/tmp/b")),
     "why": {"t": "CDN edge", "d": "A hot logo survives a burst of one-off objects; the cold stylesheet is evicted."}},
    {"args": _large(),
     "why": {"t": "Large input", "d": "700 operations on 40 keys with a few hot objects."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Frequency buckets of ordered sets (Optimal)",
     "description": "Keep value and freq per key, and buckets[f] as an ordered set of keys with f uses (oldest first). Track min_freq; evict the oldest key in buckets[min_freq].",
     "time": "O(1) average get and put", "space": "O(capacity)",
     "keyPoints": ["A touch moves a key to the end of the next bucket", "min_freq only moves up by one or resets to 1", "A new key always starts at frequency 1"]},
    {"name": "Scan for the victim", "slow": True,
     "description": "Store a use count and last-use tick per key, and scan every key for the smallest (count, tick) on each eviction.",
     "time": "O(1) get, O(n) put when full", "space": "O(capacity)",
     "keyPoints": ["Easy to verify", "Every eviction scans the whole cache"],
     "code": '''from __future__ import annotations


class LFUCache:
    def __init__(self, capacity: int) -> None:
        self.cap = capacity
        self.data: dict[str, list] = {}  # key -> [value, uses, last_tick]
        self.tick = 0

    def get(self, key: str) -> str | None:
        if key not in self.data:
            return None
        self.tick += 1
        e = self.data[key]
        e[1] += 1
        e[2] = self.tick
        return e[0]

    def put(self, key: str, value: str) -> None:
        if self.cap <= 0:
            return
        self.tick += 1
        if key in self.data:
            e = self.data[key]
            e[0] = value
            e[1] += 1
            e[2] = self.tick
            return
        if len(self.data) >= self.cap:
            victim = min(self.data, key=lambda k: (self.data[k][1], self.data[k][2]))
            del self.data[victim]
        self.data[key] = [value, 1, self.tick]
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Scan for the victim", "idea": "Count uses and last-use time per key; scan all keys on eviction.",
     "time": "O(n) per eviction", "space": "O(capacity)", "use": "Small caches or a first version."},
    {"name": "Frequency buckets", "idea": "One ordered set per use count plus a min-frequency pointer.",
     "time": "O(1) per operation", "space": "O(capacity)", "use": "Edge and CDN caches under heavy churn."},
]
