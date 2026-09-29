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

VARIANT_TITLE = "Ratio queries"
VARIANT_APPROACH = "Weighted graph + BFS per query · O(Q · (V + E)) · O(V + E)"


def _cfacts():
    names = [f"n{i}" for i in range(50)]
    facts = [[names[i], names[i + 1]] for i in range(49)]
    values = [2.0 if i % 2 else 0.5 for i in range(49)]
    facts += [["n0", "n10"], ["n5", "n45"], ["n0", "n49"]]
    values += [1.0, 1.0, 4.0]
    return {"facts": facts, "values": values}


def _qfacts():
    names = [f"u{i}" for i in range(40)]
    facts = [[names[i], names[i + 1]] for i in range(39)]
    values = [2.0 if i % 3 else 0.5 for i in range(39)]
    amounts = [[names[i], float(i % 5 + 1)] for i in range(0, 40, 3)]
    return {"facts": facts, "values": values, "base": "u20", "amounts": amounts}


VARIANTS = [
    {
        "key": "first-contradiction",
        "title": "Contradicting capacity facts",
        "approach": "Weighted union-find · O(E · α(V)) · O(V)",
        "spec": {"kind": "fn", "fn": "first_contradiction", "params": ["facts", "values"], "cmp": "exact"},
        "statement": (
            "A capacity sheet is assembled from many teams, and its facts may disagree.\n"
            "\n"
            "### Input\n"
            "- `facts[i]`, `values[i]`: one `facts[i][0]` holds `values[i]` of `facts[i][1]`; like the main problem, it also holds backwards with `1/v`\n"
            "\n"
            "### Output\n"
            "- The index of the **first** fact whose ratio disagrees with what the earlier facts already imply\n"
            "- `-1` if every fact is consistent\n"
            "\n"
            "### Rules\n"
            "- The facts are **not** guaranteed to agree; read them in order\n"
            "- Two ratios agree when they differ by at most `1e-6 · v` (relative)\n"
            "- A fact that links units not yet connected can never contradict\n"
            "- `(a, a, v)` contradicts unless `v` is 1"
        ),
        "examples": [
            {"args": {"facts": [["cluster", "node"], ["node", "pod"], ["cluster", "pod"]], "values": [20.0, 30.0, 500.0]},
             "explanation": "The first two facts imply 600 pods per cluster, so the third fact (500) is the first contradiction.",
             "why": {"t": "Closing a cycle", "d": "A fact joining two already-connected units is checked against the implied ratio."}},
            {"args": {"facts": [["a", "b"], ["b", "c"], ["c", "a"]], "values": [2.0, 3.0, 1.0 / 6.0]},
             "explanation": "a = 2b, b = 3c, so c = a/6: the third fact agrees.",
             "why": {"t": "Consistent cycle", "d": "A cycle whose product is 1 contradicts nothing."}},
        ],
        "constraints": ["0 ≤ len(facts) ≤ 2000, len(values) == len(facts)", "0 < values[i] ≤ 10^6",
                        "Names are non-empty strings of up to 30 characters"],
        "hints": [
            "Give every unit a weight relative to a group root: `w[x]` = size of x divided by size of its root.",
            "Two units in the same group have ratio `w[a] / w[b]`. Compare that with the fact's value.",
            "When the fact joins two groups, hang one root under the other with the weight that makes the new fact true.",
        ],
        "tests": [
            {"args": {"facts": [], "values": []}, "why": {"t": "No facts", "d": "Nothing to contradict: -1."}},
            {"args": {"facts": [["x", "x"]], "values": [2.0]}, "why": {"t": "Self fact", "d": "A unit holding 2 of itself is contradictory at once."}},
            {"args": {"facts": [["x", "x"], ["x", "y"]], "values": [1.0, 3.0]}, "why": {"t": "Self fact of 1", "d": "One x holds one x: consistent."}},
            {"args": {"facts": [["a", "b"], ["a", "b"], ["b", "a"]], "values": [4.0, 4.0, 0.5]},
             "why": {"t": "Duplicates", "d": "A repeated fact agrees; the reversed one with the wrong inverse does not."}},
            {"args": {"facts": [["a", "b"], ["c", "d"], ["b", "c"], ["a", "d"]], "values": [2.0, 3.0, 5.0, 30.0]},
             "why": {"t": "Groups joined later", "d": "Two groups merge, then a fact across them is consistent."}},
            {"args": {"facts": [["a", "b"], ["c", "d"], ["b", "c"], ["d", "a"]], "values": [2.0, 3.0, 5.0, 30.0]},
             "why": {"t": "Wrong direction", "d": "The same number read the wrong way round contradicts."}},
            {"args": _cfacts(), "why": {"t": "Large input", "d": "A 50-unit chain plus shortcut facts; only the last shortcut disagrees."}},
        ],
        "solutions": [
            {"name": "Weighted union-find (Optimal)",
             "description": "Each unit stores its parent and its size relative to that parent. find() compresses paths while multiplying weights. A fact inside one group is checked; a fact across groups links the two roots.",
             "time": "O(E · α(V))", "space": "O(V)",
             "keyPoints": ["w[x] is x's size over its root's size", "Same root: compare w[a] / w[b] with v", "Different roots: set w[ra] = v · w[b] / w[a]"],
             "code": '''def first_contradiction(facts, values):
    parent, w = {}, {}

    def find(x):
        if parent[x] == x:
            return x
        root = find(parent[x])
        w[x] *= w[parent[x]]
        parent[x] = root
        return root

    for i, ((a, b), v) in enumerate(zip(facts, values)):
        for u in (a, b):
            if u not in parent:
                parent[u], w[u] = u, 1.0
        ra, rb = find(a), find(b)
        if ra == rb:
            if abs(w[a] / w[b] - v) > 1e-6 * v:
                return i
        else:
            parent[ra] = rb
            w[ra] = v * w[b] / w[a]
    return -1
'''},
            {"name": "BFS before every fact", "slow": True,
             "description": "Keep the graph of accepted facts. For each new fact, BFS from a; if b is reached, compare the product along the path with the fact.",
             "time": "O(E · (V + E))", "space": "O(V + E)",
             "keyPoints": ["Reuses the main problem's BFS", "Every fact pays for a full walk"],
             "code": '''from collections import defaultdict, deque


def first_contradiction(facts, values):
    graph = defaultdict(list)
    for i, ((a, b), v) in enumerate(zip(facts, values)):
        seen, q, got = {a}, deque([(a, 1.0)]), None
        while q:
            node, acc = q.popleft()
            if node == b:
                got = acc
                break
            for nxt, wt in graph[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    q.append((nxt, acc * wt))
        if got is not None and abs(got - v) > 1e-6 * v:
            return i
        graph[a].append((b, v))
        graph[b].append((a, 1.0 / v))
    return -1
'''},
        ],
        "starter": '''def first_contradiction(facts: list[list[str]], values: list[float]) -> int:
    pass
''',
    },
    {
        "key": "quota-in-base-units",
        "title": "Quota in base units",
        "approach": "One BFS from the base unit · O(V + E + A) · O(V + E)",
        "spec": {"kind": "fn", "fn": "total_in_base", "params": ["facts", "values", "base", "amounts"], "cmp": "float"},
        "statement": (
            "A team's quota request lists amounts in mixed units; total it in one base unit.\n"
            "\n"
            "### Input\n"
            "- `facts`, `values`: as in the main problem; one `facts[i][0]` holds `values[i]` of `facts[i][1]`\n"
            "- `base`: the unit to express the total in\n"
            "- `amounts[i] = [unit, qty]`: one line of the request, such as 2 clusters, 3 nodes or 5 vCPUs\n"
            "\n"
            "### Output\n"
            "- The total in `base` units: the sum of `qty` times how many `base` one `unit` holds\n"
            "- `-1.0` if any unit cannot be converted to `base`\n"
            "- `0.0` when there are no amounts\n"
            "\n"
            "### Rules\n"
            "- A unit equal to `base` converts at 1, even when it appears in no fact"
        ),
        "examples": [
            {"args": {"facts": [["cluster", "node"], ["node", "vcpu"]], "values": [10.0, 8.0], "base": "vcpu",
                      "amounts": [["cluster", 2.0], ["node", 3.0], ["vcpu", 5.0]]},
             "explanation": "2 clusters = 160 vCPUs, 3 nodes = 24 vCPUs, plus 5: 189.",
             "why": {"t": "Mixed units", "d": "Each amount is converted along its own chain, then summed."}},
            {"args": {"facts": [["node", "vcpu"]], "values": [8.0], "base": "node", "amounts": [["vcpu", 4.0], ["gpu", 1.0]]},
             "explanation": "4 vCPUs are half a node, but gpu is unknown, so the whole request is -1.",
             "why": {"t": "Unknown unit", "d": "One unconvertible amount spoils the total."}},
        ],
        "constraints": ["0 ≤ len(facts) ≤ 2000", "0 ≤ len(amounts) ≤ 2000", "0 < values[i] ≤ 10^6, 0 ≤ qty ≤ 10^6",
                        "The facts never contradict each other"],
        "hints": [
            "Every amount is converted to the same unit, so one walk from `base` answers them all.",
            "BFS from base computing `g[u]` = how many u one base holds; then one u holds `1 / g[u]` base.",
        ],
        "tests": [
            {"args": {"facts": [], "values": [], "base": "vcpu", "amounts": []}, "why": {"t": "Empty request", "d": "No amounts: 0.0."}},
            {"args": {"facts": [], "values": [], "base": "vcpu", "amounts": [["vcpu", 7.0]]},
             "why": {"t": "Base only", "d": "The base unit converts at 1 even with no facts."}},
            {"args": {"facts": [["a", "b"]], "values": [2.0], "base": "b", "amounts": [["c", 1.0]]},
             "why": {"t": "Unknown unit", "d": "c appears in no fact: -1.0."}},
            {"args": {"facts": [["a", "b"], ["c", "d"]], "values": [2.0, 3.0], "base": "a", "amounts": [["b", 4.0], ["d", 1.0]]},
             "why": {"t": "Other group", "d": "d is known but not connected to a: -1.0."}},
            {"args": {"facts": [["gb", "mb"], ["tb", "gb"]], "values": [1024.0, 1024.0], "base": "gb",
                      "amounts": [["tb", 2.0], ["mb", 512.0], ["mb", 512.0], ["gb", 0.0]]},
             "why": {"t": "Duplicates and zero", "d": "Repeated units add up; a zero quantity adds nothing."}},
            {"args": {"facts": [["region", "az"], ["az", "node"]], "values": [3.0, 50.0], "base": "region",
                      "amounts": [["node", 75.0], ["az", 1.5]]},
             "why": {"t": "Fractions of the base", "d": "Smaller units convert to fractions of a region."}},
            {"args": _qfacts(), "why": {"t": "Large input", "d": "A 40-unit chain with 14 amounts, base in the middle."}},
        ],
        "solutions": [
            {"name": "One BFS from the base (Optimal)",
             "description": "Walk the ratio graph once from base, recording how many of each unit one base holds. Each amount then converts with one lookup.",
             "time": "O(V + E + A)", "space": "O(V + E)",
             "keyPoints": ["All amounts share the same destination unit", "One base holds g[u] of u, so one u is 1 / g[u] base", "A missing g[u] means -1.0"],
             "code": '''from collections import defaultdict, deque


def total_in_base(facts, values, base, amounts):
    graph = defaultdict(list)
    for (a, b), v in zip(facts, values):
        graph[a].append((b, v))
        graph[b].append((a, 1.0 / v))
    g = {base: 1.0}
    q = deque([base])
    while q:
        node = q.popleft()
        for nxt, wt in graph[node]:
            if nxt not in g:
                g[nxt] = g[node] * wt
                q.append(nxt)
    total = 0.0
    for unit, qty in amounts:
        if unit not in g:
            return -1.0
        total += qty / g[unit]
    return total
'''},
            {"name": "BFS per amount", "slow": True,
             "description": "Answer each amount as its own ratio query from unit to base, exactly as the main problem does.",
             "time": "O(A · (V + E))", "space": "O(V + E)",
             "keyPoints": ["Straight reuse of calc_ratios", "Repeats the same walk for every amount"],
             "code": '''from collections import defaultdict, deque


def total_in_base(facts, values, base, amounts):
    graph = defaultdict(list)
    for (a, b), v in zip(facts, values):
        graph[a].append((b, v))
        graph[b].append((a, 1.0 / v))

    def ratio(x, y):
        seen, q = {x}, deque([(x, 1.0)])
        while q:
            node, acc = q.popleft()
            if node == y:
                return acc
            for nxt, wt in graph[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    q.append((nxt, acc * wt))
        return None

    total = 0.0
    for unit, qty in amounts:
        r = ratio(unit, base)
        if r is None:
            return -1.0
        total += qty * r
    return total
'''},
        ],
        "starter": '''def total_in_base(facts: list[list[str]], values: list[float], base: str, amounts: list[list]) -> float:
    pass
''',
    },
]
