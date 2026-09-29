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

VARIANT_TITLE = "Cheapest route within a hop limit"
VARIANT_APPROACH = "Bellman-Ford with k + 1 rounds · O((k + 1) · R) · O(n)"

_FEE_FAST = '''from __future__ import annotations


def cheapest_with_fees(n: int, routes: list[list[int]], fees: list[int], src: int, dst: int, max_transit: int) -> int:
    INF = float("inf")
    cost = [INF] * n
    cost[src] = 0
    for _ in range(max_transit + 1):
        prev = cost[:]
        for a, b, price in routes:
            if prev[a] == INF:
                continue
            step = prev[a] + price + (0 if a == src else fees[a])
            if step < cost[b]:
                cost[b] = step
    return -1 if cost[dst] == INF else int(cost[dst])
'''

_FEE_SLOW = '''from __future__ import annotations


def cheapest_with_fees(n: int, routes: list[list[int]], fees: list[int], src: int, dst: int, max_transit: int) -> int:
    out: dict[int, list[tuple[int, int]]] = {}
    for a, b, p in routes:
        out.setdefault(a, []).append((b, p))
    best = -1

    def go(node: int, hops: int, cost: int) -> None:
        nonlocal best
        if node == dst and hops > 0:
            best = cost if best == -1 else min(best, cost)
        if hops == max_transit + 1:
            return
        fee = 0 if node == src else fees[node]
        for b, p in out.get(node, []):
            go(b, hops + 1, cost + p + fee)

    go(src, 0, 0)
    return best
'''

_HOPS_FAST = '''from __future__ import annotations


def fewest_hops(n: int, routes: list[list[int]], src: int, dst: int, budget: int) -> int:
    INF = float("inf")
    cost = [INF] * n
    cost[src] = 0
    for hops in range(1, n):
        prev = cost[:]
        changed = False
        for a, b, price in routes:
            if prev[a] + price < cost[b]:
                cost[b] = prev[a] + price
                changed = True
        if cost[dst] <= budget:
            return hops
        if not changed:
            break
    return -1
'''

_HOPS_SLOW = '''from __future__ import annotations


def _cheapest(n: int, routes: list[list[int]], src: int, dst: int, rounds: int) -> float:
    INF = float("inf")
    cost = [INF] * n
    cost[src] = 0
    for _ in range(rounds):
        prev = cost[:]
        for a, b, price in routes:
            if prev[a] + price < cost[b]:
                cost[b] = prev[a] + price
    return cost[dst]


def fewest_hops(n: int, routes: list[list[int]], src: int, dst: int, budget: int) -> int:
    for hops in range(1, n):
        if _cheapest(n, routes, src, dst, hops) <= budget:
            return hops
    return -1
'''


def _fee_case(n, routes, fees, src, dst, k):
    return {"n": n, "routes": routes, "fees": fees, "src": src, "dst": dst, "max_transit": k}


def _hop_case(n, routes, src, dst, budget):
    return {"n": n, "routes": routes, "src": src, "dst": dst, "budget": budget}


def _fee_large():
    rng = random.Random(1010)
    n = 12
    pairs, routes = set(), []
    while len(routes) < 45:
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b and (a, b) not in pairs:
            pairs.add((a, b))
            routes.append([a, b, rng.randint(1, 200)])
    return _fee_case(n, routes, [rng.randint(0, 150) for _ in range(n)], 0, n - 1, 3)


def _hop_large():
    rng = random.Random(1011)
    n = 40
    pairs, routes = set(), []
    while len(routes) < 300:
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b and (a, b) not in pairs:
            pairs.add((a, b))
            routes.append([a, b, rng.randint(1, 500)])
    return _hop_case(n, routes, 0, n - 1, 400)


VARIANTS = [
    {
        "key": "transit-fees",
        "title": "Transit regions charge a fee",
        "approach": "Bellman-Ford, k + 1 rounds, fee added on departure · O((k + 1) · R) · O(n)",
        "spec": {"kind": "fn", "fn": "cheapest_with_fees", "params": ["n", "routes", "fees", "src", "dst", "max_transit"]},
        "statement": (
            "Same inter-region transfer network, but now every region you pass **through** charges a processing fee on top of the route price "
            "(a NAT gateway or inspection hop in that region).\n\n"
            "- `routes[i] = [a, b, price]` is a one-way route\n"
            "- leaving any region other than `src` adds `fees[region]`; `src` never charges\n"
            "- at most `max_transit` middle regions may be used\n\n"
            "Return the cheapest total cost from `src` to `dst`, or -1 if no route fits."
        ),
        "examples": [
            {"args": _fee_case(3, [[0, 1, 10], [1, 2, 10], [0, 2, 50]], [0, 100, 0], 0, 2, 1),
             "explanation": "Through region 1 costs 10 + 100 + 10 = 120, so the direct 50 wins.",
             "why": {"t": "Fee flips the answer", "d": "The cheap path by price alone is not the cheapest once the fee is added."}},
            {"args": _fee_case(3, [[0, 1, 10], [1, 2, 10], [0, 2, 50]], [0, 5, 0], 0, 2, 1),
             "explanation": "Through region 1 costs 10 + 5 + 10 = 25.",
             "why": {"t": "Small fee", "d": "A low fee keeps the transit path cheaper."}},
        ],
        "constraints": ["2 ≤ n ≤ 100", "0 ≤ routes.length ≤ n · (n - 1)", "0 ≤ price, fees[i] ≤ 10⁴", "src ≠ dst", "0 ≤ max_transit < n"],
        "hints": [
            "The fee belongs to the edge that leaves a region, so fold it into the relaxation: `prev[a] + price + fee(a)`.",
            "`src` is the only region that never charges, so its fee term is 0.",
            "Keep the copy-per-round rule from the main problem so each round adds exactly one hop.",
        ],
        "tests": [
            {"args": _fee_case(2, [[0, 1, 7]], [99, 99], 0, 1, 0), "why": {"t": "Direct only", "d": "src and dst never charge, even with high fees."}},
            {"args": _fee_case(3, [[0, 1, 1], [1, 2, 1]], [0, 0, 0], 0, 2, 0), "why": {"t": "Hop limit binds", "d": "The only path needs one transit region."}},
            {"args": _fee_case(3, [], [0, 0, 0], 0, 2, 2), "why": {"t": "No routes", "d": "Nothing leaves src."}},
            {"args": _fee_case(4, [[0, 1, 1], [1, 3, 1], [0, 2, 1], [2, 3, 1]], [0, 30, 30, 0], 0, 3, 1),
             "why": {"t": "Tie", "d": "Two transit regions with the same fee give the same total."}},
            {"args": _fee_case(5, [[0, 1, 1], [1, 2, 1], [2, 4, 1], [0, 3, 2], [3, 4, 2]], [0, 10, 10, 50, 0], 0, 4, 2),
             "why": {"t": "Fees add up", "d": "Two small fees (total 23) beat one large fee (total 54)."}},
            {"args": _fee_case(4, [[0, 1, 1], [1, 0, 1], [1, 2, 1], [2, 3, 1]], [0, 0, 0, 0], 0, 3, 3),
             "why": {"t": "Cycle back to src", "d": "Returning to src never helps."}},
            {"args": _fee_large(), "why": {"t": "Larger input", "d": "12 regions, 45 routes, 3 transit regions."}},
        ],
        "solutions": [
            {"name": "Bellman-Ford with departure fees (Optimal)",
             "description": "Run max_transit + 1 rounds; each round relaxes every route from the previous round's copy, adding the price plus the fee of the region being left (0 for src).",
             "time": "O((k + 1) · R)", "space": "O(n)",
             "keyPoints": ["Fold the fee into the edge weight", "src's fee is 0", "Copy per round keeps the hop count honest"],
             "code": _FEE_FAST},
            {"name": "DFS over every walk", "slow": True,
             "description": "Try every walk of up to max_transit + 1 hops, paying each departed region's fee, and keep the cheapest one ending at dst.",
             "time": "O(R^(k+1))", "space": "O(k)",
             "keyPoints": ["Direct translation of the rules", "Exponential in the hop limit"],
             "code": _FEE_SLOW},
        ],
        "starter": "def cheapest_with_fees(n: int, routes: list[list[int]], fees: list[int], src: int, dst: int, max_transit: int) -> int:\n    pass\n",
    },
    {
        "key": "fewest-hops-in-budget",
        "title": "Fewest hops within a budget",
        "approach": "Bellman-Ford rounds until dst fits the budget · O(n · R) · O(n)",
        "spec": {"kind": "fn", "fn": "fewest_hops", "params": ["n", "routes", "src", "dst", "budget"]},
        "statement": (
            "Each extra hop adds latency and another place to fail, so the network team asks the question the other way round: "
            "what is the **smallest number of hops** from `src` to `dst` whose total transfer cost is at most `budget`?\n\n"
            "- `routes[i] = [a, b, price]` is a one-way route with a non-negative price\n"
            "- return the minimum hop count, or -1 if no route fits the budget"
        ),
        "examples": [
            {"args": _hop_case(4, [[0, 3, 900], [0, 1, 100], [1, 3, 300], [1, 2, 50], [2, 3, 50]], 0, 3, 400),
             "explanation": "One hop costs 900 (over). Two hops 0 to 1 to 3 cost 400, which fits.",
             "why": {"t": "Budget forces a detour", "d": "The direct route is too expensive."}},
            {"args": _hop_case(4, [[0, 3, 900], [0, 1, 100], [1, 3, 300], [1, 2, 50], [2, 3, 50]], 0, 3, 250),
             "explanation": "Only the three-hop path costs 200.",
             "why": {"t": "Tighter budget", "d": "A lower budget needs more hops."}},
        ],
        "constraints": ["2 ≤ n ≤ 100", "0 ≤ routes.length ≤ n · (n - 1)", "0 ≤ price ≤ 10⁴", "0 ≤ budget ≤ 10⁶", "src ≠ dst"],
        "hints": [
            "After round r of hop-limited Bellman-Ford, cost[dst] is the cheapest cost using at most r hops.",
            "That cost only goes down as r grows, so the first round where it fits the budget is the answer.",
            "With non-negative prices a simple path is enough, so n - 1 rounds cover everything; stop early when a round changes nothing.",
        ],
        "tests": [
            {"args": _hop_case(2, [[0, 1, 5]], 0, 1, 5), "why": {"t": "Budget exactly met", "d": "Cost equal to the budget fits."}},
            {"args": _hop_case(2, [[0, 1, 5]], 0, 1, 4), "why": {"t": "Just over", "d": "One unit over the budget."}},
            {"args": _hop_case(3, [], 0, 2, 100), "why": {"t": "No routes", "d": "Nothing reachable."}},
            {"args": _hop_case(3, [[0, 1, 0], [1, 2, 0]], 0, 2, 0), "why": {"t": "Zero budget", "d": "Free routes fit a zero budget."}},
            {"args": _hop_case(4, [[0, 1, 1], [1, 0, 1], [1, 2, 1], [2, 3, 1], [0, 3, 10]], 0, 3, 3),
             "why": {"t": "Cycle", "d": "A back-and-forth route never helps."}},
            {"args": _hop_case(5, [[0, 4, 50], [0, 1, 10], [1, 4, 30], [1, 2, 5], [2, 3, 5], [3, 4, 5]], 0, 4, 60),
             "why": {"t": "Direct already fits", "d": "One hop fits, even though a longer path is cheaper."}},
            {"args": _hop_large(), "why": {"t": "Larger input", "d": "40 regions and 300 routes."}},
        ],
        "solutions": [
            {"name": "Bellman-Ford rounds with early stop (Optimal)",
             "description": "Run hop-limited rounds from a per-round copy; return the first round whose cost[dst] fits the budget, and stop when a round changes nothing.",
             "time": "O(n · R)", "space": "O(n)",
             "keyPoints": ["Round r = cheapest with at most r hops", "The cost only falls, so the first fit is minimal", "Stop when nothing changes"],
             "code": _HOPS_FAST},
            {"name": "Recompute for every hop count", "slow": True,
             "description": "For h = 1, 2, ... run a fresh h-round Bellman-Ford and return the first h that fits.",
             "time": "O(n² · R)", "space": "O(n)",
             "keyPoints": ["Same answer, repeated work", "Each h starts over from scratch"],
             "code": _HOPS_SLOW},
        ],
        "starter": "def fewest_hops(n: int, routes: list[list[int]], src: int, dst: int, budget: int) -> int:\n    pass\n",
    },
]
