"""DC-PLAT-12 Hot-Object Cache (LFU) — your attempt.

Run your code against the tests:
    make try CHIP=03-platform/DC-PLAT-12-lfu-hot-object-cache
"""
from __future__ import annotations


class LFUCache:
    def __init__(self, capacity: int) -> None:
        """A cache holding at most `capacity` objects (capacity may be 0)."""
        # TODO
        raise NotImplementedError

    def get(self, key: str) -> str | None:
        """Return the value and count one use of key, or None if key is not cached."""
        # TODO
        raise NotImplementedError

    def put(self, key: str, value: str) -> None:
        """Insert or update key (an update also counts as one use).

        When inserting a new key into a full cache, first evict the key with the
        fewest uses; on a tie, evict the one whose last use is the oldest.
        Both calls must run in O(1) average time.
        """
        # TODO
        raise NotImplementedError
