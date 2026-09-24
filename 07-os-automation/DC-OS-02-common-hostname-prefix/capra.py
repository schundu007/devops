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
