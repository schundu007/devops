"""Capra Playground export for DC-SEC-13 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "exposed", "params": ["n", "sessions", "first"], "types": {}, "ret": "value", "cmp": "exact"}


def case(n, sessions, first):
    return {"n": n, "sessions": sessions, "first": first}


EXAMPLES = [
    {"args": case(6, [[1, 2, 5], [2, 3, 8], [1, 5, 10]], 1),
     "explanation": "0 and 1 start exposed. At t=5, 1 exposes 2. At t=8, 2 exposes 3. At t=10, 1 exposes 5. Party 4 never connects.",
     "why": {"t": "Spread over time", "d": "Exposure passes along sessions in time order."}},
    {"args": case(4, [[3, 1, 3], [1, 2, 2], [0, 3, 3]], 3),
     "explanation": "At t=2, parties 1 and 2 meet but neither is exposed yet. At t=3, 3 (exposed) meets 1, but 2 is not in that slot.",
     "why": {"t": "Too early", "d": "A session before exposure passes nothing, even if exposure comes later."}},
    {"args": case(5, [[3, 4, 2], [1, 3, 2], [0, 1, 1]], 1),
     "explanation": "Both t=2 sessions happen together: 1 exposes 3, and 3 exposes 4 in the same instant.",
     "why": {"t": "Same-time chain", "d": "Sessions sharing a time form a chain that passes the secret at once."}},
]


def _large():
    rng = random.Random(13)
    n = 400
    sessions = []
    for _ in range(900):
        a, b = rng.sample(range(n), 2)
        sessions.append([a, b, rng.randint(1, 60)])
    return case(n, sessions, 7)


TESTS = [
    {"args": case(2, [], 1), "why": {"t": "No sessions", "d": "Only party 0 and first are exposed."}},
    {"args": case(3, [], 0), "why": {"t": "first is 0", "d": "The first holder can be party 0 itself."}},
    {"args": case(4, [[2, 3, 1], [0, 2, 1]], 1), "why": {"t": "Chain order in one slot", "d": "Session order inside a slot does not matter."}},
    {"args": case(4, [[2, 3, 5], [1, 2, 6]], 1), "why": {"t": "Later exposure does not travel back", "d": "3 met 2 before 2 was exposed."}},
    {"args": case(3, [[1, 2, 4], [1, 2, 4]], 1), "why": {"t": "Duplicate sessions", "d": "The same session listed twice."}},
    {"args": case(5, [[2, 3, 1], [3, 4, 1]], 1), "why": {"t": "Unexposed slot", "d": "A slot with no exposed party passes nothing."}},
    {"args": case(6, [[1, 2, 10], [2, 3, 10], [3, 4, 10], [4, 5, 10]], 1), "why": {"t": "Long same-time chain", "d": "The whole chain is exposed in one instant."}},
    {"args": _large(), "why": {"t": "Large input", "d": "400 parties and 900 sessions over 60 time slots."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Union-find per time slot (Optimal)",
     "description": "Sort sessions by time. For each time slot, union both parties of every session so chains link instantly. Then reset every party in the slot that did not reach party 0, so a later session cannot expose them after the fact. Return everyone connected to 0.",
     "time": "O(m log m + (m + n) · α(n))", "space": "O(n + m)",
     "keyPoints": ["Process one time slot at a time", "Undo unions that did not reach the secret", "Keep 0's root as the root when merging"]},
    {"name": "Sweep each slot until stable", "slow": True,
     "description": "For each time slot, sweep its sessions again and again, exposing a party when it meets an exposed one, until a sweep changes nothing.",
     "time": "O(m²) when every session shares one time", "space": "O(n)",
     "keyPoints": ["No union-find to get wrong", "Slow when many sessions share a time"],
     "code": '''from __future__ import annotations


def exposed(n: int, sessions: list[list[int]], first: int) -> list[int]:
    held = {0, first}
    for t in sorted({s[2] for s in sessions}):
        slot = [s for s in sessions if s[2] == t]
        changed = True
        while changed:
            changed = False
            for a, b, _ in slot:
                if (a in held) != (b in held):
                    held.update((a, b))
                    changed = True
    return sorted(held)
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Sweep each slot until stable", "idea": "Repeat a slot's sessions until no new party is exposed.",
     "time": "O(m²) worst case", "space": "O(n)", "use": "Small incident timelines."},
    {"name": "Union-find per slot", "idea": "Link a slot's sessions, keep what reached party 0, undo the rest.",
     "time": "O(m log m)", "space": "O(n + m)", "use": "Large session logs."},
]

VARIANT_TITLE = "Secret exposure over time"
VARIANT_APPROACH = "Union-find per time slot · O(m log m + (m + n) · α(n)) · O(n + m)"


def _v_sessions(seed, n, m, span):
    rng = random.Random(seed)
    out = []
    for _ in range(m):
        a, b = rng.sample(range(n), 2)
        out.append([a, b, rng.randint(1, span)])
    return out


_MESH = _v_sessions(1101, 150, 700, 400)
_EXPO = _v_sessions(2092, 300, 700, 50)

VARIANTS = [
    {
        "key": "mesh-complete",
        "title": "When did the mesh join up?",
        "approach": "Sort by time + union-find with a component count · O(m log m + m · α(n)) · O(n)",
        "spec": {"kind": "fn", "fn": "mesh_complete_at", "params": ["n", "links"]},
        "statement": (
            "A service mesh rollout records each mTLS trust link as `links[i] = [a, b, t]`: services `a` and `b` "
            "trust each other from time `t` on. Trust is transitive, so services in one connected group share a "
            "trust domain. Links are **not** sorted by time.\n\n"
            "Return the earliest time at which all `n` services (numbered `0` to `n - 1`) are in a single trust "
            "domain, or `-1` if that never happens."
        ),
        "examples": [
            {"args": {"n": 4, "links": [[0, 1, 5], [2, 3, 3], [1, 2, 9], [0, 3, 7]]},
             "explanation": "At t=3: {2,3}. t=5: {0,1}. t=7: [0, 3] joins the two groups, so all four share one domain at 7.",
             "why": {"t": "Out of order", "d": "Links must be replayed in time order."}},
            {"args": {"n": 3, "links": [[0, 1, 2]]},
             "explanation": "Service 2 never joins.",
             "why": {"t": "Never complete", "d": "A service with no links keeps the answer at -1."}},
        ],
        "constraints": [
            "2 ≤ n ≤ 10⁴",
            "0 ≤ links.length ≤ 10⁵, 0 ≤ a, b < n, a ≠ b, 1 ≤ t ≤ 10⁹",
        ],
        "hints": [
            "Sort the links by time and union them in that order.",
            "Keep a count of groups; it starts at `n` and drops by one on every union that merges two groups. Return the time when it hits 1.",
        ],
        "tests": [
            {"args": {"n": 2, "links": []}, "why": {"t": "No links", "d": "Two services, never linked."}},
            {"args": {"n": 2, "links": [[1, 0, 4]]}, "why": {"t": "Minimal", "d": "One link joins both services."}},
            {"args": {"n": 3, "links": [[0, 1, 1], [1, 0, 2], [0, 1, 3], [1, 2, 3]]}, "why": {"t": "Redundant links · same time", "d": "Repeated links and a tie at t=3."}},
            {"args": {"n": 4, "links": [[0, 1, 1], [1, 2, 2], [2, 0, 3], [2, 3, 10]]}, "why": {"t": "Loop before joining", "d": "A loop link at t=3 does not reduce the group count."}},
            {"args": {"n": 5, "links": [[0, 1, 100], [1, 2, 1], [2, 3, 50], [3, 4, 7]]}, "why": {"t": "Last join is late", "d": "The earliest links do not finish the mesh."}},
            {"args": {"n": 150, "links": _MESH}, "why": {"t": "Large input", "d": "150 services and 700 random links."}},
        ],
        "solutions": [
            {"name": "Union-find with a group count (Optimal)",
             "description": "Sort links by time. Union each; when a union merges two groups, decrement the count. Return the time when the count reaches 1.",
             "time": "O(m log m + m · α(n))", "space": "O(n)",
             "keyPoints": ["Sorting fixes the replay order", "Only merging unions change the count", "Stop at the first time the count is 1"],
             "code": '''def mesh_complete_at(n, links):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    groups = n
    for a, b, t in sorted(links, key=lambda l: l[2]):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
            groups -= 1
            if groups == 1:
                return t
    return -1
'''},
            {"name": "BFS at every distinct time", "slow": True,
             "description": "For each distinct time in increasing order, build the graph of links up to that time and check with BFS whether it is connected.",
             "time": "O(T · (n + m))", "space": "O(n + m)",
             "keyPoints": ["Recomputes connectivity from scratch", "Slow when there are many distinct times"],
             "code": '''from collections import deque


def mesh_complete_at(n, links):
    for t in sorted({l[2] for l in links}):
        adj = [[] for _ in range(n)]
        for a, b, lt in links:
            if lt <= t:
                adj[a].append(b)
                adj[b].append(a)
        seen = {0}
        q = deque([0])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        if len(seen) == n:
            return t
    return -1
'''},
        ],
        "starter": '''def mesh_complete_at(n: int, links: list[list[int]]) -> int:
    """Earliest time all n services share one trust domain, or -1."""
    raise NotImplementedError
''',
    },
    {
        "key": "exposure-timeline",
        "title": "Exposure timeline per party",
        "approach": "Union-find per time slot, stamping newly exposed parties · O(m log m + (m + n) · α(n)) · O(n + m)",
        "spec": {"kind": "fn", "fn": "exposure_times", "params": ["n", "sessions", "first"]},
        "statement": (
            "The incident report needs a **timeline**, not just a list. Use the same rules as before: party `0` "
            "and party `first` hold the secret at time 0, `sessions[i] = [a, b, t]` passes it between `a` and "
            "`b` if either holds it, and sessions at the same time `t` happen together, so the secret can pass "
            "along a chain of them in one instant.\n\n"
            "Return a list where entry `p` is the time party `p` first held the secret: `0` for the two initial "
            "holders, and `-1` for parties that never got it. Rotate credentials in that order."
        ),
        "examples": [
            {"args": {"n": 6, "sessions": [[1, 2, 5], [2, 3, 8], [1, 5, 10], [3, 4, 2]], "first": 1},
             "explanation": "2 at t=5, 3 at t=8, 5 at t=10. Party 4 met 3 at t=2, before 3 held it.",
             "why": {"t": "Classic", "d": "Each party is stamped with the slot that exposed it."}},
            {"args": {"n": 5, "sessions": [[3, 4, 2], [1, 3, 2], [0, 1, 1]], "first": 1},
             "explanation": "Both t=2 sessions happen together: 3 and 4 are exposed at 2. The t=1 session is between two holders.",
             "why": {"t": "Same-time chain", "d": "A chain inside one slot stamps everyone with that time."}},
        ],
        "constraints": [
            "2 ≤ n ≤ 10⁵, 0 ≤ sessions.length ≤ 10⁵",
            "sessions[i] = [a, b, t], 0 ≤ a, b < n, a ≠ b, 1 ≤ t ≤ 10⁵",
            "1 ≤ first < n; sessions are not in time order",
        ],
        "hints": [
            "Process one time slot at a time, as in the main problem: union the slot's sessions, then reset parties that did not reach party 0.",
            "Before resetting, stamp every party in the slot that now shares party 0's root and has no time yet.",
        ],
        "tests": [
            {"args": {"n": 2, "sessions": [], "first": 1}, "why": {"t": "No sessions", "d": "Only the initial holders, both at 0."}},
            {"args": {"n": 3, "sessions": [[1, 2, 4], [1, 2, 4]], "first": 1}, "why": {"t": "Duplicate sessions", "d": "The same session twice stamps once."}},
            {"args": {"n": 4, "sessions": [[2, 3, 5], [1, 2, 6], [2, 3, 7]], "first": 1}, "why": {"t": "Exposed later", "d": "3 missed it at 5 but gets it at 7."}},
            {"args": {"n": 5, "sessions": [[2, 3, 1], [3, 4, 1]], "first": 1}, "why": {"t": "Unexposed slot", "d": "A slot with no holder passes nothing: -1."}},
            {"args": {"n": 6, "sessions": [[4, 5, 10], [3, 4, 10], [2, 3, 10], [1, 2, 10]], "first": 1}, "why": {"t": "Long same-time chain", "d": "Everyone on the chain gets the same time."}},
            {"args": {"n": 300, "sessions": _EXPO, "first": 7}, "why": {"t": "Large input", "d": "300 parties and 700 sessions over 50 slots."}},
        ],
        "solutions": [
            {"name": "Union-find per time slot (Optimal)",
             "description": "Sort sessions by time. For each slot, union its sessions, stamp slot parties that reached party 0 and have no time, then reset the rest.",
             "time": "O(m log m + (m + n) · α(n))", "space": "O(n + m)",
             "keyPoints": ["Only parties in the slot can change state", "Stamp before resetting", "Keep party 0's root as the root"],
             "code": '''from itertools import groupby


def exposure_times(n, sessions, first):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            if find(0) == rb:
                ra, rb = rb, ra
            parent[rb] = ra

    when = [-1] * n
    when[0] = when[first] = 0
    union(0, first)
    for t, group in groupby(sorted(sessions, key=lambda s: s[2]), key=lambda s: s[2]):
        group = list(group)
        for a, b, _ in group:
            union(a, b)
        root0 = find(0)
        for a, b, _ in group:
            for p in (a, b):
                if find(p) == root0:
                    if when[p] == -1:
                        when[p] = t
                else:
                    parent[p] = p
    return when
'''},
            {"name": "Sweep each slot until stable", "slow": True,
             "description": "For each time slot, sweep its sessions repeatedly, stamping a party when it meets a holder, until a sweep changes nothing.",
             "time": "O(m²) when every session shares one time", "space": "O(n)",
             "keyPoints": ["No union-find to get wrong", "Slow when many sessions share a time"],
             "code": '''def exposure_times(n, sessions, first):
    when = [-1] * n
    when[0] = when[first] = 0
    for t in sorted({s[2] for s in sessions}):
        slot = [s for s in sessions if s[2] == t]
        changed = True
        while changed:
            changed = False
            for a, b, _ in slot:
                if (when[a] == -1) != (when[b] == -1):
                    if when[a] == -1:
                        when[a] = t
                    else:
                        when[b] = t
                    changed = True
    return when
'''},
        ],
        "starter": '''def exposure_times(n: int, sessions: list[list[int]], first: int) -> list[int]:
    """Time each party first held the secret, 0 for initial holders, -1 for never."""
    raise NotImplementedError
''',
    },
]
