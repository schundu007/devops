"""Capra Playground export for DC-OS-02 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "common_prefix", "params": ["hosts"], "types": {}, "ret": "value", "cmp": "exact"}

EXAMPLES = [
    {"args": {"hosts": ["us-east-prod-api-01", "us-east-prod-worker-02"]},
     "explanation": "Both start with us-east-prod-; the next character differs (a vs w).",
     "why": {"t": "Two hosts", "d": "A shared naming prefix."}},
    {"args": {"hosts": ["web-01", "api-01", "db-01"]},
     "explanation": "The first characters already differ.",
     "why": {"t": "Nothing shared", "d": "The answer is the empty string."}},
    {"args": {"hosts": ["cache", "cache-01", "cache-02"]},
     "explanation": "The first host is itself a prefix of every other host.",
     "why": {"t": "Prefix host", "d": "A short host that is fully shared."}},
]

_rng = random.Random(14)
_SUFFIXES = ["".join(_rng.choice("abcdefghij0123456789-") for _ in range(12)) for _ in range(400)]
_BIG = ["eu-west-1-prod-k8s-node-" + s for s in _SUFFIXES]

TESTS = [
    {"args": {"hosts": []}, "why": {"t": "Empty list", "d": "No hosts: the empty string."}},
    {"args": {"hosts": ["db-primary-01"]}, "why": {"t": "Single host", "d": "One host is its own prefix."}},
    {"args": {"hosts": ["", "api-01"]}, "why": {"t": "Empty hostname", "d": "An empty name makes the prefix empty."}},
    {"args": {"hosts": ["node-01", "node-01", "node-01"]}, "why": {"t": "Duplicates", "d": "Identical hosts share the whole name."}},
    {"args": {"hosts": ["api-10", "api-1"]}, "why": {"t": "Short second host", "d": "The scan must stop when a later host runs out."}},
    {"args": {"hosts": ["ip-10-0-3-17.ec2.internal", "ip-10-0-3-171.ec2.internal", "ip-10-0-31-5.ec2.internal"]},
     "why": {"t": "EC2 private DNS", "d": "Inventory pattern for fake 10.0.x.x nodes."}},
    {"args": {"hosts": ["a" * 253, "a" * 253]}, "why": {"t": "Max length", "d": "Two 253-character names (the DNS limit)."}},
    {"args": {"hosts": _BIG}, "why": {"t": "Large input", "d": "400 node names with a long shared prefix."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Vertical scan (Optimal)",
     "description": "Walk the columns of the first host; at each column check every other host and stop at the first mismatch or short host.",
     "time": "O(S)", "space": "O(1) extra",
     "keyPoints": ["Empty list gives an empty string", "Stops at the first mismatching column", "The first host can be the whole answer"]},
    {"name": "Shrink a candidate", "slow": True,
     "description": "Start with the first host as the candidate; while some host does not start with it, drop its last character.",
     "time": "O(n · m²)", "space": "O(m)",
     "keyPoints": ["startswith does the comparison", "Rescans the candidate after every trim"],
     "code": '''from __future__ import annotations


def common_prefix(hosts: list[str]) -> str:
    if not hosts:
        return ""
    cand = hosts[0]
    while cand and not all(h.startswith(cand) for h in hosts):
        cand = cand[:-1]
    return cand
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Shrink a candidate", "idea": "Trim the first host until every host starts with it.", "time": "O(n · m²)",
     "space": "O(m)", "use": "Quick to write."},
    {"name": "Vertical scan", "idea": "Compare column by column across all hosts.", "time": "O(S)",
     "space": "O(1)", "use": "The standard answer; stops early."},
    {"name": "Sort, compare first and last", "idea": "After sorting, only the first and last names matter.", "time": "O(n · m log n)",
     "space": "O(n)", "use": "When the list is already sorted."},
]

VARIANT_TITLE = "Common character prefix"
VARIANT_APPROACH = "Vertical scan · O(S) · O(1)"

_ZONE_FAST = '''def common_zone(fqdns: list[str]) -> str:
    if not fqdns:
        return ""
    labels = [f.lower().rstrip(".").split(".")[::-1] for f in fqdns]
    first = labels[0]
    k = 0
    while k < len(first):
        lab = first[k]
        if lab == "" or any(k >= len(other) or other[k] != lab for other in labels[1:]):
            break
        k += 1
    return ".".join(reversed(first[:k]))
'''

_ZONE_SLOW = '''def common_zone(fqdns: list[str]) -> str:
    if not fqdns:
        return ""
    names = [f.lower().rstrip(".") for f in fqdns]
    cand = names[0].split(".")
    while cand:
        zone = ".".join(cand)
        if "" not in cand and all(n == zone or n.endswith("." + zone) for n in names):
            return zone
        cand = cand[1:]
    return ""
'''

_KPRE_FAST = '''def longest_shared_prefix(hosts: list[str], k: int) -> str:
    if k > len(hosts):
        return ""
    s = sorted(hosts)
    best = ""
    for i in range(len(s) - k + 1):
        a, b = s[i], s[i + k - 1]
        j = 0
        m = min(len(a), len(b))
        while j < m and a[j] == b[j]:
            j += 1
        if j > len(best):
            best = a[:j]
    return best
'''

_KPRE_SLOW = '''def longest_shared_prefix(hosts: list[str], k: int) -> str:
    counts: dict[str, int] = {}
    for h in hosts:
        for j in range(len(h) + 1):
            p = h[:j]
            counts[p] = counts.get(p, 0) + 1
    ok = [p for p, c in counts.items() if c >= k]
    if not ok:
        return ""
    return min(ok, key=lambda p: (-len(p), p))
'''

_rz = random.Random(202)
_ZONES = ["svc.prod.us-east-1.example.com", "svc.prod.eu-west-1.example.com"]
_BIG_FQDN = ["node-%d.%s" % (_rz.randint(1, 9999), _ZONES[0]) for _ in range(300)]
_BIG_K = ["%s-%s-%02d" % (_rz.choice(["web", "api", "db", "cache"]), _rz.choice(["use1", "euw1", "aps2"]), _rz.randint(1, 60)) for _ in range(400)]

VARIANTS = [
    {
        "key": "common-dns-zone",
        "title": "Shared DNS zone",
        "approach": "Vertical scan over reversed labels · O(S) · O(L)",
        "spec": {"kind": "fn", "fn": "common_zone", "params": ["fqdns"], "cmp": "exact"},
        "statement": (
            "Before issuing one wildcard certificate or delegating a zone, find the DNS zone every host "
            "shares. Given fully qualified names `fqdns`, return their longest common **suffix made of whole "
            "labels** (labels are separated by `.`).\n\n"
            "- DNS names are case-insensitive: compare in lowercase and return lowercase\n"
            "- A single trailing dot (`example.com.`) is the root and is ignored\n"
            "- Return `\"\"` when nothing is shared or the list is empty\n\n"
            "A partial label never counts: `api.foo.com` and `api.barfoo.com` share only `com`."
        ),
        "examples": [
            {"args": {"fqdns": ["api.us-east.example.com", "db.eu.example.com", "EXAMPLE.com."]},
             "explanation": "All three end with the labels example.com once case and the trailing dot are normalized.",
             "why": {"t": "Mixed case and root dot", "d": "Normalize before comparing."}},
            {"args": {"fqdns": ["api.foo.com", "api.barfoo.com"]},
             "explanation": "The strings share the suffix 'foo.com', but 'foo' is only part of the label 'barfoo'.",
             "why": {"t": "Label boundary", "d": "A character suffix is not a zone."}},
        ],
        "constraints": ["0 ≤ fqdns.length ≤ 500", "each name ≤ 253 characters", "labels are non-empty except for one optional trailing dot"],
        "hints": [
            "Split each name into labels and reverse them: the shared zone becomes a shared prefix of label lists.",
            "Run the vertical scan from the main problem over labels instead of characters.",
        ],
        "tests": [
            {"args": {"fqdns": []}, "why": {"t": "Empty list", "d": "No names: \"\"."}},
            {"args": {"fqdns": ["db.internal.corp"]}, "why": {"t": "Single name", "d": "One name is its own zone."}},
            {"args": {"fqdns": ["a.example.com", "a.example.org"]}, "why": {"t": "Different TLD", "d": "Nothing shared at the top: \"\"."}},
            {"args": {"fqdns": ["example.com", "www.example.com"]}, "why": {"t": "Apex and subdomain", "d": "The apex itself is the shared zone."}},
            {"args": {"fqdns": ["x.k8s.local", "x.k8s.local", "x.k8s.local."]}, "why": {"t": "Duplicates", "d": "Identical names share the whole name."}},
            {"args": {"fqdns": ["ip-10-0-3-17.ec2.internal", "ip-10-0-3-17.EC2.Internal"]}, "why": {"t": "Case only", "d": "Case differences do not matter."}},
            {"args": {"fqdns": _BIG_FQDN + ["lb." + _ZONES[1]]}, "why": {"t": "Large input", "d": "300 nodes in one region, one load balancer in another."}},
        ],
        "solutions": [
            {"name": "Vertical scan on reversed labels (Optimal)",
             "description": "Lowercase, drop the root dot, split into labels and reverse. Walk the first name's labels and stop at the first label any other name lacks.",
             "time": "O(S)", "space": "O(L)",
             "keyPoints": ["Reversing turns a suffix into a prefix", "Compare whole labels, never characters", "Normalize case and the trailing dot first"],
             "code": _ZONE_FAST},
            {"name": "Shrink a candidate zone", "slow": True,
             "description": "Start with the first name and drop its leftmost label until every name equals it or ends with '.' + it.",
             "time": "O(n · m · L)", "space": "O(m)",
             "keyPoints": ["endswith with a leading dot keeps label boundaries", "Rescans every name per trim"],
             "code": _ZONE_SLOW},
        ],
        "starter": "def common_zone(fqdns: list[str]) -> str:\n    pass\n",
    },
    {
        "key": "prefix-shared-by-k",
        "title": "Prefix shared by k hosts",
        "approach": "Sort, compare ends of every k-window · O(n log n · m) · O(n)",
        "spec": {"kind": "fn", "fn": "longest_shared_prefix", "params": ["hosts", "k"], "cmp": "exact"},
        "statement": (
            "An inventory holds hosts from many fleets. To propose a batch selector for a rolling restart of "
            "at least `k` machines, find the **longest prefix shared by at least `k` hosts** (duplicates count "
            "separately).\n\n"
            "If several prefixes of that length qualify, return the lexicographically smallest. If fewer than "
            "`k` hosts exist, return `\"\"`."
        ),
        "examples": [
            {"args": {"hosts": ["web-use1-01", "api-use1-01", "web-use1-02", "web-euw1-01"], "k": 2},
             "explanation": "web-use1-01 and web-use1-02 share 'web-use1-0'; no longer prefix is shared by two hosts.",
             "why": {"t": "Two of four", "d": "Only a subset has to share the prefix."}},
            {"args": {"hosts": ["db-1", "db-2", "db-3", "api-1"], "k": 4},
             "explanation": "k equals the number of hosts: this is the main problem, and nothing is shared.",
             "why": {"t": "k = n", "d": "Reduces to the classic common prefix."}},
        ],
        "constraints": ["0 ≤ hosts.length ≤ 500", "each host ≤ 253 characters", "1 ≤ k"],
        "hints": [
            "After sorting, hosts sharing a prefix sit next to each other.",
            "For k consecutive sorted hosts, their common prefix is the common prefix of the first and last one.",
            "Slide a window of k over the sorted list and keep the longest; scanning in order finds the smallest tie first.",
        ],
        "tests": [
            {"args": {"hosts": [], "k": 1}, "why": {"t": "Empty list", "d": "No hosts: \"\"."}},
            {"args": {"hosts": ["a", "b"], "k": 3}, "why": {"t": "k > n", "d": "Not enough hosts: \"\"."}},
            {"args": {"hosts": ["zeta-01", "beta-01"], "k": 1}, "why": {"t": "k = 1", "d": "The longest host itself; ties go to the smallest."}},
            {"args": {"hosts": ["node-01", "node-01", "node-02"], "k": 2}, "why": {"t": "Duplicates", "d": "Two identical hosts share their whole name."}},
            {"args": {"hosts": ["api-10", "api-11", "web-10", "web-11"], "k": 2}, "why": {"t": "Equal-length tie", "d": "api-1 and web-1 tie; api-1 is smaller."}},
            {"args": {"hosts": ["", "", "x"], "k": 2}, "why": {"t": "Empty hostnames", "d": "Only the empty prefix is shared by two."}},
            {"args": {"hosts": _BIG_K, "k": 7}, "why": {"t": "Large input", "d": "400 fleet names, any 7 sharing a prefix."}},
        ],
        "solutions": [
            {"name": "Sort + window of k (Optimal)",
             "description": "Sort the hosts. For each window of k consecutive hosts, the shared prefix is the common prefix of its first and last host; keep the longest, first one wins ties.",
             "time": "O(n log n · m)", "space": "O(n)",
             "keyPoints": ["Sorting groups hosts by prefix", "Only the window ends need comparing", "Strictly longer updates keep the smallest tie"],
             "code": _KPRE_FAST},
            {"name": "Count every prefix", "slow": True,
             "description": "Count how many hosts start with each possible prefix, then pick the longest (then smallest) with count at least k.",
             "time": "O(S · m)", "space": "O(S · m)",
             "keyPoints": ["A dict of prefix counts is a flattened trie", "Materializes every prefix string"],
             "code": _KPRE_SLOW},
        ],
        "starter": "def longest_shared_prefix(hosts: list[str], k: int) -> str:\n    pass\n",
    },
]
