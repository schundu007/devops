"""Capra Playground export for DC-NET-13 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "can_reach", "params": ["n", "links", "source", "target"], "types": {}, "ret": "value", "cmp": "exact"}


def case(n, links, s, t):
    return {"n": n, "links": links, "source": s, "target": t}


EXAMPLES = [
    {"args": case(3, [[0, 1], [1, 2]], 0, 2),
     "explanation": "Internet (0) reaches the database (2) through the app tier (1).",
     "why": {"t": "Through the middle", "d": "Two hops."}},
    {"args": case(6, [[0, 1], [0, 2], [3, 5], [5, 4], [4, 3]], 0, 5),
     "explanation": "{0,1,2} and {3,4,5} never touch.",
     "why": {"t": "Separate segments", "d": "No path between two components."}},
    {"args": case(1, [], 0, 0),
     "explanation": "A node always reaches itself.",
     "why": {"t": "Source equals target", "d": "Single node, no links."}},
]


def _chain(n):
    return [[i, i + 1] for i in range(n - 1)]


def _random(seed):
    rng = random.Random(seed)
    n = 800
    links, seen = [], set()
    while len(links) < 700:
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b and (min(a, b), max(a, b)) not in seen:
            seen.add((min(a, b), max(a, b)))
            links.append([a, b])
    return n, links


_N, _L = _random(1971)

TESTS = [
    {"args": case(2, [], 0, 1), "why": {"t": "No links", "d": "Two nodes, nothing connects them."}},
    {"args": case(2, [[1, 0]], 0, 1), "why": {"t": "Reversed link", "d": "Links are two-way, so [1,0] also connects 0 to 1."}},
    {"args": case(5, [[0, 1], [1, 2], [2, 0], [3, 4]], 2, 4), "why": {"t": "Cycle, then gap", "d": "A cycle must not loop forever, and 4 stays unreachable."}},
    {"args": case(4, [[0, 1], [2, 3]], 3, 2), "why": {"t": "Target before source", "d": "Direction of the query does not matter."}},
    {"args": case(1500, _chain(1500), 0, 1499), "why": {"t": "Long chain", "d": "1,500 nodes in a line: no recursion-depth trouble."}},
    {"args": case(7, [[0, 1], [1, 2], [3, 4], [4, 5], [5, 6]], 0, 6),
     "why": {"t": "Segmented VPC", "d": "Public subnet and data subnet with no peering: the database is not reachable."}},
    {"args": case(_N, _L, 0, 1), "why": {"t": "Large random 1", "d": "800 nodes, 700 random links."}},
    {"args": case(_N, _L, 5, 17), "why": {"t": "Large random 2", "d": "Same graph, another pair."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "BFS (Optimal)",
     "description": "Build an adjacency list in both directions, BFS from source marking nodes when they are enqueued, and stop as soon as target appears.",
     "time": "O(n + E)", "space": "O(n + E)",
     "keyPoints": ["Handle source == target first", "Mark seen on enqueue, so each node is queued once", "Iterative, so long chains cannot overflow the stack"]},
    {"name": "Repeated spreading", "slow": True,
     "description": "Keep a reachable set and scan every link again and again, spreading reachability to both ends, until nothing changes.",
     "time": "O(n · E)", "space": "O(n)",
     "keyPoints": ["No adjacency list needed", "A long chain needs up to n passes"],
     "code": '''from __future__ import annotations


def can_reach(n: int, links: list[list[int]], source: int, target: int) -> bool:
    reach = [False] * n
    reach[source] = True
    changed = True
    while changed:
        changed = False
        for a, b in links:
            if reach[a] != reach[b]:
                reach[a] = reach[b] = True
                changed = True
    return reach[target]
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Repeated spreading", "idea": "Scan all links until reachability stops growing.", "time": "O(n · E)",
     "space": "O(n)", "use": "Tiny graphs; no data structures."},
    {"name": "BFS / DFS", "idea": "Walk the graph from source with a queue or stack.", "time": "O(n + E)",
     "space": "O(n + E)", "use": "One question per graph."},
    {"name": "Union-find", "idea": "Union every link, then compare the two roots.", "time": "O(E · α(n))",
     "space": "O(n)", "use": "Many reachability questions on the same graph."},
]
