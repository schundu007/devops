"""Capra Playground export for DC-SEC-14 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "link_identities", "params": ["accounts"], "types": {}, "ret": "value", "cmp": "exact"}


def case(accounts):
    return {"accounts": accounts}


EXAMPLES = [
    {"args": case([["dana", "dana@corp.example", "dana.k@okta.example"],
                   ["dana", "dana.k@okta.example", "dk@github.example"],
                   ["lee", "lee@corp.example"]]),
     "explanation": "Dana's Okta email appears in two accounts, so they merge into one person with three emails.",
     "why": {"t": "Shared email", "d": "Two accounts linked by one email."}},
    {"args": case([["alex", "alex@a.example"], ["alex", "alex@b.example"]]),
     "explanation": "Same name, no shared email: two different people.",
     "why": {"t": "Same name, different people", "d": "Names never link accounts; only emails do."}},
]


def _large():
    rng = random.Random(14)
    accounts = []
    for i in range(400):
        name = f"user{rng.randint(0, 60)}"
        emails = [f"{name}.{rng.randint(0, 300)}@corp.example" for _ in range(rng.randint(1, 3))]
        accounts.append([name, *emails])
    return case(accounts)


TESTS = [
    {"args": case([["sam", "sam@corp.example"]]), "why": {"t": "Single account", "d": "One account, one email."}},
    {"args": case([["sam", "sam@corp.example", "sam@corp.example"]]), "why": {"t": "Duplicate email", "d": "An email listed twice appears once."}},
    {"args": case([["a", "1@x"], ["a", "2@x"], ["a", "1@x", "3@x"], ["a", "2@x", "3@x"]]),
     "why": {"t": "Chain of links", "d": "Accounts linked only through a chain of other accounts."}},
    {"args": case([["zoe", "z@x"], ["amy", "a@x"], ["amy", "b@x"]]), "why": {"t": "Row order", "d": "Rows sort by name, then first email."}},
    {"args": case([["ops", "ops@okta.example", "ops@aws.example", "ops@github.example"],
                   ["ops", "ops@aws.example"], ["ops", "oncall@corp.example"]]),
     "why": {"t": "Offboarding", "d": "Okta, AWS and GitHub accounts of one person, plus a separate shared mailbox."}},
    {"args": case([["b", "b@x", "a@x"], ["b", "c@x", "b@x"]]), "why": {"t": "Email sort", "d": "Emails inside a row are sorted."}},
    {"args": _large(), "why": {"t": "Large input", "d": "400 accounts with random overlapping emails."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Union-find by email (Optimal)",
     "description": "Union-find keyed by email. For each account, link all its emails to the first one and record each email's name. Group emails by root; each group becomes [name, *sorted emails], and rows are sorted by (name, first email).",
     "time": "O(E · α(E) + E log E)", "space": "O(E)",
     "keyPoints": ["Link emails, not names", "Every email in one account belongs to the same person", "Sort emails, then rows"]},
    {"name": "Merge overlapping sets", "slow": True,
     "description": "Keep a list of (name, email set). For each account, merge every existing set that shares an email with it into one.",
     "time": "O(A² · E)", "space": "O(E)",
     "keyPoints": ["Straightforward", "Quadratic in the number of accounts"],
     "code": '''from __future__ import annotations


def link_identities(accounts: list[list[str]]) -> list[list[str]]:
    people: list[tuple[str, set[str]]] = []
    for name, *emails in accounts:
        merged = set(emails)
        keep = []
        for other_name, other in people:
            if other & merged:
                merged |= other
            else:
                keep.append((other_name, other))
        people = keep + [(name, merged)]
    rows = [[name, *sorted(emails)] for name, emails in people]
    return sorted(rows, key=lambda r: (r[0], r[1]))
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Merge overlapping sets", "idea": "Fold each account into every existing set it overlaps.",
     "time": "O(A² · E)", "space": "O(E)", "use": "A few hundred accounts."},
    {"name": "Union-find", "idea": "Union emails within an account, then group by root.",
     "time": "O(E log E)", "space": "O(E)", "use": "Company-wide identity graphs."},
    {"name": "Graph DFS", "idea": "Emails are nodes; accounts add edges; each component is a person.",
     "time": "O(E log E)", "space": "O(E)", "use": "Same scale; explicit graph."},
]

VARIANT_TITLE = "Accounts linked by email"
VARIANT_APPROACH = "Union-find by email · O(E · α(E) + E log E) · O(E)"


def _big_sessions():
    rng = random.Random(2092)
    n = 150
    sessions = []
    for _ in range(400):
        a, b = rng.sample(range(n), 2)
        sessions.append([a, b, rng.randint(1, 60)])
    return {"n": n, "sessions": sessions, "first": 7}


def _big_links():
    rng = random.Random(684)
    n = 120
    links = [[rng.randrange(v), v] for v in range(1, n)]
    for _ in range(60):
        a, b = rng.sample(range(n), 2)
        links.insert(rng.randrange(len(links) + 1), [a, b])
    return {"n": n, "links": links}


def ls(n, sessions, first, t, d):
    return {"args": {"n": n, "sessions": sessions, "first": first}, "why": {"t": t, "d": d}}


def rl(n, links, t, d):
    return {"args": {"n": n, "links": links}, "why": {"t": t, "d": d}}


VARIANTS = [
    {
        "key": "lateral-movement",
        "title": "Lateral movement through sessions",
        "approach": "Union-find per timestamp with reset · O(S log S + S · α(n)) · O(n)",
        "spec": {"kind": "fn", "fn": "compromised_hosts", "params": ["n", "sessions", "first"], "ret": "value", "cmp": "exact"},
        "statement": """An attacker is spreading between hosts over SSH sessions.

### Input
- `n`: the number of hosts
- `sessions[i] = [a, b, t]`: an SSH session between hosts `a` and `b` at time `t`
- `first`: a host the attacker also reached at time `0`

### Output
- Every compromised host after all sessions, sorted ascending

### Rules
- Host `0` was compromised, and host `first` is compromised at time `0`
- A session between a compromised host and a clean one compromises the clean one, instantly
- Sessions at the **same** time can chain; links only count within one timestamp""",
        "examples": [
            {"args": {"n": 6, "sessions": [[1, 2, 5], [2, 3, 8], [1, 5, 10]], "first": 1},
             "explanation": "Host 1 is compromised at 0. It reaches 2 at 5, 2 reaches 3 at 8, and 1 reaches 5 at 10.",
             "why": {"t": "Spread over time", "d": "Each session passes it on."}},
            {"args": {"n": 4, "sessions": [[3, 1, 3], [1, 2, 2], [0, 3, 3]], "first": 3},
             "explanation": "At 2, session 1–2 has no compromised host. At 3, host 3 reaches 1. Host 2 stays clean: its session came too early.",
             "why": {"t": "Order matters", "d": "A session before a host is compromised passes nothing."}},
        ],
        "constraints": ["2 ≤ n ≤ 10^5", "0 ≤ sessions.length ≤ 10^5", "a ≠ b; 1 ≤ t ≤ 10^5", "1 ≤ first < n"],
        "hints": [
            "Sort sessions by time and handle each timestamp as one batch.",
            "Inside a batch, union both hosts of every session with union-find; host 0's set is the compromised set.",
            "After the batch, reset every host of the batch that is not connected to 0, so an old clean link cannot carry a later compromise.",
        ],
        "tests": [
            ls(2, [], 1, "No sessions", "Only the two starting hosts."),
            ls(3, [[1, 2, 1]], 2, "Already compromised", "Both hosts in the session are already compromised."),
            ls(5, [[1, 2, 4], [2, 3, 4], [3, 4, 4]], 1, "Chain in one second", "Sessions at one time chain instantly."),
            ls(5, [[3, 4, 2], [2, 3, 2], [1, 2, 3]], 1, "Chain too early", "The clean chain happens before host 1 reaches 2."),
            ls(4, [[2, 3, 1], [1, 2, 1], [2, 3, 2]], 1, "Duplicate sessions", "The same pair meets twice."),
            ls(6, [[1, 2, 5], [3, 4, 5], [4, 5, 5], [2, 3, 6]], 1, "Reset clean links", "The 3–4–5 group at 5 must not stay linked after it."),
            ls(8, [[1, 4, 10], [4, 6, 10], [5, 7, 10], [6, 2, 20], [7, 3, 20], [2, 5, 30]], 1, "Incident timeline", "Bastion to app hosts to the database tier."),
            {"args": _big_sessions(), "why": {"t": "Large input", "d": "150 hosts and 400 sessions in 60 timestamps."}},
        ],
        "solutions": [
            {"name": "Union-find per timestamp (Optimal)",
             "description": "Union 0 and first. For each timestamp, union the hosts of its sessions, then reset every host of that batch whose root is not host 0's root.",
             "time": "O(S log S + S · α(n))", "space": "O(n)",
             "keyPoints": ["Links matter only within one timestamp", "Reset the batch's hosts that stayed clean", "Answer: every host connected to 0"],
             "code": '''from itertools import groupby


def compromised_hosts(n, sessions, first):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            if rb == find(0):
                ra, rb = rb, ra
            parent[rb] = ra

    union(0, first)
    for _, batch in groupby(sorted(sessions, key=lambda s: s[2]), key=lambda s: s[2]):
        hosts = set()
        for a, b, _t in batch:
            union(a, b)
            hosts.update((a, b))
        root = find(0)
        for h in hosts:
            if find(h) != root:
                parent[h] = h
    root = find(0)
    return [h for h in range(n) if find(h) == root]
'''},
            {"name": "Spread until stable per timestamp", "slow": True,
             "description": "Keep a set of compromised hosts. For each timestamp, sweep its sessions again and again, compromising the clean side of any mixed session, until a sweep changes nothing.",
             "time": "O(S²) in the worst case", "space": "O(n)",
             "keyPoints": ["Simulates the spread directly", "Repeats sweeps inside a timestamp for chains"],
             "code": '''def compromised_hosts(n, sessions, first):
    bad = {0, first}
    by_time = {}
    for a, b, t in sessions:
        by_time.setdefault(t, []).append((a, b))
    for t in sorted(by_time):
        changed = True
        while changed:
            changed = False
            for a, b in by_time[t]:
                if (a in bad) != (b in bad):
                    bad.update((a, b))
                    changed = True
    return sorted(bad)
'''},
        ],
        "starter": '''def compromised_hosts(n: int, sessions: list[list[int]], first: int) -> list[int]:
    pass
''',
    },
    {
        "key": "redundant-trust",
        "title": "Redundant trust links",
        "approach": "Union-find in input order · O(L · α(n)) · O(n)",
        "spec": {"kind": "fn", "fn": "redundant_links", "params": ["n", "links"], "ret": "value", "cmp": "exact"},
        "statement": """An audit rebuilds the trust graph between accounts, adding the links one by one in the order they were created.

### Input
- `n`: the number of accounts, numbered `0` to `n - 1`
- `links`: each `[a, b]` is a two-way trust relationship, in creation order

### Output
- Every redundant link, in input order

### Rules
- A link is **redundant** if, when it is added, `a` and `b` can already reach each other through earlier links
- A redundant link widens the blast radius without connecting anything new""",
        "examples": [
            {"args": {"n": 4, "links": [[0, 1], [1, 2], [0, 2], [2, 3]]},
             "explanation": "0 and 2 are already joined through 1 when [0, 2] arrives.",
             "why": {"t": "One loop", "d": "The link that closes it is redundant."}},
            {"args": {"n": 3, "links": [[0, 1], [1, 0], [0, 1]]},
             "explanation": "The first link joins 0 and 1; both repeats are redundant.",
             "why": {"t": "Duplicate links", "d": "A repeated pair is always redundant."}},
        ],
        "constraints": ["1 ≤ n ≤ 10^5", "0 ≤ links.length ≤ 2 · 10^5", "0 ≤ a, b < n, a ≠ b"],
        "hints": [
            "Walk the links in order with a union-find over accounts.",
            "If find(a) == find(b), the link is redundant; otherwise union them.",
            "Path halving and union by size keep each call almost constant.",
        ],
        "tests": [
            rl(1, [], "No links", "Nothing to audit."),
            rl(2, [[0, 1]], "Single link", "A first link is never redundant."),
            rl(4, [[0, 1], [2, 3]], "Forest", "Separate groups, nothing redundant."),
            rl(4, [[0, 1], [1, 2], [2, 3], [3, 0], [1, 3]], "Two loops", "Two links close loops in a square."),
            rl(5, [[0, 1], [2, 3], [1, 2], [3, 0], [4, 3], [4, 0]], "Loop through a merge", "Groups merge, then a link closes a loop across them."),
            rl(6, [[0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [5, 1], [4, 2]], "Hub and spokes", "A central admin role plus spoke-to-spoke trust."),
            {"args": _big_links(), "why": {"t": "Large input", "d": "A 120-account tree plus 60 extra links in random order."}},
        ],
        "solutions": [
            {"name": "Union-find in input order (Optimal)",
             "description": "For each link, compare the roots of its ends. Same root: redundant. Otherwise union the smaller set into the larger.",
             "time": "O(L · α(n))", "space": "O(n)",
             "keyPoints": ["Same root means a loop", "Order matters: only earlier links count", "Union by size keeps trees flat"],
             "code": '''def redundant_links(n, links):
    parent = list(range(n))
    size = [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    out = []
    for a, b in links:
        ra, rb = find(a), find(b)
        if ra == rb:
            out.append([a, b])
            continue
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]
    return out
'''},
            {"name": "Search before each link", "slow": True,
             "description": "Keep an adjacency list of accepted links. Before adding a link, run a DFS from a to see whether b is already reachable.",
             "time": "O(L · (n + L))", "space": "O(n + L)",
             "keyPoints": ["Explicit graph search", "One full search per link"],
             "code": '''def redundant_links(n, links):
    adj = [[] for _ in range(n)]
    out = []
    for a, b in links:
        seen, stack = {a}, [a]
        while stack:
            v = stack.pop()
            for u in adj[v]:
                if u not in seen:
                    seen.add(u)
                    stack.append(u)
        if b in seen:
            out.append([a, b])
        else:
            adj[a].append(b)
            adj[b].append(a)
    return out
'''},
        ],
        "starter": '''def redundant_links(n: int, links: list[list[int]]) -> list[list[int]]:
    pass
''',
    },
]
