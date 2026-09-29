"""Capra Playground export for DC-PLAT-05 (see tools/export_capra.py)."""
import itertools
import random

SPEC = {"kind": "fn", "fn": "min_upgrade_steps", "params": ["start", "target", "approved"], "types": {}, "ret": "value", "cmp": "exact"}

EXAMPLES = [
    {"args": {"start": ["1.27", "1.27", "1.27"], "target": ["1.29", "1.29", "1.29"],
              "approved": [["1.28", "1.27", "1.27"], ["1.28", "1.28", "1.27"], ["1.28", "1.28", "1.28"],
                           ["1.29", "1.28", "1.28"], ["1.29", "1.29", "1.28"], ["1.29", "1.29", "1.29"]]},
     "explanation": "Control plane, kubelet, then kube-proxy move one minor version at a time: 6 approved steps.",
     "why": {"t": "Normal path", "d": "A stepwise upgrade through approved states."}},
    {"args": {"start": ["1.27", "1.27"], "target": ["1.29", "1.29"], "approved": [["1.29", "1.29"]]},
     "explanation": "No approved state is one change from the start, so the target cannot be reached: -1.",
     "why": {"t": "Unreachable", "d": "The target is approved but disconnected."}},
]


def _large():
    rng = random.Random(433)
    versions = ["v1", "v2", "v3", "v4", "v5"]
    states = [list(s) for s in itertools.product(versions, repeat=4)]
    approved = [s for s in states if rng.random() < 0.55]
    approved.append(["v5", "v5", "v5", "v5"])
    return {"start": ["v1", "v1", "v1", "v1"], "target": ["v5", "v5", "v5", "v5"], "approved": approved}


TESTS = [
    {"args": {"start": ["a"], "target": ["a"], "approved": []}, "why": {"t": "Already there", "d": "start == target needs 0 steps."}},
    {"args": {"start": ["a"], "target": ["b"], "approved": [["c"]]}, "why": {"t": "Target not approved", "d": "An unapproved target is never reachable."}},
    {"args": {"start": ["a"], "target": ["b"], "approved": [["b"]]}, "why": {"t": "L = 1", "d": "One component, one step."}},
    {"args": {"start": ["x", "x"], "target": ["y", "y"], "approved": [["y", "x"], ["y", "x"], ["y", "y"]]},
     "why": {"t": "Duplicates", "d": "Duplicate approved states mean nothing extra."}},
    {"args": {"start": ["a", "a", "a"], "target": ["b", "b", "b"],
              "approved": [["b", "a", "a"], ["b", "b", "a"], ["a", "b", "a"], ["a", "b", "b"], ["b", "b", "b"], ["c", "a", "a"]]},
     "why": {"t": "Several routes", "d": "Two shortest routes of 3; BFS finds the length."}},
    {"args": {"start": ["a", "a"], "target": ["b", "b"], "approved": [["a", "b"], ["c", "b"], ["c", "c"], ["b", "c"], ["b", "b"]]},
     "why": {"t": "Shortcut exists", "d": "A longer detour exists, but the answer is the shortest path."}},
    {"args": {"start": ["a", "a"], "target": ["b", "b"], "approved": [["a", "a"], ["b", "b"]]},
     "why": {"t": "Start in list", "d": "The start state being approved does not create a path."}},
    {"args": _large(), "why": {"t": "Large input", "d": "About 340 approved states of 4 components with 5 versions each."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "BFS with wildcard buckets (Optimal)",
     "description": "Bucket every approved state by (position, state with that position blanked). States one change apart share a bucket, so BFS finds neighbors without comparing all pairs; each bucket is used once.",
     "time": "O(N · L²)", "space": "O(N · L²)",
     "keyPoints": ["Handle start == target and an unapproved target first", "Buckets give neighbors without pairwise comparison", "Delete a bucket after using it"]},
    {"name": "BFS comparing all states", "slow": True,
     "description": "BFS where each popped state is compared with every approved state to find the ones that differ in exactly one position.",
     "time": "O(N² · L)", "space": "O(N · L)",
     "keyPoints": ["Same BFS, slower neighbor search", "Too slow at 10^4 approved states"],
     "code": '''from __future__ import annotations

from collections import deque


def min_upgrade_steps(start, target, approved) -> int:
    src, dst = tuple(start), tuple(target)
    if src == dst:
        return 0
    allowed = {tuple(s) for s in approved}
    seen = {src}
    q = deque([(src, 0)])
    while q:
        s, d = q.popleft()
        for n in allowed:
            if n not in seen and sum(a != b for a, b in zip(s, n)) == 1:
                if n == dst:
                    return d + 1
                seen.add(n)
                q.append((n, d + 1))
    return -1
'''},
]

WAYS_TO_SOLVE = [
    {"name": "BFS, compare all pairs", "idea": "For each state, scan every approved state for a one-change neighbor.",
     "time": "O(N² · L)", "space": "O(N · L)", "use": "A few hundred states."},
    {"name": "BFS with wildcard buckets", "idea": "Group states by one blanked position; a bucket lists all one-change neighbors.",
     "time": "O(N · L²)", "space": "O(N · L²)", "use": "Large approved-state catalogues."},
]

VARIANT_TITLE = "Fewest upgrade steps"
VARIANT_APPROACH = "BFS with wildcard buckets · O(N · L²) · O(N · L²)"


def _skew_large():
    rng = random.Random(752)
    states = [list(s) for s in itertools.product(range(6), repeat=3)]
    approved = [s for s in states if rng.random() < 0.6 or s == [5, 5, 5]]
    return {"start": [0, 0, 0], "target": [5, 5, 5], "approved": approved}


def _within_large():
    rng = random.Random(127)
    versions = ["a", "b", "c", "d"]
    states = [list(s) for s in itertools.product(versions, repeat=4)]
    approved = [s for s in states if rng.random() < 0.4]
    return {"start": ["a", "a", "a", "a"], "approved": approved, "k": 3}


VARIANTS = [
    {
        "key": "one-minor-at-a-time",
        "title": "One minor version at a time",
        "approach": "BFS generating ±1 neighbors · O(N · L²) · O(N · L)",
        "spec": {"kind": "fn", "fn": "min_skew_steps", "params": ["start", "target", "approved"], "cmp": "exact"},
        "statement": (
            "Kubernetes' version skew policy allows a component to move only **one minor version** at a time.\n"
            "\n"
            "### Input\n"
            "- `start`, `target`: states as lists of integer minor versions, for example `[28, 27, 5]`\n"
            "- `approved`: the list of allowed states\n"
            "\n"
            "### Output\n"
            "- The fewest steps from `start` to `target`, `0` if they are equal, or `-1` if the target cannot be reached\n"
            "\n"
            "### Rules\n"
            "- One step changes exactly one component by **+1 or -1**\n"
            "- The new state must be in `approved`\n"
            "- The start does not need to be approved"
        ),
        "examples": [
            {"args": {"start": [27, 27], "target": [28, 28], "approved": [[28, 27], [28, 28], [27, 28]]},
             "explanation": "Two single-minor steps, through either [28, 27] or [27, 28].",
             "why": {"t": "Basic path", "d": "Each step moves one component by one."}},
            {"args": {"start": [27, 27], "target": [29, 27], "approved": [[29, 27]]},
             "explanation": "Jumping from 27 to 29 skips a minor version, and [28, 27] is not approved: -1.",
             "why": {"t": "No skipping", "d": "A two-minor jump is not a step."}},
        ],
        "constraints": ["1 ≤ L ≤ 8", "0 ≤ len(approved) ≤ 10^4, duplicates allowed", "0 ≤ version ≤ 1000"],
        "hints": [
            "Each state has at most `2 · L` possible neighbors, so generate them instead of searching for them.",
            "Put the approved states in a set of tuples and BFS from the start.",
        ],
        "tests": [
            {"args": {"start": [3], "target": [3], "approved": []}, "why": {"t": "Already there", "d": "0 steps, even with nothing approved."}},
            {"args": {"start": [3], "target": [5], "approved": [[4]]}, "why": {"t": "Target not approved", "d": "An unapproved target is unreachable."}},
            {"args": {"start": [5], "target": [3], "approved": [[4], [3]]}, "why": {"t": "Downgrade", "d": "Steps may go down a minor version."}},
            {"args": {"start": [1, 1], "target": [2, 2], "approved": [[2, 1], [2, 1], [2, 2], [3, 1]]}, "why": {"t": "Duplicates", "d": "Repeated approved states add nothing."}},
            {"args": {"start": [0, 0], "target": [0, 2], "approved": [[1, 0], [1, 1], [1, 2], [0, 2]]},
             "why": {"t": "Detour", "d": "[0, 1] is not approved, so the path goes around it: 4 steps."}},
            {"args": {"start": [0, 0, 0], "target": [2, 0, 0], "approved": [[1, 0, 0], [0, 0, 0], [2, 0, 1]]}, "why": {"t": "Near miss", "d": "[2, 0, 1] is one step from the target but the target is not approved."}},
            {"args": _skew_large(), "why": {"t": "Large input", "d": "About 130 approved states of 3 components with 6 minors each."}},
        ],
        "solutions": [
            {"name": "BFS with generated neighbors (Optimal)",
             "description": "BFS from the start. For each state try every component at +1 and -1; keep the result if it is approved and unseen.",
             "time": "O(N · L²)", "space": "O(N · L)",
             "keyPoints": ["Only 2L candidate neighbors per state", "Set lookup replaces pairwise comparison", "Check start == target and an unapproved target first"],
             "code": '''from collections import deque


def min_skew_steps(start, target, approved):
    src, dst = tuple(start), tuple(target)
    if src == dst:
        return 0
    allowed = {tuple(s) for s in approved}
    if dst not in allowed:
        return -1
    seen = {src}
    q = deque([(src, 0)])
    while q:
        s, d = q.popleft()
        for i in range(len(s)):
            for delta in (1, -1):
                n = s[:i] + (s[i] + delta,) + s[i + 1:]
                if n in allowed and n not in seen:
                    if n == dst:
                        return d + 1
                    seen.add(n)
                    q.append((n, d + 1))
    return -1
'''},
            {"name": "BFS comparing all states", "slow": True,
             "description": "For each popped state, scan every approved state for one that differs in exactly one component, by exactly one.",
             "time": "O(N² · L)", "space": "O(N · L)",
             "keyPoints": ["Same BFS, slow neighbor search", "Checks every approved state per pop"],
             "code": '''from collections import deque


def min_skew_steps(start, target, approved):
    src, dst = tuple(start), tuple(target)
    if src == dst:
        return 0
    allowed = {tuple(s) for s in approved}
    seen = {src}
    q = deque([(src, 0)])
    while q:
        s, d = q.popleft()
        for n in allowed:
            if n in seen:
                continue
            diffs = [abs(a - b) for a, b in zip(s, n) if a != b]
            if diffs == [1]:
                if n == dst:
                    return d + 1
                seen.add(n)
                q.append((n, d + 1))
    return -1
'''},
        ],
        "starter": '''def min_skew_steps(start: list[int], target: list[int], approved: list[list[int]]) -> int:
    pass
''',
    },
    {
        "key": "within-k-steps",
        "title": "States within k steps",
        "approach": "Depth-limited BFS with wildcard buckets · O(N · L²) · O(N · L²)",
        "spec": {"kind": "fn", "fn": "reachable_within", "params": ["start", "approved", "k"], "cmp": "exact"},
        "statement": (
            "A maintenance window allows at most `k` component changes: count the approved states on the table.\n"
            "\n"
            "### Input\n"
            "- `start`: the current state\n"
            "- `approved`: the list of allowed states\n"
            "- `k`: the most steps allowed\n"
            "\n"
            "### Output\n"
            "- The number of **distinct approved states** other than `start` that can be reached in **at most** `k` steps\n"
            "\n"
            "### Rules\n"
            "- Steps work as in the main problem: change exactly one component to any other version, landing on an approved state\n"
            "- The start does not need to be approved, and it never counts"
        ),
        "examples": [
            {"args": {"start": ["1.27", "1.27"], "approved": [["1.28", "1.27"], ["1.28", "1.28"], ["1.29", "1.29"]], "k": 2},
             "explanation": "[1.28, 1.27] is one step away, [1.28, 1.28] two. [1.29, 1.29] would take a third step.",
             "why": {"t": "Depth limit", "d": "States beyond k steps are not counted."}},
        ],
        "constraints": ["1 ≤ L ≤ 10", "0 ≤ len(approved) ≤ 10^4, duplicates allowed", "0 ≤ k ≤ 10^4"],
        "hints": [
            "BFS visits states in order of distance, so stop expanding once the depth reaches `k`.",
            "Bucket states by `(position, state with that position removed)` to find one-change neighbors quickly.",
            "Each bucket only needs to be expanded once; delete it after use.",
        ],
        "tests": [
            {"args": {"start": ["a"], "approved": [["b"]], "k": 0}, "why": {"t": "k = 0", "d": "No steps allowed: 0."}},
            {"args": {"start": ["a"], "approved": [], "k": 5}, "why": {"t": "Nothing approved", "d": "No state to land on."}},
            {"args": {"start": ["a", "a"], "approved": [["a", "a"], ["b", "a"]], "k": 3}, "why": {"t": "Start approved", "d": "The start itself never counts."}},
            {"args": {"start": ["x"], "approved": [["y"], ["y"], ["z"]], "k": 1}, "why": {"t": "Duplicates", "d": "Each distinct state counts once; with L = 1 every state is one step away."}},
            {"args": {"start": ["a", "a", "a"], "approved": [["b", "a", "a"], ["b", "b", "a"], ["b", "b", "b"], ["c", "c", "c"]], "k": 10},
             "why": {"t": "Unreachable island", "d": "[c, c, c] differs in every position from all others."}},
            {"args": _within_large(), "why": {"t": "Large input", "d": "About 120 approved states of 4 components, k = 3."}},
        ],
        "solutions": [
            {"name": "Depth-limited bucket BFS (Optimal)",
             "description": "Same wildcard buckets as the main problem, but BFS stops expanding at depth k and counts every newly seen approved state.",
             "time": "O(N · L²)", "space": "O(N · L²)",
             "keyPoints": ["BFS order means depth is the step count", "Do not expand nodes at depth k", "Count distinct states, excluding the start"],
             "code": '''from collections import defaultdict, deque


def reachable_within(start, approved, k):
    src = tuple(start)
    allowed = {tuple(s) for s in approved}
    buckets = defaultdict(list)
    for s in allowed:
        for i in range(len(s)):
            buckets[(i, s[:i] + s[i + 1:])].append(s)
    seen = {src}
    q = deque([(src, 0)])
    count = 0
    while q:
        s, d = q.popleft()
        if d == k:
            continue
        for i in range(len(s)):
            key = (i, s[:i] + s[i + 1:])
            for n in buckets.pop(key, ()):
                if n not in seen:
                    seen.add(n)
                    count += 1
                    q.append((n, d + 1))
    return count
'''},
            {"name": "BFS comparing all states", "slow": True,
             "description": "Depth-limited BFS where neighbors are found by comparing the popped state with every approved state.",
             "time": "O(N² · L)", "space": "O(N · L)",
             "keyPoints": ["Easy to verify", "Quadratic in the number of approved states"],
             "code": '''from collections import deque


def reachable_within(start, approved, k):
    src = tuple(start)
    allowed = {tuple(s) for s in approved}
    seen = {src}
    q = deque([(src, 0)])
    while q:
        s, d = q.popleft()
        if d == k:
            continue
        for n in allowed:
            if n not in seen and sum(a != b for a, b in zip(s, n)) == 1:
                seen.add(n)
                q.append((n, d + 1))
    return len(seen) - 1
'''},
        ],
        "starter": '''def reachable_within(start: list[str], approved: list[list[str]], k: int) -> int:
    pass
''',
    },
]
