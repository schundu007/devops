"""Capra Playground export for DC-NET-04 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "network_delay", "params": ["links", "n", "source"], "types": {}, "ret": "value", "cmp": "exact"}


def c(links, n, source, t, d):
    return {"args": {"links": links, "n": n, "source": source}, "why": {"t": t, "d": d}}


EXAMPLES = [
    {"args": {"links": [[2, 1, 1], [2, 3, 1], [3, 4, 1]], "n": 4, "source": 2},
     "explanation": "From router 2: routers 1 and 3 hear it at 1 ms, router 4 at 2 ms. The slowest arrival is 2.",
     "why": {"t": "Normal flood", "d": "The answer is the latest of the shortest arrival times."}},
    {"args": {"links": [[1, 2, 1]], "n": 2, "source": 2},
     "explanation": "Links are one-way. Router 1 never hears router 2: a partition, so -1.",
     "why": {"t": "Unreachable", "d": "A one-way link pointing the wrong way."}},
]

TESTS = [
    c([], 1, 1, "Single router", "The source alone: time 0."),
    c([], 2, 1, "No links", "Two routers and no links: -1."),
    c([[1, 2, 5], [1, 3, 1], [3, 2, 1]], 3, 1, "Shorter detour", "1->3->2 (2 ms) beats the direct 5 ms link."),
    c([[1, 2, 3], [1, 2, 1]], 2, 1, "Parallel links", "Two links between the same routers: the faster one wins."),
    c([[1, 2, 0], [2, 3, 0]], 3, 1, "Zero delay", "Zero-millisecond links are allowed."),
    c([[1, 2, 1], [2, 1, 1], [2, 3, 4], [3, 2, 4]], 3, 3, "Both directions", "Two one-way links make a two-way path."),
    c([[1, 2, 1], [2, 3, 1], [3, 1, 1], [3, 4, 100]], 4, 1, "Cycle then tail", "A loop must not be revisited; the tail sets the answer."),
    c([[1, 2, 1], [1, 3, 1], [4, 5, 1]], 5, 1, "Partition", "Routers 4 and 5 are cut off from router 1."),
]


def _large():
    rng = random.Random(743)
    n = 120
    links = []
    for v in range(2, n + 1):  # a random tree rooted at 1 keeps every router reachable
        links.append([rng.randint(1, v - 1), v, rng.randint(1, 50)])
    for _ in range(300):
        u, v = rng.randint(1, n), rng.randint(1, n)
        if u != v:
            links.append([u, v, rng.randint(1, 100)])
    return links, n


L, N = _large()
TESTS.append(c(L, N, 1, "Large input", "120 routers and about 420 one-way links."))

SOLUTIONS = [
    {"file": "solution.py", "name": "Dijkstra with a min-heap (Optimal)",
     "description": "Pop the router with the smallest known arrival time; that time is final. Push each neighbour with time + delay. If every router got a time, return the largest; otherwise -1.",
     "time": "O(E log E)", "space": "O(V + E)",
     "keyPoints": ["Skip stale heap entries", "Non-negative delays make the first pop final", "Answer = max over the shortest arrival times"]},
    {"name": "Bellman-Ford", "slow": True,
     "description": "Relax every link n - 1 times. Simple and handles negative weights, but O(V·E).",
     "time": "O(V · E)", "space": "O(V)",
     "keyPoints": ["n - 1 rounds are always enough", "Too slow for large networks"],
     "code": '''def network_delay(links, n, source):
    INF = float("inf")
    dist = [INF] * (n + 1)
    dist[source] = 0
    for _ in range(n - 1):
        changed = False
        for u, v, ms in links:
            if dist[u] + ms < dist[v]:
                dist[v] = dist[u] + ms
                changed = True
        if not changed:
            break
    worst = max(dist[1:])
    return -1 if worst == INF else worst
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Bellman-Ford", "idea": "Relax all links n - 1 times.",
     "time": "O(V · E)", "space": "O(V)", "use": "Small graphs, or when delays could be negative."},
    {"name": "Dijkstra", "idea": "Min-heap of arrival times; the first pop of a router is final.",
     "time": "O(E log E)", "space": "O(V + E)", "use": "Link-state routing (OSPF, IS-IS SPF); non-negative delays."},
]
