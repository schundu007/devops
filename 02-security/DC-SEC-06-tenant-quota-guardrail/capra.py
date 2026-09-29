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

VARIANT_TITLE = "Peak usage against a quota"
VARIANT_APPROACH = "Difference map + sweep · O(n log n) · O(n)"


def _vjobs(seed, count):
    rng = random.Random(seed)
    jobs = []
    for _ in range(count):
        start = rng.randint(0, 5000)
        jobs.append([rng.randint(1, 64), start, start + rng.randint(0, 600)])
    return jobs


_WIN_JOBS = _vjobs(1851, 250)
_OVER_JOBS = _vjobs(2237, 250)


def jq(jobs, quota, t, d):
    return {"args": {"jobs": jobs, "quota": quota}, "why": {"t": t, "d": d}}


VARIANTS = [
    {
        "key": "breach-windows",
        "title": "Windows over quota",
        "approach": "Difference map + sweep · O(n log n) · O(n)",
        "spec": {"kind": "fn", "fn": "breach_windows", "params": ["jobs", "quota"], "ret": "value", "cmp": "exact"},
        "statement": """Knowing the peak says *whether* a tenant breaks its quota; the incident report needs *when*.

### Input
- `jobs`: each job is `[vcpus, start, end]`, active on `[start, end)`
- `quota`: the vCPU quota

### Output
- Every maximal time window `[from, to]` (meaning `[from, to)`) during which total vCPU in use is **strictly above** `quota`, sorted by start

### Rules
- Windows that touch are one window: `[1, 3]` and `[3, 5]` are reported as `[1, 5]`""",
        "examples": [
            {"args": {"jobs": [[2, 1, 5], [3, 3, 7], [4, 6, 9]], "quota": 4},
             "explanation": "From 3 to 5 usage is 5; from 6 to 7 it is 7. Between 5 and 6 only 3 vCPU run.",
             "why": {"t": "Two breaches", "d": "Usage dips back under quota in between."}},
            {"args": {"jobs": [[5, 0, 10], [5, 10, 20]], "quota": 4},
             "explanation": "Both jobs exceed the quota and one starts as the other ends, so it is one window [0, 20].",
             "why": {"t": "Touching windows merge", "d": "No gap at time 10."}},
        ],
        "constraints": ["0 ≤ jobs.length ≤ 10^5", "1 ≤ vcpus ≤ 10^4", "0 ≤ start ≤ end ≤ 10^9", "0 ≤ quota ≤ 10^9"],
        "hints": [
            "Build the same difference map and walk its times in order.",
            "After applying the change at time t: if you were under and are now over, a window opens at t; if you were over and are now under, it closes at t.",
            "Net all changes at one time before comparing, so touching jobs never split a window.",
        ],
        "tests": [
            jq([], 0, "No jobs", "Nothing runs: no windows."),
            jq([[8, 5, 5]], 0, "Zero-length job", "start == end never runs."),
            jq([[3, 0, 10]], 3, "Exactly at quota", "Equal to the quota is not a breach."),
            jq([[3, 0, 10]], 2, "Single job over", "One window, the job's own interval."),
            jq([[2, 0, 4], [2, 2, 6], [2, 4, 8]], 3, "Chain of overlaps", "Overlaps at [2, 4) and [4, 6) merge into one window."),
            jq([[10, 0, 1000000000], [1, 999999999, 1000000000]], 10, "Huge times", "A one-unit breach at the very end."),
            jq([[4, 60, 180], [4, 120, 240], [4, 150, 160], [4, 200, 300]], 8, "Nightly batch", "ETL, backup, a report and a reindex."),
            jq(_WIN_JOBS, 700, "Large input", "250 random jobs over about 90 minutes."),
        ],
        "solutions": [
            {"name": "Difference map + sweep (Optimal)",
             "description": "Add +vcpus at start and -vcpus at end in a dict. Walk the sorted times with a running total and record where it crosses above and back to at most the quota.",
             "time": "O(n log n)", "space": "O(n)",
             "keyPoints": ["Windows open and close only at change times", "Netting per time merges touching windows", "Strictly above the quota counts as a breach"],
             "code": '''def breach_windows(jobs, quota):
    delta = {}
    for v, s, e in jobs:
        if s < e:
            delta[s] = delta.get(s, 0) + v
            delta[e] = delta.get(e, 0) - v
    out, running, opened = [], 0, None
    for t in sorted(delta):
        running += delta[t]
        if running > quota and opened is None:
            opened = t
        elif running <= quota and opened is not None:
            out.append([opened, t])
            opened = None
    return out
'''},
            {"name": "Check each elementary interval", "slow": True,
             "description": "Sort all start and end times. For each gap between neighbors, sum the jobs running in it; mark breaching gaps and merge neighbors.",
             "time": "O(n²)", "space": "O(n)",
             "keyPoints": ["Usage is constant between neighboring times", "Recounts all jobs for every gap"],
             "code": '''def breach_windows(jobs, quota):
    times = sorted({t for _, s, e in jobs if s < e for t in (s, e)})
    out = []
    for a, b in zip(times, times[1:]):
        used = sum(v for v, s, e in jobs if s <= a < e)
        if used > quota:
            if out and out[-1][1] == a:
                out[-1][1] = b
            else:
                out.append([a, b])
    return out
'''},
        ],
        "starter": '''def breach_windows(jobs: list[list[int]], quota: int) -> list[list[int]]:
    pass
''',
    },
    {
        "key": "burst-billing",
        "title": "Burst billing over the commitment",
        "approach": "Difference map + weighted sweep · O(n log n) · O(n)",
        "spec": {"kind": "fn", "fn": "overage", "params": ["jobs", "quota"], "ret": "value", "cmp": "exact"},
        "statement": """A tenant's usage above its committed capacity is allowed but billed per vCPU-minute.

### Input
- `jobs`: each job is `[vcpus, start, end]` in minutes, active on `[start, end)`
- `quota`: the committed capacity in vCPU

### Output
- The total overage: the sum over every minute of `max(0, usage − quota)`, where `usage` is the total vCPU running in that minute""",
        "examples": [
            {"args": {"jobs": [[2, 1, 5], [3, 3, 7]], "quota": 4},
             "explanation": "Only [3, 5) is over: usage 5, one vCPU over for 2 minutes = 2.",
             "why": {"t": "One burst", "d": "Overlap of two jobs."}},
            {"args": {"jobs": [[10, 0, 60], [6, 30, 90]], "quota": 8},
             "explanation": "[0, 30): 2 over for 30 minutes = 60. [30, 60): 8 over for 30 = 240. [60, 90): under. Total 300.",
             "why": {"t": "Varying overage", "d": "Different amounts over in different stretches."}},
        ],
        "constraints": ["0 ≤ jobs.length ≤ 10^5", "1 ≤ vcpus ≤ 10^4", "0 ≤ start ≤ end ≤ 10^6", "0 ≤ quota ≤ 10^9"],
        "hints": [
            "Between two neighboring times of the difference map, usage does not change.",
            "Before applying the change at the next time, add (next − t) × max(0, running − quota).",
            "Zero-length jobs and usage exactly at quota add nothing.",
        ],
        "tests": [
            jq([], 0, "No jobs", "Nothing runs: 0."),
            jq([[8, 5, 5]], 0, "Zero-length job", "start == end never runs."),
            jq([[3, 0, 10]], 3, "Exactly at quota", "Nothing over: 0."),
            jq([[3, 0, 10]], 0, "Zero commitment", "All usage is billed: 30."),
            jq([[4, 0, 5], [4, 5, 10]], 3, "Back to back", "One vCPU over for 10 minutes; no double count at 5."),
            jq([[1, 0, 1000000], [1, 0, 1000000]], 1, "Long runs", "One vCPU over for a million minutes."),
            jq([[16, 0, 480], [32, 60, 120], [8, 300, 330], [4, 0, 1440]], 24, "One day", "Base load with a morning spike and a small afternoon job."),
            jq(_OVER_JOBS, 600, "Large input", "250 random jobs."),
        ],
        "solutions": [
            {"name": "Difference map + weighted sweep (Optimal)",
             "description": "Build the difference map, sort its times, and add the overage of each stretch between neighbors before applying the next change.",
             "time": "O(n log n)", "space": "O(n)",
             "keyPoints": ["Usage is flat between change times", "Multiply the excess by the stretch length", "The last stretch ends with usage back at 0"],
             "code": '''def overage(jobs, quota):
    delta = {}
    for v, s, e in jobs:
        if s < e:
            delta[s] = delta.get(s, 0) + v
            delta[e] = delta.get(e, 0) - v
    total, running, prev = 0, 0, None
    for t in sorted(delta):
        if prev is not None and running > quota:
            total += (t - prev) * (running - quota)
        running += delta[t]
        prev = t
    return total
'''},
            {"name": "Recount every stretch", "slow": True,
             "description": "Sort all start and end times; for each stretch between neighbors, sum the jobs running in it and add its overage.",
             "time": "O(n²)", "space": "O(n)",
             "keyPoints": ["Directly from the definition", "Recounts all jobs per stretch"],
             "code": '''def overage(jobs, quota):
    times = sorted({t for _, s, e in jobs if s < e for t in (s, e)})
    total = 0
    for a, b in zip(times, times[1:]):
        used = sum(v for v, s, e in jobs if s <= a < e)
        total += (b - a) * max(0, used - quota)
    return total
'''},
        ],
        "starter": '''def overage(jobs: list[list[int]], quota: int) -> int:
    pass
''',
    },
]
