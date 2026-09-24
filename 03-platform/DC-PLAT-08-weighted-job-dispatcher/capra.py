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
