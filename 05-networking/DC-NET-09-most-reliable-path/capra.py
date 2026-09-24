"""Capra Playground export for DC-NET-09 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "most_reliable_path", "params": ["n", "links", "success", "src", "dst"],
        "types": {}, "ret": "value", "cmp": "float"}


def c(n, links, success, src, dst, t, d):
    return {"args": {"n": n, "links": links, "success": success, "src": src, "dst": dst}, "why": {"t": t, "d": d}}


EXAMPLES = [
    {"args": {"n": 3, "links": [[0, 1], [1, 2], [0, 2]], "success": [0.5, 0.5, 0.2], "src": 0, "dst": 2},
     "explanation": "The two-hop path 0-1-2 succeeds 0.5 × 0.5 = 0.25 of the time, better than the direct link's 0.2.",
     "why": {"t": "Two hops beat one", "d": "More hops can still be more reliable."}},
    {"args": {"n": 3, "links": [[0, 1]], "success": [0.5], "src": 0, "dst": 2},
     "explanation": "Node 2 has no links at all, so the success probability is 0.0.",
     "why": {"t": "Unreachable", "d": "No path returns 0.0."}},
]

TESTS = [
    c(2, [[0, 1]], [0.999], 0, 1, "Single link", "One hop: the link's own probability."),
    c(3, [[0, 1], [1, 2]], [0.999, 0.999], 0, 2, "Availability multiplies", "99.9% x 99.9% is about 99.8%."),
    c(2, [], [], 0, 1, "No links", "Two nodes, no links: 0.0."),
    c(3, [[0, 1], [1, 2]], [1.0, 1.0], 0, 2, "Perfect links", "Probability 1 on every hop."),
    c(3, [[0, 1], [1, 2]], [0.0, 1.0], 0, 2, "Dead link", "A 0% link blocks the only path."),
    c(4, [[0, 1], [1, 3], [0, 2], [2, 3], [0, 3]], [0.9, 0.9, 0.95, 0.95, 0.85], 0, 3, "Three routes",
      "Direct 0.85, via 1 0.81, via 2 0.9025: the best is via 2."),
    c(3, [[0, 1], [0, 1], [1, 2]], [0.4, 0.8, 0.5], 0, 2, "Parallel links", "The better of two parallel links is used."),
    c(3, [[0, 1], [1, 2]], [0.6, 0.7], 2, 0, "Reverse direction", "Links work both ways."),
]


def _large():
    rng = random.Random(1514)
    n = 150
    links, success = [], []
    for v in range(1, n):
        links.append([rng.randrange(v), v])
        success.append(round(rng.uniform(0.5, 1.0), 3))
    for _ in range(250):
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b:
            links.append([a, b])
            success.append(round(rng.uniform(0.5, 1.0), 3))
    return n, links, success


N, L, S = _large()
TESTS.append(c(N, L, S, 0, N - 1, "Large input", "150 nodes and about 400 links with random success rates."))

SOLUTIONS = [
    {"file": "solution.py", "name": "Dijkstra on max-product (Optimal)",
     "description": "Keep a max-heap of path probabilities. Pop the most reliable node: its value is final, because multiplying by a probability never makes a path better. Relax neighbours by multiplying.",
     "time": "O((n + L) log n)", "space": "O(n + L)",
     "keyPoints": ["Probabilities multiply along a path", "Max-heap via negated values", "Return when dst is popped; 0.0 if never reached"]},
    {"name": "Bellman-Ford on products", "slow": True,
     "description": "Relax every link in both directions up to n - 1 times, keeping the best product found for each node.",
     "time": "O(n · L)", "space": "O(n)",
     "keyPoints": ["No heap needed", "n - 1 rounds always suffice"],
     "code": '''def most_reliable_path(n, links, success, src, dst):
    best = [0.0] * n
    best[src] = 1.0
    for _ in range(n - 1):
        changed = False
        for (a, b), p in zip(links, success):
            if best[a] * p > best[b]:
                best[b] = best[a] * p
                changed = True
            if best[b] * p > best[a]:
                best[a] = best[b] * p
                changed = True
        if not changed:
            break
    return best[dst]
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Bellman-Ford", "idea": "Relax all links n - 1 times with multiplication.",
     "time": "O(n · L)", "space": "O(n)", "use": "Small graphs; simplest to get right."},
    {"name": "Dijkstra (max-product)", "idea": "Max-heap on probability; first pop of a node is final.",
     "time": "O((n + L) log n)", "space": "O(n + L)", "use": "Large meshes; the same idea as shortest path with -log(p) weights."},
]
