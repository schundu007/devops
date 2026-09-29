"""Capra Playground export for DC-REL-03 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "pipeline_time", "params": ["n", "deps", "duration"], "types": {}, "ret": "value", "cmp": "exact"}


def case(n, deps, duration):
    return {"n": n, "deps": [list(d) for d in deps], "duration": duration}


EXAMPLES = [
    {"args": case(4, [(0, 1), (0, 2), (1, 3), (2, 3)], [2, 5, 3, 1]),
     "explanation": "build (2) fans out to test (5) and lint (3), which both gate deploy (1). The longest chain is build -> test -> deploy = 2 + 5 + 1 = 8.",
     "why": {"t": "Diamond", "d": "Two parallel branches; only the slower one counts."}},
    {"args": case(3, [], [4, 9, 2]),
     "explanation": "No dependencies: all three stages run at once, so the pipeline takes as long as the slowest stage, 9.",
     "why": {"t": "No dependencies", "d": "Everything runs in parallel."}},
]


def _large():
    rng = random.Random(2050)
    n = 300
    deps = set()
    for b in range(1, n):
        for _ in range(rng.randint(1, 3)):
            deps.add((rng.randrange(0, b), b))
    return case(n, sorted(deps), [rng.randint(1, 60) for _ in range(n)])


TESTS = [
    {"args": case(1, [], [7]), "why": {"t": "Single stage", "d": "One stage with no dependencies."}},
    {"args": case(1, [], [0]), "why": {"t": "Zero duration", "d": "A stage that takes no time."}},
    {"args": case(5, [(0, 1), (1, 2), (2, 3), (3, 4)], [1, 2, 3, 4, 5]), "why": {"t": "Straight chain", "d": "No parallelism: the sum of all durations."}},
    {"args": case(4, [(3, 2), (2, 1), (1, 0)], [1, 1, 1, 10]), "why": {"t": "Reversed numbering", "d": "Dependencies point from high to low numbers."}},
    {"args": case(5, [(0, 4), (1, 4), (2, 4), (3, 4)], [3, 8, 1, 8, 2]), "why": {"t": "Fan-in · tie", "d": "Four stages gate one; two share the longest time."}},
    {"args": case(6, [(0, 1), (1, 2), (3, 4), (4, 5)], [1, 1, 1, 5, 5, 5]), "why": {"t": "Two chains", "d": "Two independent pipelines; the longer one decides."}},
    {"args": case(4, [(0, 1), (0, 1), (1, 2)], [2, 2, 2, 1]), "why": {"t": "Duplicate dependency", "d": "The same dependency listed twice."}},
    {"args": case(6, [(0, 2), (1, 2), (2, 3), (2, 4), (3, 5), (4, 5)], [4, 6, 2, 10, 1, 3]),
     "why": {"t": "CI pipeline", "d": "checkout, deps -> build -> integration tests / image scan -> deploy."}},
    {"args": _large(), "why": {"t": "Large input", "d": "300 stages with random dependencies."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Topological sort + DP (Optimal)",
     "description": "Walk stages in Kahn's topological order. A stage starts when its latest dependency finishes; its finish time is start + duration. The pipeline time is the largest finish time.",
     "time": "O(n + E)", "space": "O(n + E)",
     "keyPoints": ["Earliest start = max finish of its dependencies", "Kahn's order guarantees dependencies are done first", "The answer is the critical path length"]},
    {"name": "DFS with memo",
     "description": "finish(s) = duration[s] + the largest finish among the stages s depends on. Memoize it and take the maximum over all stages.",
     "time": "O(n + E)", "space": "O(n + E)",
     "keyPoints": ["Same recurrence, computed top-down", "Deep chains need an explicit stack in production code"],
     "code": '''from __future__ import annotations

from functools import lru_cache


def pipeline_time(n: int, deps: list[tuple[int, int]], duration: list[int]) -> int:
    parents: list[list[int]] = [[] for _ in range(n)]
    for a, b in deps:
        parents[b].append(a)

    @lru_cache(maxsize=None)
    def finish(s: int) -> int:
        return duration[s] + max((finish(p) for p in parents[s]), default=0)

    return max((finish(s) for s in range(n)), default=0)
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Topological order + DP", "idea": "Process stages in Kahn's order, pushing each finish time forward to its children.",
     "time": "O(n + E)", "space": "O(n + E)", "use": "Iterative; no recursion limits on long pipelines."},
    {"name": "DFS with memo", "idea": "Recursively compute each stage's finish time from its parents and cache it.",
     "time": "O(n + E)", "space": "O(n + E)", "use": "Shortest code; fine for moderate depth."},
]

VARIANT_TITLE = "Pipeline critical path"
VARIANT_APPROACH = "Topological sort + DP · O(n + E) · O(n + E)"


def _v_dag(seed, n, cycle=False):
    rng = random.Random(seed)
    deps = set()
    for b in range(1, n):
        for _ in range(rng.randint(0, 2)):
            deps.add((rng.randrange(0, b), b))
    if cycle:
        deps.add((n - 1, n // 2))
        deps.add((n // 2, n - 1))
    return sorted(deps), [rng.randint(1, 40) for _ in range(n)]


_SD, _SDUR = _v_dag(3, 250)
_WD, _ = _v_dag(1136, 250)
_CD, _ = _v_dag(1137, 120, cycle=True)

VARIANTS = [
    {
        "key": "stage-slack",
        "title": "Slack per stage",
        "approach": "Forward and backward pass over a topological order · O(n + E) · O(n + E)",
        "spec": {"kind": "fn", "fn": "stage_slack", "params": ["n", "deps", "duration"]},
        "statement": (
            "The pipeline is slow and the team wants to know **which stages matter**: speeding up a stage with slack does nothing, and only stages on the critical path move the total.\n"
            "\n"
            "### Input\n"
            "- `n`: the number of stages\n"
            "- `deps`: pairs `[a, b]`; `b` waits for `a`\n"
            "- `duration[i]`: minutes stage `i` takes\n"
            "\n"
            "### Output\n"
            "- The slack of every stage, as a list indexed by stage\n"
            "\n"
            "### Rules\n"
            "- Unlimited runners; the dependencies contain no cycles\n"
            "- The pipeline finishes as early as possible\n"
            "- The **slack** of a stage is how many minutes it could start later than its earliest start without delaying the end\n"
            "- Critical stages have slack `0`"
        ),
        "examples": [
            {"args": {"n": 4, "deps": [[0, 1], [0, 2], [1, 3], [2, 3]], "duration": [2, 5, 3, 1]},
             "explanation": "The critical path is 0 -> 1 -> 3 (8 minutes). Lint (stage 2) finishes at 5 but deploy starts at 7, so it has 2 minutes of slack.",
             "why": {"t": "Diamond", "d": "The shorter branch has slack; the longer one does not."}},
        ],
        "constraints": [
            "1 ≤ n ≤ 5 · 10⁴, duration.length = n, 1 ≤ duration[i] ≤ 10⁴",
            "0 ≤ deps.length ≤ 5 · 10⁴, 0 ≤ a, b < n, a ≠ b",
            "The dependency graph has no cycles",
        ],
        "hints": [
            "The forward pass gives each stage's earliest start and the total time `T`.",
            "Walk the same order backwards: a stage's latest finish is the smallest latest start among its children, or `T` if it has none.",
            "Slack = latest start − earliest start.",
        ],
        "tests": [
            {"args": {"n": 1, "deps": [], "duration": [5]}, "why": {"t": "Single stage", "d": "One stage is always critical."}},
            {"args": {"n": 3, "deps": [], "duration": [4, 9, 2]}, "why": {"t": "No dependencies", "d": "Everything but the slowest stage has slack."}},
            {"args": {"n": 4, "deps": [[0, 1], [1, 2], [2, 3]], "duration": [1, 2, 3, 4]}, "why": {"t": "Straight chain", "d": "Every stage is critical."}},
            {"args": {"n": 5, "deps": [[0, 4], [1, 4], [2, 4], [3, 4]], "duration": [3, 8, 1, 8, 2]}, "why": {"t": "Fan-in · tie", "d": "Two stages tie for the longest; both are critical."}},
            {"args": {"n": 4, "deps": [[0, 1], [0, 1], [1, 2]], "duration": [2, 2, 2, 1]}, "why": {"t": "Duplicate dependency · loner", "d": "A repeated edge, and an isolated stage with slack."}},
            {"args": {"n": 6, "deps": [[0, 2], [1, 2], [2, 3], [2, 4], [3, 5], [4, 5]], "duration": [4, 6, 2, 10, 1, 3]}, "why": {"t": "CI pipeline", "d": "checkout, deps, build, tests, scan, deploy."}},
            {"args": {"n": 250, "deps": [list(d) for d in _SD], "duration": _SDUR}, "why": {"t": "Large input", "d": "250 stages with random dependencies."}},
        ],
        "solutions": [
            {"name": "Forward + backward pass (Optimal)",
             "description": "Kahn's order gives earliest starts and the total T. In reverse order, latest finish = min latest start of children (T if none). Slack = latest start − earliest start.",
             "time": "O(n + E)", "space": "O(n + E)",
             "keyPoints": ["Classic critical path method", "Reverse topological order for the backward pass", "Critical stages have zero slack"],
             "code": '''from collections import deque


def stage_slack(n, deps, duration):
    children = [[] for _ in range(n)]
    waiting = [0] * n
    for a, b in deps:
        children[a].append(b)
        waiting[b] += 1
    order = []
    early = [0] * n
    q = deque(i for i in range(n) if waiting[i] == 0)
    while q:
        s = q.popleft()
        order.append(s)
        for c in children[s]:
            early[c] = max(early[c], early[s] + duration[s])
            waiting[c] -= 1
            if waiting[c] == 0:
                q.append(c)
    total = max((early[s] + duration[s] for s in range(n)), default=0)
    late = [0] * n
    for s in reversed(order):
        finish = min((late[c] for c in children[s]), default=total)
        late[s] = finish - duration[s]
    return [late[s] - early[s] for s in range(n)]
'''},
            {"name": "Relax until stable", "slow": True,
             "description": "Repeat passes over all edges, raising earliest starts, until nothing changes; then repeat passes lowering latest starts the same way.",
             "time": "O(n · E)", "space": "O(n)",
             "keyPoints": ["No topological sort needed", "Bellman-Ford style: up to n passes"],
             "code": '''def stage_slack(n, deps, duration):
    early = [0] * n
    changed = True
    while changed:
        changed = False
        for a, b in deps:
            if early[a] + duration[a] > early[b]:
                early[b] = early[a] + duration[a]
                changed = True
    total = max(early[s] + duration[s] for s in range(n))
    late = [total - duration[s] for s in range(n)]
    changed = True
    while changed:
        changed = False
        for a, b in deps:
            if late[b] - duration[a] < late[a]:
                late[a] = late[b] - duration[a]
                changed = True
    return [late[s] - early[s] for s in range(n)]
'''},
        ],
        "starter": '''def stage_slack(n: int, deps: list[list[int]], duration: list[int]) -> list[int]:
    """Minutes each stage could slip without delaying the pipeline."""
    raise NotImplementedError
''',
    },
    {
        "key": "deploy-waves",
        "title": "Deploy waves with cycle check",
        "approach": "Kahn's algorithm by levels · O(n + E) · O(n + E)",
        "spec": {"kind": "fn", "fn": "deploy_waves", "params": ["n", "deps"]},
        "statement": (
            "A release train deploys services in **waves**; find how many waves it needs.\n"
            "\n"
            "### Input\n"
            "- `n`: the number of services\n"
            "- `deps[i] = [a, b]`: service `b` depends on service `a`\n"
            "\n"
            "### Output\n"
            "- The minimum number of waves needed to ship everything\n"
            "- `-1` if the dependencies contain a **cycle**\n"
            "\n"
            "### Rules\n"
            "- A wave deploys, all at once, every service whose dependencies have already shipped in earlier waves\n"
            "- The dependency file is hand-edited, so it may contain a cycle; then the release can never finish"
        ),
        "examples": [
            {"args": {"n": 4, "deps": [[0, 1], [0, 2], [1, 3], [2, 3]]},
             "explanation": "Wave 1: service 0. Wave 2: services 1 and 2. Wave 3: service 3.",
             "why": {"t": "Diamond", "d": "Parallel services share a wave."}},
            {"args": {"n": 3, "deps": [[0, 1], [1, 2], [2, 1]]},
             "explanation": "Services 1 and 2 wait on each other, so neither can ever ship.",
             "why": {"t": "Cycle", "d": "A cycle makes the release impossible."}},
        ],
        "constraints": [
            "1 ≤ n ≤ 5 · 10⁴",
            "0 ≤ deps.length ≤ 5 · 10⁴, 0 ≤ a, b < n, a ≠ b",
            "The same dependency may be listed twice",
        ],
        "hints": [
            "Wave 1 is every service with no dependencies. Removing it frees the next wave.",
            "Process Kahn's queue one level at a time and count levels. If fewer than `n` services were shipped, there is a cycle.",
        ],
        "tests": [
            {"args": {"n": 1, "deps": []}, "why": {"t": "Single service", "d": "One wave."}},
            {"args": {"n": 5, "deps": []}, "why": {"t": "No dependencies", "d": "Everything ships in one wave."}},
            {"args": {"n": 4, "deps": [[3, 2], [2, 1], [1, 0]]}, "why": {"t": "Chain", "d": "A chain of four takes four waves."}},
            {"args": {"n": 2, "deps": [[0, 1], [1, 0]]}, "why": {"t": "Two-service cycle", "d": "Mutual dependency: -1."}},
            {"args": {"n": 4, "deps": [[0, 1], [0, 1], [1, 2]]}, "why": {"t": "Duplicate dependency", "d": "A repeated edge must not block a service forever."}},
            {"args": {"n": 5, "deps": [[0, 1], [1, 2], [2, 3], [3, 1], [0, 4]]}, "why": {"t": "Cycle downstream", "d": "Some services ship, but the cycle blocks the rest."}},
            {"args": {"n": 250, "deps": [list(d) for d in _WD]}, "why": {"t": "Large input", "d": "250 services with random dependencies."}},
            {"args": {"n": 120, "deps": [list(d) for d in _CD]}, "why": {"t": "Large with a cycle", "d": "120 services with one hidden cycle."}},
        ],
        "solutions": [
            {"name": "Kahn's algorithm by levels (Optimal)",
             "description": "Count in-degrees, start with every service that has none, and process the queue level by level. Each level is a wave; if not every service was processed, return -1.",
             "time": "O(n + E)", "space": "O(n + E)",
             "keyPoints": ["Level-by-level BFS counts waves", "Duplicate edges are counted in both in-degree and decrements", "Processed < n means a cycle"],
             "code": '''def deploy_waves(n, deps):
    children = [[] for _ in range(n)]
    waiting = [0] * n
    for a, b in deps:
        children[a].append(b)
        waiting[b] += 1
    wave = [i for i in range(n) if waiting[i] == 0]
    shipped = 0
    waves = 0
    while wave:
        waves += 1
        shipped += len(wave)
        nxt = []
        for s in wave:
            for c in children[s]:
                waiting[c] -= 1
                if waiting[c] == 0:
                    nxt.append(c)
        wave = nxt
    return waves if shipped == n else -1
'''},
            {"name": "Simulate each wave", "slow": True,
             "description": "Each round, scan every unshipped service and ship those whose dependencies are all shipped. Stop when a round ships nothing.",
             "time": "O(n · (n + E))", "space": "O(n + E)",
             "keyPoints": ["Mirrors the release train literally", "Rescans everything each wave"],
             "code": '''def deploy_waves(n, deps):
    parents = [[] for _ in range(n)]
    for a, b in deps:
        parents[b].append(a)
    shipped = [False] * n
    done = 0
    waves = 0
    while done < n:
        ready = [s for s in range(n) if not shipped[s] and all(shipped[p] for p in parents[s])]
        if not ready:
            return -1
        for s in ready:
            shipped[s] = True
        done += len(ready)
        waves += 1
    return waves
'''},
        ],
        "starter": '''def deploy_waves(n: int, deps: list[list[int]]) -> int:
    """Fewest deploy waves to ship all services, or -1 on a dependency cycle."""
    raise NotImplementedError
''',
    },
]
