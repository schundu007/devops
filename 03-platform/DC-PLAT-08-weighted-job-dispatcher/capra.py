"""Capra Playground export for DC-PLAT-08 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "assign_jobs", "params": ["weights", "durations"], "types": {}, "ret": "value", "cmp": "exact"}

EXAMPLES = [
    {"args": {"weights": [3, 3, 2], "durations": [1, 2, 3, 2, 1, 2]},
     "explanation": "Worker 2 has the smallest weight, so it takes job 0; ties on weight go to the lower index.",
     "why": {"t": "Weight then index", "d": "The free worker with the smallest weight wins, then the lowest index."}},
    {"args": {"weights": [5, 1, 4], "durations": [2, 1, 2, 1, 2, 2]},
     "explanation": "When nobody is idle, the next job waits for the first worker to finish.",
     "why": {"t": "Waiting", "d": "Jobs wait when every worker is busy."}},
]


def _large():
    rng = random.Random(1882)
    return {"weights": [rng.randint(1, 50) for _ in range(40)], "durations": [rng.randint(1, 80) for _ in range(3000)]}


TESTS = [
    {"args": {"weights": [7], "durations": [3]}, "why": {"t": "Single", "d": "One worker, one job."}},
    {"args": {"weights": [7], "durations": [3, 1, 2]}, "why": {"t": "One worker", "d": "Every job queues behind the last."}},
    {"args": {"weights": [2, 2, 2], "durations": [5, 5, 5, 1]}, "why": {"t": "Equal weights", "d": "Ties always go to the lowest index."}},
    {"args": {"weights": [1, 2], "durations": [1, 1, 1, 1]}, "why": {"t": "Instant free", "d": "A worker that finishes by the next second takes the next job."}},
    {"args": {"weights": [3, 1, 2], "durations": [10, 10, 10, 1, 1]}, "why": {"t": "All busy", "d": "The first finisher takes the waiting job."}},
    {"args": {"weights": [4, 4], "durations": [2, 2, 2, 2, 2]}, "why": {"t": "Simultaneous finish", "d": "Two workers free at once: the better one goes first."}},
    {"args": _large(), "why": {"t": "Large input", "d": "3,000 jobs over 40 workers."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Two min-heaps (Optimal)",
     "description": "An idle heap keyed by (weight, index) and a busy heap keyed by finish time. The clock moves to max(clock, j); if nobody is idle, it jumps to the next finish. Release finished workers, then pop the best idle one.",
     "time": "O((n + m) log m)", "space": "O(m + n)",
     "keyPoints": ["Job j cannot start before second j", "Jump the clock when nobody is idle", "Idle order is (weight, index)"]},
    {"name": "Scan all workers", "slow": True,
     "description": "For each job, scan every worker for the idle ones and pick the best, advancing the clock when none is idle.",
     "time": "O(n · m)", "space": "O(m)",
     "keyPoints": ["Direct simulation", "4 · 10^10 steps at the limits"],
     "code": '''from __future__ import annotations


def assign_jobs(weights: list[int], durations: list[int]) -> list[int]:
    free_at = [0] * len(weights)
    out = []
    now = 0
    for j, d in enumerate(durations):
        now = max(now, j)
        if all(f > now for f in free_at):
            now = min(free_at)
        best = min((w, i) for i, w in enumerate(weights) if free_at[i] <= now)[1]
        out.append(best)
        free_at[best] = now + d
    return out
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Scan workers", "idea": "Check every worker for each job.", "time": "O(n · m)", "space": "O(m)",
     "use": "Small pools."},
    {"name": "Two heaps", "idea": "Idle heap by (weight, index), busy heap by finish time.", "time": "O((n + m) log m)",
     "space": "O(m + n)", "use": "Large pools and queues."},
]

VARIANT_TITLE = "Weighted dispatcher"
VARIANT_APPROACH = "Idle heap by (weight, index) + busy heap by finish time · O((n + m) log m) · O(m + n)"


def _runner_large():
    rng = random.Random(2402)
    starts = rng.sample(range(0, 20000), 2500)
    return {"n": 12, "jobs": [[s, s + rng.randint(1, 60)] for s in starts]}


def _sticky_large():
    rng = random.Random(1606)
    arrival, t = [], 0
    for _ in range(2500):
        t += rng.randint(1, 4)
        arrival.append(t)
    return {"k": 15, "arrival": arrival, "load": [rng.randint(1, 50) for _ in arrival]}


_RUNNER_HEAPS = '''from __future__ import annotations

import heapq


def busiest_runner(n: int, jobs: list[list[int]]) -> int:
    free = list(range(n))
    busy: list[tuple[int, int]] = []  # (time it is free again, runner)
    count = [0] * n
    for start, end in sorted(jobs):
        while busy and busy[0][0] <= start:
            heapq.heappush(free, heapq.heappop(busy)[1])
        if free:
            r = heapq.heappop(free)
            heapq.heappush(busy, (end, r))
        else:
            t, r = heapq.heappop(busy)  # wait for the first runner to finish
            heapq.heappush(busy, (t + end - start, r))
        count[r] += 1
    return count.index(max(count))
'''

_RUNNER_SCAN = '''from __future__ import annotations


def busiest_runner(n: int, jobs: list[list[int]]) -> int:
    free_at = [0] * n
    count = [0] * n
    for start, end in sorted(jobs):
        idle = [r for r in range(n) if free_at[r] <= start]
        if idle:
            r = idle[0]
            free_at[r] = end
        else:
            r = min(range(n), key=lambda x: (free_at[x], x))
            free_at[r] += end - start
        count[r] += 1
    return count.index(max(count))
'''

_STICKY_HEAP = '''from __future__ import annotations

import bisect
import heapq


def busiest_backends(k: int, arrival: list[int], load: list[int]) -> list[int]:
    free = list(range(k))                 # sorted indexes of idle backends
    busy: list[tuple[int, int]] = []      # (time it is idle again, backend)
    handled = [0] * k
    for i, (t, d) in enumerate(zip(arrival, load)):
        while busy and busy[0][0] <= t:
            bisect.insort(free, heapq.heappop(busy)[1])
        if not free:
            continue                      # every backend is busy: dropped
        pos = bisect.bisect_left(free, i % k)
        if pos == len(free):
            pos = 0                       # wrap around the ring
        b = free.pop(pos)
        handled[b] += 1
        heapq.heappush(busy, (t + d, b))
    top = max(handled)
    return [b for b in range(k) if handled[b] == top]
'''

_STICKY_SCAN = '''from __future__ import annotations


def busiest_backends(k: int, arrival: list[int], load: list[int]) -> list[int]:
    free_at = [0] * k
    handled = [0] * k
    for i, (t, d) in enumerate(zip(arrival, load)):
        for step in range(k):
            b = (i + step) % k
            if free_at[b] <= t:
                free_at[b] = t + d
                handled[b] += 1
                break
    top = max(handled)
    return [b for b in range(k) if handled[b] == top]
'''

VARIANTS = [
    {
        "key": "busiest-runner",
        "title": "Busiest CI runner",
        "approach": "Free heap by index + busy heap by finish time · O(m log m + m log n) · O(n)",
        "spec": {"kind": "fn", "fn": "busiest_runner", "params": ["n", "jobs"], "cmp": "exact"},
        "statement": "A CI fleet has `n` identical runners, `0..n-1`. `jobs[i] = [start, end]` asks for a runner over `[start, end)`; all start times are different. Jobs are handled in order of start time:\n\n- the job goes to the **lowest-numbered idle** runner (a runner that finishes at `t` is idle at `t`)\n- if no runner is idle, the job waits for the runner that frees up first (ties: lowest number) and keeps its full duration `end - start`\n\nReturn the runner that ran the most jobs; on a tie, the lowest number. Capacity reviews use this to find the runner that wears out first.",
        "examples": [
            {"args": {"n": 2, "jobs": [[0, 10], [1, 5], [2, 7], [3, 4]]},
             "explanation": "Runner 0 takes [0, 10), runner 1 takes [1, 5). The job at 2 waits for runner 1 until 5 and runs to 10; the job at 3 waits for runner 0 until 10 and runs to 11. Each ran 2 jobs, so the answer is 0.",
             "why": {"t": "Delayed jobs", "d": "A waiting job keeps its duration, and ties go to the lower runner."}},
            {"args": {"n": 3, "jobs": [[1, 20], [2, 10], [3, 5], [4, 9], [6, 8]]},
             "explanation": "Runners 0, 1 and 2 start jobs at 1, 2 and 3. The job at 4 waits for runner 2 (free at 5) and runs to 10. The job at 6 finds runners 1 and 2 both free at 10 and takes runner 1. Runners 1 and 2 ran two jobs each, so the answer is 1.",
             "why": {"t": "Tie in free time", "d": "When two busy runners free up together, the lower number takes the waiting job."}},
        ],
        "constraints": ["1 ≤ n ≤ 100", "1 ≤ jobs.length ≤ 10⁵", "0 ≤ start < end ≤ 5 · 10⁵", "All start times are distinct"],
        "hints": [
            "Sort jobs by start. Keep a min-heap of idle runner numbers and a min-heap of (free time, runner) for busy ones.",
            "Before each job, move every busy runner whose free time is <= start back to the idle heap.",
            "If the idle heap is empty, pop the busy heap's top and reschedule it at its free time plus the job's duration.",
        ],
        "tests": [
            {"args": {"n": 1, "jobs": [[0, 1]]}, "why": {"t": "Minimal", "d": "One runner, one job."}},
            {"args": {"n": 3, "jobs": [[0, 5]]}, "why": {"t": "More runners than jobs", "d": "Idle runners never count; runner 0 wins."}},
            {"args": {"n": 2, "jobs": [[0, 2], [2, 4], [4, 6]]}, "why": {"t": "Back to back", "d": "A runner free at t takes a job starting at t, so runner 0 does everything."}},
            {"args": {"n": 2, "jobs": [[5, 6], [0, 10], [1, 2]]}, "why": {"t": "Unsorted input", "d": "Jobs must be handled by start time, not input order."}},
            {"args": {"n": 2, "jobs": [[0, 10], [1, 10], [2, 3], [4, 5]]}, "why": {"t": "Simultaneous finish", "d": "Both runners free at 10: the delayed job takes runner 0."}},
            {"args": {"n": 4, "jobs": [[0, 1], [10, 11], [20, 21], [30, 31]]}, "why": {"t": "Never busy", "d": "Every job finds runner 0 idle."}},
            {"args": _runner_large(), "why": {"t": "Large input", "d": "2,500 jobs on 12 runners with heavy queuing."}},
        ],
        "solutions": [
            {"name": "Two heaps (Optimal)",
             "description": "An idle heap by runner number and a busy heap by (free time, runner). Release finished runners before each job; if none is idle, delay the job onto the first runner to finish.",
             "time": "O(m log m + m log n)", "space": "O(n)",
             "keyPoints": ["Sort by start first", "Idle order is the runner number here, not a weight", "A delayed job keeps its duration"],
             "code": _RUNNER_HEAPS},
            {"name": "Scan every runner", "slow": True,
             "description": "For each job, scan all runners for the lowest idle one, or the one that frees up first.",
             "time": "O(m log m + m · n)", "space": "O(n)",
             "keyPoints": ["A direct simulation", "Every job looks at every runner"],
             "code": _RUNNER_SCAN},
        ],
        "starter": '''from __future__ import annotations


def busiest_runner(n: int, jobs: list[list[int]]) -> int:
    """Return the runner that ran the most jobs (lowest number on a tie)."""
    # TODO
    raise NotImplementedError
''',
    },
    {
        "key": "sticky-backends",
        "title": "Sticky load balancer with drops",
        "approach": "Busy heap + sorted free list searched with bisect · O(n log k) · O(k)",
        "spec": {"kind": "fn", "fn": "busiest_backends", "params": ["k", "arrival", "load"], "cmp": "exact"},
        "statement": "A load balancer has `k` backends in a ring, `0..k-1`. Request `i` arrives at `arrival[i]` (strictly increasing) and keeps a backend busy for `load[i]` seconds, so it is free again at `arrival[i] + load[i]`.\n\n- Request `i` prefers backend `i % k` for cache affinity\n- If that one is busy, it goes to the next idle backend clockwise (`i % k + 1`, and so on, wrapping to 0)\n- If every backend is busy, the request is **dropped**; there is no queue\n\nReturn every backend that handled the most requests, in increasing order.",
        "examples": [
            {"args": {"k": 3, "arrival": [1, 2, 3, 4, 5], "load": [5, 2, 3, 3, 3]},
             "explanation": "Requests 0-2 take backends 0, 1, 2. At 4, request 3 prefers 0 (busy until 6) and finds 1 idle (free at 4). At 5 every backend is busy, so request 4 is dropped. Backend 1 handled two.",
             "why": {"t": "Skip clockwise · Drop", "d": "A busy preferred backend passes the request on; a full ring drops it."}},
            {"args": {"k": 3, "arrival": [1, 2, 3], "load": [10, 12, 11]},
             "explanation": "Each backend handles exactly one request, so all three tie.",
             "why": {"t": "Tie", "d": "Every backend with the top count is returned."}},
        ],
        "constraints": ["1 ≤ k ≤ 10⁴", "1 ≤ arrival.length ≤ 10⁵", "arrival is strictly increasing", "1 ≤ load[i] ≤ 10⁹"],
        "hints": [
            "Busy backends go in a heap by free time; release everyone whose free time is <= the arrival first.",
            "Keep the idle backends as a sorted list. The first idle one at or after i % k is a bisect_left away.",
            "If bisect runs off the end, wrap around to the smallest idle backend.",
        ],
        "tests": [
            {"args": {"k": 1, "arrival": [1], "load": [1]}, "why": {"t": "Minimal", "d": "One backend, one request."}},
            {"args": {"k": 1, "arrival": [1, 2, 3], "load": [1, 1, 1]}, "why": {"t": "Free exactly on arrival", "d": "A backend free at t takes a request arriving at t."}},
            {"args": {"k": 2, "arrival": [1, 2, 3, 4], "load": [100, 100, 1, 1]}, "why": {"t": "All dropped", "d": "After two long requests every later one is dropped."}},
            {"args": {"k": 3, "arrival": [1, 2, 3, 4, 8, 9, 10], "load": [5, 2, 10, 3, 1, 2, 2]}, "why": {"t": "Wrap around", "d": "The next idle backend clockwise is found after wrapping past k - 1."}},
            {"args": {"k": 4, "arrival": [1, 2], "load": [1, 1]}, "why": {"t": "Idle backends tie", "d": "Two backends handle one request each; two handle none."}},
            {"args": {"k": 5, "arrival": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "load": [1] * 10}, "why": {"t": "Round robin", "d": "Short requests always get their preferred backend."}},
            {"args": _sticky_large(), "why": {"t": "Large input", "d": "2,500 requests on 15 backends with drops."}},
        ],
        "solutions": [
            {"name": "Busy heap + sorted free list (Optimal)",
             "description": "Release finished backends from the busy heap into a sorted free list. bisect_left finds the first idle backend at or after i % k, wrapping to the front. Python list inserts shift memory; a SortedList or segment tree makes every step O(log k).",
             "time": "O(n log k)", "space": "O(k)",
             "keyPoints": ["Release before choosing", "bisect for the next idle backend clockwise", "An empty free list means a drop"],
             "code": _STICKY_HEAP},
            {"name": "Walk the ring", "slow": True,
             "description": "For each request, check backends i % k, i % k + 1, ... around the ring until one is idle, or drop it after k checks.",
             "time": "O(n · k)", "space": "O(k)",
             "keyPoints": ["Mirrors the rules exactly", "A full ring costs k checks per request"],
             "code": _STICKY_SCAN},
        ],
        "starter": '''from __future__ import annotations


def busiest_backends(k: int, arrival: list[int], load: list[int]) -> list[int]:
    """Return, in increasing order, every backend that handled the most requests."""
    # TODO
    raise NotImplementedError
''',
    },
]
