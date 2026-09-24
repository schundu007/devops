"""Capra Playground export for DC-NET-08 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "find_loop_link", "params": ["n", "links"], "types": {}, "ret": "value", "cmp": "exact"}


def c(n, links, t, d):
    return {"args": {"n": n, "links": links}, "why": {"t": t, "d": d}}


EXAMPLES = [
    {"args": {"n": 3, "links": [[1, 2], [1, 3], [2, 3]]},
     "explanation": "All three links form one loop. Any could go, so return the one listed last: [2, 3].",
     "why": {"t": "Triangle", "d": "The whole network is the loop."}},
    {"args": {"n": 5, "links": [[1, 2], [2, 3], [3, 4], [1, 4], [1, 5]]},
     "explanation": "The loop is 1-2-3-4-1. Of its links, [1, 4] is listed last; [1, 5] is not on the loop.",
     "why": {"t": "Loop plus tail", "d": "A link after the loop link is not a candidate."}},
]

TESTS = [
    c(2, [[1, 2], [1, 2]], "Duplicate link", "Two links between the same switches: the second closes the loop."),
    c(4, [[1, 2], [2, 3], [3, 4], [4, 1]], "Ring of four", "The last link of the ring closes it."),
    c(4, [[1, 2], [1, 3], [1, 4], [3, 4]], "Star plus chord", "The chord between two leaves is the loop link."),
    c(5, [[3, 4], [1, 2], [2, 4], [1, 5], [2, 3]], "Out of order", "Links are listed in no particular order."),
    c(4, [[1, 2], [3, 4], [2, 3], [4, 1]], "Loop closes at the end", "The loop is only complete with the last link."),
    c(6, [[1, 2], [2, 3], [3, 1], [3, 4], [4, 5], [5, 6]], "Loop first", "The loop link comes before the tail links."),
]


def _large():
    rng = random.Random(684)
    n = 300
    links = [[rng.randint(1, v - 1), v] for v in range(2, n + 1)]  # a random tree
    a, b = rng.sample(range(1, n + 1), 2)
    links.append([min(a, b), max(a, b)])  # one extra link makes exactly one loop
    rng.shuffle(links)
    return n, links


N, L = _large()
TESTS.append(c(N, L, "Large input", "300 switches in a shuffled tree plus one extra link."))

SOLUTIONS = [
    {"file": "solution.py", "name": "Union-find (Optimal)",
     "description": "Read the links in order and union their ends. The first link whose ends are already connected closes the loop, and every other loop link came before it, so it is the last one listed.",
     "time": "O(n · α(n))", "space": "O(n)",
     "keyPoints": ["Same root on both ends = loop link", "Union by size + path halving", "First loop link found = last one listed"]},
    {"name": "Remove from the end and test", "slow": True,
     "description": "Try removing each link, starting from the last one listed. The first removal that leaves a connected tree is the answer.",
     "time": "O(n²)", "space": "O(n)",
     "keyPoints": ["One BFS per candidate link", "Quadratic; fine for small networks"],
     "code": '''from collections import deque


def find_loop_link(n, links):
    def connected(skip):
        adj = [[] for _ in range(n + 1)]
        for i, (a, b) in enumerate(links):
            if i != skip:
                adj[a].append(b)
                adj[b].append(a)
        seen = {1}
        q = deque([1])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        return len(seen) == n

    for i in range(len(links) - 1, -1, -1):
        if connected(i):
            return list(links[i])
    return []
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Remove and test", "idea": "Drop each link from the last one backwards; keep the first that leaves the network connected.",
     "time": "O(n²)", "space": "O(n)", "use": "Tiny networks; easy to verify by hand."},
    {"name": "Union-find", "idea": "The first link joining two already-connected switches is the loop link.",
     "time": "O(n · α(n))", "space": "O(n)", "use": "Any size; one pass over the links."},
]
