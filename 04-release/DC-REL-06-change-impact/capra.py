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

VARIANT_TITLE = "Does u affect v?"
VARIANT_APPROACH = "Reachability bitmasks in topological order · O(n + E·n/64 + Q) · O(n²/64)"

_REACH = '''from collections import deque


def _reach(n: int, deps: list[list[int]]) -> list[int]:
    children: list[list[int]] = [[] for _ in range(n)]
    indegree = [0] * n
    for up, down in deps:
        children[up].append(down)
        indegree[down] += 1
    order = []
    ready = deque(v for v in range(n) if indegree[v] == 0)
    while ready:
        v = ready.popleft()
        order.append(v)
        for w in children[v]:
            indegree[w] -= 1
            if indegree[w] == 0:
                ready.append(w)
    reach = [0] * n
    for u in reversed(order):
        for w in children[u]:
            reach[u] |= (1 << w) | reach[w]
    return reach
'''

_BLAST_FAST = _REACH + '''

def blast_radius(n: int, deps: list[list[int]]) -> list[int]:
    return [bin(r).count("1") for r in _reach(n, deps)]
'''

_BLAST_SLOW = '''def blast_radius(n: int, deps: list[list[int]]) -> list[int]:
    children: list[list[int]] = [[] for _ in range(n)]
    for up, down in deps:
        children[up].append(down)
    out = []
    for s in range(n):
        seen = {s}
        stack = [s]
        while stack:
            x = stack.pop()
            for w in children[x]:
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
        out.append(len(seen) - 1)
    return out
'''

_REBUILD_FAST = _REACH + '''

def rebuild_sets(n: int, deps: list[list[int]], changes: list[list[int]]) -> list[list[int]]:
    reach = _reach(n, deps)
    out = []
    for changed in changes:
        mask = 0
        for c in changed:
            mask |= (1 << c) | reach[c]
        out.append([v for v in range(n) if mask >> v & 1])
    return out
'''

_REBUILD_SLOW = '''def rebuild_sets(n: int, deps: list[list[int]], changes: list[list[int]]) -> list[list[int]]:
    children: list[list[int]] = [[] for _ in range(n)]
    for up, down in deps:
        children[up].append(down)
    out = []
    for changed in changes:
        total = set()
        for c in changed:
            seen = {c}
            stack = [c]
            while stack:
                x = stack.pop()
                for w in children[x]:
                    if w not in seen:
                        seen.add(w)
                        stack.append(w)
            total |= seen
        out.append(sorted(total))
    return out
'''


def _dag(n, seed, fan):
    rng = random.Random(seed)
    deps = set()
    for v in range(1, n):
        for _ in range(rng.randint(0, fan)):
            deps.add((rng.randrange(0, v), v))
    return [list(d) for d in sorted(deps)]


def _bl(n, deps, t, d):
    return {"args": {"n": n, "deps": [list(x) for x in deps]}, "why": {"t": t, "d": d}}


def _rb(n, deps, changes, t, d):
    return {"args": {"n": n, "deps": [list(x) for x in deps], "changes": [list(c) for c in changes]}, "why": {"t": t, "d": d}}


_BIG_DEPS = _dag(120, 606, 3)
_rq = random.Random(66)
_BIG_CHANGES = [sorted(_rq.sample(range(120), _rq.randint(0, 4))) for _ in range(40)]

VARIANTS = [
    {
        "key": "blast-radius",
        "title": "Blast radius of every component",
        "approach": "Reach bitmasks + popcount · O(n + E·n/64) · O(n²/64)",
        "spec": {"kind": "fn", "fn": "blast_radius", "params": ["n", "deps"], "cmp": "exact"},
        "statement": (
            "Label each pull request with its blast radius.\n"
            "\n"
            "### Input\n"
            "- `n`: the number of components, numbered `0..n-1`\n"
            "- `deps[i] = [up, down]`: `down` depends on `up`\n"
            "\n"
            "### Output\n"
            "- A list of `n` counts, in component order: for component `c`, how many **other** components a change to `c` affects\n"
            "\n"
            "### Rules\n"
            "- A component is affected when it depends on `c` directly or through a chain\n"
            "- The graph has no cycles"
        ),
        "examples": [
            {"args": {"n": 4, "deps": [[0, 1], [1, 2], [0, 3]]},
             "explanation": "0 affects 1, 2 and 3; 1 affects 2; 2 and 3 affect nothing.",
             "why": {"t": "Chain and branch", "d": "Indirect dependents count."}},
        ],
        "constraints": ["1 ≤ n ≤ 300", "0 ≤ deps.length ≤ 2000", "the graph is acyclic; edges may repeat"],
        "hints": [
            "The set of affected components is exactly the reach set from the main problem.",
            "Build every reach bitmask once in reverse topological order, then count set bits.",
            "Do not count a component twice when it is reachable along two paths: a set or bitmask handles that.",
        ],
        "tests": [
            _bl(1, [], "Single component", "Nothing to affect: [0]."),
            _bl(3, [], "No edges", "Every radius is 0."),
            _bl(4, [(0, 1), (0, 2), (1, 3), (2, 3)], "Diamond", "Component 3 is reached twice but counted once."),
            _bl(3, [(0, 1), (0, 1), (1, 2)], "Duplicate edge", "A repeated dependency changes nothing."),
            _bl(5, [(4, 3), (3, 2), (2, 1), (1, 0)], "Reversed chain", "The highest number is the root."),
            _bl(6, [(0, 1), (0, 2), (1, 3), (2, 4), (4, 5)], "Base image", "A base image affects every service built on it."),
            _bl(120, _BIG_DEPS, "Large input", "120 components with random dependencies."),
        ],
        "solutions": [
            {"name": "Reach bitmasks + popcount (Optimal)",
             "description": "Compute each component's reach bitmask in reverse topological order, as in the main problem, and count its set bits.",
             "time": "O(n + E·n/64)", "space": "O(n²/64)",
             "keyPoints": ["Children's masks are final before their parents'", "OR merges whole sets at once", "Popcount gives the radius"],
             "code": _BLAST_FAST},
            {"name": "DFS from every component", "slow": True,
             "description": "Run a separate graph search from each component and count what it reaches.",
             "time": "O(n · (n + E))", "space": "O(n + E)",
             "keyPoints": ["No topological order needed", "Repeats work shared by common descendants"],
             "code": _BLAST_SLOW},
        ],
        "starter": "def blast_radius(n: int, deps: list[list[int]]) -> list[int]:\n    pass\n",
    },
    {
        "key": "rebuild-sets",
        "title": "Rebuild set for a change batch",
        "approach": "Precomputed reach masks, OR per batch · O(n + E·n/64 + Σ(k + n)) · O(n²/64)",
        "spec": {"kind": "fn", "fn": "rebuild_sets", "params": ["n", "deps", "changes"], "cmp": "exact"},
        "statement": (
            "A monorepo CI job receives batches of changed components and must rebuild everything they affect.\n"
            "\n"
            "### Input\n"
            "- `n`: the number of components\n"
            "- `deps[i] = [up, down]`: `down` depends on `up`, as in the main problem; the graph is acyclic\n"
            "- `changes[i]`: the components changed in batch `i`\n"
            "\n"
            "### Output\n"
            "- For each batch, the sorted list of components to rebuild\n"
            "\n"
            "### Rules\n"
            "- Rebuild the changed components themselves plus every component that depends on any of them, directly or indirectly\n"
            "- An empty batch rebuilds nothing"
        ),
        "examples": [
            {"args": {"n": 5, "deps": [[0, 1], [1, 2], [3, 4]], "changes": [[1], [0, 3], []]},
             "explanation": "Changing 1 rebuilds 1 and 2. Changing 0 and 3 rebuilds 0, 1, 2, 3 and 4. An empty batch rebuilds nothing.",
             "why": {"t": "Several batches", "d": "Each batch is the union of its components' reach."}},
        ],
        "constraints": ["1 ≤ n ≤ 300", "0 ≤ deps.length ≤ 2000", "at most 100 batches, each with distinct components"],
        "hints": [
            "Precompute every component's reach once; batches then only combine them.",
            "The rebuild set of a batch is the OR of (1 << c) | reach[c] over its changed components.",
        ],
        "tests": [
            _rb(1, [], [[0]], "Single component", "Changing the only component rebuilds it."),
            _rb(3, [(0, 1)], [], "No batches", "An empty answer list."),
            _rb(4, [(0, 1), (0, 2), (1, 3), (2, 3)], [[1, 2], [3]], "Overlapping reach", "Both changes reach 3; it is listed once."),
            _rb(4, [(0, 1), (1, 2), (2, 3)], [[2, 0]], "Changed ancestor and descendant", "A changed component inside another's reach adds nothing."),
            _rb(4, [(3, 0), (2, 3), (1, 2)], [[1], [0]], "Reversed numbering", "Output is sorted by number, not by dependency order."),
            _rb(6, [(0, 1), (0, 2), (1, 3), (2, 4), (4, 5)], [[2], [5], [1, 4]], "Base image change", "Runtime images and services built on them."),
            _rb(120, _BIG_DEPS, _BIG_CHANGES, "Large input", "120 components and 40 batches."),
        ],
        "solutions": [
            {"name": "Reach masks, OR per batch (Optimal)",
             "description": "Build reach bitmasks once in reverse topological order. For each batch, OR the changed components and their masks, then list the set bits.",
             "time": "O(n + E·n/64 + Σ(k + n))", "space": "O(n²/64)",
             "keyPoints": ["Precompute once, reuse for every batch", "Union of sets is a bitwise OR", "Reading bits in order gives a sorted list"],
             "code": _REBUILD_FAST},
            {"name": "DFS from every changed component", "slow": True,
             "description": "For each changed component in each batch, search the graph from scratch and union the results.",
             "time": "O(Σk · (n + E))", "space": "O(n + E)",
             "keyPoints": ["No precomputation", "Walks shared descendants again for every change"],
             "code": _REBUILD_SLOW},
        ],
        "starter": "def rebuild_sets(n: int, deps: list[list[int]], changes: list[list[int]]) -> list[list[int]]:\n    pass\n",
    },
]
