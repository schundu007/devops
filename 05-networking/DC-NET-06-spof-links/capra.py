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

VARIANT_TITLE = "Critical links"
VARIANT_APPROACH = "Tarjan's bridges, iterative DFS · O(V + E) · O(V + E)"


def _big(seed, n, extra):
    rng = random.Random(seed)
    links = [[rng.randrange(v), v] for v in range(1, n)]
    for _ in range(extra):
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b:
            links.append([a, b])
    return {"n": n, "links": links}


_ROUTERS_TARJAN = '''from __future__ import annotations


def critical_routers(n: int, links: list[list[int]]) -> list[int]:
    adj = [[] for _ in range(n)]
    for eid, (a, b) in enumerate(links):
        adj[a].append((b, eid))
        adj[b].append((a, eid))
    disc, low, cut = [-1] * n, [0] * n, [False] * n
    timer = 0
    for root in range(n):
        if disc[root] != -1:
            continue
        disc[root] = low[root] = timer
        timer += 1
        children = 0
        stack = [(root, -1, iter(adj[root]))]
        while stack:
            u, parent_link, it = stack[-1]
            descended = False
            for v, eid in it:
                if eid == parent_link:
                    continue
                if disc[v] == -1:
                    disc[v] = low[v] = timer
                    timer += 1
                    stack.append((v, eid, iter(adj[v])))
                    descended = True
                    break
                low[u] = min(low[u], disc[v])
            if descended:
                continue
            stack.pop()
            if stack:
                p = stack[-1][0]
                low[p] = min(low[p], low[u])
                if p == root:
                    children += 1
                elif low[u] >= disc[p]:
                    cut[p] = True
        if children > 1:
            cut[root] = True
    return [v for v in range(n) if cut[v]]
'''

_ROUTERS_REMOVE = '''from __future__ import annotations

from collections import deque


def critical_routers(n: int, links: list[list[int]]) -> list[int]:
    def components(skip):
        adj = [[] for _ in range(n)]
        for a, b in links:
            if a != skip and b != skip:
                adj[a].append(b)
                adj[b].append(a)
        seen, count = [False] * n, 0
        for s in range(n):
            if s == skip or seen[s]:
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
    return [v for v in range(n) if components(v) > base]
'''

_BLAST_TARJAN = '''from __future__ import annotations


def max_isolated(n: int, links: list[list[int]]) -> int:
    adj = [[] for _ in range(n)]
    for eid, (a, b) in enumerate(links):
        adj[a].append((b, eid))
        adj[b].append((a, eid))
    disc, low, size = [-1] * n, [0] * n, [1] * n
    disc[0] = 0
    timer, best = 1, 0
    stack = [(0, -1, iter(adj[0]))]
    while stack:
        u, parent_link, it = stack[-1]
        descended = False
        for v, eid in it:
            if eid == parent_link:
                continue
            if disc[v] == -1:
                disc[v] = low[v] = timer
                timer += 1
                stack.append((v, eid, iter(adj[v])))
                descended = True
                break
            low[u] = min(low[u], disc[v])
        if descended:
            continue
        stack.pop()
        if stack:
            p = stack[-1][0]
            low[p] = min(low[p], low[u])
            size[p] += size[u]
            if low[u] > disc[p]:
                best = max(best, size[u])  # the bridge p-u cuts u's whole subtree off
    return best
'''

_BLAST_REMOVE = '''from __future__ import annotations

from collections import deque


def max_isolated(n: int, links: list[list[int]]) -> int:
    def reach(skip):
        adj = [[] for _ in range(n)]
        for i, (a, b) in enumerate(links):
            if i != skip:
                adj[a].append(b)
                adj[b].append(a)
        seen = [False] * n
        seen[0] = True
        q, count = deque([0]), 1
        while q:
            u = q.popleft()
            for v in adj[u]:
                if not seen[v]:
                    seen[v] = True
                    count += 1
                    q.append(v)
        return count

    base = reach(-1)
    return max((base - reach(i) for i in range(len(links))), default=0)
'''

VARIANTS = [
    {
        "key": "critical-routers",
        "title": "Critical routers",
        "approach": "Tarjan's articulation points, iterative DFS · O(V + E) · O(V + E)",
        "spec": {"kind": "fn", "fn": "critical_routers", "params": ["n", "links"], "cmp": "exact"},
        "statement": "Find every router whose single failure splits the network.\n\n### Input\n- `n`: number of devices, numbered `0..n-1`\n- `links`: the same undirected links as the main problem\n\n### Output\n- The critical devices, in increasing order\n\n### Rules\n- A device is **critical** if, when it reboots or dies, the devices that remain split into more disconnected groups than before\n- A device with no links is never critical\n- Parallel links between the same pair are allowed; there are no self-links",
        "examples": [
            {"args": {"n": 5, "links": [[0, 1], [1, 2], [2, 0], [1, 3], [3, 4]]},
             "explanation": "Removing 1 cuts 3 and 4 off from the ring; removing 3 cuts 4 off. Devices 0, 2 and 4 can fail safely.",
             "why": {"t": "Ring plus chain", "d": "Both ends of a bridge can be critical, but only if something hangs beyond them."}},
            {"args": {"n": 4, "links": [[0, 1], [0, 2], [0, 3]]},
             "explanation": "The hub 0 is the only path between the leaves.",
             "why": {"t": "Hub", "d": "A DFS root is critical only when it has two or more DFS children."}},
        ],
        "constraints": ["1 ≤ n ≤ 10⁴", "0 ≤ links.length ≤ 2 · 10⁴", "links[i] = [a, b] with a ≠ b"],
        "hints": [
            "Run the bridge DFS. For a child u of p, low[u] >= disc[p] means nothing under u can reach above p without p.",
            "The condition is >= for devices (versus > for links): the child may loop back to p itself and still depend on p.",
            "The DFS root has no parent, so it is critical exactly when it has more than one DFS child.",
        ],
        "tests": [
            {"args": {"n": 1, "links": []}, "why": {"t": "Single device", "d": "Nothing to split."}},
            {"args": {"n": 2, "links": [[0, 1]]}, "why": {"t": "Single link", "d": "Removing either end leaves one device: no split, so no critical device."}},
            {"args": {"n": 4, "links": [[0, 1], [1, 2], [2, 3]]}, "why": {"t": "Chain", "d": "Every inner device of a chain is critical; the ends are not."}},
            {"args": {"n": 4, "links": [[0, 1], [1, 2], [2, 3], [3, 0]]}, "why": {"t": "Ring", "d": "A ring survives any single device failure."}},
            {"args": {"n": 5, "links": [[0, 1], [1, 2], [2, 0], [2, 3], [3, 4], [4, 2]]}, "why": {"t": "Bowtie", "d": "Two rings share device 2: it is critical although no link is a bridge."}},
            {"args": {"n": 3, "links": [[0, 1], [0, 1], [1, 2]]}, "why": {"t": "Parallel links", "d": "Doubling 0-1 does not help: device 1 is still the only way to 2."}},
            {"args": {"n": 6, "links": [[0, 1], [1, 2], [4, 5]]}, "why": {"t": "Several components", "d": "Critical devices are found in each component; device 3 is isolated."}},
            {"args": _big(4501, 150, 60), "why": {"t": "Large input", "d": "150 devices: a random tree plus 60 extra links."}},
        ],
        "solutions": [
            {"name": "Tarjan's articulation points (Optimal)",
             "description": "One iterative DFS assigns discovery times and low-links. A non-root device p is critical when some child u has low[u] >= disc[p]; a root is critical when it has two or more DFS children.",
             "time": "O(V + E)", "space": "O(V + E)",
             "keyPoints": [">= for devices, > for links", "Special rule for the DFS root", "Skip only the exact link used to enter, not every link to the parent"],
             "code": _ROUTERS_TARJAN},
            {"name": "Remove each device and recount", "slow": True,
             "description": "Count connected components with every device removed in turn and compare with the full graph. More components means that device held the network together.",
             "time": "O(V · (V + E))", "space": "O(V + E)",
             "keyPoints": ["Obvious to trust", "Quadratic: one BFS per device"],
             "code": _ROUTERS_REMOVE},
        ],
        "starter": '''from __future__ import annotations


def critical_routers(n: int, links: list[list[int]]) -> list[int]:
    """Return, in increasing order, every device whose failure splits the network."""
    # TODO
    raise NotImplementedError
''',
    },
    {
        "key": "blast-radius",
        "title": "Worst single link failure",
        "approach": "Bridge DFS from the core with subtree sizes · O(V + E) · O(V + E)",
        "spec": {"kind": "fn", "fn": "max_isolated", "params": ["n", "links"], "cmp": "exact"},
        "statement": "Capacity planning wants the blast radius of the worst single link failure.\n\n### Input\n- `n`: number of devices, numbered `0..n-1`; device `0` is the **core** (the internet uplink)\n- `links`: undirected links, as in the main problem\n\n### Output\n- The largest number of devices one link failure cuts off from device `0`, or `0` if no link failure cuts anything off\n\n### Rules\n- Every other device needs a path to the core\n- A link's count is the devices that reach device `0` now but would not with that link down\n- Devices that cannot reach the core today do not count",
        "examples": [
            {"args": {"n": 6, "links": [[0, 1], [1, 2], [2, 0], [2, 3], [3, 4], [3, 5]]},
             "explanation": "Link 2-3 is a bridge with devices 3, 4 and 5 behind it. Links 3-4 and 3-5 cut off one device each.",
             "why": {"t": "Biggest subtree wins", "d": "The worst bridge is the one closest to the core with the most behind it."}},
            {"args": {"n": 3, "links": [[0, 1], [1, 2], [2, 0]]},
             "explanation": "A ring: any one link can fail and every device still reaches 0.",
             "why": {"t": "No bridge", "d": "No single failure isolates anything."}},
        ],
        "constraints": ["1 ≤ n ≤ 10⁴", "0 ≤ links.length ≤ 2 · 10⁴", "links[i] = [a, b] with a ≠ b"],
        "hints": [
            "Root the bridge DFS at device 0 and track the size of every DFS subtree as it finishes.",
            "When the tree link p-u is a bridge (low[u] > disc[p]), failing it cuts off exactly size[u] devices.",
            "Components that do not contain 0 are never visited, which is what the problem wants.",
        ],
        "tests": [
            {"args": {"n": 1, "links": []}, "why": {"t": "Core only", "d": "Nothing to cut off."}},
            {"args": {"n": 2, "links": [[0, 1]]}, "why": {"t": "Single link", "d": "Losing the only link isolates one device."}},
            {"args": {"n": 5, "links": [[0, 1], [1, 2], [2, 3], [3, 4]]}, "why": {"t": "Chain", "d": "The link at the core cuts off the whole chain."}},
            {"args": {"n": 3, "links": [[0, 1], [0, 1], [1, 2]]}, "why": {"t": "Parallel links", "d": "The doubled uplink is safe; 1-2 isolates one device."}},
            {"args": {"n": 5, "links": [[0, 1], [2, 3], [3, 4]]}, "why": {"t": "Unreachable part", "d": "Devices 2-4 cannot reach the core today, so they never count."}},
            {"args": {"n": 8, "links": [[0, 1], [0, 2], [1, 3], [3, 4], [4, 1], [2, 5], [5, 6], [6, 7], [7, 2]]}, "why": {"t": "Two protected sites", "d": "Each site is a ring behind one uplink: the bigger site sets the answer."}},
            {"args": _big(4502, 150, 40), "why": {"t": "Large input", "d": "150 devices: a random tree plus 40 extra links."}},
        ],
        "solutions": [
            {"name": "Bridge DFS with subtree sizes (Optimal)",
             "description": "Iterative DFS from device 0 computes disc, low and subtree size. Each tree link p-u with low[u] > disc[p] is a bridge that isolates size[u] devices; keep the maximum.",
             "time": "O(V + E)", "space": "O(V + E)",
             "keyPoints": ["Root the DFS at the core", "A bridge cuts off exactly the subtree below it", "Add a child's size to its parent when the child finishes"],
             "code": _BLAST_TARJAN},
            {"name": "Fail each link and BFS from the core", "slow": True,
             "description": "Count devices reachable from 0, then remove each link in turn, BFS again, and take the largest drop.",
             "time": "O(E · (V + E))", "space": "O(V + E)",
             "keyPoints": ["A direct simulation of each failure", "One BFS per link: too slow for big networks"],
             "code": _BLAST_REMOVE},
        ],
        "starter": '''from __future__ import annotations


def max_isolated(n: int, links: list[list[int]]) -> int:
    """Return the most devices a single link failure can cut off from device 0."""
    # TODO
    raise NotImplementedError
''',
    },
]
