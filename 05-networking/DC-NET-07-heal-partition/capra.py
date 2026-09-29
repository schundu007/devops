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

VARIANT_TITLE = "Heal the partition"
VARIANT_APPROACH = "Union-find, answer = segments - 1 · O(n + E · α(n)) · O(n)"


def _net_rng_links(seed, n, m):
    rng = random.Random(seed)
    out = []
    while len(out) < m:
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b:
            out.append([a, b])
    return out


_RED_LARGE = _net_rng_links(684, 250, 300)
_SEG_LARGE = _net_rng_links(1971, 200, 220)

VARIANTS = [
    {
        "key": "redundant-links",
        "title": "Redundant cables to reclaim",
        "approach": "Union-find in cable order · O(n + E · α(n)) · O(n)",
        "spec": {"kind": "fn", "fn": "redundant_links", "params": ["n", "links"]},
        "statement": (
            "A rack audit wants to reclaim spare cables before the next build-out.\n"
            "\n"
            "### Input\n"
            "- `n`: number of devices, numbered `0` to `n - 1`\n"
            "- `links`: undirected cables `[a, b]`, in the order they were plugged in\n"
            "\n"
            "### Output\n"
            "- The indices of the redundant cables, in ascending order\n"
            "\n"
            "### Rules\n"
            "- A cable is **redundant** if, when it was plugged in, its two ends could already reach each other through earlier cables\n"
            "- Unplugging every redundant cable leaves the same segments"
        ),
        "examples": [
            {"args": {"n": 4, "links": [[0, 1], [1, 2], [0, 2], [2, 3]]},
             "explanation": "Cable 2 joins 0 and 2, which already reach each other via 0-1-2, so it is spare.",
             "why": {"t": "Loop", "d": "The cable that closes a triangle is the redundant one."}},
            {"args": {"n": 3, "links": [[0, 1], [1, 0], [0, 1]]},
             "explanation": "The first copy connects 0 and 1; both later copies are spares.",
             "why": {"t": "Duplicates", "d": "A second cable on the same pair is always redundant."}},
        ],
        "constraints": ["1 ≤ n ≤ 10^5", "0 ≤ len(links) ≤ 2 · 10^5", "0 ≤ a, b < n and a ≠ b", "The same pair may appear more than once"],
        "hints": [
            "Walk the cables in order and keep track of which segment each device belongs to.",
            "With union-find, a cable is redundant exactly when find(a) == find(b) before the union.",
            "Path compression and union by size keep each check almost O(1).",
        ],
        "tests": [
            {"args": {"n": 1, "links": []}, "why": {"t": "No cables", "d": "Nothing to reclaim."}},
            {"args": {"n": 5, "links": [[0, 1], [1, 2], [2, 3], [3, 4]]}, "why": {"t": "A tree", "d": "Every cable joins two segments: none are spare."}},
            {"args": {"n": 4, "links": [[0, 1], [2, 3], [1, 2], [3, 0], [1, 3]]}, "why": {"t": "Loop closed late", "d": "Two segments merge, then two cables close loops."}},
            {"args": {"n": 2, "links": [[0, 1], [0, 1], [1, 0], [0, 1]]}, "why": {"t": "Many copies", "d": "Only the first copy of the pair is needed."}},
            {"args": {"n": 6, "links": [[0, 1], [1, 2], [3, 4], [4, 5], [2, 0], [5, 3], [2, 3]]}, "why": {"t": "Two islands with loops", "d": "Each island has one spare before they are joined."}},
            {"args": {"n": 250, "links": _RED_LARGE}, "why": {"t": "Large input", "d": "250 devices and 300 random cables."}},
        ],
        "solutions": [
            {"name": "Union-find (Optimal)",
             "description": "Process cables in order. If both ends already share a root, the cable is redundant; otherwise union the two roots.",
             "time": "O(n + E · α(n))", "space": "O(n)",
             "keyPoints": ["Order matters: the later cable of a loop is the spare", "find(a) == find(b) means already connected", "Union by size keeps trees shallow"],
             "code": '''def redundant_links(n, links):
    parent = list(range(n))
    size = [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    out = []
    for i, (a, b) in enumerate(links):
        ra, rb = find(a), find(b)
        if ra == rb:
            out.append(i)
            continue
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]
    return out
'''},
            {"name": "BFS before each cable", "slow": True,
             "description": "Keep the kept cables as an adjacency list. Before adding a cable, BFS from one end to see whether the other is reachable.",
             "time": "O(E · (n + E))", "space": "O(n + E)",
             "keyPoints": ["Direct translation of the definition", "One full traversal per cable"],
             "code": '''from collections import deque


def redundant_links(n, links):
    adj = [[] for _ in range(n)]
    out = []
    for i, (a, b) in enumerate(links):
        seen = {a}
        q = deque([a])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        if b in seen:
            out.append(i)
        else:
            adj[a].append(b)
            adj[b].append(a)
    return out
'''},
        ],
        "starter": '''def redundant_links(n: int, links: list[list[int]]) -> list[int]:
    """Indices of cables whose ends were already connected when plugged in."""
    raise NotImplementedError
''',
    },
    {
        "key": "segments-over-time",
        "title": "Segments during a repair window",
        "approach": "Incremental union-find · O(n + E · α(n)) · O(n)",
        "spec": {"kind": "fn", "fn": "segments_after_each", "params": ["n", "links"]},
        "statement": (
            "Report how many separate segments the devices form after each cable is plugged in.\n"
            "\n"
            "### Input\n"
            "- `n`: number of devices\n"
            "- `links[i] = [a, b]`: the `i`-th cable plugged in\n"
            "\n"
            "### Output\n"
            "- A list whose `i`-th entry is the number of segments right after cable `i` is plugged in\n"
            "\n"
            "### Rules\n"
            "- Before any cable, every device is its own segment"
        ),
        "examples": [
            {"args": {"n": 4, "links": [[0, 1], [2, 3], [1, 0], [1, 2]]},
             "explanation": "4 segments start. 0-1 gives 3, 2-3 gives 2, the repeat 1-0 changes nothing, 1-2 gives 1.",
             "why": {"t": "Merges and a repeat", "d": "Only cables that join two segments lower the count."}},
        ],
        "constraints": ["1 ≤ n ≤ 10^5", "0 ≤ len(links) ≤ 2 · 10^5", "0 ≤ a, b < n and a ≠ b"],
        "hints": [
            "The count only changes when a cable joins two different segments, and then it drops by exactly one.",
            "Union-find answers 'same segment?' as each cable arrives, with no recount.",
        ],
        "tests": [
            {"args": {"n": 3, "links": []}, "why": {"t": "No cables", "d": "An empty repair window reports nothing."}},
            {"args": {"n": 2, "links": [[0, 1]]}, "why": {"t": "Minimal", "d": "One cable joins the only two devices."}},
            {"args": {"n": 3, "links": [[0, 1], [0, 1], [1, 0]]}, "why": {"t": "Duplicates", "d": "Repeats keep the count flat."}},
            {"args": {"n": 5, "links": [[0, 1], [2, 3], [3, 4], [1, 2], [0, 4]]}, "why": {"t": "Loop at the end", "d": "Reaches 1, then a loop leaves it at 1."}},
            {"args": {"n": 6, "links": [[4, 5], [0, 5], [3, 2], [1, 2], [2, 5]]}, "why": {"t": "Arbitrary order", "d": "Cables arrive in no particular order."}},
            {"args": {"n": 200, "links": _SEG_LARGE}, "why": {"t": "Large input", "d": "200 devices and 220 random cables."}},
        ],
        "solutions": [
            {"name": "Incremental union-find (Optimal)",
             "description": "Start with n segments. For each cable, union its ends; if the roots differed, subtract one. Record the count.",
             "time": "O(n + E · α(n))", "space": "O(n)",
             "keyPoints": ["A successful union removes exactly one segment", "No recount after each cable", "Same structure as the main problem, reported per step"],
             "code": '''def segments_after_each(n, links):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    count = n
    out = []
    for a, b in links:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
            count -= 1
        out.append(count)
    return out
'''},
            {"name": "Recount with DFS", "slow": True,
             "description": "After each cable, rebuild the adjacency list and count components with an iterative DFS.",
             "time": "O(E · (n + E))", "space": "O(n + E)",
             "keyPoints": ["Obviously correct", "Recounts everything on every cable"],
             "code": '''def segments_after_each(n, links):
    out = []
    for i in range(len(links)):
        adj = [[] for _ in range(n)]
        for a, b in links[:i + 1]:
            adj[a].append(b)
            adj[b].append(a)
        seen = [False] * n
        count = 0
        for s in range(n):
            if seen[s]:
                continue
            count += 1
            seen[s] = True
            stack = [s]
            while stack:
                u = stack.pop()
                for v in adj[u]:
                    if not seen[v]:
                        seen[v] = True
                        stack.append(v)
        out.append(count)
    return out
'''},
        ],
        "starter": '''def segments_after_each(n: int, links: list[list[int]]) -> list[int]:
    """Number of segments after each cable is plugged in."""
    raise NotImplementedError
''',
    },
]
