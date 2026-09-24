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
    rng = random.Random(11)
    paths = set()
    while len(paths) < 1500:
        depth = rng.randint(1, 5)
        paths.add("/" + "/".join(rng.choice(["logs", "app", "app-old", "apple", "2026", "a", "b"]) for _ in range(depth)))
    return case(sorted(paths, key=lambda _: rng.random()))


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
