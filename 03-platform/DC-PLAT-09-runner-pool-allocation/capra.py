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

VARIANT_TITLE = "Busiest runner"
VARIANT_APPROACH = "Two min-heaps (idle, busy) · O(m log m + m log n) · O(n + m)"


def _assign_large():
    rng = random.Random(1882)
    return {"weights": [rng.randint(1, 20) for _ in range(12)], "durations": [rng.randint(1, 30) for _ in range(400)]}


def _rooms_large():
    rng = random.Random(253)
    jobs = []
    for _ in range(300):
        s = rng.randint(0, 3000)
        jobs.append([s, s + rng.randint(1, 120)])
    return {"jobs": jobs}


VARIANTS = [
    {
        "key": "cheapest-runner-first",
        "title": "Cheapest idle runner first",
        "approach": "Idle heap by (cost, index) + busy heap by free time · O((n + m) log n) · O(n)",
        "spec": {"kind": "fn", "fn": "assign_builds", "params": ["weights", "durations"]},
        "statement": (
            "Runners differ in cost, so builds prefer cheap runners.\n"
            "\n"
            "### Input\n"
            "- `weights[i]`: runner `i`'s hourly price\n"
            "- `durations[j]`: seconds build `j` takes; build `j` is queued at second `j`\n"
            "\n"
            "### Output\n"
            "- A list where element `j` is the runner index build `j` ran on\n"
            "\n"
            "### Rules\n"
            "- A queued build goes to the idle runner with the **lowest weight**, then the lowest index\n"
            "- If no runner is idle, builds wait in queue order\n"
            "- As soon as runners free up, the next waiting build takes the cheapest of them the same way\n"
            "- A runner that frees at second `t` can start a build at `t`"
        ),
        "examples": [
            {"args": {"weights": [3, 3, 2], "durations": [1, 2, 3, 2, 1, 2]},
             "explanation": "Runner 2 is cheapest and takes builds 0 and 1 (free again at 1). At 2 it is busy, so build 2 takes runner 0 (tie on 3, lower index). Runner 2 is free at 3 for build 3; build 4 gets runner 1; at 5 all are free and runner 2 wins again.",
             "why": {"t": "Cost then index", "d": "The cheapest runner wins; equal cost goes to the lower index."}},
            {"args": {"weights": [5, 1], "durations": [10, 10, 1]},
             "explanation": "Builds 0 and 1 fill both runners. Build 2 waits until second 10, when both free; it takes runner 1, the cheaper.",
             "why": {"t": "Waiting build", "d": "A delayed build still picks by cost among runners freed at that moment."}},
        ],
        "constraints": ["1 ≤ len(weights) ≤ 10^4", "1 ≤ len(durations) ≤ 2 · 10^4", "1 ≤ weights[i], durations[j] ≤ 2 · 10^5"],
        "hints": [
            "Keep idle runners in a min-heap of (weight, index) and busy runners in a min-heap of (free_at, weight, index).",
            "Before placing build j, release every busy runner with free_at <= current time.",
            "If none are idle, jump the current time to the earliest free_at and release again.",
        ],
        "tests": [
            {"args": {"weights": [1], "durations": [1]}, "why": {"t": "Minimal", "d": "One runner, one build."}},
            {"args": {"weights": [4, 2, 2], "durations": [5, 5, 5]}, "why": {"t": "Ties on cost", "d": "Runner 1 then 2 then 0."}},
            {"args": {"weights": [1, 9], "durations": [1, 1, 1, 1]}, "why": {"t": "Free exactly on time", "d": "The cheap runner is free again each second."}},
            {"args": {"weights": [2, 1], "durations": [100, 100, 3, 3, 3]}, "why": {"t": "Long queue", "d": "Three builds wait behind two long ones."}},
            {"args": {"weights": [7, 7, 7], "durations": [2, 2, 2, 2, 2, 2]}, "why": {"t": "All equal cost", "d": "Index order decides every pick."}},
            {"args": _assign_large(), "why": {"t": "Large input", "d": "12 runners, 400 builds."}},
        ],
        "solutions": [
            {"name": "Two heaps (Optimal)",
             "description": "Idle runners sit in a (weight, index) heap, busy ones in a (free_at, weight, index) heap. Advance time to max(j, earliest free) when nothing is idle, release, then pop the cheapest idle runner.",
             "time": "O((n + m) log n)", "space": "O(n)",
             "keyPoints": ["Time only moves forward, so builds keep queue order", "Release everything due before choosing", "Tuple order encodes both tie-breaks"],
             "code": '''import heapq


def assign_builds(weights, durations):
    idle = [(w, i) for i, w in enumerate(weights)]
    heapq.heapify(idle)
    busy = []
    out = []
    now = 0
    for j, d in enumerate(durations):
        now = max(now, j)
        if not idle:
            now = max(now, busy[0][0])
        while busy and busy[0][0] <= now:
            _, w, i = heapq.heappop(busy)
            heapq.heappush(idle, (w, i))
        w, i = heapq.heappop(idle)
        out.append(i)
        heapq.heappush(busy, (now + d, w, i))
    return out
'''},
            {"name": "Scan all runners", "slow": True,
             "description": "For each build, find the start time (its queue second, or the earliest free time if all are busy), then scan every runner free by then for the lowest (weight, index).",
             "time": "O(m · n)", "space": "O(n)",
             "keyPoints": ["Two linear scans per build", "Fine for small pools"],
             "code": '''def assign_builds(weights, durations):
    n = len(weights)
    free_at = [0] * n
    out = []
    now = 0
    for j, d in enumerate(durations):
        now = max(now, j)
        if all(f > now for f in free_at):
            now = min(free_at)
        best = min((i for i in range(n) if free_at[i] <= now), key=lambda i: (weights[i], i))
        free_at[best] = now + d
        out.append(best)
    return out
'''},
        ],
        "starter": '''def assign_builds(weights: list[int], durations: list[int]) -> list[int]:
    """Runner index for each build, cheapest idle runner first."""
    raise NotImplementedError
''',
    },
    {
        "key": "pool-size-no-wait",
        "title": "Pool size with zero queueing",
        "approach": "Sort by start + min-heap of end times · O(m log m) · O(m)",
        "spec": {"kind": "fn", "fn": "min_runners", "params": ["jobs"]},
        "statement": (
            "Find how many runners would have let **every job start on time** yesterday.\n"
            "\n"
            "### Input\n"
            "- `jobs[i] = [start, end]`: a job occupies a runner from `start` until `end`\n"
            "\n"
            "### Output\n"
            "- The minimum number of runners. With no jobs, `0`\n"
            "\n"
            "### Rules\n"
            "- A runner freed at `t` can start another job at `t`"
        ),
        "examples": [
            {"args": {"jobs": [[0, 30], [5, 10], [15, 20]]},
             "explanation": "The long job overlaps each short one, but the two short ones never overlap: 2 runners.",
             "why": {"t": "Reuse", "d": "A runner freed by one job takes the next."}},
            {"args": {"jobs": [[0, 5], [5, 10]]},
             "explanation": "The second job starts exactly when the first ends, so one runner is enough.",
             "why": {"t": "Touching ends", "d": "End time is exclusive."}},
        ],
        "constraints": ["0 ≤ len(jobs) ≤ 10^5", "0 ≤ start < end ≤ 10^9", "Jobs may be in any order"],
        "hints": [
            "The answer is the largest number of jobs running at the same moment.",
            "Sort by start; keep a min-heap of end times of running jobs.",
            "Before placing a job, pop every end time <= its start; the heap's largest size is the answer.",
        ],
        "tests": [
            {"args": {"jobs": []}, "why": {"t": "No jobs", "d": "Zero runners."}},
            {"args": {"jobs": [[3, 4]]}, "why": {"t": "Single job", "d": "One runner."}},
            {"args": {"jobs": [[0, 10], [0, 10], [0, 10]]}, "why": {"t": "Same start", "d": "Three identical jobs need three runners."}},
            {"args": {"jobs": [[9, 12], [1, 3], [2, 6], [5, 9]]}, "why": {"t": "Unsorted", "d": "Chained jobs given out of order."}},
            {"args": {"jobs": [[0, 1000000000], [1, 2], [2, 3], [3, 4]]}, "why": {"t": "Boundaries", "d": "A day-long job plus back-to-back short ones."}},
            {"args": {"jobs": [[10 * i, 10 * i + 35] for i in range(12)]}, "why": {"t": "Merge train", "d": "A 35-minute build every 10 minutes needs 4 runners."}},
            {"args": _rooms_large(), "why": {"t": "Large input", "d": "300 random jobs."}},
        ],
        "solutions": [
            {"name": "Min-heap of end times (Optimal)",
             "description": "Sort jobs by start. For each job, pop every running job that ended by its start, push its end, and track the largest heap size.",
             "time": "O(m log m)", "space": "O(m)",
             "keyPoints": ["Heap size = runners busy right now", "Pop with <= because ends are exclusive", "The peak size is the pool size"],
             "code": '''import heapq


def min_runners(jobs):
    ends = []
    peak = 0
    for start, end in sorted(jobs):
        while ends and ends[0] <= start:
            heapq.heappop(ends)
        heapq.heappush(ends, end)
        peak = max(peak, len(ends))
    return peak
'''},
            {"name": "Count overlaps at every start", "slow": True,
             "description": "The peak happens at some job's start. For each start, count the jobs with start <= t < end.",
             "time": "O(m²)", "space": "O(1)",
             "keyPoints": ["Only start times can raise the count", "Quadratic scan"],
             "code": '''def min_runners(jobs):
    best = 0
    for t, _ in jobs:
        best = max(best, sum(1 for s, e in jobs if s <= t < e))
    return best
'''},
        ],
        "starter": '''def min_runners(jobs: list[list[int]]) -> int:
    """Fewest runners so no job waits."""
    raise NotImplementedError
''',
    },
]
