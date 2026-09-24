"""Capra Playground export for DC-PLAT-13 (see tools/export_capra.py).

Threads run inside the driver. Blocking is checked with "this Event must NOT
be set yet": a correct queue stays blocked forever, so the short wait can only
fail for a broken queue. Every join has a deadline, so a deadlock returns a
result ("stuck" > 0) instead of hanging the run.
"""

SPEC = {"kind": "driver", "fn": "BoundedBlockingQueue", "params": ["scenario", "capacity", "config"], "types": {}, "ret": "value", "cmp": "exact"}

DRIVER = '''
import threading as _th
import time as _time


def _run(targets, budget=2.0):
    errors = []

    def wrap(fn):
        def inner():
            try:
                fn()
            except BaseException as e:
                errors.append(type(e).__name__)
        return inner

    ts = [_th.Thread(target=wrap(t), daemon=True) for t in targets]
    for t in ts:
        t.start()
    deadline = _time.monotonic() + budget
    for t in ts:
        t.join(max(0.0, deadline - _time.monotonic()))
    return errors, sum(t.is_alive() for t in ts)


def __drive(args):
    scenario, cap, cfg = args["scenario"], args["capacity"], args["config"]
    try:
        q = BoundedBlockingQueue(cap)
    except ValueError:
        return "ValueError"

    if scenario == "sequential":
        sizes, out = [], []
        for op in cfg["ops"]:
            if op[0] == "enqueue":
                q.enqueue(op[1])
            elif op[0] == "dequeue":
                out.append(q.dequeue())
            sizes.append(q.size())
        return {"dequeued": out, "sizes": sizes}

    if scenario == "full_blocks":
        for x in range(cap):
            q.enqueue(x)
        done = _th.Event()

        def producer():
            q.enqueue("late")
            done.set()

        _th.Thread(target=producer, daemon=True).start()
        blocked = not done.wait(cfg["wait"])
        size_while_blocked = q.size()
        first = q.dequeue()
        woke = done.wait(2.0)
        rest = [q.dequeue() for _ in range(cap)] if woke else []
        return {"blocked": blocked, "sizeWhileBlocked": size_while_blocked, "first": first, "woke": woke, "rest": rest}

    if scenario == "empty_blocks":
        got, done = [], _th.Event()

        def consumer():
            got.append(q.dequeue())
            done.set()

        _th.Thread(target=consumer, daemon=True).start()
        blocked = not done.wait(cfg["wait"])
        q.enqueue("x")
        woke = done.wait(2.0)
        return {"blocked": blocked, "woke": woke, "got": got}

    if scenario == "many":
        producers, per = cfg["producers"], cfg["perProducer"]
        over = []
        received = [[] for _ in range(producers)]

        def producer(pid):
            def run():
                for seq in range(per):
                    q.enqueue([pid, seq])
                    if q.size() > cap:
                        over.append(1)
            return run

        def consumer(cid):
            def run():
                for _ in range(per):
                    received[cid].append(q.dequeue())
            return run

        errors, stuck = _run([producer(p) for p in range(producers)] + [consumer(c) for c in range(producers)])
        allitems = sorted(tuple(x) for got in received for x in got)
        fifo = all([s for (p, s) in got if p == pid] == sorted(s for (p, s) in got if p == pid)
                   for got in received for pid in range(producers))
        return {"received": len(allitems), "allPresent": allitems == sorted((p, s) for p in range(producers) for s in range(per)),
                "fifoPerProducer": fifo, "overCapacity": len(over), "stuck": stuck, "errors": errors, "leftInQueue": q.size()}

    if scenario == "backpressure":
        lines = cfg["lines"]
        filled, finished, go = _th.Event(), _th.Event(), _th.Event()
        produced, shipped = [0], []

        def tailer():
            for i in range(lines):
                q.enqueue("line %d" % i)
                produced[0] += 1
                if produced[0] == cap:
                    filled.set()
            finished.set()

        def shipper():
            go.wait(2.0)
            for _ in range(lines):
                shipped.append(q.dequeue())

        result = {}

        def orchestrate():
            errs, stuck = _run([tailer, shipper])
            result["errors"], result["stuck"] = errs, stuck

        runner = _th.Thread(target=orchestrate, daemon=True)
        runner.start()
        filled_ok = filled.wait(2.0)
        stopped = not finished.wait(cfg["wait"])
        stopped_at = produced[0]
        go.set()
        runner.join(2.5)
        return {"filled": filled_ok, "tailerStopped": stopped, "producedWhenStopped": stopped_at,
                "shippedInOrder": shipped == ["line %d" % i for i in range(lines)],
                "stuck": result.get("stuck", -1), "errors": result.get("errors", [])}

    raise ValueError("unknown scenario " + scenario)
'''

EXAMPLES = [
    {"args": {"scenario": "sequential", "capacity": 3,
              "config": {"ops": [["enqueue", "a"], ["enqueue", "b"], ["enqueue", "c"], ["dequeue"], ["dequeue"], ["dequeue"]]}},
     "explanation": "One thread, no blocking: items leave in the order they arrived, and size() tracks the buffer.",
     "why": {"t": "FIFO", "d": "First in, first out on a single thread."}},
    {"args": {"scenario": "full_blocks", "capacity": 1, "config": {"wait": 0.1}},
     "explanation": "The queue holds 1 item, so a second enqueue must block. The dequeue makes room and wakes the producer.",
     "why": {"t": "Full → producer blocks", "d": "Backpressure: a full buffer stops the producer until a consumer takes an item."}},
]

TESTS = [
    {"args": {"scenario": "sequential", "capacity": 0, "config": {"ops": []}},
     "why": {"t": "Invalid capacity", "d": "Capacity 0 is rejected with ValueError."}},
    {"args": {"scenario": "sequential", "capacity": 1,
              "config": {"ops": [["enqueue", 1], ["dequeue"], ["enqueue", 2], ["dequeue"], ["enqueue", 3], ["dequeue"]]}},
     "why": {"t": "Capacity 1", "d": "The smallest buffer, filled and drained in turn."}},
    {"args": {"scenario": "full_blocks", "capacity": 3, "config": {"wait": 0.1}},
     "why": {"t": "Full at capacity 3", "d": "The producer blocks only once all 3 slots are used."}},
    {"args": {"scenario": "empty_blocks", "capacity": 2, "config": {"wait": 0.1}},
     "why": {"t": "Empty → consumer blocks", "d": "A dequeue on an empty queue waits for the next enqueue."}},
    {"args": {"scenario": "many", "capacity": 8, "config": {"producers": 4, "perProducer": 300}},
     "why": {"t": "4 producers, 4 consumers", "d": "Every item arrives exactly once, each producer's items stay in order, and the size never exceeds capacity."}},
    {"args": {"scenario": "many", "capacity": 1, "config": {"producers": 3, "perProducer": 200}},
     "why": {"t": "Heavy contention", "d": "Capacity 1 with 6 threads: every operation waits on another."}},
    {"args": {"scenario": "backpressure", "capacity": 10, "config": {"lines": 300, "wait": 0.1}},
     "why": {"t": "Log shipper", "d": "A fast log tailer must stop after 10 buffered lines until the shipper catches up."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Lock + two condition variables (Optimal)",
     "description": "One lock, a deque, and two Conditions on that lock: producers wait on not_full, consumers on not_empty. Re-check the condition in a while loop after every wake-up, then notify the other side.",
     "time": "O(1) per operation, excluding time blocked", "space": "O(capacity)",
     "keyPoints": ["wait() releases the lock while sleeping", "Always re-check in a while loop (spurious wake-ups, stolen slots)", "Notify the other side after each change"]},
    {"name": "Busy-wait with sleep", "slow": True,
     "description": "Loop: take the lock, and if the queue is full (or empty) release it, sleep 1 ms and try again.",
     "time": "O(1) per operation, plus wasted polling", "space": "O(capacity)",
     "keyPoints": ["Correct but burns CPU while waiting", "Adds up to 1 ms of latency per wait"],
     "code": '''from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any


class BoundedBlockingQueue:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self._cap = capacity
        self._items: deque[Any] = deque()
        self._lock = threading.Lock()

    def enqueue(self, item: Any) -> None:
        while True:
            with self._lock:
                if len(self._items) < self._cap:
                    self._items.append(item)
                    return
            time.sleep(0.001)

    def dequeue(self) -> Any:
        while True:
            with self._lock:
                if self._items:
                    return self._items.popleft()
            time.sleep(0.001)

    def size(self) -> int:
        with self._lock:
            return len(self._items)
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Busy-wait", "idea": "Poll with a short sleep until there is room or an item.",
     "time": "O(1) + polling", "space": "O(capacity)", "use": "Never in production: it burns CPU."},
    {"name": "Condition variables", "idea": "Sleep on not_full / not_empty and wake exactly when state changes.",
     "time": "O(1)", "space": "O(capacity)", "use": "Every real bounded buffer (Go channels, Java ArrayBlockingQueue)."},
]
