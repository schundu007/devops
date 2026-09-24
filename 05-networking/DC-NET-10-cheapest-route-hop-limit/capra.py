"""Capra Playground export for DC-NET-10 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "cheapest_route", "params": ["n", "routes", "src", "dst", "max_transit"],
        "types": {}, "ret": "value", "cmp": "exact"}


def case(n, routes, src, dst, k):
    return {"n": n, "routes": routes, "src": src, "dst": dst, "max_transit": k}


R1 = [[0, 1, 100], [1, 2, 100], [2, 3, 100], [0, 3, 800], [1, 3, 600]]

EXAMPLES = [
    {"args": case(4, R1, 0, 3, 1),
     "explanation": "0->1->3 costs 700. The 300 path 0->1->2->3 needs 2 transit regions, one too many.",
     "why": {"t": "Hop limit binds", "d": "The cheapest path overall is not allowed."}},
    {"args": case(4, R1, 0, 3, 2),
     "explanation": "With 2 transit regions allowed, 0->1->2->3 for 300 is legal.",
     "why": {"t": "Hop limit relaxed", "d": "One more transit region unlocks the cheaper path."}},
    {"args": case(3, [[0, 1, 100], [1, 2, 100], [0, 2, 500]], 0, 2, 0),
     "explanation": "Zero transit regions means a direct route only: 500.",
     "why": {"t": "Direct only", "d": "max_transit = 0 allows one hop."}},
]


def _large():
    rng = random.Random(787)
    n = 60
    pairs = set()
    routes = []
    while len(routes) < 700:
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b and (a, b) not in pairs:
            pairs.add((a, b))
            routes.append([a, b, rng.randint(1, 10_000)])
    return case(n, routes, 0, n - 1, 4)


TESTS = [
    {"args": case(3, [[0, 1, 5]], 0, 2, 5),
     "why": {"t": "Unreachable", "d": "No route reaches dst at all: -1."}},
    {"args": case(2, [], 0, 1, 1),
     "why": {"t": "No routes", "d": "An empty route list."}},
    {"args": case(3, [[0, 1, 1], [1, 2, 1]], 0, 2, 0),
     "why": {"t": "Too few hops", "d": "dst is reachable, but only through a transit region the limit forbids."}},
    {"args": case(3, [[1, 0, 5], [2, 1, 5]], 0, 2, 2),
     "why": {"t": "One-way routes", "d": "Routes only go the wrong direction."}},
    {"args": case(5, [[0, 1, 1], [1, 2, 1], [2, 3, 1], [3, 4, 1], [0, 4, 100]], 0, 4, 3),
     "why": {"t": "Exact boundary", "d": "The cheap chain uses exactly max_transit = 3 middle regions."}},
    {"args": case(4, [[0, 1, 1], [1, 0, 1], [1, 2, 1], [2, 1, 1], [2, 3, 1], [0, 3, 10]], 0, 3, 5),
     "why": {"t": "Cycles", "d": "Back-and-forth routes must not lower the cost."}},
    {"args": case(4, [[0, 1, 50], [0, 2, 20], [2, 1, 10], [1, 3, 10], [2, 3, 100]], 0, 3, 1),
     "why": {"t": "Cheaper but longer", "d": "0->2->1->3 is cheapest (40) but needs 2 transits; with 1 it is 60."}},
    {"args": case(6, [[0, 1, 120], [1, 5, 80], [0, 2, 30], [2, 3, 30], [3, 5, 30], [0, 5, 400]], 0, 5, 1),
     "why": {"t": "Region transfer budget", "d": "us-east to ap-south with one transit region: 200, not the 90 three-hop path."}},
    {"args": _large(),
     "why": {"t": "Large input", "d": "60 regions, 700 routes, 4 transit regions."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Bellman-Ford with k + 1 rounds (Optimal)",
     "description": "Start with cost[src] = 0. Repeat max_transit + 1 times: copy the costs, then relax every route from the copy, so each round adds at most one hop.",
     "time": "O((k + 1) · R)", "space": "O(n)",
     "keyPoints": ["At most k transit regions means at most k + 1 hops", "Relax from the previous round's copy, or a round can chain several hops", "Return -1 when dst stays infinite"]},
    {"name": "DFS over every walk", "slow": True,
     "description": "Explore every walk of up to max_transit + 1 hops from src and keep the cheapest one that ends at dst.",
     "time": "O(R^(k+1)) in the worst case", "space": "O(k) recursion",
     "keyPoints": ["Correct but exponential in the hop limit", "Fine only for tiny graphs"],
     "code": '''from __future__ import annotations


def cheapest_route(n: int, routes: list[list[int]], src: int, dst: int, max_transit: int) -> int:
    out: dict[int, list[tuple[int, int]]] = {}
    for a, b, p in routes:
        out.setdefault(a, []).append((b, p))
    best: dict[tuple[int, int], int] = {}
    ans = -1

    def go(node: int, hops: int, cost: int) -> None:
        nonlocal ans
        if best.get((node, hops), 1 << 60) <= cost:
            return
        best[(node, hops)] = cost
        if node == dst:
            ans = cost if ans == -1 else min(ans, cost)
            return
        if hops == max_transit + 1:
            return
        for b, p in out.get(node, []):
            go(b, hops + 1, cost + p)

    go(src, 0, 0)
    return ans
'''},
]

WAYS_TO_SOLVE = [
    {"name": "DFS over walks", "idea": "Try every walk with up to k + 1 hops.", "time": "Exponential in k",
     "space": "O(k)", "use": "Tiny graphs; explains the problem."},
    {"name": "Bellman-Ford, k + 1 rounds", "idea": "Round r holds the cheapest cost using at most r hops.",
     "time": "O((k + 1) · R)", "space": "O(n)", "use": "The standard answer for a hop-limited cheapest path."},
    {"name": "Dijkstra on (node, hops)", "idea": "Priority queue over states that also track hops used.",
     "time": "O(n · k · log) roughly", "space": "O(n · k)", "use": "Sparse graphs with a large n."},
]
