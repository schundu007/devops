"""Capra Playground export for DC-NET-06 (see tools/export_capra.py)."""
import random

# Any order of links, and either end first: unorderedNested sorts both levels.
SPEC = {"kind": "fn", "fn": "critical_links", "params": ["n", "links"], "types": {}, "ret": "value", "cmp": "unorderedNested"}


def c(n, links, t, d):
    return {"args": {"n": n, "links": links}, "why": {"t": t, "d": d}}


EXAMPLES = [
    {"args": {"n": 4, "links": [[0, 1], [1, 2], [2, 0], [1, 3]]},
     "explanation": "0-1-2 form a ring, so any one of those links can fail. Device 3 hangs off 1 by a single link: [1, 3] is the SPOF.",
     "why": {"t": "Ring plus spur", "d": "Links on a cycle are never critical."}},
    {"args": {"n": 2, "links": [[0, 1]]}, "explanation": "The only link between two devices is critical.",
     "why": {"t": "Single link", "d": "The smallest network with a SPOF."}},
    {"args": {"n": 2, "links": [[0, 1], [0, 1]]},
     "explanation": "Two parallel links back each other up, so neither is critical.",
     "why": {"t": "Parallel links", "d": "Redundant cabling between the same pair."}},
]

TESTS = [
    c(1, [], "Single device", "No links, nothing to fail."),
    c(3, [], "No links", "Isolated devices: no link is critical because none exists."),
    c(5, [[0, 1], [1, 2], [2, 3], [3, 4]], "Chain", "Every link on a chain is a bridge."),
    c(4, [[0, 1], [1, 2], [2, 3], [3, 0]], "Ring", "A ring has no single point of failure."),
    c(6, [[0, 1], [1, 2], [2, 0], [3, 4], [4, 5], [5, 3], [2, 3]], "Two rings joined", "Only the link joining the rings is critical."),
    c(5, [[0, 1], [0, 2], [0, 3], [0, 4]], "Star", "Every spoke of a star is a bridge."),
    c(6, [[0, 1], [1, 2], [3, 4], [4, 5], [5, 3]], "Two components", "Bridges are found in every component."),
    c(4, [[0, 1], [1, 2], [1, 2], [2, 3]], "One doubled link", "The doubled 1-2 link survives; the other two are critical."),
]


def _large():
    rng = random.Random(1192)
    n = 150
    links = [[rng.randrange(v), v] for v in range(1, n)]  # a random tree: all bridges...
    for _ in range(60):  # ...until extra links close cycles
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b:
            links.append([a, b])
    return n, links


N, L = _large()
TESTS.append(c(N, L, "Large input", "150 devices: a random tree plus 60 extra links."))

SOLUTIONS = [
    {"file": "solution.py", "name": "Tarjan's bridges, iterative (Optimal)",
     "description": "DFS gives each device a discovery time and a low-link (the earliest discovery time reachable through one back link). A tree link parent-child is a bridge when low[child] > disc[parent]. An explicit stack avoids Python's recursion limit.",
     "time": "O(V + E)", "space": "O(V + E)",
     "keyPoints": ["Skip only the exact link you came in on, so parallel links work", "low[child] > disc[parent] means no way around", "Iterative DFS for deep networks"]},
    {"name": "Remove each link and recount", "slow": True,
     "description": "For every link, drop it and count connected components with BFS. If the count goes up, the link is critical.",
     "time": "O(E · (V + E))", "space": "O(V + E)",
     "keyPoints": ["Easy to trust", "Quadratic: far too slow for large networks"],
     "code": '''from collections import deque


def critical_links(n, links):
    def components(skip):
        adj = [[] for _ in range(n)]
        for i, (a, b) in enumerate(links):
            if i != skip:
                adj[a].append(b)
                adj[b].append(a)
        seen, count = [False] * n, 0
        for s in range(n):
            if seen[s]:
                continue
            count += 1
            seen[s] = True
            q = deque([s])
            while q:
                u = q.popleft()
                for v in adj[u]:
                    if not seen[v]:
                        seen[v] = True
                        q.append(v)
        return count

    base = components(-1)
    return [list(links[i]) for i in range(len(links)) if components(i) > base]
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Remove and recount", "idea": "Drop each link, BFS, compare component counts.",
     "time": "O(E · (V + E))", "space": "O(V + E)", "use": "Tiny networks; a reference to test against."},
    {"name": "Tarjan's bridges", "idea": "One DFS with discovery times and low-links.",
     "time": "O(V + E)", "space": "O(V + E)", "use": "Any real topology: one pass finds every SPOF link."},
]
