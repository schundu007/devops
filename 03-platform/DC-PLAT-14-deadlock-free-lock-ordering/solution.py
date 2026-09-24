"""DC-PLAT-14 Deadlock-Free Lock Ordering — reference solution."""
from __future__ import annotations

import threading
from typing import Callable

Action = Callable[[], None]


class LockTable:
    """n workers sit in a ring over n shared locks.

    Worker i needs lock i (its "left" lock) and lock (i + 1) % n (its "right" lock).
    """

    def __init__(self, n: int) -> None:
        if n < 2:
            raise ValueError("need at least 2 workers")
        self._n = n
        self._locks = [threading.Lock() for _ in range(n)]

    def run_job(self, worker: int, take_left: Action, take_right: Action,
                work: Action, release_left: Action, release_right: Action) -> None:
        left, right = worker, (worker + 1) % self._n
        # The rule: always acquire the lower-numbered lock first. With one global
        # order, no cycle of "I hold one, I wait for yours" can form.
        if left < right:
            first, second = left, right
            take_first, take_second = take_left, take_right
            release_first, release_second = release_left, release_right
        else:  # only the last worker, whose right lock wraps around to 0
            first, second = right, left
            take_first, take_second = take_right, take_left
            release_first, release_second = release_right, release_left

        with self._locks[first]:
            take_first()          # report right after acquiring
            with self._locks[second]:
                take_second()
                work()
                release_second()  # report right before releasing
            release_first()
