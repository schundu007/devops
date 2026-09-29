"""Capra Playground export for DC-SEC-11 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "remove_covered", "params": ["grants"], "types": {}, "ret": "value", "cmp": "exact"}


def case(grants):
    return {"grants": grants}


EXAMPLES = [
    {"args": case(["/logs/app", "/logs/app/2026", "/logs/apple", "/metrics"]),
     "explanation": "/logs/app covers /logs/app/2026. /logs/apple only shares text, not a path segment, so it stays.",
     "why": {"t": "Segment boundary", "d": "A prefix only counts when followed by /."}},
    {"args": case(["/logs/app/2026/01", "/logs/app-old", "/logs/app", "/logs/app/2026"]),
     "explanation": "/logs/app covers both deeper grants; /logs/app-old is a different path.",
     "why": {"t": "The sort trap", "d": "'-' sorts before '/', so a plain text sort would separate parent and child."}},
]


def _large():
    # A list, not a set: iterating a set of strings depends on PYTHONHASHSEED.
    rng = random.Random(11)
    seen, paths = set(), []
    while len(paths) < 1500:
        depth = rng.randint(1, 5)
        p = "/" + "/".join(rng.choice(["logs", "app", "app-old", "apple", "2026", "a", "b"]) for _ in range(depth))
        if p not in seen:
            seen.add(p)
            paths.append(p)
    rng.shuffle(paths)
    return case(paths)


TESTS = [
    {"args": case([]), "why": {"t": "Empty", "d": "No grants in, none out."}},
    {"args": case(["/"]), "why": {"t": "Root only", "d": "A single grant is never covered."}},
    {"args": case(["/a", "/a/b", "/a/b/c", "/a/b/c/d"]), "why": {"t": "Deep chain", "d": "Only the top of the chain survives."}},
    {"args": case(["/b", "/a", "/c"]), "why": {"t": "Siblings", "d": "Unrelated grants all stay, sorted."}},
    {"args": case(["/a/b", "/a"]), "why": {"t": "Child listed first", "d": "Input order does not matter."}},
    {"args": case(["/a/b", "/a/c", "/a/b/x", "/a/c/y", "/a/cd"]), "why": {"t": "Two parents", "d": "Each parent removes only its own children."}},
    {"args": case(["/data/s3-bucket", "/data/s3", "/data/s3/raw"]), "why": {"t": "Hyphen sibling", "d": "/data/s3 covers /data/s3/raw but not /data/s3-bucket."}},
    {"args": _large(), "why": {"t": "Large input", "d": "1,500 random grants up to 5 segments deep."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Segment sort + one pass (Optimal)",
     "description": "Sort paths by their list of segments so every parent sits directly before its children. Walk the list and skip any path that starts with the last kept grant plus '/'.",
     "time": "O(n · L · log n)", "space": "O(n · L)",
     "keyPoints": ["Sort by segments, not raw text", "Compare against the last kept grant only", "The trailing '/' prevents /logs/app covering /logs/apple"]},
    {"name": "Compare every pair", "slow": True,
     "description": "For each path, check every other path to see whether it is a parent (other + '/' is a prefix).",
     "time": "O(n² · L)", "space": "O(n)",
     "keyPoints": ["No sorting trap to get wrong", "Quadratic: slow for large policy sets"],
     "code": '''from __future__ import annotations


def remove_covered(grants: list[str]) -> list[str]:
    return sorted(
        p for p in grants
        if not any(q != p and p.startswith(q + "/") for q in grants)
    )
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Compare every pair", "idea": "Check each grant against every other as a possible parent.",
     "time": "O(n² · L)", "space": "O(n)", "use": "Small policies; simplest to trust."},
    {"name": "Segment sort + one pass", "idea": "Sort by segments so parents precede children, then one scan.",
     "time": "O(n · L · log n)", "space": "O(n · L)", "use": "Large policy sets."},
    {"name": "Trie of segments", "idea": "Insert every path into a segment trie; keep paths with no grant above them.",
     "time": "O(n · L)", "space": "O(n · L)", "use": "When grants are added incrementally."},
]

VARIANT_TITLE = "Redundant grant cleaner"
VARIANT_APPROACH = "Segment sort + one pass · O(n · L · log n) · O(n · L)"


def _rules_large():
    rng = random.Random(1111)
    words = ["logs", "app", "app-old", "secret", "2026", "a"]
    rules, paths = [], []
    for _ in range(300):
        p = "/" + "/".join(rng.choice(words) for _ in range(rng.randint(1, 4)))
        rules.append([rng.choice(["allow", "allow", "deny"]), p])
    for _ in range(600):
        paths.append("/" + "/".join(rng.choice(words) for _ in range(rng.randint(1, 6))))
    return {"rules": rules, "paths": paths}


def _cidr_large():
    rng = random.Random(1112)
    blocks = []
    for _ in range(800):
        length = rng.choice([8, 12, 16, 20, 24, 28, 32])
        ip = [10, rng.choice([0, 1, 2]), rng.randrange(0, 256, 16), rng.randrange(256)]
        blocks.append(".".join(map(str, ip)) + f"/{length}")
    return {"blocks": blocks}


_DECIDE_TRIE = '''from __future__ import annotations


def decide(rules: list[list[str]], paths: list[str]) -> list[str]:
    root: dict = {}
    for effect, prefix in rules:
        node = root
        for seg in prefix.split("/"):
            if seg:
                node = node.setdefault(seg, {})
        if node.get("") != "deny":
            node[""] = effect  # "" never names a segment, so it holds the rule
    out = []
    for path in paths:
        node, decision = root, root.get("", "deny")
        for seg in path.split("/"):
            if not seg:
                continue
            node = node.get(seg)
            if node is None:
                break
            decision = node.get("", decision)
        out.append(decision)
    return out
'''

_DECIDE_SCAN = '''from __future__ import annotations


def decide(rules: list[list[str]], paths: list[str]) -> list[str]:
    def segs(p):
        return [s for s in p.split("/") if s]

    out = []
    for path in paths:
        target = segs(path)
        best_len, decision = -1, "deny"
        for effect, prefix in rules:
            pre = segs(prefix)
            if target[:len(pre)] != pre:
                continue
            if len(pre) > best_len:
                best_len, decision = len(pre), effect
            elif len(pre) == best_len and effect == "deny":
                decision = "deny"
        out.append(decision)
    return out
'''

_CIDR_SORT = '''from __future__ import annotations


def remove_covered_cidrs(blocks: list[str]) -> list[str]:
    parsed = set()
    for b in blocks:
        ip, length = b.split("/")
        a, b2, c, d = (int(x) for x in ip.split("."))
        n, addr = int(length), (a << 24) | (b2 << 16) | (c << 8) | d
        mask = (0xFFFFFFFF << (32 - n)) & 0xFFFFFFFF
        parsed.add((addr & mask, n))
    kept = []
    last_end = -1
    for net, n in sorted(parsed):  # a parent sorts right before its children
        if net <= last_end:
            continue
        kept.append((net, n))
        last_end = net + (1 << (32 - n)) - 1
    return [f"{net >> 24}.{(net >> 16) & 255}.{(net >> 8) & 255}.{net & 255}/{n}" for net, n in kept]
'''

_CIDR_PAIRS = '''from __future__ import annotations

import ipaddress


def remove_covered_cidrs(blocks: list[str]) -> list[str]:
    nets = sorted({ipaddress.ip_network(b, strict=False) for b in blocks},
                  key=lambda x: (int(x.network_address), x.prefixlen))
    kept = [x for x in nets if not any(y != x and x.subnet_of(y) for y in nets)]
    return [str(x) for x in kept]
'''

VARIANTS = [
    {
        "key": "allow-deny-rules",
        "title": "Most specific allow or deny",
        "approach": "Segment trie, deepest rule wins · O(total segments) · O(rule segments)",
        "spec": {"kind": "fn", "fn": "decide", "params": ["rules", "paths"], "cmp": "exact"},
        "statement": "A storage policy is a list of rules `rules[i] = [effect, prefix]`, where `effect` is `\"allow\"` or `\"deny\"` and `prefix` is an absolute path. A rule **matches** a path when the prefix covers it by whole segments: `/logs` matches `/logs` and `/logs/app`, but not `/logs-old`. The prefix `/` matches everything.\n\nFor each requested path return the decision of the **most specific** matching rule, the one with the most segments:\n\n- if an allow and a deny rule tie on the same prefix, **deny** wins\n- if no rule matches, the answer is **deny** (default deny)\n\nThis is the same parent/child relation as the grant cleaner, asked for one path at a time.",
        "examples": [
            {"args": {"rules": [["allow", "/logs"], ["deny", "/logs/secret"], ["allow", "/logs/secret/public"]],
                      "paths": ["/logs/app", "/logs/secret/keys", "/logs/secret/public/readme", "/metrics"]},
             "explanation": "/logs/app only matches /logs. /logs/secret/keys hits the deeper deny. The allow under it is deeper still. /metrics matches nothing, so it is denied.",
             "why": {"t": "Deepest rule wins", "d": "Allow, deny, allow again, and the default deny."}},
            {"args": {"rules": [["allow", "/logs/app"]], "paths": ["/logs/apple", "/logs/app", "/logs"]},
             "explanation": "/logs/apple only shares text with /logs/app, and /logs sits above the rule.",
             "why": {"t": "Segment boundary", "d": "A prefix must end on a / boundary."}},
        ],
        "constraints": ["0 ≤ rules.length ≤ 10³", "0 ≤ paths.length ≤ 10³", "Paths are absolute, with no empty, . or .. segments", "Each path has at most 10 segments"],
        "hints": [
            "Split every prefix into segments and insert it into a trie of segments; mark the node with its effect.",
            "Walk each requested path down the trie, remembering the last effect you passed. That is the deepest match.",
            "Resolve the tie while inserting: once a node is marked deny, an allow on the same prefix must not overwrite it.",
        ],
        "tests": [
            {"args": {"rules": [], "paths": ["/a", "/"]}, "why": {"t": "No rules", "d": "Default deny applies to every path."}},
            {"args": {"rules": [["allow", "/"]], "paths": ["/", "/x/y/z"]}, "why": {"t": "Root rule", "d": "The / prefix matches everything, itself included."}},
            {"args": {"rules": [["allow", "/data"], ["deny", "/data"]], "paths": ["/data/x"]}, "why": {"t": "Tie on one prefix", "d": "Allow and deny on the same prefix: deny wins."}},
            {"args": {"rules": [["deny", "/data"], ["allow", "/data"], ["allow", "/data"]], "paths": ["/data"]}, "why": {"t": "Duplicate rules", "d": "Rule order does not matter and repeats change nothing."}},
            {"args": {"rules": [["allow", "/a"]], "paths": []}, "why": {"t": "No requests", "d": "No paths in, no decisions out."}},
            {"args": {"rules": [["deny", "/"], ["allow", "/s3/bucket-a"], ["allow", "/s3/bucket"]], "paths": ["/s3/bucket-a/k", "/s3/bucket/k", "/s3/bucket-b", "/s3"]},
             "why": {"t": "Hyphen sibling", "d": "bucket-a and bucket are different segments; everything else falls to the root deny."}},
            {"args": _rules_large(), "why": {"t": "Large input", "d": "300 rules and 600 requests over a small vocabulary."}},
        ],
        "solutions": [
            {"name": "Segment trie (Optimal)",
             "description": "Insert each rule's segments into a trie and store its effect on the last node, keeping deny on a tie. For a request, walk the trie along its segments and keep the last effect seen.",
             "time": "O(total segments)", "space": "O(rule segments)",
             "keyPoints": ["Segments, not characters, so /logs never matches /logs-old", "The last effect on the walk is the deepest match", "Deny is sticky on a tied prefix"],
             "code": _DECIDE_TRIE},
            {"name": "Check every rule", "slow": True,
             "description": "For each request, test every rule's segments against the path's and keep the longest match, preferring deny on a tie.",
             "time": "O(p · r · L)", "space": "O(L)",
             "keyPoints": ["Direct reading of the policy", "Every request rescans every rule"],
             "code": _DECIDE_SCAN},
        ],
        "starter": '''from __future__ import annotations


def decide(rules: list[list[str]], paths: list[str]) -> list[str]:
    """Return "allow" or "deny" for each path: the most specific matching rule wins."""
    # TODO
    raise NotImplementedError
''',
    },
    {
        "key": "covered-cidrs",
        "title": "Redundant CIDR blocks",
        "approach": "Sort by (network, prefix length) + one pass · O(n log n) · O(n)",
        "spec": {"kind": "fn", "fn": "remove_covered_cidrs", "params": ["blocks"], "cmp": "exact"},
        "statement": "A firewall allow list holds IPv4 blocks in CIDR form, like `10.1.0.0/16`. A block is **redundant** when another block in the list already contains every address it covers, for example `10.1.2.0/24` inside `10.1.0.0/16`.\n\n- A block may be written with host bits set (`10.1.2.3/16`); it means the network `10.1.0.0/16`\n- Identical blocks count once\n\nReturn the blocks that remain, in canonical form (`network/length`), sorted by network address and then prefix length. This is the grant cleaner on bits instead of path segments.",
        "examples": [
            {"args": {"blocks": ["10.1.2.0/24", "10.1.0.0/16", "10.2.0.0/16", "10.1.255.255/32"]},
             "explanation": "Both 10.1.2.0/24 and 10.1.255.255/32 sit inside 10.1.0.0/16. 10.2.0.0/16 is a separate network.",
             "why": {"t": "Nested blocks", "d": "Smaller blocks inside a bigger one disappear."}},
            {"args": {"blocks": ["192.168.1.77/24", "192.168.1.0/24", "192.168.0.0/24"]},
             "explanation": "192.168.1.77/24 is the network 192.168.1.0/24, a duplicate. 192.168.0.0/24 is its neighbor, not its parent.",
             "why": {"t": "Host bits · Neighbors", "d": "Normalize before comparing; adjacent blocks do not cover each other."}},
        ],
        "constraints": ["0 ≤ blocks.length ≤ 10⁴", "Each block is a valid IPv4 address and a length from 0 to 32"],
        "hints": [
            "Turn each block into (network as a 32-bit integer, length), masking off the host bits.",
            "Sort by network, then by length: a containing block sorts right before everything inside it.",
            "Two CIDR blocks either nest or do not overlap, so comparing with the last kept block's range is enough.",
        ],
        "tests": [
            {"args": {"blocks": []}, "why": {"t": "Empty", "d": "No blocks in, none out."}},
            {"args": {"blocks": ["0.0.0.0/0", "8.8.8.8/32", "10.0.0.0/8"]}, "why": {"t": "Default route", "d": "0.0.0.0/0 covers every address."}},
            {"args": {"blocks": ["172.16.0.0/12", "172.16.0.0/12", "172.31.255.0/24"]}, "why": {"t": "Duplicates", "d": "The repeated /12 counts once and covers the /24 at its far end."}},
            {"args": {"blocks": ["10.0.0.0/25", "10.0.0.128/25"]}, "why": {"t": "Two halves", "d": "Two adjacent halves stay: neither covers the other."}},
            {"args": {"blocks": ["10.0.0.5/32", "10.0.0.4/30", "10.0.0.0/29", "10.0.0.8/29"]}, "why": {"t": "Deep chain", "d": "A /32 in a /30 in a /29; the second /29 is separate."}},
            {"args": {"blocks": ["255.255.255.255/32", "255.255.255.254/31"]}, "why": {"t": "Top of the range", "d": "The last address in the space, inside a /31."}},
            {"args": _cidr_large(), "why": {"t": "Large input", "d": "800 random blocks inside 10.0.0.0/14."}},
        ],
        "solutions": [
            {"name": "Sort + last kept range (Optimal)",
             "description": "Parse every block to (network, length) with the host bits masked off, deduplicate, and sort. Walk the list and skip a block whose network falls inside the last kept block's address range.",
             "time": "O(n log n)", "space": "O(n)",
             "keyPoints": ["Mask host bits first so equal networks compare equal", "(network, length) order puts the parent first", "CIDR blocks nest or are disjoint, so one range check is enough"],
             "code": _CIDR_SORT},
            {"name": "Compare every pair", "slow": True,
             "description": "Build ipaddress networks, and keep a block only when no other block in the list is a supernet of it.",
             "time": "O(n²)", "space": "O(n)",
             "keyPoints": ["The standard library does the bit math", "Quadratic in the size of the allow list"],
             "code": _CIDR_PAIRS},
        ],
        "starter": '''from __future__ import annotations


def remove_covered_cidrs(blocks: list[str]) -> list[str]:
    """Return the blocks no other block contains, canonical and sorted."""
    # TODO
    raise NotImplementedError
''',
    },
]
