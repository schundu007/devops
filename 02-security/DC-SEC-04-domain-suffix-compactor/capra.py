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
