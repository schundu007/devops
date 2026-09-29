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

VARIANT_TITLE = "Find the loop link"
VARIANT_APPROACH = "Union-find · O(n · α(n)) · O(n)"


def _v_large():
    rng = random.Random(1319)
    n = 400
    links = []
    for v in range(2, n + 1):
        if rng.random() < 0.9:
            links.append([rng.randint(1, v - 1), v])
    for _ in range(70):
        a, b = rng.sample(range(1, n + 1), 2)
        links.append([a, b])
    rng.shuffle(links)
    return n, links


_VN, _VL = _v_large()

VARIANTS = [
    {
        "key": "recable-islands",
        "title": "Re-cable the islands",
        "approach": "Union-find, count spare links and components · O((n + m) · α(n)) · O(n)",
        "spec": {"kind": "fn", "fn": "recables_needed", "params": ["n", "links"]},
        "statement": (
            "A lab has `n` switches, numbered `1` to `n`, and cables `links[i] = [a, b]`. After a messy move, "
            "the switches have split into several isolated islands, and some islands have redundant cables "
            "(ones that close a loop).\n\n"
            "You may unplug any cable and plug it back in between any two switches. Return the minimum number of "
            "cables to move so every switch can reach every other one, or `-1` if there are not enough cables."
        ),
        "examples": [
            {"args": {"n": 4, "links": [[1, 2], [1, 3], [2, 3]]},
             "explanation": "Switch 4 is alone. The cable [2, 3] closes a loop, so move it to reach switch 4: one move.",
             "why": {"t": "One spare cable", "d": "A loop cable is free to move."}},
            {"args": {"n": 6, "links": [[1, 2], [1, 3], [2, 3], [1, 4]]},
             "explanation": "Six switches need at least five cables; there are only four.",
             "why": {"t": "Not enough cables", "d": "Fewer than n − 1 cables can never connect everyone."}},
        ],
        "constraints": [
            "1 ≤ n ≤ 10⁴",
            "0 ≤ links.length ≤ 10⁴",
            "1 ≤ a, b ≤ n, a ≠ b; the same pair may appear twice",
        ],
        "hints": [
            "Connecting `k` islands takes exactly `k − 1` cables.",
            "With at least `n − 1` cables in total, there are always enough loop cables to spare. Count islands with union-find.",
        ],
        "tests": [
            {"args": {"n": 1, "links": []}, "why": {"t": "Single switch", "d": "One switch is already connected: zero moves."}},
            {"args": {"n": 3, "links": [[1, 2], [2, 3]]}, "why": {"t": "Already a tree", "d": "Everything is connected: zero moves."}},
            {"args": {"n": 3, "links": [[1, 2], [1, 2]]}, "why": {"t": "Duplicate cable", "d": "The second cable between the same switches is spare."}},
            {"args": {"n": 5, "links": [[1, 2], [2, 3], [3, 1], [4, 5]]}, "why": {"t": "Two islands", "d": "One loop cable joins two islands."}},
            {"args": {"n": 2, "links": []}, "why": {"t": "No cables", "d": "Two switches and no cable: impossible."}},
            {"args": {"n": 7, "links": [[1, 2], [2, 3], [3, 1], [1, 3], [4, 5], [5, 4]]}, "why": {"t": "Exactly enough", "d": "n − 1 cables, three islands, three spares."}},
            {"args": {"n": _VN, "links": _VL}, "why": {"t": "Large input", "d": "400 switches, a broken tree plus 70 random extra cables."}},
        ],
        "solutions": [
            {"name": "Union-find (Optimal)",
             "description": "Return −1 if there are fewer than n − 1 cables. Otherwise union every cable's ends and count islands; the answer is islands − 1.",
             "time": "O((n + m) · α(n))", "space": "O(n)",
             "keyPoints": ["Fewer than n − 1 cables is impossible", "Each successful union merges two islands", "Answer = islands − 1"],
             "code": '''def recables_needed(n, links):
    if len(links) < n - 1:
        return -1
    parent = list(range(n + 1))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    islands = n
    for a, b in links:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
            islands -= 1
    return islands - 1
'''},
            {"name": "BFS per island", "slow": True,
             "description": "Build an adjacency list, then flood-fill from every unvisited switch to count islands.",
             "time": "O(n + m)", "space": "O(n + m)",
             "keyPoints": ["Same counting argument", "Needs the whole graph in memory first", "No incremental updates as cables change"],
             "code": '''from collections import deque


def recables_needed(n, links):
    if len(links) < n - 1:
        return -1
    adj = [[] for _ in range(n + 1)]
    for a, b in links:
        adj[a].append(b)
        adj[b].append(a)
    seen = [False] * (n + 1)
    islands = 0
    for s in range(1, n + 1):
        if seen[s]:
            continue
        islands += 1
        seen[s] = True
        q = deque([s])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if not seen[v]:
                    seen[v] = True
                    q.append(v)
    return islands - 1
'''},
        ],
        "starter": '''def recables_needed(n: int, links: list[list[int]]) -> int:
    """Fewest cables to move so all n switches are connected, or -1."""
    raise NotImplementedError
''',
    },
    {
        "key": "first-link-to-connect",
        "title": "When did the sites connect?",
        "approach": "Union-find over links in order · O((n + m) · α(n)) · O(n)",
        "spec": {"kind": "fn", "fn": "first_connecting_link", "params": ["n", "links", "src", "dst"]},
        "statement": (
            "A new WAN is cabled one link at a time. `links[i] = [a, b]` is the `i`-th link brought up, "
            "between routers `a` and `b` (numbered `1` to `n`).\n\n"
            "The change ticket closes as soon as router `src` can reach router `dst`. Return the index of the "
            "first link after which that is true, or `-1` if they are never connected."
        ),
        "examples": [
            {"args": {"n": 5, "links": [[1, 2], [3, 4], [2, 3], [4, 5]], "src": 1, "dst": 4},
             "explanation": "After link 2 ([2, 3]) the path 1-2-3-4 exists.",
             "why": {"t": "Classic", "d": "The connecting link joins two partial paths."}},
            {"args": {"n": 4, "links": [[1, 2], [3, 4]], "src": 1, "dst": 3},
             "explanation": "Two separate pairs never meet.",
             "why": {"t": "Never connected", "d": "The answer is −1 when no link joins the two sides."}},
        ],
        "constraints": [
            "2 ≤ n ≤ 10⁴",
            "0 ≤ links.length ≤ 10⁴",
            "1 ≤ a, b ≤ n, a ≠ b",
            "1 ≤ src, dst ≤ n, src ≠ dst",
        ],
        "hints": [
            "Replay the links in order and keep track of which routers are already joined.",
            "After each union, check whether `src` and `dst` share a root; stop at the first time they do.",
            "Links that close a loop change nothing, but they still use up an index.",
        ],
        "tests": [
            {"args": {"n": 2, "links": [], "src": 1, "dst": 2}, "why": {"t": "No links", "d": "Nothing is cabled yet."}},
            {"args": {"n": 2, "links": [[2, 1]], "src": 1, "dst": 2}, "why": {"t": "Direct link", "d": "The very first link joins them."}},
            {"args": {"n": 4, "links": [[1, 2], [1, 2], [2, 3], [3, 4]], "src": 4, "dst": 1}, "why": {"t": "Duplicate link", "d": "A repeated link still takes an index."}},
            {"args": {"n": 6, "links": [[1, 2], [2, 3], [3, 1], [4, 5], [5, 6], [3, 6]], "src": 1, "dst": 5}, "why": {"t": "Joined at the end", "d": "Two islands grow separately and meet on the last link."}},
            {"args": {"n": 5, "links": [[1, 5], [2, 3], [3, 4], [4, 5], [1, 2]], "src": 1, "dst": 3}, "why": {"t": "Loop afterwards", "d": "The later link [1, 2] would also connect them; the earlier one wins."}},
            {"args": {"n": 5, "links": [[1, 2], [2, 3], [4, 5]], "src": 3, "dst": 5}, "why": {"t": "Isolated target", "d": "The target's island never joins."}},
            {"args": {"n": _VN, "links": _VL, "src": 1, "dst": _VN}, "why": {"t": "Large input", "d": "400 routers and a shuffled order of links."}},
        ],
        "solutions": [
            {"name": "Union-find (Optimal)",
             "description": "Union each link's ends in order and return the first index at which src and dst share a root.",
             "time": "O((n + m) · α(n))", "space": "O(n)",
             "keyPoints": ["One pass, stop early", "Path halving keeps finds short", "Loop links are harmless no-ops"],
             "code": '''def first_connecting_link(n, links, src, dst):
    parent = list(range(n + 1))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, (a, b) in enumerate(links):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
        if find(src) == find(dst):
            return i
    return -1
'''},
            {"name": "BFS after every link", "slow": True,
             "description": "After adding each link, run a BFS from src over the links so far and stop once dst is reached.",
             "time": "O(m · (n + m))", "space": "O(n + m)",
             "keyPoints": ["Recomputes reachability from scratch", "Quadratic in the number of links"],
             "code": '''from collections import deque


def first_connecting_link(n, links, src, dst):
    adj = [[] for _ in range(n + 1)]
    for i, (a, b) in enumerate(links):
        adj[a].append(b)
        adj[b].append(a)
        seen = {src}
        q = deque([src])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        if dst in seen:
            return i
    return -1
'''},
        ],
        "starter": '''def first_connecting_link(n: int, links: list[list[int]], src: int, dst: int) -> int:
    """Index of the first link after which src reaches dst, or -1."""
    raise NotImplementedError
''',
    },
]
