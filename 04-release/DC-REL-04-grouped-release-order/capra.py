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
]

WAYS_TO_SOLVE = [
    {"name": "Brute force", "idea": "Try every permutation and keep the first that obeys all rules and keeps services contiguous.",
     "time": "O(n! · n)", "space": "O(n)", "use": "Only for checking tiny cases."},
    {"name": "Two-level topological sort", "idea": "Sort services, sort steps, then emit each service's steps as one block in service order.",
     "time": "O(n + m + E)", "space": "O(n + m + E)", "use": "The real answer: linear time."},
]
