"""Tests for DC-PLAT-13 Backpressure Queue.

Deterministic by design: no sleeps decide the outcome. Blocking is checked with
"this Event must NOT be set yet" (a correct queue stays blocked forever, so the
short wait can only fail for a broken queue), and every join has a timeout so a
deadlock fails the test instead of hanging it.
"""
from __future__ import annotations

import threading
import time
from typing import Callable

import pytest
from chip import load_impl

impl = load_impl(__file__)
JOIN_TIMEOUT = 10.0


def run_threads(targets: list[Callable[[], None]]) -> tuple[list[BaseException], int]:
    """Run targets in daemon threads; return (exceptions raised, threads still stuck)."""
    errors: list[BaseException] = []

    def wrap(fn: Callable[[], None]) -> Callable[[], None]:
        def inner() -> None:
            try:
                fn()
            except BaseException as e:  # noqa: BLE001 - surface anything to the test
                errors.append(e)
        return inner

    threads = [threading.Thread(target=wrap(t), daemon=True) for t in targets]
    for t in threads:
        t.start()
    deadline = time.monotonic() + JOIN_TIMEOUT
    for t in threads:
        t.join(max(0.0, deadline - time.monotonic()))
    return errors, sum(t.is_alive() for t in threads)


def test_fifo_single_thread():
    q = impl.BoundedBlockingQueue(3)
    for x in ("a", "b", "c"):
        q.enqueue(x)
    assert q.size() == 3
    assert [q.dequeue() for _ in range(3)] == ["a", "b", "c"]
    assert q.size() == 0


def test_invalid_capacity():
    with pytest.raises(ValueError):
        impl.BoundedBlockingQueue(0)


def test_enqueue_blocks_when_full_until_a_dequeue():
    q = impl.BoundedBlockingQueue(1)       # boundary: capacity 1
    q.enqueue("a")
    done = threading.Event()

    def producer() -> None:
        q.enqueue("b")
        done.set()

    threading.Thread(target=producer, daemon=True).start()
    assert not done.wait(0.2), "enqueue on a full queue must block"
    assert q.size() == 1
    assert q.dequeue() == "a"              # makes room...
    assert done.wait(5), "...which must wake the blocked producer"
    assert q.dequeue() == "b"


def test_dequeue_blocks_when_empty_until_an_enqueue():
    q = impl.BoundedBlockingQueue(2)
    got: list[str] = []
    done = threading.Event()

    def consumer() -> None:
        got.append(q.dequeue())
        done.set()

    threading.Thread(target=consumer, daemon=True).start()
    assert not done.wait(0.2), "dequeue on an empty queue must block"
    q.enqueue("x")
    assert done.wait(5)
    assert got == ["x"]


def test_many_producers_and_consumers_keep_order_and_count():
    cap, producers, per_producer = 8, 4, 2_500
    q = impl.BoundedBlockingQueue(cap)
    over_capacity: list[int] = []
    received: list[list[tuple[int, int]]] = [[] for _ in range(producers)]

    def producer(pid: int) -> Callable[[], None]:
        def run() -> None:
            for seq in range(per_producer):
                q.enqueue((pid, seq))
                if q.size() > cap:
                    over_capacity.append(q.size())
        return run

    def consumer(cid: int) -> Callable[[], None]:
        def run() -> None:
            for _ in range(per_producer):
                received[cid].append(q.dequeue())
        return run

    errors, stuck = run_threads([producer(p) for p in range(producers)] +
                                [consumer(c) for c in range(producers)])
    assert not errors and stuck == 0, (errors, stuck)
    assert not over_capacity
    everything = sorted(item for got in received for item in got)
    assert everything == sorted((p, s) for p in range(producers) for s in range(per_producer))
    # FIFO: within one consumer, each producer's items arrive in increasing order.
    for got in received:
        for p in range(producers):
            seqs = [s for (pid, s) in got if pid == p]
            assert seqs == sorted(seqs)
    assert q.size() == 0


def test_log_shipper_applies_backpressure():
    # Production flavour: a log tailer reads 1,000 lines far faster than the
    # shipper can send them. With a buffer of 10, the tailer must stop after 10
    # lines and wait, instead of growing memory without limit.
    cap, lines = 10, 1_000
    q = impl.BoundedBlockingQueue(cap)
    filled, finished, go = threading.Event(), threading.Event(), threading.Event()
    produced = [0]
    shipped: list[str] = []

    def tailer() -> None:
        for i in range(lines):
            q.enqueue(f"line {i}")
            produced[0] += 1
            if produced[0] == cap:
                filled.set()
        finished.set()

    def shipper() -> None:
        go.wait()
        for _ in range(lines):
            shipped.append(q.dequeue())

    threads_done: list = []
    t_errors: list[BaseException] = []

    def start_all() -> None:
        errs, stuck = run_threads([tailer, shipper])
        t_errors.extend(errs)
        threads_done.append(stuck)

    runner = threading.Thread(target=start_all, daemon=True)
    runner.start()
    assert filled.wait(5), "the tailer should fill the buffer"
    assert not finished.wait(0.2), "a full buffer must stop the tailer"
    assert produced[0] == cap and q.size() == cap
    go.set()                                   # the shipper catches up
    runner.join(JOIN_TIMEOUT + 5)
    assert not t_errors and threads_done == [0]
    assert shipped == [f"line {i}" for i in range(lines)]
