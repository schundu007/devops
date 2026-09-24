"""Capra Playground export for DC-SEC-06 (see tools/export_capra.py).

Driver kind: the chip has two entry points (peak_usage and fits_quota), and
each case checks both.
"""
import random

SPEC = {"kind": "driver", "fn": "peak_usage", "params": ["jobs", "quota"], "types": {}, "ret": "value", "cmp": "exact"}

DRIVER = '''
def __drive(args):
    jobs = [tuple(j) for j in args["jobs"]]
    return {"peak": peak_usage(jobs), "fits": fits_quota(jobs, args["quota"])}
'''


def case(jobs, quota):
    return {"jobs": jobs, "quota": quota}


EXAMPLES = [
    {"args": case([[2, 1, 5], [3, 3, 7]], 4),
     "explanation": "From 3 to 5 both jobs run: 2 + 3 = 5 vCPU, over the quota of 4.",
     "why": {"t": "Overlap over quota", "d": "Two overlapping jobs exceed the quota."}},
    {"args": case([[4, 0, 10], [4, 10, 20]], 4),
     "explanation": "Jobs run on [start, end), so the first frees its vCPU at 10 exactly when the second starts. The peak is 4.",
     "why": {"t": "Back to back", "d": "A job ending at t frees capacity for a job starting at t."}},
]


def _large():
    rng = random.Random(1094)
    jobs = []
    for _ in range(400):
        start = rng.randint(0, 10_000)
        jobs.append([rng.randint(1, 64), start, start + rng.randint(0, 800)])
    return case(jobs, 2000)


TESTS = [
    {"args": case([], 0), "why": {"t": "No jobs", "d": "Nothing runs, so the peak is 0 and any quota fits."}},
    {"args": case([[8, 5, 5]], 0), "why": {"t": "Zero-length job", "d": "A job with start == end never runs."}},
    {"args": case([[3, 0, 10]], 3), "why": {"t": "Exactly at quota", "d": "Peak equal to the quota still fits."}},
    {"args": case([[1, 0, 100], [1, 0, 100], [1, 0, 100]], 2), "why": {"t": "Same start", "d": "Three jobs start together."}},
    {"args": case([[10, 0, 10**9], [5, 999_999_999, 10**9]], 15), "why": {"t": "Huge times", "d": "Times up to 10^9 need a sparse map, not an array."}},
    {"args": case([[2, 1, 4], [3, 2, 6], [1, 5, 9], [4, 7, 8]], 5),
     "why": {"t": "Nightly batch window", "d": "ETL, backup, report and reindex jobs across one night."}},
    {"args": case([[5, 0, 3], [5, 3, 6], [5, 6, 9], [1, 0, 9]], 6), "why": {"t": "Chain", "d": "A chain of back-to-back jobs plus one long job."}},
    {"args": _large(), "why": {"t": "Large input", "d": "400 random jobs over a 3-hour window."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Difference map + sweep (Optimal)",
     "description": "Add +vcpus at each start and -vcpus at each end in a dict, sort the change times, and keep a running total. The largest running total is the peak.",
     "time": "O(n log n)", "space": "O(n)",
     "keyPoints": ["Jobs are active on [start, end)", "Net the changes at the same time before reading the total", "A dict handles times up to 10^9"]},
    {"name": "Check every start", "slow": True,
     "description": "The load only rises at a start time, so for each start add up every job running at that moment.",
     "time": "O(n²)", "space": "O(1)",
     "keyPoints": ["The peak always happens at some start time", "About 10^10 steps for 10^5 jobs"],
     "code": '''from __future__ import annotations


def peak_usage(jobs: list[tuple[int, int, int]]) -> int:
    peak = 0
    for _, t, e in jobs:
        if t >= e:
            continue
        peak = max(peak, sum(v for v, s, end in jobs if s <= t < end))
    return peak


def fits_quota(jobs: list[tuple[int, int, int]], quota: int) -> bool:
    return peak_usage(jobs) <= quota
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Check every start", "idea": "For each start time, sum the jobs running then.",
     "time": "O(n²)", "space": "O(1)", "use": "A handful of jobs."},
    {"name": "Difference map + sweep", "idea": "+vcpus at start, -vcpus at end, running total over sorted times.",
     "time": "O(n log n)", "space": "O(n)", "use": "Many jobs with large, sparse times."},
    {"name": "Difference array", "idea": "Same idea over a fixed array of time slots, no sort.",
     "time": "O(n + T)", "space": "O(T)", "use": "Small integer times, e.g. minutes in a day."},
]
