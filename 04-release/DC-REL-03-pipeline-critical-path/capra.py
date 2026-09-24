"""Capra Playground export for DC-REL-03 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "pipeline_time", "params": ["n", "deps", "duration"], "types": {}, "ret": "value", "cmp": "exact"}


def case(n, deps, duration):
    return {"n": n, "deps": [list(d) for d in deps], "duration": duration}


EXAMPLES = [
    {"args": case(4, [(0, 1), (0, 2), (1, 3), (2, 3)], [2, 5, 3, 1]),
     "explanation": "build (2) fans out to test (5) and lint (3), which both gate deploy (1). The longest chain is build -> test -> deploy = 2 + 5 + 1 = 8.",
     "why": {"t": "Diamond", "d": "Two parallel branches; only the slower one counts."}},
    {"args": case(3, [], [4, 9, 2]),
     "explanation": "No dependencies: all three stages run at once, so the pipeline takes as long as the slowest stage, 9.",
     "why": {"t": "No dependencies", "d": "Everything runs in parallel."}},
]


def _large():
    rng = random.Random(2050)
    n = 300
    deps = set()
    for b in range(1, n):
        for _ in range(rng.randint(1, 3)):
            deps.add((rng.randrange(0, b), b))
    return case(n, sorted(deps), [rng.randint(1, 60) for _ in range(n)])


TESTS = [
    {"args": case(1, [], [7]), "why": {"t": "Single stage", "d": "One stage with no dependencies."}},
    {"args": case(1, [], [0]), "why": {"t": "Zero duration", "d": "A stage that takes no time."}},
    {"args": case(5, [(0, 1), (1, 2), (2, 3), (3, 4)], [1, 2, 3, 4, 5]), "why": {"t": "Straight chain", "d": "No parallelism: the sum of all durations."}},
    {"args": case(4, [(3, 2), (2, 1), (1, 0)], [1, 1, 1, 10]), "why": {"t": "Reversed numbering", "d": "Dependencies point from high to low numbers."}},
    {"args": case(5, [(0, 4), (1, 4), (2, 4), (3, 4)], [3, 8, 1, 8, 2]), "why": {"t": "Fan-in · tie", "d": "Four stages gate one; two share the longest time."}},
    {"args": case(6, [(0, 1), (1, 2), (3, 4), (4, 5)], [1, 1, 1, 5, 5, 5]), "why": {"t": "Two chains", "d": "Two independent pipelines; the longer one decides."}},
    {"args": case(4, [(0, 1), (0, 1), (1, 2)], [2, 2, 2, 1]), "why": {"t": "Duplicate dependency", "d": "The same dependency listed twice."}},
    {"args": case(6, [(0, 2), (1, 2), (2, 3), (2, 4), (3, 5), (4, 5)], [4, 6, 2, 10, 1, 3]),
     "why": {"t": "CI pipeline", "d": "checkout, deps -> build -> integration tests / image scan -> deploy."}},
    {"args": _large(), "why": {"t": "Large input", "d": "300 stages with random dependencies."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Topological sort + DP (Optimal)",
     "description": "Walk stages in Kahn's topological order. A stage starts when its latest dependency finishes; its finish time is start + duration. The pipeline time is the largest finish time.",
     "time": "O(n + E)", "space": "O(n + E)",
     "keyPoints": ["Earliest start = max finish of its dependencies", "Kahn's order guarantees dependencies are done first", "The answer is the critical path length"]},
    {"name": "DFS with memo",
     "description": "finish(s) = duration[s] + the largest finish among the stages s depends on. Memoise it and take the maximum over all stages.",
     "time": "O(n + E)", "space": "O(n + E)",
     "keyPoints": ["Same recurrence, computed top-down", "Deep chains need an explicit stack in production code"],
     "code": '''from __future__ import annotations

from functools import lru_cache


def pipeline_time(n: int, deps: list[tuple[int, int]], duration: list[int]) -> int:
    parents: list[list[int]] = [[] for _ in range(n)]
    for a, b in deps:
        parents[b].append(a)

    @lru_cache(maxsize=None)
    def finish(s: int) -> int:
        return duration[s] + max((finish(p) for p in parents[s]), default=0)

    return max((finish(s) for s in range(n)), default=0)
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Topological order + DP", "idea": "Process stages in Kahn's order, pushing each finish time forward to its children.",
     "time": "O(n + E)", "space": "O(n + E)", "use": "Iterative; no recursion limits on long pipelines."},
    {"name": "DFS with memo", "idea": "Recursively compute each stage's finish time from its parents and cache it.",
     "time": "O(n + E)", "space": "O(n + E)", "use": "Shortest code; fine for moderate depth."},
]
