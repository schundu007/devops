"""Capra Playground export for DC-PLAT-09 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "busiest_runner", "params": ["n", "jobs"], "types": {}, "ret": "value", "cmp": "exact"}

EXAMPLES = [
    {"args": {"n": 2, "jobs": [[0, 10], [1, 5], [2, 7], [3, 4]]},
     "explanation": "Jobs at 0 and 1 take runners 0 and 1. The job at 2 waits for runner 1 (free at 5) and ends at 10; the job at 3 waits for runner 0 (free at 10). Both ran 2 jobs, so the lower number, 0, wins.",
     "why": {"t": "All busy · Tie", "d": "Jobs wait for the runner that frees first; a tie goes to the lower number."}},
    {"args": {"n": 3, "jobs": [[1, 20], [2, 10], [3, 5], [4, 9], [6, 10]]},
     "explanation": "Runners 0, 1, 2 take the first three jobs. At 4 nobody is idle, so the job waits for runner 2 (free at 5). At 6 runner 2 is busy again until 10, and runner 1 until 10; the job waits for runner 1. Runners 1 and 2 ran 2 jobs each: runner 1 wins.",
     "why": {"t": "Delayed jobs", "d": "A delayed job keeps its full duration and ends later than planned."}},
]


def _large():
    rng = random.Random(2402)
    starts = rng.sample(range(0, 20_000), 700)
    return {"n": 15, "jobs": [[s, s + rng.randint(1, 400)] for s in starts]}


TESTS = [
    {"args": {"n": 1, "jobs": [[5, 6]]},
     "why": {"t": "Single runner, single job", "d": "The smallest input: runner 0 runs the only job."}},
    {"args": {"n": 4, "jobs": [[0, 3], [1, 4]]},
     "why": {"t": "More runners than jobs", "d": "Idle runners are chosen lowest number first."}},
    {"args": {"n": 2, "jobs": [[0, 5], [5, 10], [10, 15]]},
     "why": {"t": "Free exactly on time", "d": "A runner whose job ends at t is idle for a job queued at t."}},
    {"args": {"n": 3, "jobs": [[3, 9], [0, 4], [1, 2]]},
     "why": {"t": "Unsorted input", "d": "Jobs arrive in any order; they run in queue-time order."}},
    {"args": {"n": 3, "jobs": [[0, 100], [1, 100], [2, 100], [3, 4], [4, 5], [5, 6]]},
     "why": {"t": "Everyone busy", "d": "Three long jobs fill every runner; the rest queue behind them."}},
    {"args": {"n": 2, "jobs": [[0, 1], [2, 3], [4, 5], [6, 7]]},
     "why": {"t": "Never overlapping", "d": "Runner 0 is always idle again, so it runs everything."}},
    {"args": {"n": 4, "jobs": [[10 * i, 10 * i + 35] for i in range(12)]},
     "why": {"t": "CI burst", "d": "A merge train queues a 35-minute build every 10 minutes on 4 runners."}},
    {"args": _large(),
     "why": {"t": "Large input", "d": "15 runners and 700 jobs at random times."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Two min-heaps (Optimal)",
     "description": "Sort jobs by queue time. Keep a min-heap of idle runner numbers and a min-heap of (free_at, runner). Free every runner done by the job's start; take the lowest idle runner, or else delay the job on the runner that frees first.",
     "time": "O(m log m + m log n)", "space": "O(n + m)",
     "keyPoints": ["Tuple order (free_at, runner) breaks ties by runner number for free", "A delayed job keeps its full duration", "Return the most jobs, lowest runner on a tie"]},
    {"name": "Scan every runner", "slow": True,
     "description": "For each job, scan all n runners: take the lowest-numbered idle one, or else the one that frees first.",
     "time": "O(m log m + m·n)", "space": "O(n + m)",
     "keyPoints": ["Easy to get right", "Too slow for fleets with thousands of runners"],
     "code": '''from __future__ import annotations


def busiest_runner(n: int, jobs: list[list[int]]) -> int:
    free_at = [0] * n
    ran = [0] * n
    for start, end in sorted(jobs):
        idle = [r for r in range(n) if free_at[r] <= start]
        if idle:
            r = idle[0]
            free_at[r] = end
        else:
            r = min(range(n), key=lambda x: (free_at[x], x))
            free_at[r] += end - start
        ran[r] += 1
    return max(range(n), key=lambda r: (ran[r], -r))
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Scan every runner", "idea": "For each job, look at all n runners to find an idle one or the first to free up.",
     "time": "O(m·n)", "space": "O(n)", "use": "Small pools; simplest to explain."},
    {"name": "Two min-heaps", "idea": "Idle runners by number, busy runners by (free_at, runner); each job costs a few heap operations.",
     "time": "O(m log n) after sorting", "space": "O(n)", "use": "Large pools and long job queues."},
]
