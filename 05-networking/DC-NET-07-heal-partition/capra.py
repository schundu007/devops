"""Capra Playground export for DC-NET-07 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "min_link_moves", "params": ["n", "links"], "types": {}, "ret": "value", "cmp": "exact"}


def c(n, links, t, d):
    return {"args": {"n": n, "links": links}, "why": {"t": t, "d": d}}


EXAMPLES = [
    {"args": {"n": 4, "links": [[0, 1], [0, 2], [1, 2]]},
     "explanation": "Devices 0-2 form a triangle, so one of its links is spare. Move it to device 3: one move.",
     "why": {"t": "One spare link", "d": "A loop frees a cable to reconnect an isolated device."}},
    {"args": {"n": 6, "links": [[0, 1], [0, 2], [0, 3], [1, 2]]},
     "explanation": "Six devices need at least 5 links; there are only 4, so no plan works: -1.",
     "why": {"t": "Not enough links", "d": "Fewer than n - 1 cables can never connect n devices."}},
]

TESTS = [
    c(1, [], "Single device", "One device is already connected: 0 moves."),
    c(2, [], "Two devices, no links", "Not enough cables: -1."),
    c(3, [[0, 1], [1, 2]], "Already connected", "A connected network needs no moves."),
    c(5, [[0, 1], [0, 2], [3, 4], [2, 3]], "Exactly n - 1 links", "A tree: connected, 0 moves."),
    c(6, [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3]], "Enough links, not connected", "Three segments and two spares: 2 moves."),
    c(4, [[0, 1], [0, 1], [2, 3]], "Duplicate cable", "A doubled cable is a spare: 1 move joins the two segments."),
    c(5, [[0, 1], [1, 2], [2, 0], [3, 4], [3, 4]], "Spares in both segments", "Two segments need exactly one move."),
    c(3, [[0, 1], [0, 1], [0, 1]], "Many duplicates", "Three copies of one link: device 2 needs one moved to it."),
]


def _large():
    rng = random.Random(1319)
    n = 400
    links = []
    for _ in range(420):
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b:
            links.append([a, b])
    return n, links


N, L = _large()
TESTS.append(c(N, L, "Large input", "400 devices and about 420 random cables."))

SOLUTIONS = [
    {"file": "solution.py", "name": "Union-find (Optimal)",
     "description": "If there are fewer than n - 1 cables, return -1. Otherwise union every cable's ends and count the segments; each move joins two segments, so the answer is segments - 1.",
     "time": "O(n + E · α(n))", "space": "O(n)",
     "keyPoints": ["Fewer than n - 1 links: impossible", "Enough links always means enough spares", "Answer = segments - 1"]},
    {"name": "BFS component count", "slow": True,
     "description": "Build the adjacency list and count connected components with BFS; same formula, different way to count.",
     "time": "O(n + E)", "space": "O(n + E)",
     "keyPoints": ["Counts components directly", "Same -1 rule for too few cables"],
     "code": '''from collections import deque


def min_link_moves(n, links):
    if len(links) < n - 1:
        return -1
    adj = [[] for _ in range(n)]
    for a, b in links:
        adj[a].append(b)
        adj[b].append(a)
    seen, segments = [False] * n, 0
    for s in range(n):
        if seen[s]:
            continue
        segments += 1
        seen[s] = True
        q = deque([s])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if not seen[v]:
                    seen[v] = True
                    q.append(v)
    return segments - 1
'''},
]

WAYS_TO_SOLVE = [
    {"name": "BFS / DFS components", "idea": "Count connected components by graph traversal.",
     "time": "O(n + E)", "space": "O(n + E)", "use": "A one-off count over a static network."},
    {"name": "Union-find", "idea": "Merge cable ends; each successful union removes a segment.",
     "time": "O(n + E · α(n))", "space": "O(n)", "use": "Cables arrive as a stream, or the count must update as links change."},
]
