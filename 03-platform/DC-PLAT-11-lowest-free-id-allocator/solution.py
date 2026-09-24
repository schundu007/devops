"""DC-PLAT-11 Lowest Free ID Allocator — reference solution."""
from __future__ import annotations

import heapq


class IdAllocator:
    def __init__(self, size: int, base: int = 0) -> None:
        """Manage the IDs base, base+1, ..., base+size-1."""
        self._base = base
        self._size = size
        self._next = 0                  # offsets >= _next have never been handed out
        self._released: list[int] = []  # min-heap of returned offsets (all < _next)
        self._in_use: set[int] = set()

    def allocate(self) -> int | None:
        """Hand out the smallest free ID, or None if the pool is exhausted."""
        if self._released:
            # Every released offset is below _next, so the heap top is the smallest free.
            offset = heapq.heappop(self._released)
        elif self._next < self._size:
            offset = self._next
            self._next += 1
        else:
            return None
        self._in_use.add(offset)
        return self._base + offset

    def release(self, id_: int) -> None:
        """Return an ID to the pool. Releasing an ID that is not in use is an error."""
        offset = id_ - self._base
        if offset not in self._in_use:
            raise ValueError(f"id {id_} is not allocated")
        self._in_use.remove(offset)
        heapq.heappush(self._released, offset)
