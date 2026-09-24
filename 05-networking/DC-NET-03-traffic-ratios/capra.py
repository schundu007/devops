"""Capra Playground export for DC-NET-03 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "calc_ratios", "params": ["facts", "values", "queries"], "types": {}, "ret": "value", "cmp": "float"}


def c(facts, values, queries, t, d):
    return {"args": {"facts": facts, "values": values, "queries": queries}, "why": {"t": t, "d": d}}


EXAMPLES = [
    {"args": {"facts": [["cluster", "node"], ["node", "pod"]], "values": [20.0, 30.0],
              "queries": [["cluster", "pod"], ["pod", "node"], ["cluster", "cluster"], ["cluster", "gpu"]]},
     "explanation": "1 cluster = 20 nodes and 1 node = 30 pods, so 600 pods per cluster; a pod is 1/30 of a node; a unit to itself is 1; gpu is unknown, so -1.",
     "why": {"t": "Chained ratios", "d": "Multiply along the chain, invert going backwards."}},
    {"args": {"facts": [["edge", "mesh"], ["mesh", "canary"]], "values": [0.5, 0.2],
              "queries": [["edge", "canary"], ["canary", "edge"]]},
     "explanation": "50% of edge traffic reaches the mesh and 20% of that goes to canary: 10% end to end, and the reverse ratio is 10.",
     "why": {"t": "Traffic weights", "d": "Mesh traffic splits multiply the same way."}},
]

TESTS = [
    c([], [], [["a", "a"]], "No facts", "Even a unit to itself is unknown when it never appears in a fact."),
    c([["a", "b"]], [2.0], [["a", "a"], ["b", "b"]], "Self query", "A known unit divided by itself is 1."),
    c([["a", "b"]], [2.0], [["b", "a"]], "Reverse edge", "Going against a fact divides."),
    c([["a", "b"], ["c", "d"]], [2.0, 3.0], [["a", "d"], ["d", "c"]], "Disconnected groups",
      "Units in separate groups cannot be compared: -1."),
    c([["region", "az"], ["az", "rack"], ["rack", "host"], ["host", "vm"]], [3.0, 40.0, 20.0, 8.0],
      [["region", "vm"], ["vm", "region"], ["az", "host"]], "Long chain", "Four hops multiply to 19,200 VMs per region."),
    c([["a", "b"], ["b", "c"], ["a", "c"]], [2.0, 3.0, 6.0], [["c", "a"], ["a", "c"]], "Consistent cycle",
      "Two paths from a to c give the same product."),
    c([["x", "y"]], [0.25], [["y", "x"], ["x", "z"], ["z", "z"]], "Fractions and unknowns", "Values below 1 invert to values above 1."),
]


def _large():
    rng = random.Random(399)
    names = [f"u{i}" for i in range(60)]
    facts, values = [], []
    for i in range(1, 60):
        facts.append([names[rng.randrange(i)], names[i]])
        values.append(float(rng.choice([2, 3, 4, 5, 0.5])))
    queries = [[rng.choice(names), rng.choice(names)] for _ in range(80)] + [["u0", "nope"]]
    return facts, values, queries


f, v, q = _large()
TESTS.append(c(f, v, q, "Large input", "60 units in one tree of facts and 81 queries."))

SOLUTIONS = [
    {"file": "solution.py", "name": "Weighted graph + BFS (Optimal)",
     "description": "Each fact a -> b with value v adds edge a -> b weight v and b -> a weight 1/v. For each query, BFS from x carrying the product of weights; return it when y is reached, else -1.0.",
     "time": "O(Q · (V + E))", "space": "O(V + E)",
     "keyPoints": ["Ratios multiply along a path", "Reverse edges carry 1/v", "Missing units or no path: -1.0"]},
    {"name": "Floyd-Warshall closure", "slow": True,
     "description": "Precompute every pair's ratio with a triple loop, then answer each query by lookup. O(V^3) up front, but constant per query.",
     "time": "O(V^3 + Q)", "space": "O(V^2)",
     "keyPoints": ["Good when queries vastly outnumber units", "ratio[i][j] = ratio[i][k] * ratio[k][j]"],
     "code": '''def calc_ratios(facts, values, queries):
    units = sorted({u for pair in facts for u in pair})
    idx = {u: i for i, u in enumerate(units)}
    n = len(units)
    r = [[None] * n for _ in range(n)]
    for i in range(n):
        r[i][i] = 1.0
    for (a, b), v in zip(facts, values):
        r[idx[a]][idx[b]] = v
        r[idx[b]][idx[a]] = 1.0 / v
    for k in range(n):
        for i in range(n):
            if r[i][k] is None:
                continue
            for j in range(n):
                if r[i][j] is None and r[k][j] is not None:
                    r[i][j] = r[i][k] * r[k][j]
    out = []
    for x, y in queries:
        if x not in idx or y not in idx or r[idx[x]][idx[y]] is None:
            out.append(-1.0)
        else:
            out.append(r[idx[x]][idx[y]])
    return out
'''},
]

WAYS_TO_SOLVE = [
    {"name": "BFS per query", "idea": "Walk the ratio graph from x, multiplying edge weights, until y.",
     "time": "O(Q · (V + E))", "space": "O(V + E)", "use": "Few queries, or facts that change often."},
    {"name": "Floyd-Warshall", "idea": "Precompute all-pairs ratios once, then look up.",
     "time": "O(V^3 + Q)", "space": "O(V^2)", "use": "Many queries over a small, fixed set of units."},
    {"name": "Weighted union-find", "idea": "Store each unit's ratio to its root; x/y = w(x)/w(y) when roots match.",
     "time": "O((E + Q) α(V))", "space": "O(V)", "use": "Large graphs with many queries."},
]
