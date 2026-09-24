"""Tests for DC-PLAT-12 Hot-Object Cache (LFU)."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


class BruteLFU:
    """Independent reference: store (uses, last_use_tick) and scan on eviction."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.data: dict[str, list] = {}  # key -> [value, uses, last_tick]
        self.tick = 0

    def get(self, key: str):
        self.tick += 1
        if key not in self.data:
            return None
        entry = self.data[key]
        entry[1] += 1
        entry[2] = self.tick
        return entry[0]

    def put(self, key: str, value: str) -> None:
        self.tick += 1
        if self.capacity <= 0:
            return
        if key in self.data:
            entry = self.data[key]
            entry[0] = value
            entry[1] += 1
            entry[2] = self.tick
            return
        if len(self.data) >= self.capacity:
            victim = min(self.data, key=lambda k: (self.data[k][1], self.data[k][2]))
            del self.data[victim]
        self.data[key] = [value, 1, self.tick]


def test_evicts_least_frequent():
    c = impl.LFUCache(2)
    c.put("/img/logo.png", "v1")
    c.put("/js/app.js", "v1")
    assert c.get("/img/logo.png") == "v1"      # logo: 2 uses, app.js: 1
    c.put("/css/site.css", "v1")               # evicts app.js
    assert c.get("/js/app.js") is None
    assert c.get("/img/logo.png") == "v1"
    assert c.get("/css/site.css") == "v1"


def test_tie_breaks_by_oldest_use():
    c = impl.LFUCache(2)
    c.put("a", "1")
    c.put("b", "2")          # both used once; a is older
    c.put("c", "3")          # evicts a
    assert c.get("a") is None
    assert c.get("b") == "2" and c.get("c") == "3"


def test_zero_and_one_capacity():
    zero = impl.LFUCache(0)
    zero.put("k", "v")
    assert zero.get("k") is None
    one = impl.LFUCache(1)
    one.put("k", "v")
    one.get("k")
    one.put("j", "w")        # boundary: even a hot key goes when capacity is 1
    assert one.get("k") is None and one.get("j") == "w"


def test_update_counts_as_use_and_keeps_value():
    c = impl.LFUCache(2)
    c.put("a", "1")
    c.put("b", "2")
    c.put("a", "1b")         # a: 2 uses now
    c.put("c", "3")          # evicts b
    assert c.get("a") == "1b"
    assert c.get("b") is None


def test_new_key_resets_min_frequency():
    # After many hits, the only low-frequency key is the new one; it must be the victim.
    c = impl.LFUCache(2)
    c.put("hot", "x")
    for _ in range(5):
        c.get("hot")
    c.put("new1", "y")
    c.put("new2", "z")       # evicts new1 (1 use), not hot (6 uses)
    assert c.get("hot") == "x" and c.get("new1") is None and c.get("new2") == "z"


def test_edge_cache_keeps_popular_assets_through_a_scan():
    # Production flavour: an edge node caches 3 objects. Two assets are hot;
    # a crawler then walks 50 one-off URLs. LFU keeps the hot assets (LRU would not).
    c = impl.LFUCache(3)
    for _ in range(20):
        c.put("/static/app.js", "js")
        c.put("/static/app.css", "css")
    for i in range(50):
        c.put(f"/blog/post-{i}", "html")
    assert c.get("/static/app.js") == "js"
    assert c.get("/static/app.css") == "css"


def test_large_random_matches_brute_force():
    rng = random.Random(460)
    for capacity in (1, 2, 10, 50):
        c, ref = impl.LFUCache(capacity), BruteLFU(capacity)
        keys = [f"k{i}" for i in range(capacity * 3 + 2)]
        for step in range(8_000):
            k = rng.choice(keys)
            if rng.random() < 0.5:
                assert c.get(k) == ref.get(k), (capacity, step)
            else:
                v = str(step)
                c.put(k, v)
                ref.put(k, v)
