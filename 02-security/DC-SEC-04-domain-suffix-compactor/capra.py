"""Capra Playground export for DC-SEC-04 (see tools/export_capra.py).

Driver kind: the chip has two entry points (compact and encoded_length), and
each case checks both.
"""
import random

SPEC = {"kind": "driver", "fn": "compact", "params": ["hostnames"], "types": {}, "ret": "value", "cmp": "exact"}

DRIVER = '''
def __drive(args):
    names = args["hostnames"]
    return {"kept": compact(list(names)), "encodedLength": encoded_length(list(names))}
'''


def case(names):
    return {"hostnames": names}


EXAMPLES = [
    {"args": case(["api.prod.example.com", "prod.example.com", "example.com"]),
     "explanation": "prod.example.com and example.com are both label-suffixes of api.prod.example.com, so only that name is stored: 20 characters + '#' = 21.",
     "why": {"t": "Nested suffixes", "d": "Each shorter name ends a longer one."}},
    {"args": case(["example.com", "ample.com"]),
     "explanation": "ample.com is a text suffix of example.com, but not a label suffix, so both are kept.",
     "why": {"t": "Label boundary", "d": "Suffixes are compared by whole labels, not characters."}},
]


def _large():
    rng = random.Random(820)
    envs, svcs, zones = ["prod", "stage", "dev"], ["api", "web", "auth", "db", "cache"], ["example.com", "example.net"]
    names = []
    for _ in range(250):
        parts = [rng.choice(svcs), rng.choice(envs), rng.choice(zones)]
        names.append(".".join(parts[rng.randint(0, 2):]))
    return case(names)


TESTS = [
    {"args": case([]), "why": {"t": "Empty", "d": "No hostnames at all."}},
    {"args": case(["example.com"]), "why": {"t": "Single name", "d": "One name is always kept."}},
    {"args": case(["API.Example.com.", "api.example.com", "example.com"]),
     "why": {"t": "Case · Trailing dot · Duplicates", "d": "DNS names are case-insensitive, and a trailing dot only marks the root."}},
    {"args": case(["", "example.com", "."]), "why": {"t": "Empty entries", "d": "Empty names are ignored."}},
    {"args": case(["a.example.com", "b.example.com", "example.com"]),
     "why": {"t": "Siblings", "d": "Two siblings both cover the parent; the parent is dropped."}},
    {"args": case(["example.com", "example.org", "com"]),
     "why": {"t": "Top-level label", "d": "'com' is covered by example.com, but example.org is separate."}},
    {"args": case(["svc-1.ns.svc.cluster.local", "ns.svc.cluster.local", "svc.cluster.local", "cluster.local", "other.local"]),
     "why": {"t": "Kubernetes DNS", "d": "A chain of cluster DNS names collapses to its longest members."}},
    {"args": _large(), "why": {"t": "Large input", "d": "250 random service names across environments and zones."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Reverse trie of labels (Optimal)",
     "description": "Clean and de-duplicate the names, insert each into a trie one label at a time from the right, and keep only names whose final node has no children.",
     "time": "O(total characters + n log n)", "space": "O(total characters)",
     "keyPoints": ["Compare by labels, not characters", "Lowercase and strip the trailing dot first", "A node with children means a longer name passes through it"]},
    {"name": "Pairwise endswith", "slow": True,
     "description": "For each cleaned name, check every other name with endswith('.' + name). Keep names no other name ends with.",
     "time": "O(n² × L)", "space": "O(n)",
     "keyPoints": ["The '.' in endswith enforces the label boundary", "Too slow for tens of thousands of names"],
     "code": '''from __future__ import annotations


def compact(hostnames: list[str]) -> list[str]:
    names = sorted({h.lower().rstrip(".") for h in hostnames if h.lower().rstrip(".")})
    return [n for n in names if not any(o != n and o.endswith("." + n) for o in names)]


def encoded_length(hostnames: list[str]) -> int:
    return sum(len(n) + 1 for n in compact(hostnames))
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Pairwise endswith", "idea": "Check each name against every other with endswith('.' + name).",
     "time": "O(n² × L)", "space": "O(n)", "use": "A short allow-list."},
    {"name": "Reverse trie", "idea": "Insert labels right to left; names ending at a leaf are kept.",
     "time": "O(total characters + n log n)", "space": "O(total characters)", "use": "Large DNS zones or allow-lists."},
]

VARIANT_TITLE = "Domain suffix compactor"
VARIANT_APPROACH = "Reverse trie of labels · O(total characters + n log n) · O(total characters)"


def _v_cert():
    rng = random.Random(4)
    envs, svcs, zones = ["prod", "stage", "dev"], ["api", "web", "auth", "db"], ["example.com", "example.net"]
    patterns = []
    for _ in range(60):
        z = rng.choice(zones)
        form = rng.randint(0, 2)
        if form == 0:
            patterns.append("*." + z)
        elif form == 1:
            patterns.append("*.%s.%s" % (rng.choice(envs), z))
        else:
            patterns.append("%s.%s.%s" % (rng.choice(svcs), rng.choice(envs), z))
    hosts = []
    for _ in range(200):
        parts = [rng.choice(svcs), rng.choice(envs), rng.choice(zones)]
        hosts.append(".".join(parts[rng.randint(0, 2):]))
    return patterns, hosts


def _v_zones():
    rng = random.Random(53)
    labels = ["corp", "eu", "us", "k8s", "svc", "db", "api"]
    zones = ["example.com"] + ["%s.example.com" % l for l in labels[:4]] + ["svc.us.example.com", "internal"]
    queries = []
    for _ in range(250):
        depth = rng.randint(1, 4)
        tail = rng.choice(["example.com", "internal", "example.org"])
        queries.append(".".join([rng.choice(labels) for _ in range(depth)] + [tail]))
    return zones, queries


_VP, _VH = _v_cert()
_VZ, _VQ = _v_zones()

VARIANTS = [
    {
        "key": "wildcard-cert",
        "title": "Does the certificate cover it?",
        "approach": "Reverse trie with wildcard leaves · O(total characters) · O(total characters)",
        "spec": {"kind": "fn", "fn": "covered_hosts", "params": ["patterns", "hosts"]},
        "statement": (
            "A TLS certificate lists Subject Alternative Names in `patterns`: exact names like `api.example.com` "
            "or wildcards like `*.example.com`. A wildcard stands for **exactly one** leftmost label, so "
            "`*.example.com` covers `api.example.com` but not `example.com` or `a.b.example.com`.\n\n"
            "For each name in `hosts`, return whether the certificate covers it. Compare names the DNS way: "
            "lowercase, and ignore a trailing dot."
        ),
        "examples": [
            {"args": {"patterns": ["*.example.com", "example.com"], "hosts": ["api.example.com", "example.com", "a.b.example.com", "API.Example.COM."]},
             "explanation": "The wildcard covers one label only, so a.b.example.com fails. Case and the trailing dot do not matter.",
             "why": {"t": "One label only", "d": "A wildcard never spans two labels."}},
        ],
        "constraints": [
            "0 ≤ patterns.length, hosts.length ≤ 10⁴",
            "A wildcard appears only as the whole leftmost label (`*.rest`)",
            "Each name has at most 253 characters",
        ],
        "hints": [
            "Insert each pattern into a trie keyed by labels from right to left. Mark exact ends, and mark a node when `*.` + that suffix is a pattern.",
            "For a host, walk its labels from the right. It is covered if the full walk hits an exact end, or if the walk after all but the leftmost label hits a wildcard mark.",
        ],
        "tests": [
            {"args": {"patterns": [], "hosts": ["example.com"]}, "why": {"t": "No patterns", "d": "An empty certificate covers nothing."}},
            {"args": {"patterns": ["*.example.com"], "hosts": []}, "why": {"t": "No hosts", "d": "Nothing to check."}},
            {"args": {"patterns": ["*.example.com"], "hosts": ["example.com", "xexample.com", "a.example.com"]}, "why": {"t": "Label boundary", "d": "The apex and a text-only suffix are not covered."}},
            {"args": {"patterns": ["*.prod.example.com", "api.example.com"], "hosts": ["web.prod.example.com", "prod.example.com", "api.example.com", "web.example.com"]}, "why": {"t": "Mixed patterns", "d": "Exact and wildcard names at different depths."}},
            {"args": {"patterns": ["*.Example.com.", "*.example.com"], "hosts": ["db.example.com"]}, "why": {"t": "Duplicates · normalize", "d": "The same pattern twice, in two spellings."}},
            {"args": {"patterns": ["api.example.com"], "hosts": ["*.example.com", "api.example.com.", ""]}, "why": {"t": "Odd hosts", "d": "A literal asterisk host and an empty name are not covered."}},
            {"args": {"patterns": _VP, "hosts": _VH}, "why": {"t": "Large input", "d": "60 patterns and 200 service names."}},
        ],
        "solutions": [
            {"name": "Reverse label trie (Optimal)",
             "description": "Build a trie from right to left over each pattern's labels, flagging exact ends and wildcard parents. Each host is one walk down the trie.",
             "time": "O(total characters)", "space": "O(total characters)",
             "keyPoints": ["Labels, not characters", "Wildcard flag sits on the parent suffix", "Normalize before inserting and looking up"],
             "code": '''def covered_hosts(patterns, hosts):
    def norm(s):
        return s.lower().rstrip(".")

    root = {}
    for p in patterns:
        p = norm(p)
        if not p:
            continue
        labels = p.split(".")
        wild = labels[0] == "*"
        if wild:
            labels = labels[1:]
        node = root
        for label in reversed(labels):
            node = node.setdefault(label, {})
        node["$wild" if wild else "$end"] = True

    out = []
    for h in hosts:
        h = norm(h)
        labels = h.split(".") if h else []
        node = root
        ok = False
        for i in range(len(labels) - 1, -1, -1):
            if i == 0 and node.get("$wild") and labels[0] != "*":
                ok = True
            node = node.get(labels[i])
            if node is None:
                break
        else:
            if labels and node.get("$end"):
                ok = True
        out.append(ok)
    return out
'''},
            {"name": "Match every pattern", "slow": True,
             "description": "For each host, compare against every pattern: equal for exact names, or strip the first label and compare the rest for wildcards.",
             "time": "O(h · p · L)", "space": "O(1)",
             "keyPoints": ["Mirrors the RFC rule directly", "Slow for large SAN lists and many hosts"],
             "code": '''def covered_hosts(patterns, hosts):
    pats = [p.lower().rstrip(".") for p in patterns]
    out = []
    for h in hosts:
        h = h.lower().rstrip(".")
        ok = False
        for p in pats:
            if not p or not h:
                continue
            if p.startswith("*."):
                head, _, rest = h.partition(".")
                if rest and head and head != "*" and rest == p[2:]:
                    ok = True
            elif p == h:
                ok = True
        out.append(ok)
    return out
'''},
        ],
        "starter": '''def covered_hosts(patterns: list[str], hosts: list[str]) -> list[bool]:
    """For each host, whether an exact or one-label wildcard pattern covers it."""
    raise NotImplementedError
''',
    },
    {
        "key": "zone-lookup",
        "title": "Most specific DNS zone",
        "approach": "Reverse label trie, deepest zone on the path · O(total characters) · O(total characters)",
        "spec": {"kind": "fn", "fn": "owning_zone", "params": ["zones", "queries"]},
        "statement": (
            "An internal resolver hosts several zones, some delegated inside others: `example.com`, "
            "`corp.example.com`, `svc.us.example.com`. A query is answered by the **most specific** zone: the "
            "longest zone that equals the name or is a label-suffix of it.\n\n"
            "For each name in `queries`, return that zone, normalized (lowercase, no trailing dot), or `\"\"` if "
            "no zone owns it."
        ),
        "examples": [
            {"args": {"zones": ["example.com", "corp.example.com"], "queries": ["vpn.corp.example.com", "www.example.com", "corp.example.com", "notexample.com"]},
             "explanation": "vpn.corp.example.com goes to the delegated corp zone; www.example.com to the parent; notexample.com shares only characters, not labels.",
             "why": {"t": "Delegation", "d": "The deepest matching zone wins."}},
        ],
        "constraints": [
            "0 ≤ zones.length, queries.length ≤ 10⁴",
            "Each name has at most 253 characters",
        ],
        "hints": [
            "Insert each zone into a trie keyed by labels from right to left, and mark the node where it ends.",
            "Walk each query from its rightmost label and remember the last marked node you passed.",
        ],
        "tests": [
            {"args": {"zones": [], "queries": ["a.example.com"]}, "why": {"t": "No zones", "d": "Nothing owns anything."}},
            {"args": {"zones": ["example.com"], "queries": []}, "why": {"t": "No queries", "d": "Empty answer list."}},
            {"args": {"zones": ["Example.COM."], "queries": ["WWW.example.com", "example.com."]}, "why": {"t": "Normalize", "d": "Case and trailing dots are ignored, and the answer is normalized."}},
            {"args": {"zones": ["com", "example.com", "a.b.example.com"], "queries": ["x.b.example.com", "a.b.example.com", "other.org"]}, "why": {"t": "Gap in the chain", "d": "b.example.com is not a zone, so x.b.example.com falls back to example.com."}},
            {"args": {"zones": ["example.com", "example.com"], "queries": ["ample.com", "example.com"]}, "why": {"t": "Duplicates · label boundary", "d": "A repeated zone, and a text-only suffix."}},
            {"args": {"zones": _VZ, "queries": _VQ}, "why": {"t": "Large input", "d": "Seven zones and 250 random queries."}},
        ],
        "solutions": [
            {"name": "Reverse label trie (Optimal)",
             "description": "Build a trie of zones from right to left. For each query, walk down label by label and keep the deepest zone end seen.",
             "time": "O(total characters)", "space": "O(total characters)",
             "keyPoints": ["Longest-suffix match by labels", "Stop as soon as a label is missing", "Store the normalized zone at its end node"],
             "code": '''def owning_zone(zones, queries):
    root = {}
    for z in zones:
        z = z.lower().rstrip(".")
        if not z:
            continue
        node = root
        for label in reversed(z.split(".")):
            node = node.setdefault(label, {})
        node["$zone"] = z
    out = []
    for q in queries:
        q = q.lower().rstrip(".")
        best = ""
        node = root
        for label in reversed(q.split(".")) if q else []:
            node = node.get(label)
            if node is None:
                break
            best = node.get("$zone", best)
        out.append(best)
    return out
'''},
            {"name": "Check every zone", "slow": True,
             "description": "For each query, test every zone with equality or endswith('.' + zone) and keep the longest match.",
             "time": "O(q · z · L)", "space": "O(z)",
             "keyPoints": ["The '.' keeps the label boundary", "Linear in the number of zones per query"],
             "code": '''def owning_zone(zones, queries):
    zs = [z.lower().rstrip(".") for z in zones]
    out = []
    for q in queries:
        q = q.lower().rstrip(".")
        best = ""
        for z in zs:
            if z and q and (q == z or q.endswith("." + z)) and len(z) > len(best):
                best = z
        out.append(best)
    return out
'''},
        ],
        "starter": '''def owning_zone(zones: list[str], queries: list[str]) -> list[str]:
    """Most specific zone owning each query, or an empty string."""
    raise NotImplementedError
''',
    },
]
