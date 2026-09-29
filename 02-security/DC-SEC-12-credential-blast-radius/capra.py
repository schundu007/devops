"""Capra Playground export for DC-SEC-12 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "blast_radius", "params": ["holds", "leaked"], "types": {}, "ret": "value", "cmp": "exact"}


def case(holds, leaked):
    return {"holds": holds, "leaked": leaked}


EXAMPLES = [
    {"args": case([[1], [2, 3], [], [4], []], 0),
     "explanation": "Resource 0 holds a key for 1; 1 holds keys for 2 and 3; 3 holds a key for 4. Everything is reachable.",
     "why": {"t": "Chain of credentials", "d": "Each takeover exposes the next set of keys."}},
    {"args": case([[1], [], [0]], 1),
     "explanation": "Resource 1 holds no credentials, so the attacker controls only 1.",
     "why": {"t": "Dead end", "d": "A leaked resource that holds nothing."}},
    {"args": case([[1], [2], [0]], 0),
     "explanation": "0 -> 1 -> 2 -> 0 is a cycle; each resource is counted once.",
     "why": {"t": "Cycle", "d": "Credentials that loop back must not loop forever."}},
]


def _large():
    rng = random.Random(12)
    n = 1200
    holds = [sorted(rng.sample(range(n), rng.randint(0, 2))) for _ in range(n)]
    return case(holds, 0)


TESTS = [
    {"args": case([[]], 0), "why": {"t": "Single resource", "d": "One resource, no credentials."}},
    {"args": case([[0]], 0), "why": {"t": "Self-reference", "d": "A resource that holds its own credential."}},
    {"args": case([[1, 1, 1], [], []], 0), "why": {"t": "Duplicate keys", "d": "The same credential listed several times."}},
    {"args": case([[], [0], [1]], 0), "why": {"t": "Edges point the other way", "d": "Others can reach 0, but 0 reaches nothing."}},
    {"args": case([[1], [0], [3], [2]], 2), "why": {"t": "Separate islands", "d": "Only the leaked resource's island is exposed."}},
    {"args": case([[i + 1] for i in range(299)] + [[]], 0), "why": {"t": "Long chain", "d": "300 hops: a recursive DFS would be deep."}},
    {"args": case([[1, 2, 3, 4], [], [], [], []], 0), "why": {"t": "Hub", "d": "One CI runner holds keys to four other systems."}},
    {"args": _large(), "why": {"t": "Large input", "d": "1,200 resources, each holding up to 2 random credentials."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Iterative DFS (Optimal)",
     "description": "Start with the leaked resource on a stack and in a visited set. Pop a resource, and for every credential it holds that is not yet visited, mark it and push it. The visited set is the blast radius.",
     "time": "O(n + E + R log R)", "space": "O(n)",
     "keyPoints": ["Mark on push so each resource is expanded once", "An explicit stack avoids the recursion limit", "Sort only the reachable set"]},
    {"name": "Repeat until nothing changes", "slow": True,
     "description": "Keep a controlled set. Repeatedly add everything each controlled resource holds, until a full pass adds nothing.",
     "time": "O(n · (n + E))", "space": "O(n)",
     "keyPoints": ["Easy to reason about", "Long chains need one pass per hop"],
     "code": '''from __future__ import annotations


def blast_radius(holds: list[list[int]], leaked: int) -> list[int]:
    owned = {leaked}
    while True:
        grown = owned | {x for r in owned for x in holds[r]}
        if grown == owned:
            return sorted(owned)
        owned = grown
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Repeat until stable", "idea": "Grow the controlled set pass by pass until it stops changing.",
     "time": "O(n · (n + E))", "space": "O(n)", "use": "Tiny graphs; obviously correct."},
    {"name": "DFS / BFS", "idea": "Walk the credential graph once from the leaked resource.",
     "time": "O(n + E)", "space": "O(n)", "use": "Real attack-path graphs with millions of edges."},
]

VARIANT_TITLE = "Blast radius from one leak"
VARIANT_APPROACH = "Iterative DFS · O(n + E) · O(n)"


def _tier_large():
    rng = random.Random(1212)
    n = 400
    return case([sorted(rng.sample(range(n), rng.randint(0, 3))) for _ in range(n)], 0)


def _ring_large():
    rng = random.Random(2121)
    n = 200
    return {"holds": [sorted(rng.sample(range(n), rng.randint(0, 2))) for _ in range(n)]}


VARIANTS = [
    {
        "key": "exposure-tiers",
        "title": "Hops to each takeover",
        "approach": "BFS from the leaked resource · O(n + E) · O(n)",
        "spec": {"kind": "fn", "fn": "exposure_tiers", "params": ["holds", "leaked"]},
        "statement": (
            "Incident response rotates credentials in order of urgency: one step away first, then two, and so on.\n"
            "\n"
            "### Input\n"
            "- `holds[i]`: the resources whose credentials sit in resource `i`\n"
            "- `leaked`: the resource the attacker controls\n"
            "\n"
            "### Output\n"
            "- A list `dist` of length `n`: `dist[r]` is the fewest takeovers needed to control `r`\n"
            "- `0` for `leaked`, `-1` if `r` can never be reached"
        ),
        "examples": [
            {"args": case([[1, 2], [3], [3], [], [0]], 0),
             "explanation": "1 and 2 are one hop away, 3 is two hops (through either). 4 holds a key to 0, but nothing reaches 4.",
             "why": {"t": "Tiers", "d": "Shortest hop count, and an unreachable resource."}},
        ],
        "constraints": ["1 ≤ n ≤ 10^5", "Total entries across holds ≤ 3 · 10^5", "Entries may repeat or point to the resource itself"],
        "hints": [
            "Fewest hops in an unweighted graph is breadth-first search.",
            "Set a resource's distance when it is first enqueued; later paths can only be as long or longer.",
        ],
        "tests": [
            {"args": case([[]], 0), "why": {"t": "Single resource", "d": "Only the leaked one: [0]."}},
            {"args": case([[0, 0]], 0), "why": {"t": "Self-reference", "d": "A resource holding its own key."}},
            {"args": case([[1], [2], [0]], 1), "why": {"t": "Cycle from the middle", "d": "Start at 1: 2 is one hop, 0 is two."}},
            {"args": case([[3], [2], [], [1], [1]], 0), "why": {"t": "Deep path", "d": "2 is three hops away through 3 and 1; 4 is unreachable."}},
            {"args": case([[1, 2, 3], [4], [4], [4], []], 0), "why": {"t": "Diamond", "d": "Three paths to 4 all have length 2."}},
            {"args": case([[i + 1] for i in range(149)] + [[]], 0), "why": {"t": "Long chain", "d": "150 hops end to end."}},
            {"args": _tier_large(), "why": {"t": "Large input", "d": "400 resources with up to 3 credentials each."}},
        ],
        "solutions": [
            {"name": "BFS (Optimal)",
             "description": "Queue the leaked resource at distance 0. Pop in FIFO order; every unseen resource it holds gets distance + 1 and joins the queue.",
             "time": "O(n + E)", "space": "O(n)",
             "keyPoints": ["FIFO order means the first visit is the shortest", "-1 marks unseen and unreachable at once", "Each edge is looked at once"],
             "code": '''from collections import deque


def exposure_tiers(holds, leaked):
    dist = [-1] * len(holds)
    dist[leaked] = 0
    q = deque([leaked])
    while q:
        r = q.popleft()
        for x in holds[r]:
            if dist[x] == -1:
                dist[x] = dist[r] + 1
                q.append(x)
    return dist
'''},
            {"name": "Relax until stable", "slow": True,
             "description": "Bellman-Ford style: repeatedly pass over every edge, lowering distances, until a full pass changes nothing.",
             "time": "O(n · E)", "space": "O(n)",
             "keyPoints": ["Works for weighted edges too", "Needs one pass per hop on a long chain"],
             "code": '''def exposure_tiers(holds, leaked):
    inf = float("inf")
    dist = [inf] * len(holds)
    dist[leaked] = 0
    changed = True
    while changed:
        changed = False
        for r, keys in enumerate(holds):
            if dist[r] == inf:
                continue
            for x in keys:
                if dist[r] + 1 < dist[x]:
                    dist[x] = dist[r] + 1
                    changed = True
    return [d if d != inf else -1 for d in dist]
'''},
        ],
        "starter": '''def exposure_tiers(holds: list[list[int]], leaked: int) -> list[int]:
    """Fewest takeovers to reach each resource, -1 if unreachable."""
    raise NotImplementedError
''',
    },
    {
        "key": "credential-rings",
        "title": "Credential rings",
        "approach": "Strongly connected components (Kosaraju, iterative) · O(n + E) · O(n + E)",
        "spec": {"kind": "fn", "fn": "credential_rings", "params": ["holds"]},
        "statement": (
            "Leaking any member of a ring exposes the whole ring, so rings are rotated together.\n"
            "\n"
            "### Input\n"
            "- `holds[i]`: the resources whose credentials sit in resource `i`\n"
            "\n"
            "### Output\n"
            "- Every ring with **at least two** resources, each as a sorted list, ordered by their smallest member\n"
            "\n"
            "### Rules\n"
            "- A **credential ring** is a group of resources where each one can, directly or through others, take over every other one"
        ),
        "examples": [
            {"args": {"holds": [[1], [2], [0, 3], [4], [3], []]},
             "explanation": "0, 1, 2 reach each other in a loop; 3 and 4 hold each other's keys. 5 is alone.",
             "why": {"t": "Two rings", "d": "A three-way loop and a mutual pair."}},
        ],
        "constraints": ["1 ≤ n ≤ 10^5", "Total entries across holds ≤ 3 · 10^5", "Entries may repeat or point to the resource itself"],
        "hints": [
            "A ring is a strongly connected component of the credential graph.",
            "Kosaraju: record DFS finish order, then run DFS on the reversed graph in reverse finish order; each tree is a component.",
            "Use explicit stacks so long chains do not hit the recursion limit.",
        ],
        "tests": [
            {"args": {"holds": [[]]}, "why": {"t": "Single resource", "d": "No ring."}},
            {"args": {"holds": [[0]]}, "why": {"t": "Self-loop only", "d": "One resource is not a ring, even if it holds its own key."}},
            {"args": {"holds": [[1], [2], []]}, "why": {"t": "Chain", "d": "One-way access never forms a ring."}},
            {"args": {"holds": [[1, 1], [0, 0]]}, "why": {"t": "Duplicate keys", "d": "A mutual pair listed twice."}},
            {"args": {"holds": [[1], [2], [0], [2, 4], [3]]}, "why": {"t": "Ring feeding a ring", "d": "3-4 reach 0-1-2, but not back: two rings."}},
            {"args": {"holds": [[i + 1] for i in range(99)] + [[0]]}, "why": {"t": "One big loop", "d": "100 resources in a single cycle."}},
            {"args": _ring_large(), "why": {"t": "Large input", "d": "200 resources with up to 2 random credentials."}},
        ],
        "solutions": [
            {"name": "Kosaraju, iterative (Optimal)",
             "description": "First DFS records finish order. A second DFS on the reversed graph, taking roots in reverse finish order, collects one component per tree. Keep those with two or more members.",
             "time": "O(n + E)", "space": "O(n + E)",
             "keyPoints": ["Finish order guarantees each tree stays inside one component", "Explicit stacks avoid recursion limits", "Filter out single-resource components"],
             "code": '''def credential_rings(holds):
    n = len(holds)
    order = []
    seen = [False] * n
    for s in range(n):
        if seen[s]:
            continue
        seen[s] = True
        stack = [(s, 0)]
        while stack:
            u, i = stack.pop()
            if i < len(holds[u]):
                stack.append((u, i + 1))
                v = holds[u][i]
                if not seen[v]:
                    seen[v] = True
                    stack.append((v, 0))
            else:
                order.append(u)
    rev = [[] for _ in range(n)]
    for u in range(n):
        for v in holds[u]:
            rev[v].append(u)
    comp = [-1] * n
    rings = []
    for s in reversed(order):
        if comp[s] != -1:
            continue
        comp[s] = s
        members = [s]
        stack = [s]
        while stack:
            u = stack.pop()
            for v in rev[u]:
                if comp[v] == -1:
                    comp[v] = s
                    members.append(v)
                    stack.append(v)
        if len(members) > 1:
            rings.append(sorted(members))
    return sorted(rings)
'''},
            {"name": "Reach set from every resource", "slow": True,
             "description": "Compute each resource's reachable set with a DFS. Two resources share a ring when each is in the other's set.",
             "time": "O(n · (n + E))", "space": "O(n²)",
             "keyPoints": ["Direct from the definition", "One traversal per resource"],
             "code": '''def credential_rings(holds):
    n = len(holds)
    reach = []
    for s in range(n):
        seen = {s}
        stack = [s]
        while stack:
            u = stack.pop()
            for v in holds[u]:
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        reach.append(seen)
    placed = [False] * n
    rings = []
    for s in range(n):
        if placed[s]:
            continue
        ring = [t for t in range(n) if t in reach[s] and s in reach[t]]
        for t in ring:
            placed[t] = True
        if len(ring) > 1:
            rings.append(ring)
    return rings
'''},
        ],
        "starter": '''def credential_rings(holds: list[list[int]]) -> list[list[int]]:
    """Every group of 2+ resources that can all take each other over."""
    raise NotImplementedError
''',
    },
]
