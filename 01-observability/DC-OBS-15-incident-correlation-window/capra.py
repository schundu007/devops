"""Capra Playground export for DC-OBS-15 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "tightest_window", "params": ["error_times"], "types": {}, "ret": "value", "cmp": "exact"}


def case(times):
    return {"error_times": times}


EXAMPLES = [
    {"args": case([[4, 10, 15, 24, 26], [0, 9, 12, 20], [5, 18, 22, 30]]),
     "explanation": "[20, 24] holds 24 (service 0), 20 (service 1) and 22 (service 2). No narrower window covers all three.",
     "why": {"t": "Three services", "d": "The classic case: one error from every service inside the narrowest window."}},
    {"args": case([[1, 2, 3], [1, 2, 3], [1, 2, 3]]),
     "explanation": "All services failed at second 1, so a zero-width window [1, 1] works. It is the earliest of the ties.",
     "why": {"t": "Same second · Ties", "d": "Several zero-width windows; the earliest one wins."}},
    {"args": case([[5, 9]]),
     "explanation": "With one service, any single error is a window of width 0. The earliest is [5, 5].",
     "why": {"t": "Single service", "d": "Only one list, so the answer is its first error."}},
]


def _large():
    rng = random.Random(632)
    return case([sorted(rng.sample(range(-100_000, 100_000), 40)) for _ in range(12)])


TESTS = [
    {"args": case([[7]]),
     "why": {"t": "Single error", "d": "One service with one error time."}},
    {"args": case([[10], [30]]),
     "why": {"t": "One error each", "d": "Each service failed once, so the window spans both."}},
    {"args": case([[1, 5], [3, 7]]),
     "why": {"t": "Tie on width", "d": "[1, 3] and [3, 5] are both width 2; the one starting earlier wins."}},
    {"args": case([[-50, -10, 0], [-20, 40], [-15, 100]]),
     "why": {"t": "Negative times", "d": "Times before the reference point are allowed."}},
    {"args": case([[1, 100], [1, 100], [100]]),
     "why": {"t": "Late single error", "d": "One service only failed late, which pulls the window to [100, 100]."}},
    {"args": case([[1000, 1004, 1030], [1002, 1003], [900, 1001, 1200], [1003, 1050]]),
     "why": {"t": "Incident correlation", "d": "api, db, cache and queue errors; the 4-second window points at one shared cause."}},
    {"args": case([[i] for i in range(0, 200, 5)]),
     "why": {"t": "Many services", "d": "40 services with one error each; the window must cover them all."}},
    {"args": _large(),
     "why": {"t": "Large input", "d": "12 services with 40 random error times each."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Min-heap + sliding window (Optimal)",
     "description": "Put the first error of every service in a min-heap and track the largest head. The heap top and that largest head form a window holding one error per service. Pop the smallest, advance that service, and stop when a service runs out.",
     "time": "O(n log k)", "space": "O(k)",
     "keyPoints": ["The window is [smallest head, largest head]", "Only the smallest head can move the window forward", "Stop when the popped service has no later error"]},
    {"name": "Try every start", "slow": True,
     "description": "For every error time as a start, take each service's first error at or after it; the window ends at the largest of those.",
     "time": "O(n · k log m)", "space": "O(n)",
     "keyPoints": ["Every optimal window starts at some error time", "A binary search per service finds its first error at or after the start"],
     "code": '''from __future__ import annotations

from bisect import bisect_left


def tightest_window(error_times: list[list[int]]) -> list[int]:
    best = None
    for start in sorted({t for times in error_times for t in times}):
        end = start
        for times in error_times:
            i = bisect_left(times, start)
            if i == len(times):
                end = None
                break
            end = max(end, times[i])
        if end is None:
            continue
        if best is None or end - start < best[1] - best[0]:
            best = [start, end]
    return best
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Try every start", "idea": "For each error time, find each service's first error at or after it with binary search.",
     "time": "O(n · k log m)", "space": "O(n)", "use": "Few services and short lists; easy to explain."},
    {"name": "Min-heap of heads", "idea": "Keep one pointer per service in a min-heap and slide the smallest forward.",
     "time": "O(n log k)", "space": "O(k)", "use": "Many services and long error lists."},
]

VARIANT_TITLE = "Tightest incident window"
VARIANT_APPROACH = "Min-heap of service heads · O(n log k) · O(k)"


def _merge_large():
    rng = random.Random(23)
    return {"error_times": [sorted(rng.sample(range(0, 5000), rng.randint(1, 40))) for _ in range(15)]}


def _quorum_large():
    rng = random.Random(76)
    return {"error_times": [sorted(rng.sample(range(-2000, 2000), 25)) for _ in range(8)], "m": 5}


VARIANTS = [
    {
        "key": "merged-timeline",
        "title": "One incident timeline",
        "approach": "k-way merge with a min-heap · O(n log k) · O(k) extra",
        "spec": {"kind": "fn", "fn": "merge_timelines", "params": ["error_times"]},
        "statement": (
            "Build a single postmortem timeline of every error across services.\n"
            "\n"
            "### Input\n"
            "- `error_times[s]`: service `s`'s error times, sorted ascending (a list may be empty)\n"
            "\n"
            "### Output\n"
            "- Every error as `[time, service]`, ordered by time\n"
            "\n"
            "### Rules\n"
            "- Errors at the same time are ordered by service number"
        ),
        "examples": [
            {"args": {"error_times": [[1, 5], [2, 5], [0]]},
             "explanation": "0 (service 2), 1 (service 0), 2 (service 1), then 5 from services 0 and 1 in service order.",
             "why": {"t": "Interleave · Tie", "d": "Same-second errors sort by service number."}},
        ],
        "constraints": ["1 ≤ len(error_times) ≤ 1000", "0 ≤ len(error_times[s]) ≤ 1000, sorted ascending", "-10^5 ≤ time ≤ 10^5"],
        "hints": [
            "Each list is already sorted: only the head of each list can be next.",
            "Keep one (time, service, index) tuple per service in a min-heap; the tuple order handles ties.",
        ],
        "tests": [
            {"args": {"error_times": [[]]}, "why": {"t": "No errors", "d": "One quiet service: []."}},
            {"args": {"error_times": [[], [3], []]}, "why": {"t": "Mostly empty", "d": "Empty lists are skipped."}},
            {"args": {"error_times": [[7, 7], [7]]}, "why": {"t": "Duplicate times", "d": "Repeats within and across services."}},
            {"args": {"error_times": [[-5, 10], [-10, 20], [0]]}, "why": {"t": "Negative times", "d": "Times before the reference point."}},
            {"args": {"error_times": [[1, 2, 3, 4], [100]]}, "why": {"t": "One list runs out", "d": "The long tail comes from a single service."}},
            {"args": _merge_large(), "why": {"t": "Large input", "d": "15 services with up to 40 errors each."}},
        ],
        "solutions": [
            {"name": "Heap of heads (Optimal)",
             "description": "Push each non-empty service's first error as (time, service, index). Pop the smallest, emit it, and push that service's next error.",
             "time": "O(n log k)", "space": "O(k) extra",
             "keyPoints": ["Only k heads are compared at a time", "(time, service) tuples give the tie-break", "Same heap as the tightest-window problem"],
             "code": '''import heapq


def merge_timelines(error_times):
    heap = [(times[0], s, 0) for s, times in enumerate(error_times) if times]
    heapq.heapify(heap)
    out = []
    while heap:
        t, s, i = heapq.heappop(heap)
        out.append([t, s])
        if i + 1 < len(error_times[s]):
            heapq.heappush(heap, (error_times[s][i + 1], s, i + 1))
    return out
'''},
            {"name": "Scan every head", "slow": True,
             "description": "Keep one pointer per service; each step scans all k heads for the smallest (time, service).",
             "time": "O(n · k)", "space": "O(k) extra",
             "keyPoints": ["No heap needed", "Every emitted error costs a scan of all services"],
             "code": '''def merge_timelines(error_times):
    ptr = [0] * len(error_times)
    out = []
    while True:
        best = None
        for s, times in enumerate(error_times):
            if ptr[s] < len(times) and (best is None or times[ptr[s]] < error_times[best][ptr[best]]):
                best = s
        if best is None:
            return out
        out.append([error_times[best][ptr[best]], best])
        ptr[best] += 1
'''},
        ],
        "starter": '''def merge_timelines(error_times: list[list[int]]) -> list[list[int]]:
    """Every error as [time, service], by time then service."""
    raise NotImplementedError
''',
    },
    {
        "key": "quorum-window",
        "title": "Window covering m of k services",
        "approach": "Merge + sliding window with per-service counts · O(n log n) · O(n)",
        "spec": {"kind": "fn", "fn": "quorum_window", "params": ["error_times", "m"]},
        "statement": (
            "Some services fail for unrelated reasons, so an incident needs only `m` services, not all of them.\n"
            "\n"
            "### Input\n"
            "- `error_times[s]`: service `s`'s error times, sorted ascending and never empty\n"
            "- `m`: the minimum number of distinct services\n"
            "\n"
            "### Output\n"
            "- `[start, end]`, the narrowest window holding errors from **at least `m`** distinct services\n"
            "\n"
            "### Rules\n"
            "- Both ends are **inclusive**\n"
            "- On equal width, return the smallest `start`"
        ),
        "examples": [
            {"args": {"error_times": [[1, 50], [48], [100, 200]], "m": 2},
             "explanation": "Services 0 and 1 have errors at 50 and 48: [48, 50], width 2. Service 2 is unrelated.",
             "why": {"t": "Quorum", "d": "One noisy service no longer stretches the window."}},
            {"args": {"error_times": [[4, 9], [2]], "m": 1},
             "explanation": "Any single error is a width-0 window; the earliest is [2, 2].",
             "why": {"t": "m = 1", "d": "The trivial quorum."}},
        ],
        "constraints": ["1 ≤ m ≤ len(error_times) ≤ 1000", "1 ≤ len(error_times[s]) ≤ 50, sorted ascending", "-10^5 ≤ time ≤ 10^5"],
        "hints": [
            "Merge every error into one list of (time, service) sorted by time.",
            "Slide a window over that list, keeping a count per service and the number of distinct services inside.",
            "While the window has m services, record it and move the left edge forward.",
        ],
        "tests": [
            {"args": {"error_times": [[5]], "m": 1}, "why": {"t": "Minimal", "d": "One service, one error."}},
            {"args": {"error_times": [[1, 5], [3, 7]], "m": 2}, "why": {"t": "Tie on width", "d": "[1, 3] and [3, 5] tie; the earlier start wins."}},
            {"args": {"error_times": [[10, 10], [10]], "m": 2}, "why": {"t": "Same second", "d": "Duplicate times give a width-0 window."}},
            {"args": {"error_times": [[0], [100], [200], [300]], "m": 4}, "why": {"t": "m = k", "d": "Needs every service, like the main problem."}},
            {"args": {"error_times": [[-30, 5], [-28], [6, 90], [7]], "m": 3}, "why": {"t": "Several quorums", "d": "[5, 7] beats the earlier cluster."}},
            {"args": _quorum_large(), "why": {"t": "Large input", "d": "8 services, 25 errors each, quorum of 5."}},
        ],
        "solutions": [
            {"name": "Sliding window over merged errors (Optimal)",
             "description": "Sort all (time, service) pairs. Extend the right edge; while the window holds m services, record it if narrower and drop the left error.",
             "time": "O(n log n)", "space": "O(n)",
             "keyPoints": ["Distinct count changes only when a service's count hits 0 or leaves 0", "Record before shrinking", "Compare (width, start) for the tie-break"],
             "code": '''def quorum_window(error_times, m):
    events = sorted((t, s) for s, times in enumerate(error_times) for t in times)
    count = {}
    distinct = 0
    best = None
    left = 0
    for t, s in events:
        count[s] = count.get(s, 0) + 1
        if count[s] == 1:
            distinct += 1
        while distinct >= m:
            start = events[left][0]
            if best is None or (t - start, start) < (best[1] - best[0], best[0]):
                best = [start, t]
            ls = events[left][1]
            count[ls] -= 1
            if count[ls] == 0:
                distinct -= 1
            left += 1
    return best
'''},
            {"name": "Try every start and end", "slow": True,
             "description": "For every pair of error times start <= end, count the services with an error inside using binary search.",
             "time": "O(T² · k log L)", "space": "O(T)",
             "keyPoints": ["Every optimal window starts and ends on an error time", "Quadratic in the number of distinct times"],
             "code": '''from bisect import bisect_left


def quorum_window(error_times, m):
    times = sorted({t for ts in error_times for t in ts})
    best = None
    for i, start in enumerate(times):
        for end in times[i:]:
            if best is not None and end - start >= best[1] - best[0]:
                break
            hit = 0
            for ts in error_times:
                j = bisect_left(ts, start)
                if j < len(ts) and ts[j] <= end:
                    hit += 1
            if hit >= m:
                best = [start, end]
                break
    return best
'''},
        ],
        "starter": '''def quorum_window(error_times: list[list[int]], m: int) -> list[int]:
    """Narrowest [start, end] holding errors from at least m services."""
    raise NotImplementedError
''',
    },
]
