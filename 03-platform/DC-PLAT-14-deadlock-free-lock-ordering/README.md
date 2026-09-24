Source: New

# DC-PLAT-14 · Deadlock-Free Lock Ordering

## 1. Header
| | |
|---|---|
| Chip ID | DC-PLAT-14 |
| Difficulty | Medium |
| Pattern | Concurrency / locks |
| Track | Platform Engineering, Scheduling & Allocation (PLAT) |
| Classic pattern | LeetCode 1226 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
A rebalancing job runs 5 migration workers over a ring of 5 database shards, `shard-0` to
`shard-4`. Worker `i` moves rows between shard `i` and shard `i+1`, and the last worker moves
rows between `shard-4` and `shard-0`. Each worker must lock both of its shards while it copies.
Last Tuesday at 03:12 the whole job froze: every worker held one shard lock and waited forever
for its neighbour's. Nothing crashed and nothing alerted. Throughput simply went to zero.

## 3. Why This Is DevOps
**Production reality:** Any time one task needs two shared resources, such as two database rows,
two shards, two files or two distributed locks, a deadlock is possible. If A holds X and waits
for Y while B holds Y and waits for X, both wait forever. The standard fix is a global lock
order: always acquire the lower-numbered (or alphabetically first) resource first. With one
order, a waiting cycle cannot form.

**Where you see it:** PostgreSQL (it detects deadlocks after `deadlock_timeout`, 1 s by default,
and aborts one transaction). The usual advice is to update rows in a consistent order, such as
by primary key. The Linux kernel's lockdep checks lock ordering at runtime. The same rule
applies to taking several Redis or etcd locks, or to a Terraform run that must lock two state backends.

**Reality check:** Databases detect deadlocks and kill a victim. Lock ordering prevents them
instead, so you avoid retries and wasted work. Distributed locks add problems this chip leaves
out: lease expiry, clock skew, and a holder that dies while holding a lock.

**What breaks if you get it wrong:** The job hangs with no error. Depending on the timeouts,
connections pile up, pools run dry, and unrelated services that share the database start timing out.

## 4. Problem Statement
`n` workers sit in a ring over `n` locks. Worker `i` needs lock `i` (its **left** lock) and
lock `(i + 1) % n` (its **right** lock).

Implement `LockTable(n)` and `run_job(worker, take_left, take_right, work, release_left, release_right)`:

- Each worker's own thread calls `run_job` many times, at the same time as the other workers.
- Hold **both** of the worker's locks while calling `work()`.
- Call `take_left` or `take_right` right after acquiring that lock, and `release_left` or
  `release_right` right before releasing it. The tests use these calls to check safety.
- The table must **never deadlock**, whatever the thread interleaving.
- `n < 2` raises `ValueError`.

## 5. Input / Output format and Constraints
- `n`: `2 <= n <= 100`. `worker`: `0 <= worker < n`.
- The five callbacks take no arguments and return `None`.
- Up to 5,000 `run_job` calls per worker. Use the `threading` module.

## 6. Examples
**Example 1: the deadlock this chip prevents**
```
n = 5, everyone takes their left lock first:
worker 0 holds lock 0, waits for 1
worker 1 holds lock 1, waits for 2
...
worker 4 holds lock 4, waits for 0     -> a cycle, and nobody ever proceeds
```

**Example 2: the fix, lower lock first**
```
workers 0-3: take lock i, then lock i+1
worker 4:    take lock 0, then lock 4  # its right lock (0) is the lower one
worker 4 now competes with worker 0 for lock 0 first, so the cycle cannot close
```

**Example 3: the smallest ring (edge case)**
```
n = 2: worker 0 needs locks 0 and 1, and so does worker 1.
Both acquire lock 0 first, so one of them simply waits its turn.
```

## 7. Starter Code
See [`starter.py`](starter.py): `LockTable(n)` and `run_job(...)` with docstrings and type
hints. Bodies are TODO.

```bash
make try CHIP=03-platform/DC-PLAT-14-deadlock-free-lock-ordering
```

## 8. Hints
1. **Nudge:** A deadlock needs a cycle of "I hold one, I wait for yours". What would make a cycle impossible?
2. **Pattern:** Give every lock a rank and always acquire in increasing rank. Waiting then only
   goes "upward", and an upward chain cannot loop back.
3. **Near-solution:** Compute `left, right`. If `left > right`, which only happens for the last
   worker, swap the order and swap the matching take and release callbacks. Nest `with` blocks:
   the first lock, `take_first()`, the second lock, `take_second()`, `work()`, `release_second()`,
   exit, `release_first()`, exit.

## 9. Solution
**Approach**
1. Create one `threading.Lock` per resource.
2. In `run_job`, find the worker's two locks and order them by number.
3. Acquire the lower-numbered lock first, then the higher one. Call the matching take callback
   after each acquisition.
4. Call `work()` while holding both, then release in reverse order, calling the matching
   release callback just before each release.

**Brute force:** One global lock around every job. It is trivially deadlock-free, but only one
worker can run at a time, so with 5 workers you lose up to 80% of the throughput. Another naive
fix, "try the second lock and back off if it's busy", avoids deadlock but can livelock under load.

**Optimal code:** [`solution.py`](solution.py)

```python
import threading
from typing import Callable

Action = Callable[[], None]


class LockTable:
    def __init__(self, n: int) -> None:
        if n < 2:
            raise ValueError("need at least 2 workers")
        self._n = n
        self._locks = [threading.Lock() for _ in range(n)]

    def run_job(self, worker: int, take_left: Action, take_right: Action,
                work: Action, release_left: Action, release_right: Action) -> None:
        left, right = worker, (worker + 1) % self._n
        if left < right:                                   # lower-numbered lock first
            first, second = left, right
            take_first, take_second = take_left, take_right
            release_first, release_second = release_left, release_right
        else:                                              # the wrap-around worker
            first, second = right, left
            take_first, take_second = take_right, take_left
            release_first, release_second = release_right, release_left
        with self._locks[first]:
            take_first()
            with self._locks[second]:
                take_second()
                work()
                release_second()
            release_first()
```

**Complexity**
- Time: O(1) per job, excluding time spent waiting: two lock operations and five callbacks.
- Space: O(n), one lock per resource.

## 10. Tests
[`test_chip.py`](test_chip.py) has 9 cases. A recorder checks every callback: nobody takes a
lock that someone else holds, and `work()` always runs with both locks.
- 5 workers × 1 round;
- 2 workers × 500 rounds (the boundary);
- `n = 0` and `n = 1` rejected;
- the lock-order rule, called single-threaded;
- a forced worst case, where a `Barrier` makes every worker try to hold its left lock at the
  same moment;
- a self-check that the same harness catches the naive left-first version (it does deadlock);
- a 5 × 2,000-round stress test;
- a production-style 6-shard migration ring.

Deadlock is detected with join deadlines. No sleep decides a result.

## 11. Interview Talk Track
"This is dining philosophers wearing a DevOps badge: migration workers that each need two
adjacent shard locks. The deadlock is a cycle where everyone holds their left lock and waits
for their right. I break it with a global lock order: always take the lower-numbered lock
first. For every worker except the last, that's left then right. For the last worker, whose
right lock wraps to 0, it's right then left. Now waiting only goes from lower to higher locks,
and that can't form a cycle. Each worker still runs in parallel with its non-neighbours, so we
keep the throughput a global lock would lose. It's the same advice PostgreSQL gives: update rows
in primary-key order. And I test it by forcing the bad interleaving with a barrier, then
proving the naive version really deadlocks under the same harness."

## 12. Level Up
1. **"Workers need an arbitrary set of locks, not two neighbours."** Sort the set by a global
   key (shard ID, row primary key, or the lock's name) and acquire in that order. Release in
   reverse. The rule scales to any number of locks as long as every code path uses the same order.
2. **"The locks are distributed (etcd or Redis) and a worker can die while holding one."**
   Use leases with TTLs and fencing tokens. Each acquisition returns an increasing token, and
   the storage rejects writes carrying an old token. Order still prevents deadlock, and leases
   handle crashed holders.
3. **"You can't control the order: third-party code takes locks too."** Fall back to detection:
   `try_acquire` with a timeout, and on timeout release everything, back off with jitter and
   retry. Or build a wait-for graph and break cycles the way PostgreSQL does. Add a metric for
   lock wait time so a hang shows up as an alert.

## 13. Related Chips
- **DC-PLAT-13 Backpressure Queue**: the other core `threading` pattern, condition variables.
- **DC-PLAT-02 Circular Dependency Detector**: a deadlock is a cycle in the wait-for graph.
- **DC-REL-07 Safe Services Finder**: nodes caught in or leading into cycles can never finish.
