"""Capra Playground export for DC-REL-07 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "safe_services", "params": ["waits_on"], "types": {}, "ret": "value", "cmp": "exact"}


def case(waits_on):
    return {"waits_on": waits_on}


EXAMPLES = [
    {"args": case([[1, 2], [2, 3], [5], [0], [5], [], []]),
     "explanation": "0 -> 1 -> 3 -> 0 is a cycle, so 0, 1 and 3 are unsafe. 2 waits on 5, which waits on nothing, so 2 is safe; so are 4, 5 and 6.",
     "why": {"t": "Cycle plus safe chains", "d": "Some services lead into a cycle, others end cleanly."}},
    {"args": case([[1], [0]]),
     "explanation": "The two services wait on each other: neither can ever start.",
     "why": {"t": "Two-service deadlock", "d": "The smallest cycle between services."}},
]


def _large():
    rng = random.Random(802)
    n = 400
    waits_on = []
    for i in range(n):
        k = rng.randint(0, 3)
        waits_on.append(sorted(set(rng.randrange(n) for _ in range(k))))
    return case(waits_on)


TESTS = [
    {"args": case([]), "why": {"t": "No services", "d": "An empty list."}},
    {"args": case([[]]), "why": {"t": "Single service", "d": "One service that waits on nothing is safe."}},
    {"args": case([[0]]), "why": {"t": "Self wait", "d": "A service waiting on itself is a one-node cycle."}},
    {"args": case([[1], [2], [3], []]), "why": {"t": "Chain", "d": "A chain that ends cleanly: all safe."}},
    {"args": case([[1], [2], [0], [0]]), "why": {"t": "Leads into a cycle", "d": "Service 3 is not in the cycle but waits on it."}},
    {"args": case([[], [], []]), "why": {"t": "No waits", "d": "Independent services are all safe."}},
    {"args": case([[1, 2], [3], [3], []]), "why": {"t": "Diamond", "d": "Two paths to the same safe service."}},
    {"args": case([[1], [], [3], [2], [1, 2]]), "why": {"t": "One bad dependency", "d": "Service 4 has a safe dependency and an unsafe one: unsafe."}},
    {"args": case([[2], [0], [], [4], [3], [1]]),
     "why": {"t": "Startup plan", "d": "api -> db -> ok; cache and queue wait on each other."}},
    {"args": _large(), "why": {"t": "Large input", "d": "400 services with random waits."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Reverse graph + topological peel (Optimal)",
     "description": "Count each service's unproven dependencies. Start from services that wait on nothing (safe) and walk the reversed edges: when all of a service's dependencies are safe, it is safe too. Whatever is never reached is in or leads into a cycle.",
     "time": "O(n + E)", "space": "O(n + E)",
     "keyPoints": ["Reverse the edges so safety flows from sinks", "Kahn's peel on the reversed graph", "Unreached services are unsafe"]},
    {"name": "DFS with three colours",
     "description": "Colour each service white (unvisited), grey (on the current path) or black (safe). A DFS that meets a grey service has found a cycle, so every service on the path is unsafe.",
     "time": "O(n + E)", "space": "O(n)",
     "keyPoints": ["Grey means 'on the current path'", "Memoise results so each service is explored once"],
     "code": '''from __future__ import annotations


def safe_services(waits_on: list[list[int]]) -> list[int]:
    n = len(waits_on)
    state = [0] * n   # 0 new, 1 on the current path, 2 safe, 3 unsafe

    def visit(root: int) -> None:
        stack = [(root, 0)]
        state[root] = 1
        while stack:
            s, i = stack.pop()
            deps = waits_on[s]
            if i < len(deps):
                stack.append((s, i + 1))
                d = deps[i]
                if state[d] == 0:
                    state[d] = 1
                    stack.append((d, 0))
                elif state[d] in (1, 3):
                    for t, _ in stack:          # every service on the path is unsafe
                        state[t] = 3
                    stack.clear()
            else:
                state[s] = 2

    for s in range(n):
        if state[s] == 0:
            visit(s)
    for s in range(n):                          # a service that reached an unsafe one is unsafe
        if state[s] == 1:
            state[s] = 3
    changed = True
    while changed:
        changed = False
        for s in range(n):
            if state[s] == 2 and any(state[d] == 3 for d in waits_on[s]):
                state[s] = 3
                changed = True
    return [s for s in range(n) if state[s] == 2]
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Reverse graph + Kahn", "idea": "Peel safe services from the sinks backwards along reversed edges.",
     "time": "O(n + E)", "space": "O(n + E)", "use": "Iterative and easy to prove correct."},
    {"name": "DFS three colours", "idea": "A DFS that reaches a node on its own path has found a cycle.",
     "time": "O(n + E)", "space": "O(n)", "use": "When you already think in DFS; no reverse graph needed."},
]
