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

VARIANT_TITLE = "One source, one target"
VARIANT_APPROACH = "BFS · O(n + E) · O(n + E)"


def _many():
    rng = random.Random(1319)
    n = 300
    links, seen = [], set()
    while len(links) < 250:
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b and (min(a, b), max(a, b)) not in seen:
            seen.add((min(a, b), max(a, b)))
            links.append([a, b])
    queries = [[rng.randrange(n), rng.randrange(n)] for _ in range(150)]
    return {"n": n, "links": links, "queries": queries}


def _failing():
    rng = random.Random(684)
    n = 120
    links = [[i, i + 1] for i in range(n - 1)]
    seen = {(i, i + 1) for i in range(n - 1)}
    while len(links) < 150:
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b and (min(a, b), max(a, b)) not in seen:
            seen.add((min(a, b), max(a, b)))
            links.append([a, b])
    failures = rng.sample(range(len(links)), 130)
    return {"n": n, "links": links, "failures": failures, "source": 0, "target": n - 1}


VARIANTS = [
    {
        "key": "many-queries",
        "title": "Many reachability checks",
        "approach": "Union-find · O((E + Q) · α(n)) · O(n)",
        "spec": {"kind": "fn", "fn": "reach_many", "params": ["n", "links", "queries"], "cmp": "exact"},
        "statement": (
            "A network policy linter checks hundreds of flows against one topology.\n"
            "\n"
            "### Input\n"
            "- `n`, `links`: the systems and two-way links, as in the main problem\n"
            "- `queries[j] = [source, target]`: one flow to check\n"
            "\n"
            "### Output\n"
            "- One boolean per query, in order: `True` if traffic from `source` can reach `target`\n"
            "\n"
            "### Rules\n"
            "- A system always reaches itself"
        ),
        "examples": [
            {"args": {"n": 5, "links": [[0, 1], [1, 2], [3, 4]], "queries": [[0, 2], [2, 3], [4, 3], [1, 1]]},
             "explanation": "{0,1,2} and {3,4} are two segments: 0 reaches 2 and 4 reaches 3, but 2 cannot reach 3.",
             "why": {"t": "Two segments", "d": "Queries inside and across components."}},
        ],
        "constraints": ["1 ≤ n ≤ 2 · 10^5", "0 ≤ len(links) ≤ 2 · 10^5, no duplicates, a != b", "1 ≤ len(queries) ≤ 2 · 10^5"],
        "hints": [
            "Two systems can reach each other exactly when they are in the same connected component.",
            "Union every link into a disjoint-set structure, then each query is two find() calls.",
            "Path compression and union by size keep find() almost constant.",
        ],
        "tests": [
            {"args": {"n": 1, "links": [], "queries": [[0, 0]]}, "why": {"t": "Single system", "d": "A system reaches itself."}},
            {"args": {"n": 3, "links": [], "queries": [[0, 1], [2, 2], [1, 0]]}, "why": {"t": "No links", "d": "Only self queries are True."}},
            {"args": {"n": 4, "links": [[3, 2], [2, 1], [1, 0]], "queries": [[0, 3], [3, 0], [0, 3]]},
             "why": {"t": "Repeated query", "d": "The same pair asked twice, both directions."}},
            {"args": {"n": 6, "links": [[0, 1], [1, 2], [2, 0], [3, 4]], "queries": [[2, 1], [4, 3], [5, 0], [5, 5]]},
             "why": {"t": "Cycle and isolated", "d": "A cycle, a pair and one isolated system."}},
            {"args": {"n": 400, "links": [[i, i + 1] for i in range(399)], "queries": [[0, 399], [399, 0], [200, 17]]},
             "why": {"t": "Long chain", "d": "A 400-system line: unions must not build deep trees."}},
            {"args": _many(), "why": {"t": "Large input", "d": "300 systems, 250 random links, 150 queries."}},
        ],
        "solutions": [
            {"name": "Union-find (Optimal)",
             "description": "Union the two ends of every link with path compression and union by size. A query is True when both systems have the same root.",
             "time": "O((E + Q) · α(n))", "space": "O(n)",
             "keyPoints": ["Components answer every reachability question", "Iterative find avoids recursion limits", "Build once, answer in near-constant time"],
             "code": '''def reach_many(n, links, queries):
    parent = list(range(n))
    size = [1] * n

    def find(x):
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root

    for a, b in links:
        ra, rb = find(a), find(b)
        if ra != rb:
            if size[ra] < size[rb]:
                ra, rb = rb, ra
            parent[rb] = ra
            size[ra] += size[rb]
    return [find(s) == find(t) for s, t in queries]
'''},
            {"name": "BFS per query", "slow": True,
             "description": "Run the main problem's BFS separately for every query.",
             "time": "O(Q · (n + E))", "space": "O(n + E)",
             "keyPoints": ["Correct and simple", "Rewalks the same component for every query"],
             "code": '''from collections import deque


def reach_many(n, links, queries):
    adj = [[] for _ in range(n)]
    for a, b in links:
        adj[a].append(b)
        adj[b].append(a)
    out = []
    for s, t in queries:
        seen = [False] * n
        seen[s] = True
        q = deque([s])
        while q:
            node = q.popleft()
            for nxt in adj[node]:
                if not seen[nxt]:
                    seen[nxt] = True
                    q.append(nxt)
        out.append(seen[t])
    return out
'''},
        ],
        "starter": '''def reach_many(n: int, links: list[list[int]], queries: list[list[int]]) -> list[bool]:
    pass
''',
    },
    {
        "key": "links-failing",
        "title": "Links failing one by one",
        "approach": "Reverse union-find (add links back) · O((E + F) · α(n)) · O(n + E)",
        "spec": {"kind": "fn", "fn": "still_reachable", "params": ["n", "links", "failures", "source", "target"], "cmp": "exact"},
        "statement": (
            "A chaos drill takes links down one at a time.\n"
            "\n"
            "### Input\n"
            "- `n`, `links`: the systems and two-way links, as in the main problem\n"
            "- `failures`: distinct indices into `links`, in the order those links fail\n"
            "- `source`, `target`: the two systems to check\n"
            "\n"
            "### Output\n"
            "- One boolean per failure, in order: whether `source` can still reach `target`\n"
            "\n"
            "### Rules\n"
            "- A failed link stays down\n"
            "- Check after **each** failure, over the links that are still up"
        ),
        "examples": [
            {"args": {"n": 4, "links": [[0, 1], [1, 3], [0, 2], [2, 3]], "failures": [1, 3, 0], "source": 0, "target": 3},
             "explanation": "Losing 1-3 leaves 0-2-3. Losing 2-3 cuts the last path, and it stays cut after 0-1 fails too.",
             "why": {"t": "Redundant path", "d": "The target survives the first failure through the second path."}},
        ],
        "constraints": ["1 ≤ n ≤ 10^5", "0 ≤ len(links) ≤ 10^5, no duplicates, a != b",
                        "1 ≤ len(failures) ≤ len(links), indices distinct", "0 ≤ source, target < n"],
        "hints": [
            "The answers only get worse over time: once cut, always cut. But that alone does not say when.",
            "Start from the final state (every failed link down), union the links that never fail, and record the answer.",
            "Then add the failed links back in reverse order, recording the answer before each one is restored.",
        ],
        "tests": [
            {"args": {"n": 2, "links": [[0, 1]], "failures": [0], "source": 0, "target": 1},
             "why": {"t": "Single link", "d": "The only link fails: unreachable."}},
            {"args": {"n": 3, "links": [[0, 1], [1, 2]], "failures": [0], "source": 1, "target": 1},
             "why": {"t": "Source is target", "d": "A system always reaches itself."}},
            {"args": {"n": 5, "links": [[0, 1], [1, 2], [3, 4]], "failures": [2, 1], "source": 0, "target": 1},
             "why": {"t": "Unrelated failures", "d": "Links elsewhere fail; 0-1 is untouched."}},
            {"args": {"n": 4, "links": [[0, 1], [1, 2], [2, 3], [3, 0]], "failures": [0, 2, 1], "source": 0, "target": 2},
             "why": {"t": "Ring", "d": "A ring survives one cut, not two on both sides."}},
            {"args": {"n": 3, "links": [[0, 2], [1, 2]], "failures": [0, 1], "source": 0, "target": 1},
             "why": {"t": "Never reachable", "d": "Still False even before anything relevant is restored."}},
            {"args": _failing(), "why": {"t": "Large input", "d": "A 120-system chain with 31 extra links; 130 of 150 links fail."}},
        ],
        "solutions": [
            {"name": "Reverse union-find (Optimal)",
             "description": "Union every link that never fails. Walking the failures backwards, the current answer belongs to the step after that failure; then restore the link by union.",
             "time": "O((E + F) · α(n))", "space": "O(n + E)",
             "keyPoints": ["Deletions forwards are additions backwards", "Record the answer before restoring each link", "Only union-find, no graph walks"],
             "code": '''def still_reachable(n, links, failures, source, target):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    failed = set(failures)
    for i, (a, b) in enumerate(links):
        if i not in failed:
            union(a, b)
    out = [False] * len(failures)
    for k in range(len(failures) - 1, -1, -1):
        out[k] = find(source) == find(target)
        a, b = links[failures[k]]
        union(a, b)
    return out
'''},
            {"name": "BFS after every failure", "slow": True,
             "description": "Mark the link as down and run a fresh BFS over the remaining links after each failure.",
             "time": "O(F · (n + E))", "space": "O(n + E)",
             "keyPoints": ["Straight simulation", "Every failure pays for a full walk"],
             "code": '''from collections import deque


def still_reachable(n, links, failures, source, target):
    down = [False] * len(links)
    adj = [[] for _ in range(n)]
    for i, (a, b) in enumerate(links):
        adj[a].append((b, i))
        adj[b].append((a, i))
    out = []
    for f in failures:
        down[f] = True
        seen = [False] * n
        seen[source] = True
        q = deque([source])
        while q:
            node = q.popleft()
            for nxt, i in adj[node]:
                if not down[i] and not seen[nxt]:
                    seen[nxt] = True
                    q.append(nxt)
        out.append(seen[target])
    return out
'''},
        ],
        "starter": '''def still_reachable(n: int, links: list[list[int]], failures: list[int], source: int, target: int) -> list[bool]:
    pass
''',
    },
]
