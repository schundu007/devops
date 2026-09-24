"""Capra Playground export for DC-NET-11 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "min_interconnect_cost", "params": ["sites"], "types": {}, "ret": "value", "cmp": "exact"}

EXAMPLES = [
    {"args": {"sites": [[0, 0], [2, 2], [3, 10], [5, 2], [7, 0]]},
     "explanation": "Links (0,0)-(2,2)=4, (2,2)-(5,2)=3, (5,2)-(7,0)=4 and (2,2)-(3,10)=9. The total is 20.",
     "why": {"t": "Five sites", "d": "A small complete graph."}},
    {"args": {"sites": [[3, 12], [-2, 5]]},
     "explanation": "One link of Manhattan length 5 + 7 = 12.",
     "why": {"t": "Two sites · Negative coordinates", "d": "A single link, with negative x."}},
    {"args": {"sites": [[4, 4]]},
     "explanation": "A single site is already connected: 0.",
     "why": {"t": "Single site", "d": "No links needed."}},
]


def _rand(n, seed, span):
    rng = random.Random(seed)
    pts = set()
    while len(pts) < n:
        pts.add((rng.randint(-span, span), rng.randint(-span, span)))
    return [list(p) for p in sorted(pts)]


TESTS = [
    {"args": {"sites": []}, "why": {"t": "Empty", "d": "No sites: cost 0."}},
    {"args": {"sites": [[0, 0], [0, 1], [0, 2], [0, 3]]}, "why": {"t": "Collinear", "d": "Sites on one line: the chain of unit links."}},
    {"args": {"sites": [[0, 0], [1, 1], [1, 0], [0, 1]]}, "why": {"t": "Equal-cost ties", "d": "Many links cost the same; the total is still unique."}},
    {"args": {"sites": [[-1000000, -1000000], [1000000, 1000000]]}, "why": {"t": "Coordinate limits", "d": "The largest possible single link, 4 * 10^6."}},
    {"args": {"sites": [[0, 0], [100, 0], [0, 100], [100, 100], [50, 50]]}, "why": {"t": "Hub in the middle", "d": "A centre site makes every corner cheaper to reach."}},
    {"args": {"sites": [[10, 0], [12, 0], [500, 500], [502, 501], [1000, 0], [1001, 3]]},
     "why": {"t": "Three data centres", "d": "Pairs of close sites far apart: two expensive backbone links."}},
    {"args": {"sites": _rand(40, 1584, 50)}, "why": {"t": "Random", "d": "40 random sites."}},
    {"args": {"sites": _rand(200, 11, 10**6)}, "why": {"t": "Large input", "d": "200 sites with large coordinates."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Prim, array version (Optimal)",
     "description": "Grow a tree from site 0. Each round, add the outside site with the cheapest link to the tree, then update every outside site's cheapest link through the new one.",
     "time": "O(n²)", "space": "O(n)",
     "keyPoints": ["The graph is complete, so a plain O(n) scan beats a heap", "Edges are computed on the fly, never stored", "n rounds, each adds one site"]},
    {"name": "Kruskal with union-find", "slow": True,
     "description": "List all n(n-1)/2 links, sort them by length, and add each one unless both ends are already connected.",
     "time": "O(n² log n)", "space": "O(n²)",
     "keyPoints": ["Stores every edge", "The sort dominates on a complete graph"],
     "code": '''from __future__ import annotations


def min_interconnect_cost(sites: list[list[int]]) -> int:
    n = len(sites)
    edges = sorted(
        (abs(sites[i][0] - sites[j][0]) + abs(sites[i][1] - sites[j][1]), i, j)
        for i in range(n) for j in range(i + 1, n)
    )
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    total = used = 0
    for d, i, j in edges:
        a, b = find(i), find(j)
        if a != b:
            parent[a] = b
            total += d
            used += 1
            if used == n - 1:
                break
    return total
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Kruskal", "idea": "Sort every link and add the cheapest one that joins two groups.", "time": "O(n² log n)",
     "space": "O(n²)", "use": "Sparse graphs with an explicit edge list."},
    {"name": "Prim, array", "idea": "Grow one tree; track each outside site's cheapest link to it.", "time": "O(n²)",
     "space": "O(n)", "use": "Dense or complete graphs, like every site pair."},
]
