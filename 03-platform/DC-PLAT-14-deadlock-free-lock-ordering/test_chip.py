"""Tests for DC-PLAT-14 Deadlock-Free Lock Ordering.

Deterministic by design. A shared recorder checks the safety invariants on every
callback (nobody takes a lock someone else holds; work() runs with both locks).
Deadlock is detected by joins with a deadline, never by timing the work. A
Barrier forces the worst-case interleaving ("everyone grabs their left lock at
once"), and one test proves that interleaving really deadlocks a naive version.
"""
from __future__ import annotations

import threading
import time
from typing import Callable

import pytest
from chip import load_impl

impl = load_impl(__file__)
JOIN_TIMEOUT = 10.0


class Ring:
    """Records who holds each lock and flags any violation."""

    def __init__(self, n: int) -> None:
        self.n = n
        self.guard = threading.Lock()
        self.holder: list[int | None] = [None] * n
        self.worked = [0] * n
        self.violations: list[tuple] = []

    def take(self, w: int, lock: int) -> None:
        with self.guard:
            if self.holder[lock] is not None:
                self.violations.append(("taken while held", w, lock, self.holder[lock]))
            self.holder[lock] = w

    def release(self, w: int, lock: int) -> None:
        with self.guard:
            if self.holder[lock] != w:
                self.violations.append(("released by non-holder", w, lock, self.holder[lock]))
            self.holder[lock] = None

    def work(self, w: int) -> None:
        with self.guard:
            left, right = w, (w + 1) % self.n
            if self.holder[left] != w or self.holder[right] != w:
                self.violations.append(("worked without both locks", w))
            self.worked[w] += 1


def run_ring(table, n: int, rounds: int,
             on_take_left: Callable[[int, int], None] | None = None):
    """Each worker thread calls run_job `rounds` times. Returns (ring, errors, stuck)."""
    ring = Ring(n)
    errors: list[BaseException] = []

    def worker(w: int) -> None:
        try:
            for r in range(rounds):
                def take_left(w=w, r=r) -> None:
                    ring.take(w, w)
                    if on_take_left:
                        on_take_left(w, r)
                table.run_job(
                    w,
                    take_left,
                    lambda w=w: ring.take(w, (w + 1) % n),
                    lambda w=w: ring.work(w),
                    lambda w=w: ring.release(w, w),
                    lambda w=w: ring.release(w, (w + 1) % n),
                )
        except BaseException as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(w,), daemon=True) for w in range(n)]
    for t in threads:
        t.start()
    deadline = time.monotonic() + JOIN_TIMEOUT
    for t in threads:
        t.join(max(0.0, deadline - time.monotonic()))
    return ring, errors, sum(t.is_alive() for t in threads)


def assert_clean(ring: Ring, errors, stuck: int, rounds: int) -> None:
    assert stuck == 0, "deadlock: threads still waiting after the deadline"
    assert not errors, errors
    assert not ring.violations, ring.violations[:5]
    assert ring.worked == [rounds] * ring.n


def everyone_grabs_left_at_once(n: int, barrier_timeout: float):
    """A hook that makes all workers try to hold their left lock at the same moment (round 0)."""
    barrier = threading.Barrier(n)

    def hook(w: int, r: int) -> None:
        if r == 0:
            try:
                barrier.wait(barrier_timeout)
            except threading.BrokenBarrierError:
                pass  # expected with a correct lock order: at most n-1 can get here together

    return hook


def test_five_workers_one_round():
    assert_clean(*run_ring(impl.LockTable(5), 5, 1), rounds=1)


def test_two_workers_boundary():
    # With 2 workers, both need both locks: the smallest ring.
    assert_clean(*run_ring(impl.LockTable(2), 2, 500), rounds=500)


@pytest.mark.parametrize("n", [0, 1])
def test_too_few_workers_rejected(n):
    with pytest.raises(ValueError):
        impl.LockTable(n)


def test_lock_order_rule_single_threaded():
    n = 5
    table = impl.LockTable(n)
    for w in range(n):
        calls: list[str] = []
        table.run_job(w, lambda: calls.append("take L"), lambda: calls.append("take R"),
                      lambda: calls.append("work"), lambda: calls.append("release L"),
                      lambda: calls.append("release R"))
        # Lower-numbered lock first: left for everyone except the last worker,
        # whose right lock is lock 0.
        first = "take R" if w == n - 1 else "take L"
        assert calls[0] == first
        assert calls[2] == "work" and sorted(calls[:2]) == ["take L", "take R"]
        assert sorted(calls[3:]) == ["release L", "release R"]


def test_forced_worst_case_interleaving_does_not_deadlock():
    n = 5
    ring = run_ring(impl.LockTable(n), n, 50, everyone_grabs_left_at_once(n, 1.0))
    assert_clean(*ring, rounds=50)


def test_harness_catches_the_naive_left_first_order():
    # Self-check of the test above: a table that always takes the left lock first
    # MUST deadlock under the forced interleaving, and the harness must notice.
    class NaiveTable:
        def __init__(self, n: int) -> None:
            self.n = n
            self.locks = [threading.Lock() for _ in range(n)]

        def run_job(self, w, take_left, take_right, work, release_left, release_right):
            with self.locks[w]:
                take_left()
                with self.locks[(w + 1) % self.n]:
                    take_right()
                    work()
                    release_right()
                release_left()

    n = 5
    global JOIN_TIMEOUT
    saved, JOIN_TIMEOUT = JOIN_TIMEOUT, 3.0
    try:
        _, _, stuck = run_ring(NaiveTable(n), n, 1, everyone_grabs_left_at_once(n, 2.0))
    finally:
        JOIN_TIMEOUT = saved
    assert stuck == n  # every worker holds its left lock and waits for its neighbour's


def test_many_rounds_stress():
    assert_clean(*run_ring(impl.LockTable(5), 5, 2_000), rounds=2_000)


def test_shard_migration_ring():
    # Production flavour: 6 migration workers on a ring of 6 shards. Worker i moves
    # rows between shard i and shard i+1, so it must lock both shards.
    assert_clean(*run_ring(impl.LockTable(6), 6, 300), rounds=300)
