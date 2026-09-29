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
     "description": "Keep a max-heap of path probabilities. Pop the most reliable node: its value is final, because multiplying by a probability never makes a path better. Relax neighbors by multiplying.",
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

VARIANT_TITLE = "Most reliable path"
VARIANT_APPROACH = "Dijkstra on max-product · O((n + L) log n) · O(n + L)"


def _mesh(seed, n, extra, lo, hi, as_int):
    rng = random.Random(seed)
    links, vals = [], []
    for v in range(1, n):
        links.append([rng.randrange(v), v])
        vals.append(rng.randint(lo, hi) if as_int else round(rng.uniform(lo, hi), 3))
    for _ in range(extra):
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b:
            links.append([a, b])
            vals.append(rng.randint(lo, hi) if as_int else round(rng.uniform(lo, hi), 3))
    return links, vals


_WL, _WB = _mesh(1976, 120, 200, 1, 10000, True)
_HL, _HS = _mesh(787, 60, 120, 0.5, 1.0, False)


def w(n, links, bandwidth, src, dst, t, d):
    return {"args": {"n": n, "links": links, "bandwidth": bandwidth, "src": src, "dst": dst}, "why": {"t": t, "d": d}}


def h(n, links, success, src, dst, max_hops, t, d):
    return {"args": {"n": n, "links": links, "success": success, "src": src, "dst": dst, "max_hops": max_hops},
            "why": {"t": t, "d": d}}


VARIANTS = [
    {
        "key": "widest-path",
        "title": "Widest path for a bulk transfer",
        "approach": "Dijkstra on max-min · O((n + L) log n) · O(n + L)",
        "spec": {"kind": "fn", "fn": "widest_path", "params": ["n", "links", "bandwidth", "src", "dst"], "ret": "value", "cmp": "exact"},
        "statement": """A backup job copies a snapshot between two data centers over one path. The path runs only as fast as its slowest link, so its throughput is the **minimum** bandwidth along it.

`links[i] = [a, b]` is a two-way link with `bandwidth[i]` Gbps. Return the highest throughput of any path from `src` to `dst`, or `0` if `dst` cannot be reached.

Same Dijkstra skeleton as the reliable path, with a different way to combine: `min` along a path instead of a product, and `max` across paths.""",
        "examples": [
            {"args": {"n": 4, "links": [[0, 1], [1, 3], [0, 2], [2, 3]], "bandwidth": [100, 10, 40, 40], "src": 0, "dst": 3},
             "explanation": "Via node 1 the 10 Gbps link caps the path at 10. Via node 2 both links carry 40.",
             "why": {"t": "Bottleneck link", "d": "A fast first hop does not help if a later hop is slow."}},
            {"args": {"n": 3, "links": [[0, 1]], "bandwidth": [25], "src": 0, "dst": 2},
             "explanation": "Node 2 has no links, so nothing can be sent: 0.",
             "why": {"t": "Unreachable", "d": "No path returns 0."}},
        ],
        "constraints": ["2 ≤ n ≤ 10^4", "0 ≤ links.length ≤ 2 · 10^4", "1 ≤ bandwidth[i] ≤ 10^6", "src ≠ dst; parallel links may exist"],
        "hints": [
            "The best width to reach a node is final once it is the widest in the heap: extending a path can only keep or lower its width.",
            "Use a max-heap keyed on width; relax a neighbor with min(width, bandwidth).",
            "Alternative: add links from widest to narrowest with union-find and stop when src and dst join.",
        ],
        "tests": [
            w(2, [[0, 1]], [7], 0, 1, "Single link", "One hop: that link's bandwidth."),
            w(2, [], [], 0, 1, "No links", "Nothing connects the two nodes."),
            w(3, [[0, 1], [0, 1], [1, 2]], [5, 50, 30], 0, 2, "Parallel links", "The wider of the two parallel links is used."),
            w(3, [[0, 1], [1, 2], [0, 2]], [20, 20, 20], 2, 0, "Ties", "Every path has the same width; links work both ways."),
            w(5, [[0, 1], [1, 2], [2, 4], [0, 3], [3, 4]], [9, 9, 9, 100, 1], 0, 4, "Long path wins", "Three hops at 9 beat two hops capped at 1."),
            w(4, [[0, 1], [2, 3]], [10, 10], 0, 3, "Split network", "Two islands: 0."),
            w(120, _WL, _WB, 0, 119, "Large input", "120 nodes and about 320 links."),
        ],
        "solutions": [
            {"name": "Dijkstra on max-min (Optimal)",
             "description": "Max-heap of (width, node). Pop the widest node; its width is final. Relax each neighbor with min(width, link bandwidth).",
             "time": "O((n + L) log n)", "space": "O(n + L)",
             "keyPoints": ["Width only shrinks along a path", "Negate widths for heapq", "Stop when dst is popped"],
             "code": '''import heapq


def widest_path(n, links, bandwidth, src, dst):
    adj = [[] for _ in range(n)]
    for (a, b), bw in zip(links, bandwidth):
        adj[a].append((b, bw))
        adj[b].append((a, bw))
    best = [0] * n
    best[src] = float("inf")
    heap = [(-best[src], src)]
    while heap:
        neg, v = heapq.heappop(heap)
        width = -neg
        if v == dst:
            return width
        if width < best[v]:
            continue
        for u, bw in adj[v]:
            cand = min(width, bw)
            if cand > best[u]:
                best[u] = cand
                heapq.heappush(heap, (-cand, u))
    return 0
'''},
            {"name": "Try each bandwidth with BFS", "slow": True,
             "description": "For each distinct bandwidth from widest to narrowest, keep only links at least that wide and check with BFS whether dst is reachable.",
             "time": "O(L · (n + L))", "space": "O(n + L)",
             "keyPoints": ["The answer is always one of the link bandwidths", "One BFS per candidate"],
             "code": '''from collections import deque


def widest_path(n, links, bandwidth, src, dst):
    for cap in sorted(set(bandwidth), reverse=True):
        adj = [[] for _ in range(n)]
        for (a, b), bw in zip(links, bandwidth):
            if bw >= cap:
                adj[a].append(b)
                adj[b].append(a)
        seen = {src}
        q = deque([src])
        while q:
            v = q.popleft()
            for u in adj[v]:
                if u not in seen:
                    seen.add(u)
                    q.append(u)
        if dst in seen:
            return cap
    return 0
'''},
        ],
        "starter": '''def widest_path(n: int, links: list[list[int]], bandwidth: list[int], src: int, dst: int) -> int:
    pass
''',
    },
    {
        "key": "hop-limit",
        "title": "Most reliable path within a hop limit",
        "approach": "Bellman-Ford for k rounds · O(k · L) · O(n)",
        "spec": {"kind": "fn", "fn": "reliable_within_hops", "params": ["n", "links", "success", "src", "dst", "max_hops"], "ret": "value", "cmp": "float"},
        "statement": """A service mesh caps every request at `max_hops` proxies: a path longer than that is dropped by the TTL check, however reliable it is.

`links[i] = [a, b]` is a two-way link that works with probability `success[i]`. Return the highest success probability of a path from `src` to `dst` that uses **at most** `max_hops` links, or `0.0` if there is none.

Plain Dijkstra no longer works: the most reliable path to a middle node may use too many hops. Track the best probability per hop count instead.""",
        "examples": [
            {"args": {"n": 4, "links": [[0, 1], [1, 2], [2, 3], [0, 3]], "success": [0.99, 0.99, 0.99, 0.5], "src": 0, "dst": 3, "max_hops": 2},
             "explanation": "The three-hop path (0.97) is over the limit, so the direct link, 0.5, is the best allowed.",
             "why": {"t": "Limit bites", "d": "The globally best path is too long."}},
            {"args": {"n": 4, "links": [[0, 1], [1, 2], [2, 3], [0, 3]], "success": [0.99, 0.99, 0.99, 0.5], "src": 0, "dst": 3, "max_hops": 3},
             "explanation": "With three hops allowed, 0.99³ ≈ 0.970 beats the direct link.",
             "why": {"t": "Limit relaxed", "d": "Same mesh, one more hop allowed."}},
        ],
        "constraints": ["2 ≤ n ≤ 1000", "0 ≤ links.length ≤ 5000", "0 ≤ success[i] ≤ 1", "1 ≤ max_hops ≤ n − 1", "src ≠ dst; answers within 1e-9 relative error are accepted"],
        "hints": [
            "Let best[v] be the best probability to reach v using at most h hops. Going from h to h + 1 needs one pass over the links.",
            "Relax from a copy of the previous round, so one round never chains two links.",
            "Longer paths never help beyond the limit, so max_hops rounds are enough.",
        ],
        "tests": [
            h(2, [[0, 1]], [0.9], 0, 1, 1, "Single link", "One hop allowed, one hop needed."),
            h(3, [[0, 1], [1, 2]], [0.9, 0.9], 0, 2, 1, "Too far", "The only path needs two hops: 0.0."),
            h(2, [], [], 0, 1, 1, "No links", "Nothing connects the nodes."),
            h(3, [[0, 1], [1, 2], [0, 2]], [1.0, 1.0, 1.0], 0, 2, 2, "Ties", "Direct and two-hop paths both succeed always."),
            h(3, [[0, 1], [0, 1], [1, 2]], [0.3, 0.7, 0.5], 2, 0, 2, "Parallel links", "The better parallel link; links work both ways."),
            h(5, [[0, 1], [1, 2], [2, 3], [3, 4], [0, 4]], [0.95, 0.95, 0.95, 0.95, 0.0], 0, 4, 3, "Dead shortcut", "The direct link never works and the chain is too long."),
            h(60, _HL, _HS, 0, 59, 4, "Large input", "60 nodes, about 180 links, at most 4 hops."),
        ],
        "solutions": [
            {"name": "Bellman-Ford for k rounds (Optimal)",
             "description": "Start with best[src] = 1. Each round, relax every link in both directions from a copy of the previous round's values. After max_hops rounds, best[dst] is the answer.",
             "time": "O(k · L)", "space": "O(n)",
             "keyPoints": ["Round h holds paths of at most h hops", "Relax from the previous round's copy", "Stop early when a round changes nothing"],
             "code": '''def reliable_within_hops(n, links, success, src, dst, max_hops):
    best = [0.0] * n
    best[src] = 1.0
    for _ in range(max_hops):
        prev = best[:]
        changed = False
        for (a, b), p in zip(links, success):
            if prev[a] * p > best[b]:
                best[b] = prev[a] * p
                changed = True
            if prev[b] * p > best[a]:
                best[a] = prev[b] * p
                changed = True
        if not changed:
            break
    return best[dst]
'''},
            {"name": "Table per hop count, node by node", "slow": True,
             "description": "Fill dp[h][v] for every hop count h and node v by scanning every link for a way into v from dp[h - 1].",
             "time": "O(k · n · L)", "space": "O(k · n)",
             "keyPoints": ["Direct from the definition", "Rescans all links for every node"],
             "code": '''def reliable_within_hops(n, links, success, src, dst, max_hops):
    dp = [[0.0] * n for _ in range(max_hops + 1)]
    dp[0][src] = 1.0
    for hop in range(1, max_hops + 1):
        for v in range(n):
            best = dp[hop - 1][v]
            for (a, b), p in zip(links, success):
                if a == v:
                    best = max(best, dp[hop - 1][b] * p)
                elif b == v:
                    best = max(best, dp[hop - 1][a] * p)
            dp[hop][v] = best
    return dp[max_hops][dst]
'''},
        ],
        "starter": '''def reliable_within_hops(n: int, links: list[list[int]], success: list[float], src: int, dst: int, max_hops: int) -> float:
    pass
''',
    },
]
