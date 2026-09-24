"""Capra Playground export for DC-REL-06 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "impacts", "params": ["n", "deps", "queries"], "types": {}, "ret": "value", "cmp": "exact"}


def case(n, deps, queries):
    return {"n": n, "deps": [list(d) for d in deps], "queries": [list(q) for q in queries]}


EXAMPLES = [
    {"args": case(4, [(0, 1), (1, 2), (0, 3)], [(0, 2), (2, 0), (3, 1)]),
     "explanation": "vpc (0) is used by subnet (1), which is used by the cluster (2): 2 depends on 0 through 1. The reverse is False, and 3 and 1 are unrelated.",
     "why": {"t": "Indirect dependency", "d": "A chain of two, the same pair reversed, and unrelated components."}},
    {"args": case(2, [], [(0, 1), (1, 1)]),
     "explanation": "No dependencies at all, and a component does not count as depending on itself.",
     "why": {"t": "No edges · self query", "d": "Nothing depends on anything."}},
]


def _large():
    rng = random.Random(1462)
    n = 120
    deps = set()
    for v in range(1, n):
        for _ in range(rng.randint(0, 3)):
            deps.add((rng.randrange(0, v), v))
    queries = [(rng.randrange(n), rng.randrange(n)) for _ in range(400)]
    return case(n, sorted(deps), queries)


TESTS = [
    {"args": case(1, [], [(0, 0)]), "why": {"t": "Single component", "d": "Self query on the only component."}},
    {"args": case(3, [(0, 1), (1, 2)], []), "why": {"t": "No queries", "d": "An empty answer list."}},
    {"args": case(5, [(0, 1), (1, 2), (2, 3), (3, 4)], [(0, 4), (4, 0), (1, 3), (2, 2)]), "why": {"t": "Long chain", "d": "Four hops, reversed, middle and self."}},
    {"args": case(4, [(0, 1), (0, 2), (1, 3), (2, 3)], [(0, 3), (1, 2), (2, 1)]), "why": {"t": "Diamond", "d": "Two paths to the same node; siblings do not depend on each other."}},
    {"args": case(4, [(0, 1), (0, 1), (1, 2)], [(0, 2), (0, 1)]), "why": {"t": "Duplicate edge", "d": "The same dependency listed twice."}},
    {"args": case(4, [(3, 0), (2, 3), (1, 2)], [(1, 0), (0, 1)]), "why": {"t": "Reversed numbering", "d": "Edges point from high to low numbers."}},
    {"args": case(6, [(0, 1), (0, 2), (1, 3), (2, 4), (4, 5)], [(0, 5), (1, 5), (3, 5), (2, 5), (0, 3)]),
     "why": {"t": "Base image change", "d": "base-image -> runtime images -> services: who is affected by a change?"}},
    {"args": _large(), "why": {"t": "Large input", "d": "120 components and 400 queries."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Reachability bitmasks in topological order (Optimal)",
     "description": "Sort components topologically. Walk them in reverse: each component's reach is the union of its children and their reach, kept as an integer bitmask. Each query is then one bit test.",
     "time": "O(n + E·n/64 + Q)", "space": "O(n²/64)",
     "keyPoints": ["Precompute once, answer every query in O(1)", "Reverse topological order means children are done first", "Bitmask OR merges a whole reach set at once"]},
    {"name": "BFS per query", "slow": True,
     "description": "For each query (u, v), run a BFS from u along the dependency edges and see whether it reaches v.",
     "time": "O(Q · (n + E))", "space": "O(n + E)",
     "keyPoints": ["No precomputation", "Repeats the same search for every query"],
     "code": '''from __future__ import annotations

from collections import deque


def impacts(n: int, deps: list[tuple[int, int]], queries: list[tuple[int, int]]) -> list[bool]:
    children: list[list[int]] = [[] for _ in range(n)]
    for up, down in deps:
        children[up].append(down)
    out = []
    for u, v in queries:
        seen = {u}
        q = deque([u])
        found = False
        while q and not found:
            x = q.popleft()
            for w in children[x]:
                if w == v:
                    found = True
                    break
                if w not in seen:
                    seen.add(w)
                    q.append(w)
        out.append(found)
    return out
'''},
]

WAYS_TO_SOLVE = [
    {"name": "BFS per query", "idea": "Search from u for every query.",
     "time": "O(Q · (n + E))", "space": "O(n + E)", "use": "Few queries."},
    {"name": "Floyd-Warshall closure", "idea": "reach[i][j] |= reach[i][k] and reach[k][j] for every k.",
     "time": "O(n³)", "space": "O(n²)", "use": "Small graphs, many queries; simplest closure."},
    {"name": "Bitmasks in topological order", "idea": "Merge children's reach sets in reverse topological order.",
     "time": "O(n + E·n/64 + Q)", "space": "O(n²/64)", "use": "Many queries on a DAG."},
]
