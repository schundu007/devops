"""DC-PLAT-13 Backpressure Queue — your attempt.

Use the threading module (Lock / Condition). Do not use queue.Queue.
Run your code against the tests:
    make try CHIP=03-platform/DC-PLAT-13-backpressure-queue
"""
from __future__ import annotations

from typing import Any


class BoundedBlockingQueue:
    def __init__(self, capacity: int) -> None:
        """A FIFO queue holding at most `capacity` items. Raise ValueError if capacity < 1."""
        # TODO
        raise NotImplementedError

    def enqueue(self, item: Any) -> None:
        """Add item at the back. If the queue is full, block until there is room."""
        # TODO
        raise NotImplementedError

    def dequeue(self) -> Any:
        """Remove and return the front item. If the queue is empty, block until one arrives."""
        # TODO
        raise NotImplementedError

    def size(self) -> int:
        """Number of items currently in the queue."""
        # TODO
        raise NotImplementedError
