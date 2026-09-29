"""Capra Playground export for DC-PLAT-10 (see tools/export_capra.py).

The router must draw its randomness from the injected rng. The driver passes a
scripted rng that hands out preset tickets, so every case is deterministic, and
it checks that each pick draws exactly one ticket over the total weight.
"""
import random

SPEC = {"kind": "driver", "fn": "WeightedRouter", "params": ["weights", "tickets", "report"], "types": {}, "ret": "value", "cmp": "exact"}

DRIVER = '''
class _ScriptedRng:
    def __init__(self, tickets):
        self._tickets = list(tickets)
        self.stops = []

    def randrange(self, stop):
        self.stops.append(stop)
        if not self._tickets:
            raise RuntimeError("pick() drew more random numbers than picks were made")
        return self._tickets.pop(0)


def __drive(args):
    weights, tickets = args["weights"], args["tickets"]
    rng = _ScriptedRng(tickets)
    try:
        router = WeightedRouter(weights, rng)
    except ValueError:
        return "ValueError"
    picks = [router.pick() for _ in range(len(tickets))]
    total = sum(weights)
    if rng.stops != [total] * len(tickets):
        return "each pick must call rng.randrange(%d) exactly once" % total
    if args["report"] == "counts":
        counts = [0] * len(weights)
        for p in picks:
            counts[p] += 1
        return counts
    return picks
'''

EXAMPLES = [
    {"args": {"weights": [90, 10], "tickets": [0, 8, 89, 90, 99], "report": "picks"},
     "explanation": "Backend 0 owns tickets 0-89 and backend 1 owns 90-99, so tickets 89 and 90 fall on either side of the boundary.",
     "why": {"t": "Ticket boundaries", "d": "The last ticket of one backend and the first of the next."}},
    {"args": {"weights": [5, 0, 5], "tickets": list(range(10)), "report": "picks"},
     "explanation": "Backend 1 has weight 0 (drained), so it owns no tickets and is never picked.",
     "why": {"t": "Drained backend", "d": "A zero weight must never receive traffic."}},
]

_rng = random.Random(7)
_W = [_rng.randint(0, 50) for _ in range(300)] + [1]
_T = sum(_W)

TESTS = [
    {"args": {"weights": [7], "tickets": [0, 3, 6], "report": "picks"},
     "why": {"t": "Single backend", "d": "With one backend every ticket goes to it."}},
    {"args": {"weights": [], "tickets": [], "report": "picks"},
     "why": {"t": "Empty list", "d": "No backends at all is rejected with ValueError."}},
    {"args": {"weights": [0, 0], "tickets": [], "report": "picks"},
     "why": {"t": "All drained", "d": "A total weight of 0 is rejected with ValueError."}},
    {"args": {"weights": [3, -1], "tickets": [], "report": "picks"},
     "why": {"t": "Negative weight", "d": "A negative weight is rejected with ValueError."}},
    {"args": {"weights": [0, 0, 4], "tickets": [0, 3], "report": "picks"},
     "why": {"t": "Leading zeros", "d": "Drained backends at the front are skipped."}},
    {"args": {"weights": [95, 5], "tickets": list(range(100)), "report": "counts"},
     "why": {"t": "Canary 5%", "d": "Every ticket drawn once: the traffic split must equal the weights exactly."}},
    {"args": {"weights": [75, 25], "tickets": list(range(100)), "report": "counts"},
     "why": {"t": "Canary 25%", "d": "An Argo-Rollouts-style step: 25% of tickets go to the canary."}},
    {"args": {"weights": _W, "tickets": [_rng.randrange(_T) for _ in range(400)] + [0, _T - 1], "report": "picks"},
     "why": {"t": "Large input", "d": "301 backends (many drained) and 402 tickets, including the first and last."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Prefix sums + binary search (Optimal)",
     "description": "Build running totals of the weights once. Each pick draws one ticket in [0, total) and returns bisect_right(prefix, ticket), the first backend whose range ends after the ticket.",
     "time": "O(n) build, O(log n) per pick", "space": "O(n)",
     "keyPoints": ["Backend i owns tickets [prefix[i-1], prefix[i])", "bisect_right skips zero-weight backends", "Draw exactly one ticket per pick from the injected rng"]},
    {"name": "Walk the backends", "slow": True,
     "description": "Draw one ticket, then subtract weights backend by backend until the ticket falls inside one.",
     "time": "O(n) per pick", "space": "O(n)",
     "keyPoints": ["No precomputation", "Too slow for thousands of weighted endpoints at high request rates"],
     "code": '''from __future__ import annotations

import random


class WeightedRouter:
    def __init__(self, weights: list[int], rng: random.Random | None = None) -> None:
        if not weights or any(w < 0 for w in weights) or sum(weights) == 0:
            raise ValueError("bad weights")
        self._weights = list(weights)
        self._total = sum(weights)
        self._rng = rng if rng is not None else random.Random()

    def pick(self) -> int:
        ticket = self._rng.randrange(self._total)
        for i, w in enumerate(self._weights):
            if ticket < w:
                return i
            ticket -= w
        raise AssertionError("unreachable")
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Walk the backends", "idea": "Subtract weights one by one until the ticket fits.",
     "time": "O(n) per pick", "space": "O(1) extra", "use": "A handful of backends (stable + canary)."},
    {"name": "Prefix sums + binary search", "idea": "Precompute running totals; binary search the ticket.",
     "time": "O(log n) per pick", "space": "O(n)", "use": "Many weighted endpoints and high request rates."},
]

VARIANT_TITLE = "Weighted canary router"
VARIANT_APPROACH = "Prefix sums + binary search · O(n) build, O(log n) per pick · O(n)"


def _v_ops():
    rng = random.Random(1845)
    n = 200
    weights = [rng.randint(0, 20) for _ in range(n)]
    start = list(weights)
    total = sum(weights)
    ops = []
    for _ in range(600):
        if rng.random() < 0.3:
            i, w = rng.randrange(n), rng.randint(0, 20)
            total += w - weights[i]
            weights[i] = w
            ops.append(["set", i, w])
        else:
            ops.append(["pick", rng.randrange(max(total, 1))])
    return start, ops


def _v_ring():
    rng = random.Random(5381)
    positions = rng.sample(range(0, 2**20), 300)
    nodes = [["node-%d" % (i % 60), p] for i, p in enumerate(positions)]
    keys = [rng.randrange(2**20) for _ in range(500)] + [0, 2**20 - 1]
    return nodes, keys


_VW, _VOPS = _v_ops()
_VN, _VK = _v_ring()

VARIANTS = [
    {
        "key": "live-reweight",
        "title": "Shift weights mid-rollout",
        "approach": "Fenwick tree + binary lifting · O(log n) per op · O(n)",
        "spec": {"kind": "fn", "fn": "route_with_updates", "params": ["weights", "ops"]},
        "statement": (
            "A progressive rollout changes backend weights while traffic keeps flowing (the controller moves the canary from 5% to 25% to 50%, or drains a bad pod by setting its weight to `0`); route requests as the weights change.\n"
            "\n"
            "### Input\n"
            "- `weights`: the starting weight of each backend\n"
            "- `ops`: operations, applied in order:\n"
            "  - `[\"set\", i, w]`: set backend `i`'s weight to `w`\n"
            "  - `[\"pick\", ticket]`: route one request\n"
            "\n"
            "### Output\n"
            "- The list of answers for the picks, in order\n"
            "\n"
            "### Rules\n"
            "- A pick uses the **current** weights: backend 0 owns tickets `[0, w0)`, backend 1 owns `[w0, w0 + w1)`, and so on\n"
            "- A pick returns the owning backend, or `-1` if the total weight is `0` or `ticket` is not below the total"
        ),
        "examples": [
            {"args": {"weights": [95, 5], "ops": [["pick", 94], ["pick", 95], ["set", 1, 25], ["pick", 94], ["pick", 110]]},
             "explanation": "At 95/5, ticket 94 is stable (0) and 95 is canary (1). After the canary goes to 25, ticket 110 lands on it; 94 still maps to 0.",
             "why": {"t": "Canary step", "d": "A weight change moves the ticket boundaries."}},
            {"args": {"weights": [3, 3, 3], "ops": [["set", 1, 0], ["pick", 3], ["pick", 5], ["pick", 6]]},
             "explanation": "Draining backend 1 leaves 0 with [0, 3) and 2 with [3, 6). Ticket 6 is past the total of 6: -1.",
             "why": {"t": "Drain", "d": "A drained backend owns no tickets."}},
        ],
        "constraints": [
            "1 ≤ weights.length ≤ 10⁵, 0 ≤ weights[i] ≤ 10⁵",
            "1 ≤ ops.length ≤ 10⁵",
            "0 ≤ i < weights.length, 0 ≤ w ≤ 10⁵, 0 ≤ ticket ≤ 10¹⁰",
        ],
        "hints": [
            "Rebuilding prefix sums after every `set` is O(n). A Fenwick (binary indexed) tree updates a prefix total in O(log n).",
            "To find the owner, walk down the Fenwick tree from the highest power of two, skipping blocks whose total is `<= ticket`.",
        ],
        "tests": [
            {"args": {"weights": [0], "ops": [["pick", 0]]}, "why": {"t": "All drained", "d": "Total weight 0: every pick is -1."}},
            {"args": {"weights": [7], "ops": [["pick", 0], ["pick", 6], ["pick", 7]]}, "why": {"t": "Single backend", "d": "Boundaries of the only range, and one past it."}},
            {"args": {"weights": [0, 0, 4], "ops": [["pick", 0], ["set", 0, 2], ["pick", 0], ["pick", 2]]}, "why": {"t": "Leading zeros", "d": "Drained backends at the front, then one comes back."}},
            {"args": {"weights": [5, 5], "ops": [["set", 0, 0], ["set", 1, 0], ["pick", 0], ["set", 1, 1], ["pick", 0]]}, "why": {"t": "Drain everything", "d": "Picks during a full drain return -1."}},
            {"args": {"weights": [1, 2, 3], "ops": [["set", 2, 3], ["pick", 2], ["pick", 3]]}, "why": {"t": "No-op update", "d": "Setting a weight to its current value changes nothing."}},
            {"args": {"weights": _VW, "ops": _VOPS}, "why": {"t": "Large input", "d": "200 backends and 600 mixed updates and picks."}},
        ],
        "solutions": [
            {"name": "Fenwick tree (Optimal)",
             "description": "Store weights in a Fenwick tree. A set adds the difference along the update path. A pick descends from the top bit, taking each block whose sum is <= the remaining ticket.",
             "time": "O(n log n) build, O(log n) per op", "space": "O(n)",
             "keyPoints": ["Point update, prefix query in O(log n)", "Binary lifting finds the first prefix > ticket", "Keep the raw weights to compute each difference"],
             "code": '''def route_with_updates(weights, ops):
    n = len(weights)
    w = list(weights)
    tree = [0] * (n + 1)

    def add(i, delta):
        i += 1
        while i <= n:
            tree[i] += delta
            i += i & -i

    for i, x in enumerate(w):
        add(i, x)
    total = sum(w)
    top = 1
    while top * 2 <= n:
        top *= 2
    out = []
    for op in ops:
        if op[0] == "set":
            i, x = op[1], op[2]
            add(i, x - w[i])
            total += x - w[i]
            w[i] = x
            continue
        ticket = op[1]
        if ticket >= total:
            out.append(-1)
            continue
        pos, step = 0, top
        while step:
            nxt = pos + step
            if nxt <= n and tree[nxt] <= ticket:
                ticket -= tree[nxt]
                pos = nxt
            step //= 2
        out.append(pos)
    return out
'''},
            {"name": "Walk the backends", "slow": True,
             "description": "Keep a plain list of weights. For each pick, subtract weights one by one until the ticket falls inside a backend.",
             "time": "O(n) per pick, O(1) per set", "space": "O(n)",
             "keyPoints": ["Updates are trivial", "Every pick scans the list"],
             "code": '''def route_with_updates(weights, ops):
    w = list(weights)
    out = []
    for op in ops:
        if op[0] == "set":
            w[op[1]] = op[2]
            continue
        ticket = op[1]
        if ticket >= sum(w):
            out.append(-1)
            continue
        for i, x in enumerate(w):
            if ticket < x:
                out.append(i)
                break
            ticket -= x
    return out
'''},
        ],
        "starter": '''def route_with_updates(weights: list[int], ops: list[list]) -> list[int]:
    """Apply set/pick operations in order; return the backend for each pick."""
    raise NotImplementedError
''',
    },
    {
        "key": "hash-ring",
        "title": "Consistent-hash ring lookup",
        "approach": "Sorted ring positions + binary search · O((v + k) log v) · O(v)",
        "spec": {"kind": "fn", "fn": "ring_owners", "params": ["nodes", "keys", "ring_size"]},
        "statement": (
            "A cache tier uses consistent hashing so that adding a node moves only a slice of the keys; find the node that owns each key.\n"
            "\n"
            "### Input\n"
            "- `nodes[i] = [name, position]`: a (virtual) node placed at `position` on the ring; one physical node usually appears many times\n"
            "- `keys`: key hashes\n"
            "- `ring_size`: the size of the ring\n"
            "\n"
            "### Output\n"
            "- The owning node's name for each hash in `keys`, in order\n"
            "\n"
            "### Rules\n"
            "- A key hashed to `h` belongs to the first node at a position `>= h`, going clockwise\n"
            "- Past the end of the ring, wrap around to the smallest position\n"
            "- Positions are distinct"
        ),
        "examples": [
            {"args": {"nodes": [["cache-a", 100], ["cache-b", 400], ["cache-a", 700]], "keys": [50, 100, 101, 650, 900], "ring_size": 1000},
             "explanation": "50 and 100 go to position 100 (cache-a); 101 goes to 400 (cache-b); 650 to 700 (cache-a); 900 wraps to 100 (cache-a).",
             "why": {"t": "Wrap-around", "d": "Keys past the last node belong to the first one."}},
        ],
        "constraints": [
            "1 ≤ nodes.length ≤ 10⁵, positions distinct, 0 ≤ position < ring_size",
            "0 ≤ keys.length ≤ 10⁵, 0 ≤ keys[i] < ring_size",
            "1 ≤ ring_size ≤ 2³²",
        ],
        "hints": [
            "Sort the nodes by position once. Each lookup is then the first position `>= h`.",
            "`bisect_left` gives that index; if it equals the number of nodes, wrap to index 0.",
        ],
        "tests": [
            {"args": {"nodes": [["solo", 5]], "keys": [0, 5, 9], "ring_size": 10}, "why": {"t": "Single node", "d": "One node owns the whole ring."}},
            {"args": {"nodes": [["a", 3], ["b", 7]], "keys": [], "ring_size": 10}, "why": {"t": "No keys", "d": "Nothing to look up."}},
            {"args": {"nodes": [["b", 7], ["a", 3]], "keys": [3, 4, 7, 8], "ring_size": 10}, "why": {"t": "Unsorted nodes · exact hits", "d": "Nodes arrive unsorted; a key on a node's position belongs to it."}},
            {"args": {"nodes": [["a", 0], ["b", 9]], "keys": [0, 1, 9], "ring_size": 10}, "why": {"t": "Ring edges", "d": "Nodes at the first and last positions."}},
            {"args": {"nodes": [["x", 2], ["x", 4], ["y", 6]], "keys": [1, 3, 5, 7], "ring_size": 8}, "why": {"t": "Virtual nodes", "d": "One physical node at several positions."}},
            {"args": {"nodes": _VN, "keys": _VK, "ring_size": 2**20}, "why": {"t": "Large input", "d": "60 nodes with 5 virtual positions each, 502 keys."}},
        ],
        "solutions": [
            {"name": "Sort + binary search (Optimal)",
             "description": "Sort the virtual nodes by position. For each key, bisect_left into the positions and wrap to 0 past the end.",
             "time": "O((v + k) log v)", "space": "O(v)",
             "keyPoints": ["Sort once, look up many times", "bisect_left: a key on a position belongs to that node", "Wrap past the last position"],
             "code": '''from bisect import bisect_left


def ring_owners(nodes, keys, ring_size):
    ring = sorted(nodes, key=lambda nd: nd[1])
    positions = [p for _, p in ring]
    out = []
    for h in keys:
        i = bisect_left(positions, h)
        out.append(ring[i % len(ring)][0])
    return out
'''},
            {"name": "Scan every node", "slow": True,
             "description": "For each key, scan all nodes for the smallest position >= h; if none, take the smallest position overall.",
             "time": "O(k · v)", "space": "O(1)",
             "keyPoints": ["No sorting needed", "Linear per lookup; too slow for a hot cache path"],
             "code": '''def ring_owners(nodes, keys, ring_size):
    out = []
    first = min(nodes, key=lambda nd: nd[1])
    for h in keys:
        best = None
        for name, p in nodes:
            if p >= h and (best is None or p < best[1]):
                best = (name, p)
        out.append(best[0] if best else first[0])
    return out
'''},
        ],
        "starter": '''def ring_owners(nodes: list[list], keys: list[int], ring_size: int) -> list[str]:
    """Owner of each key hash on the consistent-hash ring."""
    raise NotImplementedError
''',
    },
]
