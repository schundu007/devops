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
    {"name": "DFS with three colors",
     "description": "Color each service white (unvisited), grey (on the current path) or black (safe). A DFS that meets a grey service has found a cycle, so every service on the path is unsafe.",
     "time": "O(n + E)", "space": "O(n)",
     "keyPoints": ["Grey means 'on the current path'", "Memoize results so each service is explored once"],
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
    {"name": "DFS three colors", "idea": "A DFS that reaches a node on its own path has found a cycle.",
     "time": "O(n + E)", "space": "O(n)", "use": "When you already think in DFS; no reverse graph needed."},
]

VARIANT_TITLE = "Safe services"
VARIANT_APPROACH = "Reverse graph + topological peel · O(n + E) · O(n + E)"


def _waves_large():
    rng = random.Random(2050)
    n = 300
    waits_on = []
    for i in range(n):
        deps = set(rng.randrange(i) for _ in range(rng.randint(0, 3))) if i else set()
        waits_on.append(sorted(deps))
    waits_on[10].append(250)
    waits_on[250].append(10)
    return {"waits_on": waits_on}


def _named_large():
    rng = random.Random(1203)
    names = [f"svc-{i:03d}" for i in range(150)]
    deps = []
    for i in range(1, 150):
        for _ in range(rng.randint(1, 2)):
            deps.append([names[i], names[rng.randrange(i)]])
    deps += [[names[40], names[90]], [names[90], names[40]], [names[3], names[3]]]
    return {"deps": deps}


VARIANTS = [
    {
        "key": "startup-waves",
        "title": "Startup waves",
        "approach": "Level-by-level Kahn peel · O(n + E) · O(n + E)",
        "spec": {"kind": "fn", "fn": "startup_waves", "params": ["waits_on"], "cmp": "exact"},
        "statement": (
            "The rollout controller starts services in **waves**: wave 0 is every service that waits on nothing; "
            "wave `k` is every service whose dependencies all started in earlier waves (and at least one in wave `k - 1`).\n\n"
            "Using the same `waits_on` lists as the main problem, return the waves in order, each sorted ascending. "
            "Services in or behind a cycle never start and appear in no wave. No services gives `[]`.\n\n"
            "This is the same peel as finding safe services, but it keeps track of the layer each service joins."
        ),
        "examples": [
            {"args": {"waits_on": [[], [0], [0], [1, 2], [4]]},
             "explanation": "0 starts first, then 1 and 2, then 3. Service 4 waits on itself and never starts.",
             "why": {"t": "Layers", "d": "A diamond gives three waves; a self wait gives none."}},
        ],
        "constraints": ["0 ≤ n ≤ 10^4", "Total waits ≤ 4 · 10^4", "Entries of waits_on[i] are distinct and may include i"],
        "hints": [
            "Count each service's unstarted dependencies and reverse the edges, as in the main problem.",
            "Process the ready queue one whole level at a time: everything ready now is one wave.",
            "Sort each wave before adding it to the answer.",
        ],
        "tests": [
            {"args": {"waits_on": []}, "why": {"t": "No services", "d": "No waves at all."}},
            {"args": {"waits_on": [[], [], []]}, "why": {"t": "All independent", "d": "One wave with everything."}},
            {"args": {"waits_on": [[1], [0]]}, "why": {"t": "Only a cycle", "d": "Nothing can start: []."}},
            {"args": {"waits_on": [[1], [2], [3], []]}, "why": {"t": "Chain", "d": "A chain of four gives four waves of one."}},
            {"args": {"waits_on": [[], [0], [0, 1], [2, 4], [3]]}, "why": {"t": "Behind a cycle", "d": "3 and 4 wait on each other; 0, 1, 2 still start."}},
            {"args": {"waits_on": [[3], [], [1], []]}, "why": {"t": "Later index first", "d": "Wave order is by readiness, not by index."}},
            {"args": _waves_large(), "why": {"t": "Large input", "d": "300 services with random earlier dependencies and one planted cycle."}},
        ],
        "solutions": [
            {"name": "Level-by-level peel (Optimal)",
             "description": "Kahn's algorithm on the reversed graph, draining the ready list one level at a time so each level becomes a wave.",
             "time": "O(n + E + n log n)", "space": "O(n + E)",
             "keyPoints": ["Pending counts as in the main problem", "Everything ready at the same time is one wave", "Cycles simply never become ready"],
             "code": '''def startup_waves(waits_on):
    n = len(waits_on)
    pending = [len(d) for d in waits_on]
    waited_by = [[] for _ in range(n)]
    for s, deps in enumerate(waits_on):
        for d in deps:
            waited_by[d].append(s)
    wave = [s for s in range(n) if pending[s] == 0]
    out = []
    while wave:
        out.append(sorted(wave))
        nxt = []
        for d in wave:
            for s in waited_by[d]:
                pending[s] -= 1
                if pending[s] == 0:
                    nxt.append(s)
        wave = nxt
    return out
'''},
            {"name": "Repeated passes", "slow": True,
             "description": "Each round, scan every unstarted service and start the ones whose dependencies all started in earlier rounds.",
             "time": "O(n · (n + E))", "space": "O(n)",
             "keyPoints": ["Mirrors how an operator would reason", "A long chain needs n full scans"],
             "code": '''def startup_waves(waits_on):
    n = len(waits_on)
    started = [False] * n
    out = []
    while True:
        wave = [s for s in range(n) if not started[s] and all(started[d] for d in waits_on[s])]
        if not wave:
            return out
        for s in wave:
            started[s] = True
        out.append(wave)
'''},
        ],
        "starter": '''def startup_waves(waits_on: list[list[int]]) -> list[list[int]]:
    pass
''',
    },
    {
        "key": "named-deadlock-report",
        "title": "Stuck services by name",
        "approach": "Reverse-edge peel over names · O(V + E + V log V) · O(V + E)",
        "spec": {"kind": "fn", "fn": "stuck_services", "params": ["deps"], "cmp": "exact"},
        "statement": (
            "A Compose or Helm chart lists dependencies by name: `deps[i] = [service, dependency]` means `service` "
            "waits for `dependency`. Pairs may repeat, and a service may appear only as a dependency.\n\n"
            "Return the names of every service that can **never** start, because it is in a cycle or waits "
            "(directly or indirectly) on one. Sort the names ascending; return `[]` if every service can start.\n\n"
            "This is the complement of the main problem's safe set, over names instead of indices."
        ),
        "examples": [
            {"args": {"deps": [["api", "db"], ["api", "cache"], ["cache", "queue"], ["queue", "cache"], ["web", "api"]]},
             "explanation": "cache and queue wait on each other; api waits on cache and web on api. db is fine.",
             "why": {"t": "Blocked behind a cycle", "d": "Services upstream of the cycle are stuck too."}},
        ],
        "constraints": ["0 ≤ len(deps) ≤ 4 · 10^4", "Names are non-empty strings of up to 40 characters",
                        "Pairs may repeat; [a, a] is a self wait"],
        "hints": [
            "Map names to their distinct dependency sets first, so a repeated pair is counted once.",
            "Peel from services with no dependencies along reversed edges; whatever is never peeled is stuck.",
        ],
        "tests": [
            {"args": {"deps": []}, "why": {"t": "No dependencies", "d": "Nothing listed: []."}},
            {"args": {"deps": [["worker", "worker"]]}, "why": {"t": "Self wait", "d": "A service waiting on itself is stuck."}},
            {"args": {"deps": [["api", "db"], ["api", "db"], ["web", "api"]]}, "why": {"t": "Repeated pair", "d": "A duplicate pair must not block api forever."}},
            {"args": {"deps": [["a", "b"], ["b", "c"], ["c", "a"], ["d", "e"]]}, "why": {"t": "Cycle plus clean chain", "d": "Only the three-cycle is stuck."}},
            {"args": {"deps": [["x", "ok"], ["x", "bad"], ["bad", "bad"], ["y", "ok"]]}, "why": {"t": "One bad dependency", "d": "x has a fine dependency and a stuck one: stuck."}},
            {"args": _named_large(), "why": {"t": "Large input", "d": "150 named services, a two-service cycle and a self wait."}},
        ],
        "solutions": [
            {"name": "Reverse-edge peel (Optimal)",
             "description": "Build the distinct dependency set for every name, count pending dependencies, and peel from services that wait on nothing along reversed edges. Unpeeled names are stuck.",
             "time": "O(V + E + V log V)", "space": "O(V + E)",
             "keyPoints": ["De-duplicate pairs before counting", "Names seen only as dependencies wait on nothing", "Stuck = never peeled"],
             "code": '''from collections import deque


def stuck_services(deps):
    waits = {}
    for s, d in deps:
        waits.setdefault(s, set()).add(d)
        waits.setdefault(d, set())
    pending = {s: len(ds) for s, ds in waits.items()}
    waited_by = {s: [] for s in waits}
    for s, ds in waits.items():
        for d in ds:
            waited_by[d].append(s)
    q = deque(s for s in waits if pending[s] == 0)
    ok = set()
    while q:
        d = q.popleft()
        ok.add(d)
        for s in waited_by[d]:
            pending[s] -= 1
            if pending[s] == 0:
                q.append(s)
    return sorted(s for s in waits if s not in ok)
'''},
            {"name": "Repeated passes", "slow": True,
             "description": "Keep marking services as able to start when every dependency already can, until a full pass changes nothing.",
             "time": "O(V · (V + E))", "space": "O(V + E)",
             "keyPoints": ["No reverse graph needed", "A long chain needs one pass per service"],
             "code": '''def stuck_services(deps):
    waits = {}
    for s, d in deps:
        waits.setdefault(s, set()).add(d)
        waits.setdefault(d, set())
    ok = set()
    changed = True
    while changed:
        changed = False
        for s, ds in waits.items():
            if s not in ok and ds <= ok:
                ok.add(s)
                changed = True
    return sorted(s for s in waits if s not in ok)
'''},
        ],
        "starter": '''def stuck_services(deps: list[list[str]]) -> list[str]:
    pass
''',
    },
]
