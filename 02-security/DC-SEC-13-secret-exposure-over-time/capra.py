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
