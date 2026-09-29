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

VARIANT_TITLE = "LFU hot-object cache"
VARIANT_APPROACH = "Frequency buckets of ordered sets · O(1) per operation · O(capacity)"

_HOT_FAST = '''from __future__ import annotations

from collections import OrderedDict, defaultdict


class HotKeys:
    def __init__(self) -> None:
        self._count: dict[str, int] = {}
        self._buckets: defaultdict[int, OrderedDict[str, None]] = defaultdict(OrderedDict)
        self._max = 0

    def hit(self, key: str) -> int:
        f = self._count.get(key, 0)
        if f:
            bucket = self._buckets[f]
            del bucket[key]
            if not bucket:
                del self._buckets[f]
        self._count[key] = f + 1
        self._buckets[f + 1][key] = None
        if f + 1 > self._max:
            self._max = f + 1
        return f + 1

    def count(self, key: str) -> int:
        return self._count.get(key, 0)

    def top(self) -> str | None:
        if not self._max:
            return None
        return next(iter(self._buckets[self._max]))
'''

_HOT_SLOW = '''from __future__ import annotations


class HotKeys:
    def __init__(self) -> None:
        self._count: dict[str, int] = {}
        self._last: dict[str, int] = {}
        self._tick = 0

    def hit(self, key: str) -> int:
        self._tick += 1
        self._count[key] = self._count.get(key, 0) + 1
        self._last[key] = self._tick
        return self._count[key]

    def count(self, key: str) -> int:
        return self._count.get(key, 0)

    def top(self) -> str | None:
        if not self._count:
            return None
        return min(self._count, key=lambda k: (-self._count[k], self._last[k]))
'''

_PIN_FAST = '''from __future__ import annotations

from collections import OrderedDict, defaultdict


class PinnedLFUCache:
    def __init__(self, capacity: int) -> None:
        self._capacity = capacity
        self._value: dict[str, str] = {}
        self._pinned: set[str] = set()
        self._freq: dict[str, int] = {}
        self._buckets: defaultdict[int, OrderedDict[str, None]] = defaultdict(OrderedDict)
        self._min_freq = 0

    def _touch(self, key: str) -> None:
        f = self._freq[key]
        bucket = self._buckets[f]
        del bucket[key]
        if not bucket:
            del self._buckets[f]
            if self._min_freq == f:
                self._min_freq = f + 1
        self._freq[key] = f + 1
        self._buckets[f + 1][key] = None

    def get(self, key: str) -> str | None:
        if key not in self._value:
            return None
        if key not in self._pinned:
            self._touch(key)
        return self._value[key]

    def put(self, key: str, value: str, pinned: bool) -> None:
        if self._capacity <= 0:
            return
        if key in self._value:
            self._value[key] = value
            if key not in self._pinned:
                self._touch(key)
            return
        if len(self._value) >= self._capacity:
            if not self._freq:
                return
            coldest = self._buckets[self._min_freq]
            victim, _ = coldest.popitem(last=False)
            if not coldest:
                del self._buckets[self._min_freq]
            del self._value[victim]
            del self._freq[victim]
        self._value[key] = value
        if pinned:
            self._pinned.add(key)
            if self._freq and self._min_freq not in self._buckets:
                self._min_freq = min(self._buckets)
            return
        self._freq[key] = 1
        self._buckets[1][key] = None
        self._min_freq = 1
'''

_PIN_SLOW = '''from __future__ import annotations


class PinnedLFUCache:
    def __init__(self, capacity: int) -> None:
        self.cap = capacity
        self.data: dict[str, list] = {}
        self.tick = 0

    def get(self, key: str) -> str | None:
        if key not in self.data:
            return None
        e = self.data[key]
        if not e[3]:
            self.tick += 1
            e[1] += 1
            e[2] = self.tick
        return e[0]

    def put(self, key: str, value: str, pinned: bool) -> None:
        if self.cap <= 0:
            return
        self.tick += 1
        if key in self.data:
            e = self.data[key]
            e[0] = value
            if not e[3]:
                e[1] += 1
                e[2] = self.tick
            return
        if len(self.data) >= self.cap:
            loose = [k for k in self.data if not self.data[k][3]]
            if not loose:
                return
            victim = min(loose, key=lambda k: (self.data[k][1], self.data[k][2]))
            del self.data[victim]
        self.data[key] = [value, 1, self.tick, pinned]
'''


def _hops(*calls):
    return {"ops": ["HotKeys"] + [c[0] for c in calls], "vals": [[]] + [list(c[1:]) for c in calls]}


def _pops(capacity, *calls):
    return {"ops": ["PinnedLFUCache"] + [c[0] for c in calls], "vals": [[capacity]] + [list(c[1:]) for c in calls]}


def _hot_large():
    rng = random.Random(1201)
    keys = [f"shard-{i}" for i in range(30)]
    calls = []
    for _ in range(600):
        r = rng.random()
        k = keys[min(int(rng.expovariate(0.2)), 29)]
        calls.append(("hit", k) if r < 0.8 else ("top",) if r < 0.93 else ("count", k))
    return _hops(*calls)


def _pin_large():
    rng = random.Random(1202)
    keys = [f"obj-{i}" for i in range(30)]
    calls = [("put", "/config/flags.json", "F", True), ("put", "/config/routes.json", "R", True)]
    for i in range(500):
        k = keys[min(int(rng.expovariate(0.15)), 29)]
        calls.append(("get", k) if rng.random() < 0.6 else ("put", k, f"v{i}", rng.random() < 0.03))
    calls += [("get", "/config/flags.json"), ("get", "/config/routes.json")]
    return _pops(8, *calls)


VARIANTS = [
    {
        "key": "hot-keys",
        "title": "Hottest shard key tracker",
        "approach": "Count buckets of ordered sets plus a max pointer · O(1) per call · O(keys)",
        "spec": {"kind": "design", "fn": "HotKeys", "params": []},
        "statement": (
            "A Redis cluster slows down when one key takes most of the traffic. The proxy tracks hits and must name the hottest key at any moment. "
            "Build `HotKeys` with:\n\n"
            "- `hit(key)`: count one request for `key` and return its new count\n"
            "- `count(key)`: the key's count, 0 if never seen\n"
            "- `top()`: the key with the most hits; on a tie, the one that **reached** that count first; `None` if there are no hits\n\n"
            "Every call must be O(1): this runs on every request."
        ),
        "examples": [
            {"args": _hops(("hit", "user:1"), ("hit", "user:2"), ("top",), ("hit", "user:2"), ("top",), ("hit", "user:1"), ("top",)),
             "explanation": "user:1 reached 1 first. Then user:2 reaches 2 first, and keeps the top spot when user:1 ties it at 2.",
             "why": {"t": "Tie goes to the first to arrive", "d": "The count bucket keeps keys in the order they reached it."}},
        ],
        "constraints": ["0 ≤ calls ≤ 1,000", "keys are non-empty strings"],
        "hints": [
            "Reuse the LFU buckets: `buckets[c]` is an ordered set of keys whose count is exactly `c`, in the order they got there.",
            "A hit moves the key to the end of the next bucket.",
            "Counts only go up, so the max pointer only moves up; `top()` is the first key of `buckets[max]`.",
        ],
        "tests": [
            {"args": _hops(("top",)), "why": {"t": "Empty", "d": "No hits yet, so there is no top key."}},
            {"args": _hops(("count", "nope"), ("hit", "a"), ("count", "a")), "why": {"t": "Unknown key", "d": "count is 0 before the first hit."}},
            {"args": _hops(("hit", "a"), ("hit", "a"), ("hit", "a"), ("top",)), "why": {"t": "Single key", "d": "One key is always the top."}},
            {"args": _hops(("hit", "a"), ("hit", "b"), ("hit", "c"), ("top",), ("hit", "c"), ("hit", "b"), ("hit", "b"), ("top",)),
             "why": {"t": "Overtaken", "d": "b passes c after c briefly led."}},
            {"args": _hops(("hit", "x"), ("hit", "y"), ("hit", "y"), ("hit", "x"), ("top",), ("hit", "x"), ("top",)),
             "why": {"t": "Tie at a higher count", "d": "y reached 2 before x did."}},
            {"args": _hops(*[("hit", f"k{i % 5}") for i in range(25)], ("top",), ("count", "k4")),
             "why": {"t": "All tied", "d": "Five keys with 5 hits each; k0 got there first."}},
            {"args": _hot_large(), "why": {"t": "Larger input", "d": "600 calls on 30 keys with a few hot ones."}},
        ],
        "solutions": [
            {"name": "Count buckets with a max pointer (Optimal)",
             "description": "Keep count per key and buckets[c] as an ordered set. A hit moves the key into bucket c + 1 at its end and raises max if needed; top reads the first key of buckets[max].",
             "time": "O(1) per call", "space": "O(keys)",
             "keyPoints": ["Same bucket move as the LFU touch", "The max only ever rises", "Bucket order breaks ties"],
             "code": _HOT_FAST},
            {"name": "Scan for the top", "slow": True,
             "description": "Store count and last-hit tick per key; top scans every key for the highest count and, on a tie, the earliest last hit.",
             "time": "O(1) hit, O(keys) top", "space": "O(keys)",
             "keyPoints": ["A key reaches its count on its last hit", "Every top call scans all keys"],
             "code": _HOT_SLOW},
        ],
        "starter": "class HotKeys:\n    def __init__(self) -> None:\n        pass\n\n    def hit(self, key: str) -> int:\n        pass\n\n    def count(self, key: str) -> int:\n        pass\n\n    def top(self) -> str | None:\n        pass\n",
    },
    {
        "key": "pinned-objects",
        "title": "LFU with pinned objects",
        "approach": "Frequency buckets for unpinned keys only · O(1) per operation · O(capacity)",
        "spec": {"kind": "design", "fn": "PinnedLFUCache", "params": []},
        "statement": (
            "The edge cache holds a few objects that must never be evicted (feature-flag and routing configs). "
            "Build `PinnedLFUCache(capacity)` with `get(key)` and `put(key, value, pinned)`:\n\n"
            "- `pinned` only matters when the key is first inserted; a pinned key is never evicted and its uses are not counted\n"
            "- unpinned keys follow the LFU rule of the main problem (fewest uses, then touched longest ago)\n"
            "- pinned keys still take up capacity; if the cache is full and **every** key is pinned, the new key is not stored\n\n"
            "`get` returns the value or `None`. Updating an existing key's value counts as a use."
        ),
        "examples": [
            {"args": _pops(2, ("put", "flags", "F", True), ("put", "a", "1", False), ("put", "b", "2", False), ("get", "flags"), ("get", "a"), ("get", "b")),
             "explanation": "The cache is full with flags (pinned) and a, so adding b evicts a, never flags.",
             "why": {"t": "Pinned survives", "d": "Only unpinned keys are eviction candidates."}},
        ],
        "constraints": ["0 ≤ capacity ≤ 50", "0 ≤ calls ≤ 600"],
        "hints": [
            "Keep pinned keys out of the frequency buckets entirely; they only live in the value map.",
            "When full, if no unpinned key exists there is nothing to evict: drop the insert.",
            "Only an unpinned insert resets min_freq to 1; a pinned insert leaves it alone.",
        ],
        "tests": [
            {"args": _pops(0, ("put", "a", "1", True), ("get", "a")), "why": {"t": "Capacity 0", "d": "Nothing is stored, pinned or not."}},
            {"args": _pops(1, ("put", "p", "P", True), ("put", "a", "1", False), ("get", "p"), ("get", "a")),
             "why": {"t": "All pinned", "d": "The only slot is pinned, so the new key is dropped."}},
            {"args": _pops(2, ("put", "a", "1", False), ("put", "a", "2", True), ("put", "b", "3", False), ("put", "c", "4", False), ("get", "a"), ("get", "b"), ("get", "c")),
             "why": {"t": "Pin flag on update", "d": "pinned is ignored for an existing key, so a stays evictable but has 2 uses."}},
            {"args": _pops(3, ("put", "p", "P", True), ("get", "p"), ("get", "p"), ("put", "a", "1", False), ("put", "b", "2", False), ("get", "a"), ("put", "c", "3", False), ("get", "b"), ("get", "c"), ("get", "p")),
             "why": {"t": "Pinned hits not counted", "d": "Reads of a pinned key do not change which unpinned key leaves."}},
            {"args": _pops(2, ("get", "missing")), "why": {"t": "Miss", "d": "A missing key returns None."}},
            {"args": _pops(3, ("put", "x", "1", False), ("get", "x"), ("put", "y", "2", False), ("get", "y"), ("put", "p", "P", True), ("put", "z", "3", False), ("get", "x"), ("get", "y"), ("get", "z")),
             "why": {"t": "Tie among unpinned", "d": "x and y both have 2 uses; x was touched longer ago and leaves."}},
            {"args": _pin_large(), "why": {"t": "Larger input", "d": "500 operations with two pinned configs that must survive."}},
        ],
        "solutions": [
            {"name": "Buckets for unpinned keys (Optimal)",
             "description": "The main problem's LFU structure, but pinned keys live only in the value map. Eviction pops the oldest key in buckets[min_freq]; with no unpinned keys the insert is dropped.",
             "time": "O(1) average per operation", "space": "O(capacity)",
             "keyPoints": ["Pinned keys never enter a bucket", "A pinned insert after an eviction may leave min_freq on an empty bucket: move it to the lowest bucket left", "An empty frequency map means nothing can be evicted"],
             "code": _PIN_FAST},
            {"name": "Scan unpinned keys for the victim", "slow": True,
             "description": "Store value, uses, last tick and the pinned flag per key; on eviction scan the unpinned keys for the smallest (uses, tick).",
             "time": "O(n) per eviction", "space": "O(capacity)",
             "keyPoints": ["Easy to check by hand", "Every eviction scans the cache"],
             "code": _PIN_SLOW},
        ],
        "starter": "class PinnedLFUCache:\n    def __init__(self, capacity: int) -> None:\n        pass\n\n    def get(self, key: str) -> str | None:\n        pass\n\n    def put(self, key: str, value: str, pinned: bool) -> None:\n        pass\n",
    },
]
