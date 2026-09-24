"""DC-PLAT-06 Image Cache with LRU Eviction — your attempt.  (added: the handbook has no stored starter)

Signatures match Source: Handbook #88 LRU Cache.
Run your code against the tests:
    make try CHIP=03-platform/DC-PLAT-06-image-cache-lru
"""


class LRUCache:
    def __init__(self, capacity: int):
        """Keep at most `capacity` entries."""
        # TODO
        pass

    def get(self, key: int) -> int:
        """Value for key, or -1. A hit counts as a use."""
        # TODO
        raise NotImplementedError

    def put(self, key: int, value: int) -> None:
        """Insert or overwrite (a use). Over capacity: evict the least recently used key."""
        # TODO
        raise NotImplementedError
