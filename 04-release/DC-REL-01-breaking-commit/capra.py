"""Capra Playground export for DC-REL-01 (see tools/export_capra.py).

The user's first_bad_commit(n, is_bad) receives a callback, so a driver builds
a fake CI that counts runs. It returns the answer and whether the number of CI
runs stayed within ceil(log2 n), the bound git bisect meets.
"""

SPEC = {"kind": "driver", "fn": "first_bad_commit", "params": ["n", "first_bad"], "types": {}, "ret": "value", "cmp": "exact"}

DRIVER = '''
def __drive(args):
    n, first_bad = args["n"], args["first_bad"]
    runs = [0]

    def is_bad(commit):
        runs[0] += 1
        if not 1 <= commit <= n:
            raise ValueError("is_bad(%r): commits are numbered 1..%d" % (commit, n))
        return commit >= first_bad

    answer = first_bad_commit(n, is_bad)
    limit = (n - 1).bit_length()  # ceil(log2 n)
    return {"first_bad": answer, "ci_runs_within_limit": runs[0] <= limit, "limit": limit}
'''


def case(n, first_bad):
    return {"n": n, "first_bad": first_bad}


EXAMPLES = [
    {"args": case(5, 4),
     "explanation": "Commits 1-3 pass and 4-5 fail, so the first bad commit is 4. Binary search needs at most ceil(log2 5) = 3 CI runs.",
     "why": {"t": "Middle commit", "d": "The break sits in the middle of the range."}},
    {"args": case(1, 1),
     "explanation": "Only one commit, and it is known to be bad: no CI run is needed at all.",
     "why": {"t": "Single commit", "d": "The smallest range: the answer is known without testing."}},
    {"args": case(40, 23),
     "explanation": "40 commits between tag v1.27.3 and HEAD; the 23rd broke the suite. At most 6 CI runs are allowed.",
     "why": {"t": "Release regression", "d": "A realistic bisect between two release tags."}},
]

TESTS = [
    {"args": case(10, 1), "why": {"t": "First commit bad", "d": "The very first commit already broke it."}},
    {"args": case(10, 10), "why": {"t": "Only HEAD bad", "d": "The last commit is the first bad one."}},
    {"args": case(2, 1), "why": {"t": "Two commits · first bad", "d": "Smallest range with a choice to make."}},
    {"args": case(2, 2), "why": {"t": "Two commits · last bad", "d": "Smallest range, break at the end."}},
    {"args": case(1024, 513), "why": {"t": "Power of two", "d": "Exactly 10 runs allowed for 1024 commits."}},
    {"args": case(1025, 1025), "why": {"t": "Just past a power of two", "d": "1025 commits allow 11 runs."}},
    {"args": case(2**31 - 1, 1_000_003), "why": {"t": "Huge range · overflow", "d": "2^31 - 1 commits: lo + (hi - lo) // 2 avoids overflow in fixed-width languages; at most 31 runs."}},
    {"args": case(2**31 - 1, 2**31 - 1), "why": {"t": "Huge range · last bad", "d": "The break is at HEAD of a huge range."}},
    {"args": case(2**31 - 1, 1), "why": {"t": "Huge range · first bad", "d": "The break is at the first of a huge range."}},
    {"args": case(1000, 999), "why": {"t": "Near the end", "d": "One before HEAD."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Binary search (Optimal)",
     "description": "Keep the answer inside [lo, hi]. Test the middle commit: if it is bad, the first bad one is mid or earlier (hi = mid); otherwise it is after mid (lo = mid + 1). Stop when lo == hi.",
     "time": "O(log n) calls to is_bad", "space": "O(1)",
     "keyPoints": ["Commits are good then bad: a sorted, monotone predicate", "hi = mid keeps a bad mid as a candidate", "mid = lo + (hi - lo) // 2 avoids overflow in fixed-width languages"]},
]

WAYS_TO_SOLVE = [
    {"name": "Linear scan", "idea": "Test commits 1, 2, 3, ... until one fails.",
     "time": "O(n) CI runs", "space": "O(1)", "use": "Never for real builds: 40 commits could mean 40 builds."},
    {"name": "Binary search (git bisect)", "idea": "Halve the good/bad range with every CI run.",
     "time": "O(log n) CI runs", "space": "O(1)", "use": "Always: this is what git bisect does."},
]

import random

SOLUTIONS.append(
    {"name": "Bisect between a good and a bad marker",
     "description": "Keep lo as a commit known good (0 stands for the tag before commit 1) and hi as a commit known bad (n). Test the middle and move whichever marker it matches. When they are neighbors, hi is the first bad commit. This is exactly how git bisect tracks its good and bad refs.",
     "time": "O(log n) calls to is_bad", "space": "O(1)",
     "keyPoints": ["Invariant: lo is good, hi is bad", "Stop when hi - lo == 1", "mid is never 0 or n, so it never tests a known commit"],
     "code": '''from __future__ import annotations

from typing import Callable


def first_bad_commit(n: int, is_bad: Callable[[int], bool]) -> int:
    lo, hi = 0, n
    while hi - lo > 1:
        mid = lo + (hi - lo) // 2
        if is_bad(mid):
            hi = mid
        else:
            lo = mid
    return hi
'''})

VARIANT_TITLE = "git bisect"
VARIANT_APPROACH = "Binary search on a monotone predicate · O(log n) CI runs · O(1)"


def _backlog_large():
    rng = random.Random(1011)
    backlog = [rng.randint(1, 5000) for _ in range(200)]
    return {"backlog": backlog, "minutes": 900}


def _logs_large():
    rng = random.Random(1012)
    ts, t = [], 1_700_000_000
    for _ in range(2000):
        t += rng.choice([0, 0, 1, 2, 5])
        ts.append(t)
    queries = []
    for _ in range(300):
        a = rng.randint(ts[0] - 20, ts[-1] + 20)
        queries.append([a, a + rng.randint(0, 200)])
    return {"timestamps": ts, "queries": queries}


_RATE_BINARY = '''from __future__ import annotations


def min_drain_rate(backlog: list[int], minutes: int) -> int:
    def fits(rate):
        return sum((b + rate - 1) // rate for b in backlog) <= minutes

    lo, hi = 1, max(backlog)  # max(backlog) always fits: one minute per partition
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if fits(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo
'''

_RATE_LINEAR = '''from __future__ import annotations


def min_drain_rate(backlog: list[int], minutes: int) -> int:
    rate = 1
    while sum((b + rate - 1) // rate for b in backlog) > minutes:
        rate += 1
    return rate
'''

_LOGS_BINARY = '''from __future__ import annotations


def count_in_windows(timestamps: list[int], queries: list[list[int]]) -> list[int]:
    def first_at_least(x):
        lo, hi = 0, len(timestamps)
        while lo < hi:
            mid = (lo + hi) // 2
            if timestamps[mid] >= x:
                hi = mid
            else:
                lo = mid + 1
        return lo

    return [first_at_least(end + 1) - first_at_least(start) for start, end in queries]
'''

_LOGS_SCAN = '''from __future__ import annotations


def count_in_windows(timestamps: list[int], queries: list[list[int]]) -> list[int]:
    return [sum(1 for t in timestamps if start <= t <= end) for start, end in queries]
'''

VARIANTS = [
    {
        "key": "min-drain-rate",
        "title": "Minimum consumer throughput",
        "approach": "Binary search on the rate with a feasibility check · O(p · log max) · O(1)",
        "spec": {"kind": "fn", "fn": "min_drain_rate", "params": ["backlog", "minutes"], "cmp": "exact"},
        "statement": "After an outage, a Kafka consumer must drain a backlog before the maintenance window closes.\n\n### Input\n- `backlog[i]`: the number of messages stuck on partition `i`\n- `minutes`: the time available\n\n### Output\n- The **smallest integer** `rate` (messages per minute) that drains every partition within `minutes`\n\n### Rules\n- The consumer works on one partition at a time at `rate` messages per minute\n- It only moves to the next partition at a whole minute, so partition `i` takes `ceil(backlog[i] / rate)` minutes",
        "examples": [
            {"args": {"backlog": [3, 6, 7, 11], "minutes": 8},
             "explanation": "At 4 per minute: 1 + 2 + 2 + 3 = 8 minutes, which fits. At 3 per minute it takes 1 + 2 + 3 + 4 = 10.",
             "why": {"t": "Boundary rate", "d": "The answer is the first rate whose total fits."}},
            {"args": {"backlog": [30, 11, 23, 4, 20], "minutes": 5},
             "explanation": "Five partitions in five minutes: each must drain in one minute, so the rate is the largest backlog, 30.",
             "why": {"t": "Tightest window", "d": "minutes equal to the partition count forces the maximum."}},
        ],
        "constraints": ["1 ≤ backlog.length ≤ 10⁴", "1 ≤ backlog[i] ≤ 10⁹", "backlog.length ≤ minutes ≤ 10⁹"],
        "hints": [
            "Write fits(rate): the sum of ceil(b / rate). It only gets smaller as the rate grows.",
            "The answer lies between 1 and max(backlog): at max(backlog) every partition takes one minute.",
            "Binary search for the first rate where fits is true, the same lo/hi loop as first_bad_commit.",
        ],
        "tests": [
            {"args": {"backlog": [1], "minutes": 1}, "why": {"t": "Minimal", "d": "One message, one minute: rate 1."}},
            {"args": {"backlog": [1000], "minutes": 3}, "why": {"t": "Single partition", "d": "ceil(1000 / r) <= 3 needs r = 334."}},
            {"args": {"backlog": [5, 5, 5], "minutes": 1000}, "why": {"t": "Plenty of time", "d": "Rate 1 already fits."}},
            {"args": {"backlog": [9, 9, 9, 9], "minutes": 8}, "why": {"t": "Equal partitions", "d": "Two minutes each: ceil(9 / r) <= 2 needs r = 5."}},
            {"args": {"backlog": [1_000_000_000, 1_000_000_000], "minutes": 400_000}, "why": {"t": "Huge backlog", "d": "10⁹ messages per partition: the search takes about 30 checks, not one per rate."}},
            {"args": {"backlog": [2, 3, 1000], "minutes": 4}, "why": {"t": "One hot partition", "d": "Two small partitions take a minute each; the hot one gets two minutes, so r = 500."}},
            {"args": _backlog_large(), "why": {"t": "Large input", "d": "200 partitions with up to 5,000 messages each, 900 minutes."}},
        ],
        "solutions": [
            {"name": "Binary search on the rate (Optimal)",
             "description": "The check 'this rate drains in time' is false then true as the rate grows. Binary search the first true rate in [1, max(backlog)], evaluating the check in O(p) each time.",
             "time": "O(p · log max)", "space": "O(1)",
             "keyPoints": ["Monotone check, like good then bad commits", "Integer ceiling: (b + r - 1) // r", "hi = mid keeps a feasible mid as a candidate"],
             "code": _RATE_BINARY},
            {"name": "Try every rate from 1", "slow": True,
             "description": "Start at rate 1 and increase by one until the backlog fits. This is the linear scan of commits, one CI run at a time.",
             "time": "O(p · answer)", "space": "O(1)",
             "keyPoints": ["Correct and simple", "A 10⁹ answer means 10⁹ checks"],
             "code": _RATE_LINEAR},
        ],
        "starter": '''from __future__ import annotations


def min_drain_rate(backlog: list[int], minutes: int) -> int:
    """Return the smallest messages-per-minute rate that drains every partition in time."""
    # TODO
    raise NotImplementedError
''',
    },
    {
        "key": "log-window-count",
        "title": "Log lines in a time window",
        "approach": "Lower and upper bound binary searches · O(q · log n) · O(1)",
        "spec": {"kind": "fn", "fn": "count_in_windows", "params": ["timestamps", "queries"], "cmp": "exact"},
        "statement": "Count log lines per time range for an incident review.\n\n### Input\n- `timestamps`: the epoch second of every log line, in **non-decreasing** order; many lines can share a second\n- `queries`: each `[start, end]` asks how many lines fall in `start <= t <= end`\n\n### Output\n- One count per query, in order",
        "examples": [
            {"args": {"timestamps": [100, 101, 101, 101, 105, 110], "queries": [[101, 105], [102, 104], [0, 1000]]},
             "explanation": "Three lines at 101 and one at 105 make 4. Nothing was logged from 102 to 104. The last window covers everything.",
             "why": {"t": "Duplicates at the edge", "d": "Every line in a repeated second is counted, at both ends."}},
        ],
        "constraints": ["0 ≤ timestamps.length ≤ 10⁵, non-decreasing", "0 ≤ queries.length ≤ 10⁴", "start ≤ end"],
        "hints": [
            "Find the first index whose timestamp is >= start, and the first index whose timestamp is > end.",
            "'First index with t > end' is the same as 'first index with t >= end + 1' for integers, so one helper is enough.",
            "The count is the difference between the two indexes.",
        ],
        "tests": [
            {"args": {"timestamps": [], "queries": [[0, 10]]}, "why": {"t": "No logs", "d": "An empty file gives 0 for every window."}},
            {"args": {"timestamps": [5], "queries": [[5, 5], [4, 4], [6, 9]]}, "why": {"t": "Single line", "d": "A zero-width window on the line, just before it and just after."}},
            {"args": {"timestamps": [7, 7, 7, 7], "queries": [[7, 7], [0, 6], [8, 8]]}, "why": {"t": "All in one second", "d": "Every line shares a timestamp."}},
            {"args": {"timestamps": [1, 2, 3], "queries": []}, "why": {"t": "No queries", "d": "No windows in, no counts out."}},
            {"args": {"timestamps": [10, 20, 30, 40], "queries": [[0, 9], [41, 99], [10, 40], [15, 35]]}, "why": {"t": "Outside and across", "d": "Windows before, after, exactly covering, and inside the data."}},
            {"args": _logs_large(), "why": {"t": "Large input", "d": "2,000 log lines and 300 windows around epoch seconds."}},
        ],
        "solutions": [
            {"name": "Two binary searches (Optimal)",
             "description": "A lower-bound search finds the first line at or after start and the first line after end. Their difference is the count. Python's bisect_left and bisect_right do the same.",
             "time": "O(q · log n)", "space": "O(1)",
             "keyPoints": ["Lower bound: first index with t >= x", "t > end is t >= end + 1 on integers", "No per-query scan of the file"],
             "code": _LOGS_BINARY},
            {"name": "Scan the file per query", "slow": True,
             "description": "For every window, walk all log lines and count those inside it.",
             "time": "O(q · n)", "space": "O(1)",
             "keyPoints": ["Obviously correct", "Rereads the whole file for every question"],
             "code": _LOGS_SCAN},
        ],
        "starter": '''from __future__ import annotations


def count_in_windows(timestamps: list[int], queries: list[list[int]]) -> list[int]:
    """Return, per [start, end] query, how many timestamps lie in start..end inclusive."""
    # TODO
    raise NotImplementedError
''',
    },
]
