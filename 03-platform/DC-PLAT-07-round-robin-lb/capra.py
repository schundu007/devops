"""Capra Playground export for DC-PLAT-07 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "busiest_backends", "params": ["k", "arrival", "load"], "types": {}, "ret": "value", "cmp": "exact"}

EXAMPLES = [
    {"args": {"k": 3, "arrival": [1, 2, 3, 4, 5], "load": [5, 2, 3, 3, 3]},
     "explanation": "Request 3 prefers backend 0 (busy) and skips to 1. Request 4 prefers 1 (busy), then 2 (busy), then 0 (busy): dropped. Backend 1 served 2.",
     "why": {"t": "Skip busy", "d": "Busy backends are skipped in order, wrapping around."}},
    {"args": {"k": 3, "arrival": [1, 2, 3], "load": [10, 12, 11]},
     "explanation": "Each backend served one request, so all three tie.",
     "why": {"t": "Tie", "d": "Every backend with the top count is returned."}},
]


def _large():
    rng = random.Random(1606)
    n, t = 3000, 0
    arrival, load = [], []
    for _ in range(n):
        t += rng.randint(1, 4)
        arrival.append(t)
        load.append(rng.randint(1, 60))
    return {"k": 17, "arrival": arrival, "load": load}


TESTS = [
    {"args": {"k": 1, "arrival": [1], "load": [1]}, "why": {"t": "Single backend", "d": "One backend, one request."}},
    {"args": {"k": 1, "arrival": [1, 2, 3], "load": [5, 1, 1]}, "why": {"t": "All dropped", "d": "While the only backend is busy, requests are dropped."}},
    {"args": {"k": 2, "arrival": [1, 3], "load": [2, 2]}, "why": {"t": "Free at arrival", "d": "A backend that finishes exactly at the arrival time is free."}},
    {"args": {"k": 4, "arrival": [1, 2, 3, 4, 5, 6, 7], "load": [100, 100, 100, 1, 1, 1, 1]},
     "why": {"t": "Hot backend", "d": "Three backends stay busy; the fourth takes every later request."}},
    {"args": {"k": 3, "arrival": [1, 2, 3, 4], "load": [1, 1, 1, 1]}, "why": {"t": "Plain round-robin", "d": "Nobody is ever busy: request i goes to i % k."}},
    {"args": {"k": 5, "arrival": [1, 2], "load": [1, 1]}, "why": {"t": "More backends than requests", "d": "Idle backends still count, with 0 served."}},
    {"args": _large(), "why": {"t": "Large input", "d": "3,000 requests over 17 backends."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Sorted idle list + busy heap (Optimal)",
     "description": "Keep a sorted list of idle backends and a min-heap of (free time, backend). Release finished backends, then binary-search the idle list for the first ID >= i % k, wrapping to the front.",
     "time": "O(n log n) plus O(k) list shifts", "space": "O(k)",
     "keyPoints": ["Finished at t counts as free at t", "bisect finds the next idle backend with wrap-around", "Drop the request when nobody is idle"]},
    {"name": "Check backends one by one", "slow": True,
     "description": "For each request, try backends i % k, i % k + 1, … until one is idle.",
     "time": "O(n · k)", "space": "O(k)",
     "keyPoints": ["Direct simulation", "10^10 steps at the limits"],
     "code": '''from __future__ import annotations


def busiest_backends(k: int, arrival: list[int], load: list[int]) -> list[int]:
    free_at = [0] * k
    served = [0] * k
    for i, (t, d) in enumerate(zip(arrival, load)):
        for step in range(k):
            b = (i + step) % k
            if free_at[b] <= t:
                free_at[b] = t + d
                served[b] += 1
                break
    top = max(served)
    return [b for b in range(k) if served[b] == top]
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Linear probe", "idea": "Try i % k, i % k + 1, … for each request.", "time": "O(n · k)", "space": "O(k)",
     "use": "Few backends."},
    {"name": "Sorted idle set + heap", "idea": "Binary-search the idle set; a heap releases finished backends.",
     "time": "O(n log k) with a balanced tree", "space": "O(k)", "use": "Large pools."},
]

VARIANT_TITLE = "Busiest backends"
VARIANT_APPROACH = "Sorted idle list + busy heap · O(n log n) · O(k)"


def _assign_large():
    rng = random.Random(1882)
    return {"weights": [rng.randint(1, 20) for _ in range(30)], "jobs": [rng.randint(1, 60) for _ in range(2000)]}


def _runner_large():
    rng = random.Random(2402)
    starts = rng.sample(range(0, 20000), 1500)
    return {"n": 12, "jobs": [[s, s + rng.randint(1, 200)] for s in starts]}


def aj(weights, jobs, t, d):
    return {"args": {"weights": weights, "jobs": jobs}, "why": {"t": t, "d": d}}


def br(n, jobs, t, d):
    return {"args": {"n": n, "jobs": jobs}, "why": {"t": t, "d": d}}


VARIANTS = [
    {
        "key": "weighted-queue",
        "title": "Smallest free node, jobs wait",
        "approach": "Free heap by (weight, id) + busy heap by finish time · O((n + k) log k) · O(k)",
        "spec": {"kind": "fn", "fn": "assign_backends", "params": ["weights", "jobs"]},
        "statement": (
            "A build farm prefers its cheapest node for every job, and it never drops work: a job that finds every node busy "
            "waits in a queue.\n\n"
            "Node `i` has cost `weights[i]`. Job `j` arrives at second `j` and runs for `jobs[j]` seconds. Jobs leave the queue "
            "in order, each as soon as some node is free (a node finishing at time t is free at t).\n\n"
            "A starting job takes the free node with the smallest weight, then the smallest index. "
            "Return the node each job ran on."
        ),
        "examples": [
            {"args": {"weights": [3, 3, 2], "jobs": [1, 2, 3, 2, 1, 2]},
             "explanation": "Job 0 takes node 2 (weight 2); job 1 takes node 2 again at second 1; job 2 takes node 0 at second 2; job 3 gets node 2 back at second 3, and job 4 takes node 1.",
             "why": {"t": "Weight first, then index", "d": "The cheapest free node wins; index breaks ties."}},
            {"args": {"weights": [5], "jobs": [4, 1, 1]},
             "explanation": "One node: job 1 waits until second 4, job 2 until second 5. Every job still runs on node 0.",
             "why": {"t": "Queueing", "d": "Busy means wait, never drop."}},
        ],
        "constraints": ["1 ≤ weights.length ≤ 10⁴", "1 ≤ jobs.length ≤ 10⁴", "1 ≤ weights[i], jobs[j] ≤ 10⁵"],
        "hints": [
            "Keep free nodes in a heap ordered by (weight, index), and busy nodes in a heap ordered by finish time.",
            "Keep a clock t = max(t, j). Release every busy node with finish time <= t before choosing.",
            "If nothing is free, jump the clock to the earliest finish time and release every node finishing then.",
        ],
        "tests": [
            aj([1], [1], "One node, one job", "The only choice."),
            aj([2, 1], [1, 1, 1], "Always free", "Jobs of one second: the cheapest node is free again each time."),
            aj([1, 1, 1], [10, 10, 10, 1], "All busy", "Every node is busy: job 3 waits for the first to finish at second 10."),
            aj([4, 2, 3], [5, 5, 5, 5, 5, 5], "Long jobs", "The queue forms and drains in weight order."),
            aj([7, 7], [3, 1, 1, 1], "Equal weights", "Index decides every tie."),
            aj([1, 100], [2, 2, 2, 2], "Cheap node reused", "Finishing exactly when the next job arrives counts as free."),
            {"args": _assign_large(), "why": {"t": "Large input", "d": "2,000 jobs over 30 nodes."}},
        ],
        "solutions": [
            {"name": "Two heaps and a clock (Optimal)",
             "description": "Free heap of (weight, index), busy heap of (finish, weight, index). Advance the clock to the job's arrival, or to the next finish when all are busy.",
             "time": "O((n + k) log k)", "space": "O(k)",
             "keyPoints": ["Finish at t means free at t", "Jump the clock when all nodes are busy", "Release before choosing"],
             "code": '''import heapq


def assign_backends(weights, jobs):
    free = [(w, i) for i, w in enumerate(weights)]
    heapq.heapify(free)
    busy = []
    out = []
    t = 0
    for j, d in enumerate(jobs):
        t = max(t, j)
        if not free and busy[0][0] > t:
            t = busy[0][0]
        while busy and busy[0][0] <= t:
            _, w, i = heapq.heappop(busy)
            heapq.heappush(free, (w, i))
        w, i = heapq.heappop(free)
        out.append(i)
        heapq.heappush(busy, (t + d, w, i))
    return out
'''},
            {"name": "Scan every node", "slow": True,
             "description": "Track each node's finish time; for each job scan all nodes for free ones, jumping the clock to the earliest finish when none are free.",
             "time": "O(n · k)", "space": "O(k)",
             "keyPoints": ["Direct simulation", "A full scan per job"],
             "code": '''def assign_backends(weights, jobs):
    k = len(weights)
    free_at = [0] * k
    out = []
    t = 0
    for j, d in enumerate(jobs):
        t = max(t, j)
        if all(f > t for f in free_at):
            t = min(free_at)
        best = min((i for i in range(k) if free_at[i] <= t), key=lambda i: (weights[i], i))
        free_at[best] = t + d
        out.append(best)
    return out
'''},
        ],
        "starter": '''def assign_backends(weights, jobs):
    """Node index each job runs on."""
    pass
''',
    },
    {
        "key": "ci-runners",
        "title": "CI runner that ran the most jobs",
        "approach": "Free-id heap + busy heap by (end, id) · O(m log m + m log n) · O(n)",
        "spec": {"kind": "fn", "fn": "busiest_runner", "params": ["n", "jobs"]},
        "statement": (
            "A CI system has `n` runners numbered `0..n-1`. `jobs[i] = [start, end]` asks for a runner over `[start, end)`; "
            "every start time is distinct.\n\n"
            "- Jobs are handled in order of start time.\n"
            "- A job takes the **lowest-numbered** free runner.\n"
            "- If none is free, it waits for the runner that frees up first (lowest number on a tie) and keeps its "
            "original duration, so it ends later.\n\n"
            "Return the runner that ran the most jobs, the lowest number on a tie."
        ),
        "examples": [
            {"args": {"n": 2, "jobs": [[0, 10], [1, 5], [2, 7], [3, 4]]},
             "explanation": "Runners 0 and 1 take the first two jobs. The job at 2 waits for runner 1 (free at 5) and ends at 10. The job at 3 waits for runner 0 (free at 10) and ends at 11. Each ran two jobs: runner 0.",
             "why": {"t": "Delayed jobs", "d": "A delayed job keeps its duration and ties go to the lowest id."}},
        ],
        "constraints": ["1 ≤ n ≤ 100", "1 ≤ jobs.length ≤ 10⁴", "0 ≤ start < end ≤ 5 · 10⁵", "All start times are distinct"],
        "hints": [
            "Sort by start. Keep free runner ids in a min-heap and busy runners in a heap of (end, id).",
            "Before placing a job, release every runner whose end is at or before the job's start.",
            "When none is free, pop the busy top (earliest end, lowest id) and push it back with end + duration.",
        ],
        "tests": [
            br(1, [[0, 1]], "Single runner", "One job, one runner."),
            br(3, [[5, 6]], "Idle runners", "Only runner 0 works; ties among zeros do not matter."),
            br(2, [[0, 5], [5, 10], [10, 15]], "Back to back", "Free exactly at the next start: runner 0 takes all."),
            br(2, [[3, 4], [0, 10], [1, 2]], "Unsorted input", "Jobs must be handled in start order."),
            br(3, [[0, 10], [1, 10], [2, 10], [3, 4], [4, 5]], "Tie on release", "Three runners free at 10: runner 0 is chosen first."),
            br(2, [[0, 1], [1, 2], [2, 3], [3, 4]], "Runner 0 hogs", "Short jobs always find runner 0 free."),
            {"args": _runner_large(), "why": {"t": "Large input", "d": "1,500 jobs over 12 runners."}},
        ],
        "solutions": [
            {"name": "Two heaps (Optimal)",
             "description": "Free heap of ids and busy heap of (end, id). Release finished runners, take the lowest free id, or delay the job onto the earliest-ending runner.",
             "time": "O(m log m + m log n)", "space": "O(n)",
             "keyPoints": ["Sort jobs by start first", "(end, id) tie-breaks by the lowest id", "A delayed job ends at end + duration"],
             "code": '''import heapq


def busiest_runner(n, jobs):
    free = list(range(n))
    busy = []
    count = [0] * n
    for s, e in sorted(jobs):
        while busy and busy[0][0] <= s:
            heapq.heappush(free, heapq.heappop(busy)[1])
        if free:
            r = heapq.heappop(free)
            heapq.heappush(busy, (e, r))
        else:
            end, r = heapq.heappop(busy)
            heapq.heappush(busy, (end + e - s, r))
        count[r] += 1
    return count.index(max(count))
'''},
            {"name": "Scan every runner", "slow": True,
             "description": "Track each runner's end time; for each job scan for the lowest free runner, else the earliest-ending one.",
             "time": "O(m · n)", "space": "O(n)",
             "keyPoints": ["Easy to trust", "A full scan per job"],
             "code": '''def busiest_runner(n, jobs):
    end_at = [0] * n
    count = [0] * n
    for s, e in sorted(jobs):
        free = [r for r in range(n) if end_at[r] <= s]
        if free:
            r = free[0]
            end_at[r] = e
        else:
            r = min(range(n), key=lambda x: (end_at[x], x))
            end_at[r] += e - s
        count[r] += 1
    return count.index(max(count))
'''},
        ],
        "starter": '''def busiest_runner(n, jobs):
    """Runner id that ran the most jobs (lowest id on a tie)."""
    pass
''',
    },
]
