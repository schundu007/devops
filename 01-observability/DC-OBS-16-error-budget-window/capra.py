"""Capra Playground export for DC-OBS-16 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "longest_window", "params": ["checks", "budget"], "types": {}, "ret": "value", "cmp": "exact"}


def case(checks, budget):
    return {"checks": checks, "budget": budget}


EXAMPLES = [
    {"args": case([1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0], 2),
     "explanation": "The last 6 checks [0, 1, 1, 1, 1, 0] hold exactly 2 failures, and no longer run does.",
     "why": {"t": "Budget of 2", "d": "The best window uses the whole failure budget."}},
    {"args": case([0, 0, 0], 0),
     "explanation": "Every check failed and the budget is 0, so no window is allowed: the answer is 0.",
     "why": {"t": "All failed · Zero budget", "d": "No window fits, so the answer is 0."}},
    {"args": case([1, 0, 1, 1, 0, 1], 1),
     "explanation": "[1, 1, 0, 1] at the end, or [1, 0, 1, 1] at the start: 4 checks with one failure.",
     "why": {"t": "Two equal windows", "d": "Several windows share the best length."}},
]


def _large():
    rng = random.Random(1004)
    return case([0 if rng.random() < 0.15 else 1 for _ in range(3000)], 25)


TESTS = [
    {"args": case([], 0), "why": {"t": "Empty", "d": "No checks at all."}},
    {"args": case([1], 0), "why": {"t": "Single pass", "d": "One passing check."}},
    {"args": case([0], 1), "why": {"t": "Single failure", "d": "One failed check that the budget covers."}},
    {"args": case([1, 1, 1, 1], 0), "why": {"t": "All passed", "d": "No failures, so the whole list is the window."}},
    {"args": case([0, 1, 0, 1, 0], 5), "why": {"t": "Budget ≥ failures", "d": "The budget covers every failure."}},
    {"args": case([0, 1, 0, 1, 0, 1, 0], 1), "why": {"t": "Alternating", "d": "Pass and fail alternate; the window slides often."}},
    {"args": case([1] * 50 + [0] * 3 + [1] * 20 + [0] + [1] * 40, 2),
     "why": {"t": "Outage burst", "d": "A 3-check outage then one blip; the budget can't cover the burst."}},
    {"args": _large(), "why": {"t": "Large input", "d": "3,000 checks with about 15% failures."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Sliding window (Optimal)",
     "description": "Two pointers bound the window and a counter tracks its failures. Move the right edge every step; while failures exceed the budget, move the left edge.",
     "time": "O(n)", "space": "O(1)",
     "keyPoints": ["Each check enters and leaves the window at most once", "Shrink from the left only while over budget", "Record the length after every step"]},
    {"name": "Try every start", "slow": True,
     "description": "For every start, extend the window until the failures would exceed the budget, and keep the longest.",
     "time": "O(n²)", "space": "O(1)",
     "keyPoints": ["Simple, but re-scans overlapping windows", "Too slow for 30 days of 10-second probes"],
     "code": '''from __future__ import annotations


def longest_window(checks: list[int], budget: int) -> int:
    best = 0
    for start in range(len(checks)):
        failures = 0
        for end in range(start, len(checks)):
            failures += checks[end] == 0
            if failures > budget:
                break
            best = max(best, end - start + 1)
    return best
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Try every start", "idea": "Extend from each start until the budget breaks.",
     "time": "O(n²)", "space": "O(1)", "use": "Short lists; easiest to reason about."},
    {"name": "Sliding window", "idea": "Grow the right edge; shrink the left while failures > budget.",
     "time": "O(n)", "space": "O(1)", "use": "Long probe histories, e.g. 30 days of checks."},
]

VARIANT_TITLE = "Error budget window"
VARIANT_APPROACH = "Sliding window with a failure counter · O(n) · O(1)"


def _v_counts():
    rng = random.Random(209)
    return [rng.choice([0, 0, 0, 0, 1, 2, 3, 8]) for _ in range(3000)]


def _v_checks():
    rng = random.Random(1004)
    return [0 if rng.random() < 0.1 else 1 for _ in range(3000)]


VARIANTS = [
    {
        "key": "error-counts",
        "title": "Budget of failed requests",
        "approach": "Sliding window over a running sum · O(n) · O(1)",
        "spec": {"kind": "fn", "fn": "longest_within_budget", "params": ["errors_per_min", "budget"]},
        "statement": (
            "Instead of pass/fail probes, your SLO dashboard stores `errors_per_min[i]`, the number of failed "
            "requests in minute `i`. The error budget allows `budget` failed requests in total.\n\n"
            "Return the length of the longest run of **consecutive** minutes whose failed requests add up to at "
            "most `budget`. Return `0` if no minute fits on its own."
        ),
        "examples": [
            {"args": {"errors_per_min": [0, 2, 0, 5, 1, 0, 0, 3], "budget": 4},
             "explanation": "[1, 0, 0, 3] uses exactly 4 over four minutes; [0, 2, 0] uses 2 over three minutes.",
             "why": {"t": "Classic", "d": "The best run spends the whole budget."}},
            {"args": {"errors_per_min": [9, 7], "budget": 5},
             "explanation": "Each minute alone is over budget.",
             "why": {"t": "Nothing fits", "d": "Every minute exceeds the budget, so the answer is 0."}},
        ],
        "constraints": [
            "0 ≤ errors_per_min.length ≤ 10⁵",
            "0 ≤ errors_per_min[i] ≤ 10⁴",
            "0 ≤ budget ≤ 10⁹",
        ],
        "hints": [
            "Counts are never negative, so widening a window never lowers its total.",
            "Keep a running sum. Add the right minute; while the sum is over budget, subtract the left minute and move it.",
        ],
        "tests": [
            {"args": {"errors_per_min": [], "budget": 3}, "why": {"t": "Empty", "d": "No minutes at all."}},
            {"args": {"errors_per_min": [0, 0, 0], "budget": 0}, "why": {"t": "Zero budget · clean", "d": "Clean minutes fit a zero budget."}},
            {"args": {"errors_per_min": [4], "budget": 4}, "why": {"t": "Exactly the budget", "d": "A total equal to the budget counts."}},
            {"args": {"errors_per_min": [1, 1, 1, 1, 1], "budget": 100}, "why": {"t": "Huge budget", "d": "The whole series fits."}},
            {"args": {"errors_per_min": [3, 0, 0, 50, 0, 0, 0, 3], "budget": 3}, "why": {"t": "Outage minute", "d": "One huge minute splits the series."}},
            {"args": {"errors_per_min": [2, 2, 2, 2], "budget": 5}, "why": {"t": "Ties", "d": "Several runs of the same length."}},
            {"args": {"errors_per_min": _v_counts(), "budget": 40}, "why": {"t": "Large input", "d": "3,000 minutes of error counts."}},
        ],
        "solutions": [
            {"name": "Sliding window (Optimal)",
             "description": "Grow the right edge and add its count; while the total exceeds the budget, drop minutes from the left.",
             "time": "O(n)", "space": "O(1)",
             "keyPoints": ["Works because counts are non-negative", "Each minute enters and leaves once", "Record the length after shrinking"],
             "code": '''def longest_within_budget(errors_per_min, budget):
    left = total = best = 0
    for right, c in enumerate(errors_per_min):
        total += c
        while total > budget:
            total -= errors_per_min[left]
            left += 1
        best = max(best, right - left + 1)
    return best
'''},
            {"name": "Prefix sums, every pair", "slow": True,
             "description": "Build prefix sums, then check every start and end pair.",
             "time": "O(n²)", "space": "O(n)",
             "keyPoints": ["O(1) window totals from prefix sums", "Still quadratic in the number of pairs"],
             "code": '''def longest_within_budget(errors_per_min, budget):
    prefix = [0]
    for c in errors_per_min:
        prefix.append(prefix[-1] + c)
    n = len(errors_per_min)
    best = 0
    for i in range(n):
        for j in range(i + best, n):
            if prefix[j + 1] - prefix[i] > budget:
                break
            best = j - i + 1
    return best
'''},
        ],
        "starter": '''def longest_within_budget(errors_per_min: list[int], budget: int) -> int:
    """Longest run of consecutive minutes with at most `budget` failed requests."""
    raise NotImplementedError
''',
    },
    {
        "key": "alert-burst",
        "title": "Tightest failure burst",
        "approach": "Window over failure positions · O(n) · O(f)",
        "spec": {"kind": "fn", "fn": "tightest_burst", "params": ["checks", "k"]},
        "statement": (
            "An alert fires when `k` health checks fail close together. To tune its evaluation window, find the "
            "**shortest** run of consecutive checks that contains at least `k` failures (`0` in `checks`).\n\n"
            "Return its length, or `0` if the whole list has fewer than `k` failures."
        ),
        "examples": [
            {"args": {"checks": [1, 0, 1, 1, 0, 0, 1, 0], "k": 3},
             "explanation": "[0, 0, 1, 0] at the end holds three failures in four checks.",
             "why": {"t": "Classic", "d": "The burst is the tightest group of k failures."}},
            {"args": {"checks": [1, 1, 0, 1], "k": 2},
             "explanation": "Only one failure: the alert can never fire.",
             "why": {"t": "Too few failures", "d": "Fewer than k failures means 0."}},
        ],
        "constraints": [
            "0 ≤ checks.length ≤ 10⁵, each value 0 or 1",
            "1 ≤ k ≤ 10⁵",
        ],
        "hints": [
            "The shortest run always starts and ends on a failure.",
            "Collect the failure indices. Every window of `k` consecutive failures gives a run of `f[i + k − 1] − f[i] + 1` checks.",
        ],
        "tests": [
            {"args": {"checks": [], "k": 1}, "why": {"t": "Empty", "d": "No checks, no alert."}},
            {"args": {"checks": [0], "k": 1}, "why": {"t": "k = 1", "d": "Any single failure is a burst of length 1."}},
            {"args": {"checks": [0, 0, 0], "k": 3}, "why": {"t": "All failed", "d": "The whole list is the burst."}},
            {"args": {"checks": [0, 1, 1, 1, 0, 1, 0], "k": 2}, "why": {"t": "Ties", "d": "Two bursts of the same length."}},
            {"args": {"checks": [0, 1, 1, 1, 1, 1, 0], "k": 2}, "why": {"t": "Spread out", "d": "The only two failures are far apart."}},
            {"args": {"checks": [1, 1, 1], "k": 1}, "why": {"t": "All passed", "d": "No failures at all."}},
            {"args": {"checks": _v_checks(), "k": 12}, "why": {"t": "Large input", "d": "3,000 checks with about 10% failures."}},
        ],
        "solutions": [
            {"name": "Failure positions (Optimal)",
             "description": "List the indices of failures, then slide a window of k of them and take the smallest span.",
             "time": "O(n)", "space": "O(f)",
             "keyPoints": ["A tightest run starts and ends on a failure", "k consecutive failure indices define each candidate", "O(1) per candidate"],
             "code": '''def tightest_burst(checks, k):
    fails = [i for i, c in enumerate(checks) if c == 0]
    if len(fails) < k:
        return 0
    return min(fails[i + k - 1] - fails[i] + 1 for i in range(len(fails) - k + 1))
'''},
            {"name": "Extend from every start", "slow": True,
             "description": "From each start, extend until k failures are inside, and keep the shortest length.",
             "time": "O(n²)", "space": "O(1)",
             "keyPoints": ["Simple counting", "Rescans long passing stretches"],
             "code": '''def tightest_burst(checks, k):
    best = 0
    n = len(checks)
    for i in range(n):
        seen = 0
        for j in range(i, n):
            seen += checks[j] == 0
            if seen >= k:
                if best == 0 or j - i + 1 < best:
                    best = j - i + 1
                break
    return best
'''},
        ],
        "starter": '''def tightest_burst(checks: list[int], k: int) -> int:
    """Length of the shortest run holding at least k failures, or 0."""
    raise NotImplementedError
''',
    },
]
