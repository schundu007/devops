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
     "description": "Bucket every approved state by (position, state with that position blanked). States one change apart share a bucket, so BFS finds neighbours without comparing all pairs; each bucket is used once.",
     "time": "O(N · L²)", "space": "O(N · L²)",
     "keyPoints": ["Handle start == target and an unapproved target first", "Buckets give neighbours without pairwise comparison", "Delete a bucket after using it"]},
    {"name": "BFS comparing all states", "slow": True,
     "description": "BFS where each popped state is compared with every approved state to find the ones that differ in exactly one position.",
     "time": "O(N² · L)", "space": "O(N · L)",
     "keyPoints": ["Same BFS, slower neighbour search", "Too slow at 10^4 approved states"],
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
    {"name": "BFS, compare all pairs", "idea": "For each state, scan every approved state for a one-change neighbour.",
     "time": "O(N² · L)", "space": "O(N · L)", "use": "A few hundred states."},
    {"name": "BFS with wildcard buckets", "idea": "Group states by one blanked position; a bucket lists all one-change neighbours.",
     "time": "O(N · L²)", "space": "O(N · L²)", "use": "Large approved-state catalogues."},
]
