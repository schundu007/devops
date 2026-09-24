"""DC-PLAT-12 Hot-Object Cache (LFU) — reference solution."""
from __future__ import annotations

from collections import OrderedDict, defaultdict


class LFUCache:
    def __init__(self, capacity: int) -> None:
        self._capacity = capacity
        self._value: dict[str, str] = {}
        self._freq: dict[str, int] = {}
        # freq -> keys with that freq, oldest touch first (an ordered set).
        self._buckets: defaultdict[int, OrderedDict[str, None]] = defaultdict(OrderedDict)
        self._min_freq = 0

    def _touch(self, key: str) -> None:
        """Move key from its frequency bucket to the next one, as the newest entry."""
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
        """Return the cached value (and count the hit), or None on a miss."""
        if key not in self._value:
            return None
        self._touch(key)
        return self._value[key]

    def put(self, key: str, value: str) -> None:
        """Insert or update. When full, evict the least frequently used key;
        on a tie, the one touched longest ago."""
        if self._capacity <= 0:
            return
        if key in self._value:
            self._value[key] = value
            self._touch(key)
            return
        if len(self._value) >= self._capacity:
            coldest = self._buckets[self._min_freq]
            victim, _ = coldest.popitem(last=False)  # oldest in the lowest bucket
            if not coldest:
                del self._buckets[self._min_freq]
            del self._value[victim]
            del self._freq[victim]
        self._value[key] = value
        self._freq[key] = 1
        self._buckets[1][key] = None
        self._min_freq = 1  # a brand-new key is always the least frequent
