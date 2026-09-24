"""DC-PLAT-14 Deadlock-Free Lock Ordering — your attempt.

Use the threading module. Run your code against the tests:
    make try CHIP=03-platform/DC-PLAT-14-deadlock-free-lock-ordering
"""
from __future__ import annotations

from typing import Callable

Action = Callable[[], None]


class LockTable:
    """n workers sit in a ring over n shared locks.

    Worker i needs lock i (its "left" lock) and lock (i + 1) % n (its "right" lock).
    """

    def __init__(self, n: int) -> None:
        """Create the n locks. Raise ValueError if n < 2."""
        # TODO
        raise NotImplementedError

    def run_job(self, worker: int, take_left: Action, take_right: Action,
                work: Action, release_left: Action, release_right: Action) -> None:
        """Called by worker's own thread, many times, concurrently with other workers.

        Hold both of the worker's locks while calling work(). Call take_left /
        take_right right after acquiring that lock, and release_left / release_right
        right before releasing it. Must never deadlock, whatever the interleaving.
        """
        # TODO
        raise NotImplementedError
