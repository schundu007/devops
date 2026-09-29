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
     "description": "Pop the router with the smallest known arrival time; that time is final. Push each neighbor with time + delay. If every router got a time, return the largest; otherwise -1.",
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

VARIANT_TITLE = "Broadcast delay"
VARIANT_APPROACH = "Dijkstra with a min-heap · O(E log E) · O(V + E)"


def _hop_large():
    rng = random.Random(787)
    n, links = 40, []
    for _ in range(150):
        u, v = rng.randint(1, n), rng.randint(1, n)
        if u != v:
            links.append([u, v, rng.randint(1, 90)])
    return {"links": links, "n": n, "src": 1, "dst": 40, "max_hops": 5}


def _wide_large():
    rng = random.Random(1514)
    n, links = 150, []
    for v in range(2, n + 1):
        links.append([rng.randint(1, v - 1), v, rng.choice([1, 10, 25, 40, 100])])
    for _ in range(450):
        u, v = rng.randint(1, n), rng.randint(1, n)
        if u != v:
            links.append([u, v, rng.choice([1, 10, 25, 40, 100, 400])])
    return {"links": links, "n": n, "src": 1, "dst": n}


def hop(links, n, src, dst, max_hops, t, d):
    return {"args": {"links": links, "n": n, "src": src, "dst": dst, "max_hops": max_hops}, "why": {"t": t, "d": d}}


def wide(links, n, src, dst, t, d):
    return {"args": {"links": links, "n": n, "src": src, "dst": dst}, "why": {"t": t, "d": d}}


VARIANTS = [
    {
        "key": "hop-limited",
        "title": "Fastest path within a hop limit",
        "approach": "Bellman-Ford for max_hops rounds · O(max_hops · E) · O(V)",
        "spec": {"kind": "fn", "fn": "fastest_within_hops", "params": ["links", "n", "src", "dst", "max_hops"]},
        "statement": (
            "Find the fastest path that fits a hop budget, like an IP TTL: every relay decrements it, and the packet is dropped when it runs out.\n"
            "\n"
            "### Input\n"
            "- `links[i] = [u, v, ms]`: a one-way link from router `u` to router `v` with `ms` milliseconds of delay\n"
            "- `n`: routers, numbered `1..n`\n"
            "- `src`, `dst`: the start and end routers\n"
            "- `max_hops`: the most links a path may use\n"
            "\n"
            "### Output\n"
            "- The smallest total delay from `src` to `dst` over a path that uses **at most** `max_hops` links\n"
            "- `-1` if no such path exists\n"
            "\n"
            "### Rules\n"
            "- A path from a router to itself uses zero links and costs 0"
        ),
        "examples": [
            {"args": {"links": [[1, 2, 1], [2, 3, 1], [3, 4, 1], [1, 4, 10]], "n": 4, "src": 1, "dst": 4, "max_hops": 2},
             "explanation": "The 3 ms path 1-2-3-4 needs three links, over the budget of 2. The direct 10 ms link is the best allowed path.",
             "why": {"t": "Budget beats speed", "d": "The fastest path overall is not allowed; the answer is the fastest within the budget."}},
            {"args": {"links": [[1, 2, 5], [2, 3, 5]], "n": 3, "src": 1, "dst": 3, "max_hops": 1},
             "explanation": "Router 3 is two links away and the budget is one: -1.",
             "why": {"t": "Out of reach", "d": "Reachable in the graph, but not within the hop limit."}},
        ],
        "constraints": ["1 ≤ n ≤ 100", "0 ≤ links.length ≤ 2000", "0 ≤ ms ≤ 1000", "1 ≤ src, dst ≤ n", "0 ≤ max_hops ≤ n"],
        "hints": [
            "Plain Dijkstra finalizes a router by delay alone, but a slower path with fewer hops can still matter later.",
            "After round r of Bellman-Ford relaxation, dist[v] is the best delay using at most r links, as long as each round reads the previous round's copy.",
            "Relax from a snapshot of dist, not the array you are writing, or one round can chain several links.",
        ],
        "tests": [
            hop([], 1, 1, 1, 0, "Source is destination", "Zero links and zero hops: delay 0."),
            hop([[1, 2, 3]], 2, 1, 2, 0, "Zero budget", "A budget of 0 reaches only the source."),
            hop([[1, 2, 1], [2, 3, 1], [1, 3, 5]], 3, 1, 3, 2, "Budget exactly fits", "The two-link path fits the budget of 2 and beats the direct link."),
            hop([[1, 2, 4], [1, 2, 2], [2, 3, 1]], 3, 1, 3, 3, "Parallel links", "Two links between the same routers: the faster one wins."),
            hop([[1, 2, 1], [2, 1, 1], [2, 3, 7]], 3, 1, 3, 5, "Cycle in range", "A loop never helps with non-negative delays."),
            hop([[2, 1, 1]], 2, 1, 2, 3, "Wrong direction", "Links are one-way: -1."),
            {"args": _hop_large(), "why": {"t": "Large input", "d": "40 routers, about 150 links, a budget of 5 hops."}},
        ],
        "solutions": [
            {"name": "Bellman-Ford, max_hops rounds (Optimal)",
             "description": "Start with dist[src] = 0. Run max_hops rounds; each round relaxes every link from a copy of the previous round, so round r allows one more link.",
             "time": "O(max_hops · E)", "space": "O(V)",
             "keyPoints": ["Relax from the previous round's copy", "Round r = best delay with at most r links", "Stop early when a round changes nothing"],
             "code": '''def fastest_within_hops(links, n, src, dst, max_hops):
    INF = float("inf")
    dist = [INF] * (n + 1)
    dist[src] = 0
    for _ in range(max_hops):
        nxt = dist[:]
        for u, v, ms in links:
            if dist[u] + ms < nxt[v]:
                nxt[v] = dist[u] + ms
        if nxt == dist:
            break
        dist = nxt
    return -1 if dist[dst] == INF else dist[dst]
'''},
            {"name": "Try every path", "slow": True,
             "description": "Depth-first search over every path of at most max_hops links from src, keeping the cheapest arrival at dst.",
             "time": "O(deg^max_hops)", "space": "O(max_hops)",
             "keyPoints": ["Obviously correct", "Exponential in the hop budget"],
             "code": '''def fastest_within_hops(links, n, src, dst, max_hops):
    out = {}
    for u, v, ms in links:
        out.setdefault(u, []).append((v, ms))
    best = [float("inf")]

    def go(u, hops, cost):
        if u == dst:
            best[0] = min(best[0], cost)
        if hops == max_hops:
            return
        for v, ms in out.get(u, []):
            go(v, hops + 1, cost + ms)

    go(src, 0, 0)
    return -1 if best[0] == float("inf") else best[0]
'''},
        ],
        "starter": '''def fastest_within_hops(links, n, src, dst, max_hops):
    """Smallest delay from src to dst using at most max_hops links, or -1."""
    pass
''',
    },
    {
        "key": "widest-path",
        "title": "Highest-bandwidth route",
        "approach": "Max-heap Dijkstra on the bottleneck · O(E log E) · O(V + E)",
        "spec": {"kind": "fn", "fn": "max_bandwidth", "params": ["links", "n", "src", "dst"]},
        "statement": (
            "Find the route with the highest bottleneck bandwidth for a snapshot copy between data centers.\n"
            "\n"
            "### Input\n"
            "- `links[i] = [u, v, mbps]`: a one-way link from `u` to `v` with `mbps` of spare bandwidth\n"
            "- `n`: data centers, numbered `1..n`\n"
            "- `src`, `dst`: the source and destination; `src != dst`\n"
            "\n"
            "### Output\n"
            "- The largest bottleneck bandwidth over all routes from `src` to `dst`\n"
            "- `0` if `dst` cannot be reached\n"
            "\n"
            "### Rules\n"
            "- A route's throughput is limited by its **slowest** link"
        ),
        "examples": [
            {"args": {"links": [[1, 2, 100], [2, 4, 10], [1, 3, 40], [3, 4, 40]], "n": 4, "src": 1, "dst": 4},
             "explanation": "Route 1-2-4 is limited to 10 by its second link; route 1-3-4 keeps 40 all the way.",
             "why": {"t": "Bottleneck, not sum", "d": "A fast first hop does not help if a later link is slow."}},
            {"args": {"links": [[2, 1, 50]], "n": 2, "src": 1, "dst": 2},
             "explanation": "The only link points the wrong way: 0.",
             "why": {"t": "Unreachable", "d": "No route means no bandwidth."}},
        ],
        "constraints": ["2 ≤ n ≤ 1000", "0 ≤ links.length ≤ 5000", "1 ≤ mbps ≤ 10⁶", "src != dst"],
        "hints": [
            "Dijkstra works for any path score that never improves as the path grows. The bottleneck only goes down.",
            "Pop the data center with the widest known route from a max-heap; that value is final.",
            "Extending a route through a link gives min(route width, link width).",
        ],
        "tests": [
            wide([], 2, 1, 2, "No links", "Nothing connects the two data centers: 0."),
            wide([[1, 2, 7]], 2, 1, 2, "Single link", "The route's width is that link's width."),
            wide([[1, 2, 5], [1, 2, 9]], 2, 1, 2, "Parallel links", "The wider of two parallel links wins."),
            wide([[1, 2, 10], [2, 3, 10], [1, 3, 10]], 3, 1, 3, "Ties", "Two routes share the same bottleneck."),
            wide([[1, 2, 100], [2, 1, 100], [2, 3, 1], [1, 3, 2]], 3, 1, 3, "Cycle", "A loop cannot widen a route."),
            wide([[1, 2, 3], [3, 4, 9]], 4, 1, 4, "Partition", "Two islands: 0."),
            {"args": _wide_large(), "why": {"t": "Large input", "d": "150 data centers and about 600 links."}},
        ],
        "solutions": [
            {"name": "Max-heap Dijkstra (Optimal)",
             "description": "Keep the widest known route to each node. Pop the widest from a max-heap; it is final. Push each neighbor with min(width, link).",
             "time": "O(E log E)", "space": "O(V + E)",
             "keyPoints": ["Widths only shrink along a route", "The first pop of a node is final", "Return 0 when dst is never reached"],
             "code": '''import heapq


def max_bandwidth(links, n, src, dst):
    out = {}
    for u, v, w in links:
        out.setdefault(u, []).append((v, w))
    best = [0] * (n + 1)
    heap = [(-float("inf"), src)]
    done = set()
    while heap:
        w, u = heapq.heappop(heap)
        w = -w
        if u in done:
            continue
        done.add(u)
        if u == dst:
            return w
        for v, cap in out.get(u, []):
            nw = min(w, cap)
            if nw > best[v]:
                best[v] = nw
                heapq.heappush(heap, (-nw, v))
    return 0
'''},
            {"name": "Try each threshold", "slow": True,
             "description": "For each distinct bandwidth, widest first, check with BFS whether dst is reachable using only links at least that wide.",
             "time": "O(E · (V + E))", "space": "O(V + E)",
             "keyPoints": ["The first threshold that connects the pair is the answer", "One full search per distinct width"],
             "code": '''from collections import deque


def max_bandwidth(links, n, src, dst):
    for cap in sorted({w for _, _, w in links}, reverse=True):
        out = {}
        for u, v, w in links:
            if w >= cap:
                out.setdefault(u, []).append(v)
        seen, q = {src}, deque([src])
        while q:
            u = q.popleft()
            for v in out.get(u, []):
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        if dst in seen:
            return cap
    return 0
'''},
        ],
        "starter": '''def max_bandwidth(links, n, src, dst):
    """Largest bottleneck bandwidth from src to dst, or 0 if unreachable."""
    pass
''',
    },
]
