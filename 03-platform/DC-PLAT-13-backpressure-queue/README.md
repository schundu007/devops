Source: New

# DC-PLAT-13 · Backpressure Queue

## 1. Header
| | |
|---|---|
| Chip ID | DC-PLAT-13 |
| Difficulty | Medium |
| Pattern | Locks + condition variables |
| Track | Platform Engineering, Scheduling & Allocation (PLAT) |
| Classic pattern | LeetCode 1188 |
| Premium | Yes (P). Free alternatives: LeetCode 622 Design Circular Queue (the bounded buffer, without blocking) and LeetCode 1115 Print FooBar Alternately (threads waiting on each other with a condition variable). |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
A log shipper on `ip-10-0-4-19` has two threads. The tailer reads `/var/log/app/*.log` at
tens of thousands of lines a second. The shipper sends batches to a log backend that, during
an incident, accepts only a few hundred a second. Between them sits an in-memory buffer. Last
month the buffer was unbounded: during a backend slowdown it grew to 6 GB, and the node's
OOM killer took out the shipper and two application pods with it. This time the buffer holds
at most 10,000 lines, and the tailer must **wait** when it is full.

## 3. Why This Is DevOps
**Production reality:** Every pipeline has a fast stage and a slow stage. Without a limit, the
buffer between them grows until memory runs out. With a bounded buffer that blocks the
producer when full, the slowdown travels upstream: the tailer pauses and the files on disk
act as the overflow. This is backpressure, and it is how a pipeline survives a slow
dependency instead of crashing.

**Where you see it:** Go buffered channels (a send blocks when the buffer is full), the Kafka
producer's `buffer.memory` (`send()` blocks up to `max.block.ms` when it is full), Python's
`queue.Queue(maxsize=…)`, and Fluent Bit's `Mem_Buf_Limit` (it pauses the input when reached).

**Reality check:** Real systems rarely block forever. Kafka gives up after `max.block.ms`, and
many shippers drop or spill to disk after a timeout. Across machines, backpressure comes from
TCP flow control or protocol-level credits, not from one process's lock. This chip is the
in-process core.

**What breaks if you get it wrong:** Use `if` instead of `while` around `wait()`, and a spurious
or stolen wake-up lets two consumers pop one item: one gets an exception on an empty queue, or
the buffer goes past its limit. Forget to notify, and the pipeline silently stops, with every
thread asleep.

## 4. Problem Statement
Build a thread-safe `BoundedBlockingQueue` with a fixed capacity.

- `enqueue(item)` adds at the back. If the queue is full, the calling thread **blocks** until
  there is room.
- `dequeue()` removes and returns the front item. If the queue is empty, the calling thread
  **blocks** until an item arrives.
- `size()` returns the current number of items.
- The queue is FIFO and must never hold more than `capacity` items. Many producer and consumer
  threads may call it at once.
- `capacity < 1` raises `ValueError`. Use `threading` primitives, not `queue.Queue`.

## 5. Input / Output format and Constraints
- `capacity`: `1 <= capacity <= 10^4`. Items are any Python object.
- Up to 16 threads and `10^5` operations in total.
- `enqueue -> None`, `dequeue -> item`, `size -> int`.

## 6. Examples
**Example 1: FIFO**
```
q = BoundedBlockingQueue(3)
enqueue("a"); enqueue("b"); enqueue("c")
dequeue(), dequeue(), dequeue()  -> "a", "b", "c"
```

**Example 2: a producer blocks (edge case: capacity 1)**
```
q = BoundedBlockingQueue(1); q.enqueue("a")
thread T: q.enqueue("b")     # T blocks, the queue is full
main:     q.dequeue() -> "a" # room appears, T wakes and adds "b"
main:     q.dequeue() -> "b"
```

**Example 3: a consumer blocks**
```
q = BoundedBlockingQueue(2)
thread T: q.dequeue()        # T blocks, the queue is empty
main:     q.enqueue("x")     # T wakes and returns "x"
```

## 7. Starter Code
See [`starter.py`](starter.py): the class with `enqueue`, `dequeue` and `size`, docstrings
and type hints. Bodies are TODO.

```bash
make try CHIP=03-platform/DC-PLAT-13-backpressure-queue
```

## 8. Hints
1. **Nudge:** A thread that cannot proceed needs to sleep until something changes, without
   burning CPU and without holding the lock while it sleeps.
2. **Pattern:** A lock protecting a deque, plus two condition variables on that same lock:
   "not full" for producers and "not empty" for consumers.
3. **Near-solution:** In `enqueue`: `while full: not_full.wait()`, append, `not_empty.notify()`.
   In `dequeue`: `while empty: not_empty.wait()`, pop, `not_full.notify()`. Always `while`,
   never `if`.

## 9. Solution
**Approach**
1. One `Lock`, one `deque` and two `Condition`s built on the same lock.
2. `enqueue` takes the lock and waits on `not_full` while the queue is at capacity. `wait()`
   releases the lock while sleeping. Then it appends and notifies one consumer.
3. `dequeue` mirrors it: wait on `not_empty` while empty, pop the front, notify one producer.
4. Re-check the condition in a `while` loop after every wake-up. Another thread may have taken
   the slot first, and spurious wake-ups are allowed.

**Brute force:** Busy-wait: loop on `if full: release the lock, sleep 1 ms, try again`. It
burns CPU, adds latency, and under load it is hard to reason about fairness. Condition
variables sleep until they are notified.

**Optimal code:** [`solution.py`](solution.py)

```python
import threading
from collections import deque
from typing import Any


class BoundedBlockingQueue:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least 1")
        self._capacity = capacity
        self._items: deque[Any] = deque()
        lock = threading.Lock()                      # one lock, two conditions
        self._not_full = threading.Condition(lock)
        self._not_empty = threading.Condition(lock)

    def enqueue(self, item: Any) -> None:
        with self._not_full:
            while len(self._items) >= self._capacity:   # while, not if
                self._not_full.wait()
            self._items.append(item)
            self._not_empty.notify()

    def dequeue(self) -> Any:
        with self._not_empty:
            while not self._items:
                self._not_empty.wait()
            item = self._items.popleft()
            self._not_full.notify()
            return item

    def size(self) -> int:
        with self._not_full:
            return len(self._items)
```

**Complexity**
- Time: O(1) per operation, excluding the time spent blocked, because a deque append or pop
  and a notify are constant time.
- Space: O(capacity). The buffer can never hold more, which is the point.

## 10. Tests
[`test_chip.py`](test_chip.py) has 6 cases, and none of them depend on timing to pass:
- single-thread FIFO order;
- invalid capacity;
- a producer blocked on a full queue of capacity 1 (the boundary);
- a consumer blocked on an empty queue;
- 4 producers × 2,500 items and 4 consumers: every item arrives exactly once, each producer's
  items stay in order, and the capacity is never exceeded;
- a production-style log shipper where the tailer must stop at exactly 10 lines until the
  shipper starts.

Blocking is checked as "this event must *not* be set yet". A correct queue stays blocked
forever, so that check cannot flake. Every join has a timeout, so a deadlock fails the test
instead of hanging it.

## 11. Interview Talk Track
"This is backpressure in its simplest form: a bounded buffer between a fast producer and a
slow consumer. I use one lock, a deque, and two condition variables on that lock: not-full
for producers and not-empty for consumers. Enqueue waits while the queue is full, and wait
releases the lock while it sleeps. Then it appends and notifies one consumer. Dequeue mirrors
that. The two classic bugs are using 'if' instead of 'while' around wait, which breaks on
spurious or stolen wake-ups, and forgetting to notify, which stalls the whole pipeline. This
is what a Go buffered channel gives you, and what Kafka's producer does with buffer.memory,
except Kafka gives up after max.block.ms. In production I'd add that timeout, so a dead
consumer turns into an error you can alert on instead of a silent hang."

## 12. Level Up
1. **"Don't block forever: fail after 2 seconds."** Use `Condition.wait_for(predicate, timeout)`
   and raise a `QueueFullError` (or return `False`) on timeout. Callers can then drop, spill to
   disk, or shed load, and the timeouts show up in metrics.
2. **"Limit by bytes, not item count."** Track the total bytes in the buffer and wait while
   `used + len(item) > limit`. Allow one oversized item into an empty buffer, or it can never
   be sent. Kafka's `buffer.memory` and Fluent Bit's `Mem_Buf_Limit` are byte limits.
3. **"Shutdown: stop producers and drain consumers cleanly."** Add a `close()` that sets a flag
   and `notify_all()`s both conditions. After close, producers get an error, and consumers
   drain what is left and then get a sentinel or exception. That turns a SIGTERM into a clean
   flush instead of lost logs.

## 13. Related Chips
- **DC-PLAT-14 Deadlock-Free Lock Ordering**: the other half of concurrency safety.
- **DC-PLAT-04 Job Queue with Cooldown**: queueing policy when jobs must wait.
- **DC-CAP-01 Backlog Drain Rate**: how fast consumers must run to drain the backlog that backpressure creates.
