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

import random as _random

VARIANT_TITLE = "Blocking bounded queue"
VARIANT_APPROACH = "Lock + two condition variables · O(1) per operation · O(capacity)"

_RING_FAST = '''from typing import Any


class RingBuffer:
    def __init__(self, capacity: int) -> None:
        self._buf: list[Any] = [None] * capacity
        self._head = 0
        self._count = 0

    def push(self, item: Any) -> Any:
        cap = len(self._buf)
        if self._count < cap:
            self._buf[(self._head + self._count) % cap] = item
            self._count += 1
            return None
        evicted = self._buf[self._head]
        self._buf[self._head] = item
        self._head = (self._head + 1) % cap
        return evicted

    def pop(self) -> Any:
        if self._count == 0:
            return None
        item = self._buf[self._head]
        self._buf[self._head] = None
        self._head = (self._head + 1) % len(self._buf)
        self._count -= 1
        return item

    def size(self) -> int:
        return self._count
'''

_RING_SLOW = '''from typing import Any


class RingBuffer:
    def __init__(self, capacity: int) -> None:
        self._cap = capacity
        self._items: list[Any] = []

    def push(self, item: Any) -> Any:
        self._items.append(item)
        if len(self._items) > self._cap:
            return self._items.pop(0)
        return None

    def pop(self) -> Any:
        return self._items.pop(0) if self._items else None

    def size(self) -> int:
        return len(self._items)
'''

_STALL_FAST = '''def stall_times(capacity: int, produce: list[int], consume: list[int]) -> list[list[int]]:
    n = len(produce)
    enq = [0] * n
    deq = [0] * n
    for i in range(n):
        t = produce[i]
        if i:
            t = max(t, enq[i - 1])
        if i >= capacity:
            t = max(t, deq[i - capacity])
        enq[i] = t
        d = max(consume[i], t)
        if i:
            d = max(d, deq[i - 1])
        deq[i] = d
    return [[enq[i], deq[i]] for i in range(n)]
'''

_STALL_SLOW = '''def stall_times(capacity: int, produce: list[int], consume: list[int]) -> list[list[int]]:
    n = len(produce)
    out = [[0, 0] for _ in range(n)]
    if n == 0:
        return []
    horizon = max(produce + consume)
    nxt_p = nxt_c = 0
    in_queue = 0
    for t in range(horizon + 1):
        moved = True
        while moved:
            moved = False
            if nxt_p < n and produce[nxt_p] <= t and in_queue < capacity:
                out[nxt_p][0] = t
                nxt_p += 1
                in_queue += 1
                moved = True
            if nxt_c < nxt_p and consume[nxt_c] <= t and in_queue > 0:
                out[nxt_c][1] = t
                nxt_c += 1
                in_queue -= 1
                moved = True
    return out
'''


def _rops(cap, *steps):
    ops, vals = ["RingBuffer"], [[cap]]
    for s in steps:
        ops.append(s[0])
        vals.append(list(s[1:]))
    return {"ops": ops, "vals": vals}


def _ring_large():
    rng = _random.Random(1313)
    steps = []
    for i in range(600):
        r = rng.random()
        steps.append(("push", "ev-%d" % i) if r < 0.6 else ("pop",) if r < 0.9 else ("size",))
    return _rops(16, *steps)


def _stall_large():
    rng = _random.Random(1188)
    p, c, tp, tc = [], [], 0, 0
    for _ in range(300):
        tp += rng.randint(0, 5)
        tc += rng.randint(0, 9)
        p.append(tp)
        c.append(tc)
    return {"capacity": 8, "produce": p, "consume": c}


VARIANTS = [
    {
        "key": "drop-oldest-ring",
        "title": "Drop-oldest ring buffer",
        "approach": "Fixed array with head and count · O(1) per operation · O(capacity)",
        "spec": {"kind": "design", "fn": "RingBuffer", "params": [], "cmp": "exact"},
        "statement": (
            "A stalled exporter must never stall the application, so this buffer keeps the newest data and **drops the oldest** instead of blocking.\n"
            "\n"
            "### Methods\n"
            "- `RingBuffer(capacity)`: create the buffer (single-threaded)\n"
            "- `push(item)`: append `item`; if the buffer was full, evict and return the oldest item, otherwise return `None`\n"
            "- `pop()`: remove and return the oldest item, or `None` when empty\n"
            "- `size()`: return the number of buffered items\n"
            "\n"
            "### Rules\n"
            "- `push` and `pop` must be O(1): no shifting of the whole buffer"
        ),
        "examples": [
            {"args": _rops(2, ("push", "a"), ("push", "b"), ("push", "c"), ("pop",), ("pop",), ("pop",)),
             "explanation": "Pushing c into a full buffer evicts a. The buffer then yields b, c, and None when empty.",
             "why": {"t": "Evict the oldest", "d": "A full buffer drops from the front, not the back."}},
        ],
        "constraints": ["1 ≤ capacity ≤ 10⁴", "at most 2,000 calls", "items are strings or integers"],
        "hints": [
            "Allocate an array of size capacity once and keep a head index and a count.",
            "The tail slot is (head + count) % capacity. A push into a full buffer overwrites the head and moves it forward.",
        ],
        "tests": [
            {"args": _rops(1, ("pop",), ("size",)), "why": {"t": "Pop empty", "d": "An empty buffer returns None and has size 0."}},
            {"args": _rops(1, ("push", 1), ("push", 2), ("push", 3), ("pop",), ("size",)), "why": {"t": "Capacity 1", "d": "Each push evicts the previous item."}},
            {"args": _rops(3, ("push", "x"), ("push", "x"), ("push", "x"), ("push", "y"), ("pop",), ("pop",), ("pop",)),
             "why": {"t": "Duplicates", "d": "Equal items are still evicted one at a time, in order."}},
            {"args": _rops(3, ("push", 1), ("push", 2), ("pop",), ("push", 3), ("push", 4), ("push", 5), ("pop",), ("pop",), ("pop",), ("pop",)),
             "why": {"t": "Wrap-around", "d": "Head and tail wrap past the end of the array."}},
            {"args": _rops(4, ("push", 1), ("pop",), ("pop",), ("push", 2), ("size",)), "why": {"t": "Drain then refill", "d": "Popping past empty does not break the next push."}},
            {"args": _ring_large(), "why": {"t": "Large input", "d": "600 mixed pushes, pops and sizes on 16 slots."}},
        ],
        "solutions": [
            {"name": "Circular array (Optimal)",
             "description": "A preallocated array, a head index and a count. Push writes at (head + count) % cap or overwrites the head when full; pop reads the head.",
             "time": "O(1) per operation", "space": "O(capacity)",
             "keyPoints": ["No element ever moves", "Full-buffer push overwrites and advances head", "Clear popped slots so old items can be freed"],
             "code": _RING_FAST},
            {"name": "List with pop(0)", "slow": True,
             "description": "Append to a Python list and pop from the front when it grows past capacity.",
             "time": "O(capacity) per push and pop", "space": "O(capacity)",
             "keyPoints": ["Correct and short", "pop(0) shifts every remaining element"],
             "code": _RING_SLOW},
        ],
        "starter": "class RingBuffer:\n    def __init__(self, capacity: int) -> None:\n        pass\n\n    def push(self, item):\n        pass\n\n    def pop(self):\n        pass\n\n    def size(self) -> int:\n        pass\n",
    },
    {
        "key": "producer-stall-times",
        "title": "Predict producer stalls",
        "approach": "Recurrence over item index · O(n) · O(n)",
        "spec": {"kind": "fn", "fn": "stall_times", "params": ["capacity", "produce", "consume"], "cmp": "exact"},
        "statement": (
            "Simulate a log pipeline: one tailer enqueues lines into a blocking queue, and one shipper dequeues them.\n"
            "\n"
            "### Input\n"
            "- `capacity`: the queue's size\n"
            "- `produce[i]`: when item `i` is ready to be enqueued (non-decreasing)\n"
            "- `consume[i]`: when the shipper is ready for item `i` (non-decreasing)\n"
            "\n"
            "### Output\n"
            "- `[enqueued_at, dequeued_at]` for every item\n"
            "\n"
            "### Rules\n"
            "- Operations take no time\n"
            "- The tailer handles items in order; an enqueue blocks while the queue is full\n"
            "- The shipper handles items in order; a dequeue blocks while the queue is empty\n"
            "- A slot freed at time `t` can be used at time `t`"
        ),
        "examples": [
            {"args": {"capacity": 1, "produce": [0, 0, 0], "consume": [5, 6, 7]},
             "explanation": "Item 0 goes in at 0. Item 1 waits for the only slot until item 0 leaves at 5; item 2 waits until 6.",
             "why": {"t": "Slow shipper", "d": "Backpressure delays the tailer to the shipper's pace."}},
            {"args": {"capacity": 2, "produce": [3, 4], "consume": [0, 0]},
             "explanation": "The shipper is waiting, so each item leaves the moment it arrives.",
             "why": {"t": "Slow tailer", "d": "Dequeues block on an empty queue instead."}},
        ],
        "constraints": ["0 ≤ n ≤ 300", "1 ≤ capacity ≤ 100", "0 ≤ produce[i], consume[i] ≤ 3000, each list non-decreasing"],
        "hints": [
            "Item i can enter only after item i - capacity has left, since the queue is FIFO.",
            "enq[i] = max(produce[i], enq[i-1], deq[i-capacity]) and deq[i] = max(consume[i], deq[i-1], enq[i]).",
            "Both depend only on earlier items, so one pass in index order computes everything.",
        ],
        "tests": [
            {"args": {"capacity": 3, "produce": [], "consume": []}, "why": {"t": "No items", "d": "Nothing to schedule: []."}},
            {"args": {"capacity": 1, "produce": [2], "consume": [2]}, "why": {"t": "Single item, same time", "d": "Enqueue and dequeue in the same instant."}},
            {"args": {"capacity": 2, "produce": [0, 0, 0, 0], "consume": [10, 10, 10, 10]}, "why": {"t": "Burst then drain", "d": "Two items wait; the rest enter as the shipper frees slots at 10."}},
            {"args": {"capacity": 5, "produce": [0, 1, 2], "consume": [0, 1, 2]}, "why": {"t": "Never full", "d": "Capacity is larger than the backlog: no stalls."}},
            {"args": {"capacity": 1, "produce": [0, 1, 2, 3], "consume": [0, 0, 0, 9]}, "why": {"t": "Late last read", "d": "Only the last item waits for the shipper."}},
            {"args": {"capacity": 100, "produce": [7, 7, 7], "consume": [7, 7, 7]}, "why": {"t": "All at one instant", "d": "Every enqueue and dequeue happens at time 7."}},
            {"args": _stall_large(), "why": {"t": "Large input", "d": "300 items; the shipper is slower on average."}},
        ],
        "solutions": [
            {"name": "Recurrence in index order (Optimal)",
             "description": "Walk items in order. An enqueue waits for its ready time, the previous enqueue and the dequeue of item i - capacity; a dequeue waits for its ready time, the previous dequeue and its own enqueue.",
             "time": "O(n)", "space": "O(n)",
             "keyPoints": ["FIFO means slot i is freed by item i - capacity", "Each time is a max of earlier times", "No clock simulation needed"],
             "code": _STALL_FAST},
            {"name": "Tick-by-tick simulation", "slow": True,
             "description": "Advance a clock one unit at a time; at each tick keep letting the tailer and shipper act until neither can.",
             "time": "O(T + n)", "space": "O(n)",
             "keyPoints": ["Mirrors the real system", "Cost grows with the time span, not the item count"],
             "code": _STALL_SLOW},
        ],
        "starter": "def stall_times(capacity: int, produce: list[int], consume: list[int]) -> list[list[int]]:\n    pass\n",
    },
]
