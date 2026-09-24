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
