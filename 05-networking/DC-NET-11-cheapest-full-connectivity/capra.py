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
    {"args": {"sites": [[0, 0], [100, 0], [0, 100], [100, 100], [50, 50]]}, "why": {"t": "Hub in the middle", "d": "A center site makes every corner cheaper to reach."}},
    {"args": {"sites": [[10, 0], [12, 0], [500, 500], [502, 501], [1000, 0], [1001, 3]]},
     "why": {"t": "Three data centers", "d": "Pairs of close sites far apart: two expensive backbone links."}},
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

VARIANT_TITLE = "Connect every site"
VARIANT_APPROACH = "Prim, array version · O(n²) · O(n)"

_LINKS_FAST = '''def min_extra_cost(sites: list[list[int]], links: list[list[int]]) -> int:
    n = len(sites)
    if n == 0:
        return 0
    free = set()
    for a, b in links:
        free.add((a, b))
        free.add((b, a))
    inf = float("inf")
    best = [inf] * n
    used = [False] * n
    best[0] = 0
    total = 0
    for _ in range(n):
        u = -1
        for v in range(n):
            if not used[v] and (u < 0 or best[v] < best[u]):
                u = v
        used[u] = True
        total += best[u]
        ux, uy = sites[u]
        for v in range(n):
            if not used[v]:
                d = 0 if (u, v) in free else abs(ux - sites[v][0]) + abs(uy - sites[v][1])
                if d < best[v]:
                    best[v] = d
    return total
'''

_LINKS_SLOW = '''def min_extra_cost(sites: list[list[int]], links: list[list[int]]) -> int:
    n = len(sites)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in links:
        parent[find(a)] = find(b)
    edges = sorted(
        (abs(sites[i][0] - sites[j][0]) + abs(sites[i][1] - sites[j][1]), i, j)
        for i in range(n) for j in range(i + 1, n)
    )
    total = 0
    for d, i, j in edges:
        a, b = find(i), find(j)
        if a != b:
            parent[a] = b
            total += d
    return total
'''

_REGIONS_FAST = '''def min_cost_regions(sites: list[list[int]], k: int) -> int:
    n = len(sites)
    if n <= k:
        return 0
    inf = float("inf")
    best = [inf] * n
    used = [False] * n
    best[0] = 0
    chosen = []
    for step in range(n):
        u = -1
        for v in range(n):
            if not used[v] and (u < 0 or best[v] < best[u]):
                u = v
        used[u] = True
        if step:
            chosen.append(best[u])
        ux, uy = sites[u]
        for v in range(n):
            if not used[v]:
                d = abs(ux - sites[v][0]) + abs(uy - sites[v][1])
                if d < best[v]:
                    best[v] = d
    chosen.sort()
    return sum(chosen[:len(chosen) - (k - 1)])
'''

_REGIONS_SLOW = '''def min_cost_regions(sites: list[list[int]], k: int) -> int:
    n = len(sites)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    edges = sorted(
        (abs(sites[i][0] - sites[j][0]) + abs(sites[i][1] - sites[j][1]), i, j)
        for i in range(n) for j in range(i + 1, n)
    )
    groups, total = n, 0
    for d, i, j in edges:
        if groups <= k:
            break
        a, b = find(i), find(j)
        if a != b:
            parent[a] = b
            total += d
            groups -= 1
    return total
'''


def _lk(sites, links, t, d):
    return {"args": {"sites": sites, "links": links}, "why": {"t": t, "d": d}}


def _rg(sites, k, t, d):
    return {"args": {"sites": sites, "k": k}, "why": {"t": t, "d": d}}


_R60 = _rand(60, 77, 1000)

VARIANTS = [
    {
        "key": "existing-links",
        "title": "Reuse existing fiber",
        "approach": "Prim with zero-cost existing links · O(n² + L) · O(n + L)",
        "spec": {"kind": "fn", "fn": "min_extra_cost", "params": ["sites", "links"], "cmp": "exact"},
        "statement": (
            "Some sites are already wired together: `links[i] = [a, b]` is a fiber run between site `a` and "
            "site `b` that costs nothing to use. Every new link between two sites costs their Manhattan "
            "distance.\n\n"
            "Return the minimum cost of **new** links so that every site can reach every other site, through "
            "any mix of existing and new links.\n\n"
            "Existing links may be redundant or form cycles; that is fine, they are free."
        ),
        "examples": [
            {"args": {"sites": [[0, 0], [10, 0], [10, 10], [0, 10]], "links": [[0, 2]]},
             "explanation": "0 and 2 are already joined. Two 10-unit links (1 to 0 and 3 to 0) finish the job: 20.",
             "why": {"t": "One free diagonal", "d": "A free link replaces the most expensive new one."}},
            {"args": {"sites": [[0, 0], [5, 5], [9, 1]], "links": [[0, 1], [1, 2]]},
             "explanation": "The existing links already connect all three sites: 0.",
             "why": {"t": "Already connected", "d": "Nothing new to buy."}},
        ],
        "constraints": ["0 ≤ sites.length ≤ 300", "-10⁶ ≤ x, y ≤ 10⁶, sites distinct", "0 ≤ links.length ≤ 1000, 0 ≤ a, b < n"],
        "hints": [
            "Give every existing link weight 0 and run the same minimum spanning tree algorithm.",
            "In Prim, when a site joins the tree, a free link to an outside site lowers that site's best cost to 0.",
            "Kruskal works too: union the existing links first, then add sorted new links between different groups.",
        ],
        "tests": [
            _lk([], [], "Empty", "No sites: cost 0."),
            _lk([[3, 3]], [], "Single site", "Nothing to connect."),
            _lk([[0, 0], [1, 0], [2, 0]], [], "No existing links", "Same as the main problem."),
            _lk([[0, 0], [100, 0], [200, 0]], [[0, 1], [1, 0], [0, 1]], "Duplicate links", "Repeated and reversed links count once."),
            _lk([[0, 0], [1, 0], [50, 50], [51, 50]], [[0, 1], [2, 3]], "Two islands", "One new link bridges two wired islands."),
            _lk([[0, 0], [0, 1], [0, 2], [0, 3]], [[0, 1], [1, 2], [2, 0]], "Cycle of links", "A redundant cycle; only site 3 needs a new link."),
            _lk(_R60, [[i, i + 1] for i in range(0, 58, 3)], "Large input", "60 sites with 20 existing links."),
        ],
        "solutions": [
            {"name": "Prim with free links (Optimal)",
             "description": "Grow one tree as in the main problem. A set of existing pairs makes those edges cost 0 when updating each outside site's cheapest link.",
             "time": "O(n² + L)", "space": "O(n + L)",
             "keyPoints": ["Free links are just zero-weight edges", "Transitive wiring falls out of the tree growth", "No edge list is ever stored"],
             "code": _LINKS_FAST},
            {"name": "Kruskal after unioning links", "slow": True,
             "description": "Union every existing link first, then sort all n(n-1)/2 new links and add those that join two groups.",
             "time": "O(n² log n)", "space": "O(n²)",
             "keyPoints": ["Easy to explain", "Sorts every pair of sites"],
             "code": _LINKS_SLOW},
        ],
        "starter": "def min_extra_cost(sites: list[list[int]], links: list[list[int]]) -> int:\n    pass\n",
    },
    {
        "key": "k-regions",
        "title": "Split into k regions",
        "approach": "Prim, then drop the k-1 longest tree links · O(n²) · O(n)",
        "spec": {"kind": "fn", "fn": "min_cost_regions", "params": ["sites", "k"], "cmp": "exact"},
        "statement": (
            "Compliance wants the sites grouped into exactly `k` separate regional networks: sites inside a "
            "region must reach each other, and no link may cross regions. Which site goes in which region is "
            "up to you.\n\n"
            "Return the minimum total Manhattan length of links so that the sites form **exactly** `k` "
            "connected regions (or one region per site when `k` is at least the number of sites)."
        ),
        "examples": [
            {"args": {"sites": [[0, 0], [1, 0], [100, 0], [101, 0]], "k": 2},
             "explanation": "Two pairs, each joined by a 1-unit link: 2. The 99-unit backbone is not needed.",
             "why": {"t": "Two clusters", "d": "Dropping the longest tree link splits the obvious clusters."}},
            {"args": {"sites": [[0, 0], [2, 2], [3, 10], [5, 2], [7, 0]], "k": 1},
             "explanation": "k = 1 is the main problem: 20.",
             "why": {"t": "One region", "d": "The full spanning tree."}},
        ],
        "constraints": ["0 ≤ sites.length ≤ 300", "-10⁶ ≤ x, y ≤ 10⁶, sites distinct", "1 ≤ k"],
        "hints": [
            "Build the minimum spanning tree first; the best forest with k trees is inside it.",
            "Removing a tree link splits one region into two. Remove the k-1 longest ones.",
            "Equivalently, run Kruskal and stop once only k groups remain.",
        ],
        "tests": [
            _rg([], 1, "Empty", "No sites: cost 0."),
            _rg([[5, 5]], 1, "Single site", "One site is one region."),
            _rg([[0, 0], [3, 4], [9, 9]], 3, "k = n", "Every site alone: no links."),
            _rg([[0, 0], [3, 4], [9, 9]], 7, "k > n", "More regions than sites: still no links."),
            _rg([[0, 0], [0, 1], [0, 2], [0, 3]], 2, "Equal-length ties", "Every tree link has length 1."),
            _rg([[0, 0], [2, 0], [500, 500], [502, 500], [1000, 0], [1002, 0]], 3, "Three data centers", "Three pairs, far apart."),
            _rg(_R60, 5, "Large input", "60 sites, 5 regions."),
        ],
        "solutions": [
            {"name": "Prim, drop the longest links (Optimal)",
             "description": "Build the spanning tree with array Prim, record each added link, sort them and sum all but the k-1 longest.",
             "time": "O(n²)", "space": "O(n)",
             "keyPoints": ["An optimal k-forest is an MST minus k-1 edges", "Sorting n-1 tree links is cheap", "k ≥ n means cost 0"],
             "code": _REGIONS_FAST},
            {"name": "Kruskal, stop at k groups", "slow": True,
             "description": "Sort every pair by length and union groups until only k remain.",
             "time": "O(n² log n)", "space": "O(n²)",
             "keyPoints": ["Single-linkage clustering", "Stores every edge"],
             "code": _REGIONS_SLOW},
        ],
        "starter": "def min_cost_regions(sites: list[list[int]], k: int) -> int:\n    pass\n",
    },
]
