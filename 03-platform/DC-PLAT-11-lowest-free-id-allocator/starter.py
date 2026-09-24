"""DC-PLAT-11 Lowest Free ID Allocator — your attempt.

Run your code against the tests:
    make try CHIP=03-platform/DC-PLAT-11-lowest-free-id-allocator
"""
from __future__ import annotations


class IdAllocator:
    def __init__(self, size: int, base: int = 0) -> None:
        """Manage the IDs base, base+1, ..., base+size-1 (size may be 0)."""
        # TODO
        raise NotImplementedError

    def allocate(self) -> int | None:
        """Hand out the smallest ID that is not in use, or None if all are in use."""
        # TODO
        raise NotImplementedError

    def release(self, id_: int) -> None:
        """Return id_ to the pool. Raise ValueError if id_ is not currently allocated
        (a double release, or an ID outside the pool)."""
        # TODO
        raise NotImplementedError
