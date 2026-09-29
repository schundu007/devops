"""Capra Playground export for DC-REL-04 (see tools/export_capra.py).

Many orders can be correct, so a driver calls release_order and checks the
result: it returns "valid" for a correct order, "impossible" for an empty list,
or a short reason the order is wrong.
"""
import random

SPEC = {"kind": "driver", "fn": "release_order", "params": ["n", "m", "service", "before"], "types": {}, "ret": "value", "cmp": "exact"}

DRIVER = '''
def __drive(args):
    n, m, service, before = args["n"], args["m"], args["service"], args["before"]
    order = release_order(n, m, list(service), [list(b) for b in before])
    if not isinstance(order, list):
        return "not a list: %r" % (order,)
    if n > 0 and order == []:
        return "impossible"
    if sorted(order) != list(range(n)):
        return "every step 0..n-1 must appear exactly once"
    pos = {s: i for i, s in enumerate(order)}
    for i in range(n):
        for p in before[i]:
            if pos[p] >= pos[i]:
                return "step %d must come before step %d" % (p, i)
    for g in set(x for x in service if x != -1):
        idx = sorted(pos[s] for s in range(n) if service[s] == g)
        if idx[-1] - idx[0] + 1 != len(idx):
            return "service %d's steps are not contiguous" % g
    return "valid"
'''


def case(n, m, service, before):
    return {"n": n, "m": m, "service": service, "before": before}


EXAMPLES = [
    {"args": case(8, 2, [-1, -1, 1, 0, 0, 1, 0, -1], [[], [6], [5], [6], [3, 6], [], [], []]),
     "explanation": "One valid order is [6, 3, 4, 1, 5, 2, 0, 7]: service 0's steps (3, 4, 6) and service 1's steps (2, 5) each form one block, and every before-rule holds. Any order that passes those checks is accepted.",
     "why": {"t": "Mixed services", "d": "Grouped and ungrouped steps with cross-service rules."}},
    {"args": case(8, 2, [-1, -1, 1, 0, 0, 1, 0, -1], [[], [6], [5], [6], [3], [], [4], []]),
     "explanation": "Step 4 must precede step 6 and step 6 must precede step 3 (all service 0), yet step 3 must precede step 4: a cycle. No order exists, so return [].",
     "why": {"t": "Impossible", "d": "A cycle inside one service."}},
]


def _large():
    rng = random.Random(1203)
    n, m = 150, 12
    service = [rng.randrange(-1, m) for _ in range(n)]
    # Rules only point from a lower "rank" to a higher one, so an order exists:
    # rank services, then steps inside each service.
    rank = {g: r for r, g in enumerate(rng.sample(range(-1, m), m + 1))}
    key = lambda s: (rank[service[s]], s)
    ranked = sorted(range(n), key=key)
    before = [[] for _ in range(n)]
    for _ in range(300):
        i, j = sorted(rng.sample(range(n), 2))   # rules only point forward in the ranking
        a, b = ranked[i], ranked[j]
        if a not in before[b]:
            before[b].append(a)
    return case(n, m, service, before)


TESTS = [
    {"args": case(0, 0, [], []), "why": {"t": "Empty release", "d": "No steps: the empty order is valid."}},
    {"args": case(1, 1, [0], [[]]), "why": {"t": "Single step", "d": "One step in one service."}},
    {"args": case(1, 0, [-1], [[]]), "why": {"t": "Single ungrouped step", "d": "One step with no service."}},
    {"args": case(3, 0, [-1, -1, -1], [[], [0], [1]]), "why": {"t": "No services", "d": "Plain topological order."}},
    {"args": case(4, 2, [0, 1, 0, 1], [[], [0], [1], [2]]), "why": {"t": "Services interleave", "d": "0 -> 1 -> 2 -> 3 forces service 0 and 1 to alternate: impossible."}},
    {"args": case(2, 1, [0, 0], [[1], [0]]), "why": {"t": "Cycle", "d": "Two steps that each wait on the other."}},
    {"args": case(5, 2, [0, 0, 1, 1, -1], [[], [0], [1], [2], [3]]), "why": {"t": "Chain across services", "d": "A strict chain that keeps each service contiguous."}},
    {"args": case(6, 3, [0, 0, 1, 1, 2, 2], [[], [0], [1], [2], [3], [4]]),
     "why": {"t": "Release train", "d": "db migration steps -> api steps -> frontend steps."}},
    {"args": case(3, 2, [0, 1, 0], [[], [], []]), "why": {"t": "No rules", "d": "Only the grouping constraint applies."}},
    {"args": _large(), "why": {"t": "Large input", "d": "150 steps in 12 services with about 300 rules that allow an order."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Two-level topological sort (Optimal)",
     "description": "Give each ungrouped step its own group. Topologically sort the steps and, separately, the groups (a cross-group rule orders the groups). Bucket the sorted steps by group, then output the buckets in group order.",
     "time": "O(n + m + E)", "space": "O(n + m + E)",
     "keyPoints": ["Ungrouped steps become singleton groups", "A cross-service rule adds a group edge", "Either sort finding a cycle means no order exists"]},
    {"name": "Repeated scans for ready work", "slow": True,
     "description": "Same two-level plan without queues: repeatedly scan all groups for one whose incoming rules are satisfied, then inside it repeatedly scan its steps for one whose earlier steps are placed.",
     "time": "O((n + g)² + E · (n + g))", "space": "O(n + E)",
     "keyPoints": ["Pick groups first, then steps inside the chosen group", "A full scan that finds nothing ready means a cycle"],
     "code": '''from __future__ import annotations


def release_order(n: int, m: int, service: list[int], before: list[list[int]]) -> list[int]:
    group = list(service)
    g = m
    for i in range(n):
        if group[i] == -1:
            group[i] = g
            g += 1
    members = [[] for _ in range(g)]
    for i in range(n):
        members[group[i]].append(i)
    group_deps = [set() for _ in range(g)]
    for i in range(n):
        for p in before[i]:
            if group[p] != group[i]:
                group_deps[group[i]].add(group[p])
    done_groups, placed, order = set(), set(), []
    while len(done_groups) < g:
        ready = next((x for x in range(g) if x not in done_groups and group_deps[x] <= done_groups), None)
        if ready is None:
            return []
        todo = list(members[ready])
        while todo:
            step = next((s for s in todo if all(p in placed for p in before[s])), None)
            if step is None:
                return []
            todo.remove(step)
            placed.add(step)
            order.append(step)
        done_groups.add(ready)
    return order
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Brute force", "idea": "Try every permutation and keep the first that obeys all rules and keeps services contiguous.",
     "time": "O(n! · n)", "space": "O(n)", "use": "Only for checking tiny cases."},
    {"name": "Two-level topological sort", "idea": "Sort services, sort steps, then emit each service's steps as one block in service order.",
     "time": "O(n + m + E)", "space": "O(n + m + E)", "use": "The real answer: linear time."},
]

VARIANT_TITLE = "Grouped release order"
VARIANT_APPROACH = "Two-level topological sort · O(n + m + E) · O(n + m + E)"


def _dag(seed, n, edges):
    rng = random.Random(seed)
    perm = rng.sample(range(n), n)
    before = [[] for _ in range(n)]
    for _ in range(edges):
        i, j = sorted(rng.sample(range(n), 2))
        a, b = perm[i], perm[j]
        if a not in before[b]:
            before[b].append(a)
    return before, rng


_WAVE_BEFORE, _ = _dag(2050, 200, 350)
_TIME_BEFORE, _trng = _dag(1136, 200, 400)
_TIME_DUR = [_trng.randint(1, 30) for _ in range(200)]

VARIANTS = [
    {
        "key": "deploy-waves",
        "title": "Parallel deploy waves",
        "approach": "Kahn's algorithm by levels · O(n + E + n log n) · O(n + E)",
        "spec": {"kind": "fn", "fn": "deploy_waves", "params": ["n", "before"], "ret": "value", "cmp": "exact"},
        "statement": """The release tool runs steps in **waves**: every step whose earlier steps have all finished starts in the next wave, all at once. `before[i]` lists the steps that must finish before step `i`.

Return the waves as lists of step numbers, each sorted ascending, in the order they run. If the rules contain a cycle, no step in it can ever start: return `[]`. For `n = 0` return `[]` as well.

This is the topological sort from the main problem processed level by level: a wave is exactly the set of steps whose in-degree reached zero in the previous round.""",
        "examples": [
            {"args": {"n": 5, "before": [[], [0], [0], [1, 2], []]},
             "explanation": "Steps 0 and 4 need nothing; 1 and 2 wait for 0; 3 waits for both.",
             "why": {"t": "Diamond", "d": "Two parallel steps between a start and a join."}},
            {"args": {"n": 3, "before": [[2], [0], [1]]},
             "explanation": "0 waits for 2, 2 for 1, 1 for 0: nothing can start.",
             "why": {"t": "Cycle", "d": "A cycle returns []."}},
        ],
        "constraints": ["0 ≤ n ≤ 10^4", "Entries of before[i] are distinct, in 0..n-1, never i", "Total rules ≤ 5 · 10^4"],
        "hints": [
            "Compute in-degrees. The first wave is every step with in-degree 0.",
            "Process a whole wave, decrementing the in-degree of each step it unblocks; steps that reach 0 form the next wave.",
            "If fewer than n steps were placed, there is a cycle.",
        ],
        "tests": [
            {"args": {"n": 0, "before": []}, "why": {"t": "Empty release", "d": "No steps, no waves."}},
            {"args": {"n": 1, "before": [[]]}, "why": {"t": "Single step", "d": "One wave of one step."}},
            {"args": {"n": 4, "before": [[], [], [], []]}, "why": {"t": "No rules", "d": "Everything runs in one wave."}},
            {"args": {"n": 4, "before": [[], [0], [1], [2]]}, "why": {"t": "Chain", "d": "One step per wave."}},
            {"args": {"n": 4, "before": [[], [0], [3], [2]]}, "why": {"t": "Partial cycle", "d": "Some steps could run, but a cycle blocks the rest: []."}},
            {"args": {"n": 6, "before": [[], [], [0, 1], [0], [2, 3], [4]]}, "why": {"t": "Release train", "d": "Migrations, then API, then canary and full rollout."}},
            {"args": {"n": 200, "before": _WAVE_BEFORE}, "why": {"t": "Large input", "d": "200 steps and about 350 random rules without a cycle."}},
        ],
        "solutions": [
            {"name": "Kahn's algorithm by levels (Optimal)",
             "description": "Build successor lists and in-degrees. Start with every step of in-degree 0 as wave one; each wave unblocks the next.",
             "time": "O(n + E + n log n)", "space": "O(n + E)",
             "keyPoints": ["One wave = one level of Kahn's algorithm", "Sort each wave for a stable output", "Count placed steps to detect a cycle"],
             "code": '''def deploy_waves(n, before):
    succ = [[] for _ in range(n)]
    indeg = [0] * n
    for i in range(n):
        for p in before[i]:
            succ[p].append(i)
            indeg[i] += 1
    wave = sorted(i for i in range(n) if indeg[i] == 0)
    waves, placed = [], 0
    while wave:
        waves.append(wave)
        placed += len(wave)
        nxt = []
        for v in wave:
            for w in succ[v]:
                indeg[w] -= 1
                if indeg[w] == 0:
                    nxt.append(w)
        wave = sorted(nxt)
    return waves if placed == n else []
'''},
            {"name": "Rescan every round", "slow": True,
             "description": "Each round, scan every unplaced step and take those whose earlier steps were all placed in previous rounds.",
             "time": "O(n · (n + E))", "space": "O(n)",
             "keyPoints": ["No in-degree bookkeeping", "A round that places nothing means a cycle"],
             "code": '''def deploy_waves(n, before):
    done = set()
    waves = []
    while len(done) < n:
        wave = [i for i in range(n) if i not in done and all(p in done for p in before[i])]
        if not wave:
            return []
        waves.append(wave)
        done.update(wave)
    return waves
'''},
        ],
        "starter": '''def deploy_waves(n: int, before: list[list[int]]) -> list[list[int]]:
    pass
''',
    },
    {
        "key": "release-duration",
        "title": "Shortest release time",
        "approach": "Topological order + longest-path DP · O(n + E) · O(n + E)",
        "spec": {"kind": "fn", "fn": "min_release_time", "params": ["n", "duration", "before"], "ret": "value", "cmp": "exact"},
        "statement": """Each release step takes `duration[i]` minutes, and any number of steps can run in parallel. A step starts as soon as every step in `before[i]` has finished.

Return the minimum total time until every step has finished. If the rules contain a cycle, return `-1`. For `n = 0` return `0`.

The answer is the longest (critical) path through the dependency graph: walk the steps in topological order and let each finish at `duration[i] + max(finish of its earlier steps)`.""",
        "examples": [
            {"args": {"n": 4, "duration": [5, 10, 3, 2], "before": [[], [0], [0], [1, 2]]},
             "explanation": "0 ends at 5; 1 at 15 and 2 at 8 run in parallel; 3 starts at 15 and ends at 17.",
             "why": {"t": "Critical path", "d": "The slower branch sets the time."}},
            {"args": {"n": 2, "duration": [1, 1], "before": [[1], [0]]},
             "explanation": "Each step waits for the other: -1.",
             "why": {"t": "Cycle", "d": "No schedule exists."}},
        ],
        "constraints": ["0 ≤ n ≤ 5 · 10^4", "1 ≤ duration[i] ≤ 10^4", "Entries of before[i] are distinct, in 0..n-1, never i"],
        "hints": [
            "finish[i] = duration[i] + max(finish[p] for p in before[i]), or just duration[i] with no rules.",
            "Compute finish in topological order so every finish[p] is ready when you need it.",
            "The answer is the largest finish; a topological sort that stops early means a cycle.",
        ],
        "tests": [
            {"args": {"n": 0, "duration": [], "before": []}, "why": {"t": "Empty release", "d": "Nothing to run: 0."}},
            {"args": {"n": 1, "duration": [7], "before": [[]]}, "why": {"t": "Single step", "d": "Its own duration."}},
            {"args": {"n": 3, "duration": [4, 9, 2], "before": [[], [], []]}, "why": {"t": "All parallel", "d": "The longest step."}},
            {"args": {"n": 3, "duration": [4, 9, 2], "before": [[], [0], [1]]}, "why": {"t": "Chain", "d": "Durations add up."}},
            {"args": {"n": 3, "duration": [5, 5, 5], "before": [[], [0], [0]]}, "why": {"t": "Ties", "d": "Two equal branches."}},
            {"args": {"n": 4, "duration": [1, 1, 1, 1], "before": [[], [0], [3], [2]]}, "why": {"t": "Partial cycle", "d": "Steps 2 and 3 wait on each other: -1."}},
            {"args": {"n": 5, "duration": [15, 8, 20, 3, 5], "before": [[], [], [0, 1], [2], [2]]}, "why": {"t": "Release train", "d": "Build and migrate, deploy, then smoke test and flag flip."}},
            {"args": {"n": 200, "duration": _TIME_DUR, "before": _TIME_BEFORE}, "why": {"t": "Large input", "d": "200 steps and about 400 random rules."}},
        ],
        "solutions": [
            {"name": "Topological order + longest-path DP (Optimal)",
             "description": "Kahn's algorithm. When a step is popped its finish time is final; push that time forward as the earliest start of each successor.",
             "time": "O(n + E)", "space": "O(n + E)",
             "keyPoints": ["finish = start + duration, start = max over predecessors", "Parallelism is unlimited, so only the critical path matters", "Fewer than n pops means a cycle"],
             "code": '''from collections import deque


def min_release_time(n, duration, before):
    succ = [[] for _ in range(n)]
    indeg = [0] * n
    for i in range(n):
        for p in before[i]:
            succ[p].append(i)
            indeg[i] += 1
    start = [0] * n
    q = deque(i for i in range(n) if indeg[i] == 0)
    seen, best = 0, 0
    while q:
        v = q.popleft()
        seen += 1
        end = start[v] + duration[v]
        best = max(best, end)
        for w in succ[v]:
            start[w] = max(start[w], end)
            indeg[w] -= 1
            if indeg[w] == 0:
                q.append(w)
    return best if seen == n else -1
'''},
            {"name": "Relax until stable", "slow": True,
             "description": "Start every finish time at its duration and repeatedly apply finish[i] = duration[i] + max(finish[p]). With no cycle it settles within n rounds; if it still changes after n rounds, a cycle keeps pushing times up.",
             "time": "O(n · (n + E))", "space": "O(n)",
             "keyPoints": ["Bellman-Ford style, for the longest path", "Durations are positive, so a cycle never settles"],
             "code": '''def min_release_time(n, duration, before):
    finish = list(duration)
    for _ in range(n + 1):
        changed = False
        for i in range(n):
            f = duration[i] + max((finish[p] for p in before[i]), default=0)
            if f != finish[i]:
                finish[i] = f
                changed = True
        if not changed:
            return max(finish, default=0)
    return -1
'''},
        ],
        "starter": '''def min_release_time(n: int, duration: list[int], before: list[list[int]]) -> int:
    pass
''',
    },
]
