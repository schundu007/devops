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
     "description": "Each worker needs two neighbouring locks. Acquire the lower-numbered one first, then the higher one; release in reverse. With one global order, no cycle of waiting workers can form.",
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
