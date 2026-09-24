"""DC-PLAT-13 Backpressure Queue — reference solution."""
from __future__ import annotations

import threading
from collections import deque
from typing import Any


class BoundedBlockingQueue:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self._capacity = capacity
        self._items: deque[Any] = deque()
        # Two conditions share one lock: producers wait on "not full",
        # consumers wait on "not empty".
        lock = threading.Lock()
        self._not_full = threading.Condition(lock)
        self._not_empty = threading.Condition(lock)

    def enqueue(self, item: Any) -> None:
        """Add item at the back; block while the queue is full."""
        with self._not_full:
            # A while loop, not an if: re-check after every wake-up.
            while len(self._items) >= self._capacity:
                self._not_full.wait()
            self._items.append(item)
            self._not_empty.notify()  # wake one waiting consumer

    def dequeue(self) -> Any:
        """Remove and return the front item; block while the queue is empty."""
        with self._not_empty:
            while not self._items:
                self._not_empty.wait()
            item = self._items.popleft()
            self._not_full.notify()   # wake one waiting producer
            return item

    def size(self) -> int:
        with self._not_full:
            return len(self._items)
