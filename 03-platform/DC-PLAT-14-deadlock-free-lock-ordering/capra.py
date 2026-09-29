"""Capra Playground export for DC-PLAT-14 (see tools/export_capra.py).

Threads run inside the driver. A recorder checks the safety invariants on every
callback, a Barrier forces the worst-case interleaving ("everyone grabs their
left lock at once"), and joins have a deadline, so a deadlock returns
"stuck" > 0 instead of hanging the run.
"""

SPEC = {"kind": "driver", "fn": "LockTable", "params": ["scenario", "n", "rounds"], "types": {}, "ret": "value", "cmp": "exact"}

DRIVER = '''
import threading as _th
import time as _time


class _Ring:
    def __init__(self, n):
        self.n = n
        self.guard = _th.Lock()
        self.holder = [None] * n
        self.worked = [0] * n
        self.violations = 0

    def take(self, w, lock):
        with self.guard:
            if self.holder[lock] is not None:
                self.violations += 1
            self.holder[lock] = w

    def release(self, w, lock):
        with self.guard:
            if self.holder[lock] != w:
                self.violations += 1
            self.holder[lock] = None

    def work(self, w):
        with self.guard:
            if self.holder[w] != w or self.holder[(w + 1) % self.n] != w:
                self.violations += 1
            self.worked[w] += 1


def __drive(args):
    scenario, n, rounds = args["scenario"], args["n"], args["rounds"]
    try:
        table = LockTable(n)
    except ValueError:
        return "ValueError"

    if scenario == "order":
        seqs = []
        for w in range(n):
            calls = []
            table.run_job(w, lambda: calls.append("take L"), lambda: calls.append("take R"),
                          lambda: calls.append("work"), lambda: calls.append("release L"),
                          lambda: calls.append("release R"))
            seqs.append(calls[:3])
        return seqs

    ring = _Ring(n)
    errors = []
    barrier = _th.Barrier(n) if scenario == "forced" else None

    def worker(w):
        try:
            for r in range(rounds):
                def take_left(w=w, r=r):
                    ring.take(w, w)
                    if barrier is not None and r == 0:
                        try:
                            barrier.wait(0.2)  # at most n-1 can arrive with a correct order
                        except _th.BrokenBarrierError:
                            pass
                table.run_job(w, take_left,
                              lambda w=w: ring.take(w, (w + 1) % n),
                              lambda w=w: ring.work(w),
                              lambda w=w: ring.release(w, w),
                              lambda w=w: ring.release(w, (w + 1) % n))
        except BaseException as e:
            errors.append(type(e).__name__)

    threads = [_th.Thread(target=worker, args=(w,), daemon=True) for w in range(n)]
    for t in threads:
        t.start()
    deadline = _time.monotonic() + 1.5
    for t in threads:
        t.join(max(0.0, deadline - _time.monotonic()))
    return {"worked": ring.worked, "violations": ring.violations,
            "stuck": sum(t.is_alive() for t in threads), "errors": errors}
'''

EXAMPLES = [
    {"args": {"scenario": "order", "n": 5, "rounds": 1},
     "explanation": "The first two lock takes and the work call for each worker. Workers 0-3 take their left (lower) lock first; worker 4's right lock is lock 0, the lower one, so it takes right first.",
     "why": {"t": "Lock order rule", "d": "Always acquire the lower-numbered lock first."}},
    {"args": {"scenario": "forced", "n": 5, "rounds": 20},
     "explanation": "All workers try to hold their first lock at the same moment. With a global order nobody deadlocks: every worker works 20 times and no thread is stuck.",
     "why": {"t": "Worst-case interleaving", "d": "The interleaving that deadlocks a naive left-first order."}},
]

TESTS = [
    {"args": {"scenario": "ring", "n": 0, "rounds": 1},
     "why": {"t": "No workers", "d": "Fewer than 2 workers is rejected with ValueError."}},
    {"args": {"scenario": "ring", "n": 1, "rounds": 1},
     "why": {"t": "One worker", "d": "One worker would need the same lock twice: rejected with ValueError."}},
    {"args": {"scenario": "ring", "n": 2, "rounds": 300},
     "why": {"t": "Two workers", "d": "The smallest ring: both workers need both locks."}},
    {"args": {"scenario": "order", "n": 2, "rounds": 1},
     "why": {"t": "Order with 2 workers", "d": "Worker 1's right lock wraps to lock 0."}},
    {"args": {"scenario": "ring", "n": 5, "rounds": 1},
     "why": {"t": "One round", "d": "Five workers, one job each."}},
    {"args": {"scenario": "forced", "n": 3, "rounds": 50},
     "why": {"t": "Forced, 3 workers", "d": "The worst-case interleaving on a small ring."}},
    {"args": {"scenario": "ring", "n": 5, "rounds": 1000},
     "why": {"t": "Stress", "d": "5,000 jobs with no violations and no deadlock."}},
    {"args": {"scenario": "ring", "n": 6, "rounds": 200},
     "why": {"t": "Shard migration", "d": "6 workers each move rows between shard i and shard i+1, so each locks two shards."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Global lock order (Optimal)",
     "description": "Each worker needs two neighboring locks. Acquire the lower-numbered one first, then the higher one; release in reverse. With one global order, no cycle of waiting workers can form.",
     "time": "O(1) per job, excluding waiting", "space": "O(n)",
     "keyPoints": ["Deadlock needs a cycle; a global order makes cycles impossible", "Only the last worker (whose right lock wraps to 0) reverses its order", "Report take right after acquiring, release right before releasing"]},
]

WAYS_TO_SOLVE = [
    {"name": "One global lock", "idea": "Wrap every job in a single lock.",
     "time": "O(1)", "space": "O(1)", "use": "Trivially safe, but only one worker runs at a time."},
    {"name": "Try and back off", "idea": "Take one lock, try the other, release and retry if busy.",
     "time": "Unbounded under contention", "space": "O(n)", "use": "Avoids deadlock but can livelock."},
    {"name": "Global lock order", "idea": "Always take the lower-numbered lock first.",
     "time": "O(1)", "space": "O(n)", "use": "Database row locks, distributed locks, any multi-lock code."},
]

SOLUTIONS.append({
    "name": "Waiter hands out both locks",
    "description": "A single Condition acts as a waiter: a worker waits until both of its locks are free, marks them busy in one step, works, then frees them and wakes the others. Nobody ever holds one lock while waiting for another, so no cycle can form.",
    "time": "O(1) per job, excluding waiting", "space": "O(n)",
    "keyPoints": ["Take both locks atomically or none", "notify_all after releasing so neighbors re-check", "Simple to reason about, but every job touches one shared monitor"],
    "code": '''from __future__ import annotations

import threading


class LockTable:
    def __init__(self, n: int) -> None:
        if n < 2:
            raise ValueError("need at least 2 workers")
        self._n = n
        self._busy = [False] * n
        self._cv = threading.Condition()

    def run_job(self, worker, take_left, take_right, work, release_left, release_right) -> None:
        left, right = worker, (worker + 1) % self._n
        with self._cv:
            while self._busy[left] or self._busy[right]:
                self._cv.wait()
            self._busy[left] = self._busy[right] = True
        if left < right:
            take_left()
            take_right()
            work()
            release_right()
            release_left()
        else:
            take_right()
            take_left()
            work()
            release_left()
            release_right()
        with self._cv:
            self._busy[left] = self._busy[right] = False
            self._cv.notify_all()
''',
})

VARIANT_TITLE = "Ring of workers"
VARIANT_APPROACH = "Global lock order · O(1) per job · O(n)"

SHARD_DRIVER = '''
import threading as _th
import time as _time


def __drive(args):
    scenario, n = args["scenario"], args["n"]
    try:
        table = ShardLocks(n)
    except ValueError:
        return "ValueError"
    plans, rounds = args["plans"], args["rounds"]

    if scenario == "order":
        out = []
        for txn in plans:
            got = []
            table.run_txn(txn, lambda s: got.append("take %d" % s), lambda: got.append("work"),
                          lambda s: got.append("release %d" % s))
            out.append(got)
        return out

    guard = _th.Lock()
    holder = {}
    stats = {"violations": 0}
    worked = [0] * len(plans)
    errors = []
    barrier = _th.Barrier(len(plans)) if scenario == "forced" else None

    def worker(w):
        try:
            for r in range(rounds):
                txn = plans[w][r % len(plans[w])]
                first = [r == 0]

                def take(s):
                    with guard:
                        if holder.get(s) is not None:
                            stats["violations"] += 1
                        holder[s] = w
                    if barrier is not None and first[0]:
                        first[0] = False
                        try:
                            barrier.wait(0.2)
                        except _th.BrokenBarrierError:
                            pass

                def release(s):
                    with guard:
                        if holder.get(s) != w:
                            stats["violations"] += 1
                        holder[s] = None

                def work():
                    with guard:
                        if any(holder.get(s) != w for s in txn):
                            stats["violations"] += 1
                        worked[w] += 1

                table.run_txn(txn, take, work, release)
        except BaseException as e:
            errors.append(type(e).__name__)

    threads = [_th.Thread(target=worker, args=(w,), daemon=True) for w in range(len(plans))]
    for t in threads:
        t.start()
    deadline = _time.monotonic() + 1.5
    for t in threads:
        t.join(max(0.0, deadline - _time.monotonic()))
    return {"worked": worked, "violations": stats["violations"],
            "stuck": sum(t.is_alive() for t in threads), "errors": errors}
'''


def _sh(scenario, n, plans, rounds=1):
    return {"scenario": scenario, "n": n, "plans": plans, "rounds": rounds}


def _audit_large():
    locks = [f"L{i:02d}" for i in range(30)]
    traces = [[locks[i], locks[j]] for i in range(30) for j in range(i + 1, min(30, i + 4))]
    traces.append(["L05", "L20", "L29"])
    traces.append(["L29", "L03"])
    return {"traces": traces}


VARIANTS = [
    {
        "key": "lock-order-audit",
        "title": "Lock-order inversion audit",
        "approach": "Incremental cycle check on the acquired-before graph · O(T · k² · (V + E)) · O(V + E)",
        "spec": {"kind": "fn", "fn": "first_inversion", "params": ["traces"], "cmp": "exact"},
        "statement": (
            "Linux's lockdep finds deadlocks **before** they happen by recording, for every lock taken, which locks were already held.\n"
            "\n"
            "### Input\n"
            "- `traces[t]`: the lock names one code path acquires, in order, each held until the end of the trace\n"
            "\n"
            "### Output\n"
            "- The index of the **first** trace that creates a cycle in the acquired-before graph (a possible deadlock)\n"
            "- `-1` if the lock order stays consistent\n"
            "\n"
            "### Rules\n"
            "- A trace adds an edge `a` before `b` for every pair where `a` comes earlier in the trace\n"
            "- Process traces in order\n"
            "- If anything ever takes `A` then `B`, and anything else takes `B` then `A`, the two can deadlock even if the test run was lucky"
        ),
        "examples": [
            {"args": {"traces": [["db", "cache"], ["cache", "queue"], ["queue", "db"]]},
             "explanation": "db before cache before queue, then a path takes queue before db: a three-lock cycle at trace 2.",
             "why": {"t": "Three-lock cycle", "d": "No single pair is reversed, but the chain is."}},
            {"args": {"traces": [["a", "b", "c"], ["a", "c"], ["b", "c"]]},
             "explanation": "Every trace agrees with the order a, b, c.",
             "why": {"t": "Consistent order", "d": "Repeated edges in the same direction are fine."}},
        ],
        "constraints": ["0 ≤ len(traces) ≤ 1000", "1 ≤ len(traces[t]) ≤ 8, lock names distinct within a trace",
                        "At most 500 distinct lock names"],
        "hints": [
            "A trace `[a, b, c]` adds three edges: a before b, a before c, b before c.",
            "Adding edge `a` before `b` closes a cycle exactly when `a` is already reachable from `b`.",
            "Skip edges you have already seen; only a new edge can create a new cycle.",
        ],
        "tests": [
            {"args": {"traces": []}, "why": {"t": "No traces", "d": "Nothing recorded: -1."}},
            {"args": {"traces": [["a"], ["b"]]}, "why": {"t": "Single locks", "d": "One lock per trace adds no edges."}},
            {"args": {"traces": [["a", "b"], ["b", "a"]]}, "why": {"t": "Classic AB-BA", "d": "The two-lock inversion is caught at trace 1."}},
            {"args": {"traces": [["a", "b"], ["a", "b"], ["c", "d"], ["d", "e"]]}, "why": {"t": "Duplicates", "d": "A repeated trace and unrelated locks: -1."}},
            {"args": {"traces": [["x", "y", "z"], ["w", "x"], ["z", "w"], ["y", "x"]]}, "why": {"t": "First of several", "d": "Trace 2 closes w, x, y, z; the later AB-BA is not reported."}},
            {"args": _audit_large(), "why": {"t": "Large input", "d": "30 locks taken in rank order, then one late path goes from L29 back to L03."}},
        ],
        "solutions": [
            {"name": "Incremental cycle check (Optimal)",
             "description": "Keep the acquired-before graph. For every new edge a before b, DFS from b; if it reaches a, this trace closes a cycle. Otherwise add the edge.",
             "time": "O(T · k² · (V + E))", "space": "O(V + E)",
             "keyPoints": ["Only a new edge can close a cycle", "Reachability from b to a is the cycle test", "Known edges are skipped for free"],
             "code": '''def first_inversion(traces):
    adj = {}

    def reaches(src, dst):
        stack, seen = [src], {src}
        while stack:
            node = stack.pop()
            if node == dst:
                return True
            for nxt in adj.get(node, ()):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return False

    for t, trace in enumerate(traces):
        for i in range(len(trace)):
            for j in range(i + 1, len(trace)):
                a, b = trace[i], trace[j]
                if b in adj.get(a, ()):
                    continue
                if reaches(b, a):
                    return t
                adj.setdefault(a, set()).add(b)
    return -1
'''},
            {"name": "Full cycle detection after every trace", "slow": True,
             "description": "Add the trace's edges, then run Kahn's algorithm on the whole graph; if some lock is never peeled, there is a cycle.",
             "time": "O(T · (V + E))", "space": "O(V + E)",
             "keyPoints": ["Reuses a standard topological sort", "Re-checks the whole graph every time"],
             "code": '''from collections import deque


def first_inversion(traces):
    adj = {}
    for t, trace in enumerate(traces):
        for i in range(len(trace)):
            adj.setdefault(trace[i], set())
            for j in range(i + 1, len(trace)):
                adj[trace[i]].add(trace[j])
                adj.setdefault(trace[j], set())
        indeg = {u: 0 for u in adj}
        for u in adj:
            for v in adj[u]:
                indeg[v] += 1
        q = deque(u for u in adj if indeg[u] == 0)
        peeled = 0
        while q:
            u = q.popleft()
            peeled += 1
            for v in adj[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)
        if peeled < len(adj):
            return t
    return -1
'''},
        ],
        "starter": '''def first_inversion(traces: list[list[str]]) -> int:
    pass
''',
    },
    {
        "key": "multi-shard-transactions",
        "title": "Multi-shard transactions",
        "approach": "Sorted, de-duplicated lock order · O(k log k) per transaction · O(n)",
        "spec": {"kind": "driver", "fn": "ShardLocks", "params": ["scenario", "n", "plans", "rounds"], "cmp": "exact",
                 "driver": SHARD_DRIVER},
        "statement": (
            "A resharding job moves rows between **any** set of shards, not just two neighbors.\n"
            "\n"
            "### Methods\n"
            "- `ShardLocks(n)`: locks over shards `0..n-1`; `n < 1` raises `ValueError`\n"
            "- `run_txn(shards, take, work, release)`: run one transaction over `shards`\n"
            "\n"
            "### Rules\n"
            "- `shards` lists the shards one transaction touches, in any order, possibly with repeats or empty\n"
            "- Hold the lock of **every** distinct shard while calling `work()`\n"
            "- Call `take(s)` right after acquiring shard `s`, and `release(s)` right before releasing it\n"
            "- Release in the reverse order of acquiring\n"
            "- Many threads call `run_txn` at once; it must never deadlock\n"
            "- The tests replay transactions sequentially to check the order, and under threads to check safety"
        ),
        "examples": [
            {"args": _sh("order", 5, [[3, 1, 3], []]),
             "explanation": "Shards 1 and 3, lowest first, each once; released in reverse. An empty transaction just works.",
             "why": {"t": "Sorted and de-duplicated", "d": "A repeated shard is locked once; order is ascending."}},
            {"args": _sh("forced", 3, [[[0, 1]], [[1, 2]], [[2, 0]]], 30),
             "explanation": "Three transactions form a ring. With a global order nobody deadlocks: each runs 30 times.",
             "why": {"t": "Worst-case interleaving", "d": "Taking shards in the given order would deadlock here."}},
        ],
        "constraints": ["1 ≤ n ≤ 100, shard ids in 0..n-1", "0 ≤ len(shards) ≤ 10", "Up to 8 threads, 500 transactions each"],
        "hints": [
            "The two-lock rule generalizes: acquire every lock in one global order.",
            "Sort the distinct shard ids; a set removes repeats, which would otherwise self-deadlock on a plain Lock.",
            "Release in reverse, and make sure release still happens if `work()` raises.",
        ],
        "tests": [
            {"args": _sh("order", 0, [[0]]), "why": {"t": "No shards", "d": "n = 0 is rejected with ValueError."}},
            {"args": _sh("order", 1, [[0, 0, 0]]), "why": {"t": "One shard, repeated", "d": "Locked once, released once."}},
            {"args": _sh("order", 8, [[7, 0, 4], [2], [5, 6, 5, 1]]), "why": {"t": "Order check", "d": "Several transactions, each ascending."}},
            {"args": _sh("ring", 4, [[[0, 1, 2, 3]], [[3, 2, 1, 0]], [[1, 3]], [[2, 0]]], 200),
             "why": {"t": "Opposite orders", "d": "Two threads list the same shards in opposite orders."}},
            {"args": _sh("forced", 4, [[[0, 1]], [[1, 2]], [[2, 3]], [[3, 0]]], 30), "why": {"t": "Forced ring of 4", "d": "The dining-philosophers shape with four shards."}},
            {"args": _sh("ring", 6, [[[0, 2, 4], [1]], [[4, 5], []], [[5, 3, 1, 1]], [[2, 3], [0, 5]], [[1, 4]], [[0, 3, 5]]], 150),
             "why": {"t": "Stress", "d": "Six threads, mixed and empty transactions, 900 in total."}},
        ],
        "solutions": [
            {"name": "Sorted lock order (Optimal)",
             "description": "Acquire the distinct shards in ascending order, report each take, run the work, then release in reverse inside finally.",
             "time": "O(k log k) per transaction, excluding waiting", "space": "O(n)",
             "keyPoints": ["One global order rules out waiting cycles", "set() removes repeats before locking", "finally releases even if work fails"],
             "code": '''import threading


class ShardLocks:
    def __init__(self, n):
        if n < 1:
            raise ValueError("need at least one shard")
        self._locks = [threading.Lock() for _ in range(n)]

    def run_txn(self, shards, take, work, release):
        held = []
        try:
            for s in sorted(set(shards)):
                self._locks[s].acquire()
                held.append(s)
                take(s)
            work()
        finally:
            for s in reversed(held):
                release(s)
                self._locks[s].release()
'''},
            {"name": "One big lock", "slow": True,
             "description": "Serialize every transaction behind a single lock. Trivially deadlock-free, but no two transactions ever run at once, even on unrelated shards.",
             "time": "O(k log k) per transaction, fully serialized", "space": "O(1)",
             "keyPoints": ["Safe by construction", "Throughput of a single thread"],
             "code": '''import threading


class ShardLocks:
    def __init__(self, n):
        if n < 1:
            raise ValueError("need at least one shard")
        self._big = threading.Lock()

    def run_txn(self, shards, take, work, release):
        order = sorted(set(shards))
        with self._big:
            for s in order:
                take(s)
            work()
            for s in reversed(order):
                release(s)
'''},
        ],
        "starter": '''import threading


class ShardLocks:
    def __init__(self, n: int) -> None:
        pass

    def run_txn(self, shards, take, work, release) -> None:
        pass
''',
    },
]
