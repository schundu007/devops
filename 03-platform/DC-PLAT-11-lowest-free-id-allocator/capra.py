"""Capra Playground export for DC-PLAT-11 (see tools/export_capra.py).

A driver, not a design case: an invalid release must raise ValueError and
change nothing, so the driver records "ValueError" and keeps going.
"""
import random

SPEC = {"kind": "driver", "fn": "IdAllocator", "params": ["size", "base", "ops"], "types": {}, "ret": "value", "cmp": "exact"}

DRIVER = '''
def __drive(args):
    alloc = IdAllocator(args["size"], args["base"])
    out = []
    for op in args["ops"]:
        if op[0] == "allocate":
            out.append(alloc.allocate())
        else:
            try:
                out.append(alloc.release(op[1]))
            except ValueError:
                out.append("ValueError")
    return out
'''

A, R = ["allocate"], (lambda i: ["release", i])

EXAMPLES = [
    {"args": {"size": 3, "base": 100, "ops": [A, A, A, A, R(101), A]},
     "explanation": "IDs 100, 101, 102 go out, then the pool is empty (None). After 101 comes back it is the smallest free ID again.",
     "why": {"t": "Exhausted · Reuse", "d": "An empty pool returns None; a released ID is handed out again."}},
    {"args": {"size": 5, "base": 0, "ops": [A, A, A, R(2), R(0), A, A, A]},
     "explanation": "0 and 2 come back. The next allocations hand out 0, then 2, then 3: always the smallest free.",
     "why": {"t": "Smallest first", "d": "Released IDs are reused lowest first, before never-used ones."}},
]


def _large_case():
    # Build a valid random sequence by simulating a simple reference allocator.
    rng = random.Random(1845)
    free, in_use, nxt, ops = [], set(), 0, []
    for _ in range(900):
        if in_use and rng.random() < 0.4:
            i = rng.choice(sorted(in_use))
            in_use.remove(i)
            free.append(i)
            ops.append(R(40000 + i))
        else:
            ops.append(A)
            if free:
                i = min(free)
                free.remove(i)
            else:
                i = nxt
                nxt += 1
            in_use.add(i)
    return {"size": 1_000_000, "base": 40000, "ops": ops}


TESTS = [
    {"args": {"size": 0, "base": 0, "ops": [A]},
     "why": {"t": "Empty pool", "d": "A pool of size 0 has nothing to hand out."}},
    {"args": {"size": 1, "base": 7, "ops": [A, A, R(7), A]},
     "why": {"t": "Single ID", "d": "One ID: out, exhausted, back, out again."}},
    {"args": {"size": 3, "base": 0, "ops": [A, R(0), R(0), A, A]},
     "why": {"t": "Double release", "d": "Releasing an ID twice raises ValueError and changes nothing."}},
    {"args": {"size": 3, "base": 10, "ops": [A, R(99), R(11), A]},
     "why": {"t": "Foreign ID", "d": "IDs outside the pool, or never handed out, raise ValueError."}},
    {"args": {"size": 4, "base": -2, "ops": [A, A, A, A, R(-1), R(-2), A, A]},
     "why": {"t": "Negative base", "d": "The pool can start below zero."}},
    {"args": {"size": 5, "base": 0, "ops": [R(0), A]},
     "why": {"t": "Release before allocate", "d": "Nothing is in use yet, so the release is invalid."}},
    {"args": {"size": 1000, "base": 30000, "ops": [A] * 5 + [R(30001), R(30003)] + [A] * 3},
     "why": {"t": "Port allocator", "d": "A NodePort-style range starting at 30000: freed ports come back lowest first."}},
    {"args": _large_case(),
     "why": {"t": "Large input", "d": "A million-ID pool and 900 random operations; the pool must not be built up front."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Watermark + min-heap (Optimal)",
     "description": "Track offsets from base. _next is the first never-used offset; released offsets go into a min-heap and are all below _next, so the heap top (if any) is the smallest free ID.",
     "time": "O(log r) per call", "space": "O(k) for k IDs ever handed out",
     "keyPoints": ["Never build the full free list", "Released IDs are always below the watermark", "Reject releases of IDs not in use"]},
    {"name": "Scan for the smallest free", "slow": True,
     "description": "Keep the set of IDs in use and scan upward from the start of the pool for the first free one.",
     "time": "O(size) per allocate", "space": "O(k)",
     "keyPoints": ["Simple and correct", "A pool of a million IDs makes every call slow"],
     "code": '''from __future__ import annotations


class IdAllocator:
    def __init__(self, size: int, base: int = 0) -> None:
        self._size, self._base = size, base
        self._in_use: set[int] = set()

    def allocate(self) -> int | None:
        for off in range(self._size):
            if off not in self._in_use:
                self._in_use.add(off)
                return self._base + off
        return None

    def release(self, id_: int) -> None:
        off = id_ - self._base
        if off not in self._in_use:
            raise ValueError(f"id {id_} is not allocated")
        self._in_use.remove(off)
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Scan for the smallest free", "idea": "Scan from the start of the pool for the first ID not in use.",
     "time": "O(size) per allocate", "space": "O(k)", "use": "Tiny pools only."},
    {"name": "Watermark + min-heap", "idea": "Never-used IDs sit above a watermark; returned IDs wait in a min-heap.",
     "time": "O(log r) per call", "space": "O(k)", "use": "Port ranges, IPAM pools, large ID spaces."},
]

VARIANT_TITLE = "Lowest free ID"
VARIANT_APPROACH = "Watermark + min-heap · O(log r) per call · O(k)"


def _big_ports():
    rng = random.Random(30000)
    ops = []
    for _ in range(700):
        r = rng.random()
        if r < 0.5:
            ops.append(["allocate"])
        elif r < 0.7:
            ops.append(["reserve", 30000 + rng.randrange(400)])
        else:
            ops.append(["release", 30000 + rng.randrange(400)])
    return {"size": 2768, "base": 30000, "ops": ops}


def _big_leases():
    rng = random.Random(2131)
    t, reqs = 0, []
    for _ in range(600):
        t += rng.randint(0, 3)
        reqs.append(t)
    return {"size": 150, "ttl": 240, "requests": reqs}


VARIANTS = [
    {
        "key": "static-reservations",
        "title": "Node ports with static reservations",
        "approach": "Watermark + min-heap with lazy skips · O(log r) amortized per call · O(k)",
        "spec": {"kind": "fn", "fn": "run_ports", "params": ["size", "base", "ops"], "ret": "value", "cmp": "exact"},
        "statement": """A cluster hands out node ports. Most services take the lowest free port, but some pin a specific one.

### Input
- `size`, `base`: the ports run from `base` to `base + size - 1`
- `ops`: the operations, processed in order

### Output
- One result per operation:
  - `["allocate"]`: the smallest free port, now in use, or `null` if none is free
  - `["reserve", p]`: `true` and mark `p` in use if it is in the range and free, else `false`
  - `["release", p]`: `true` and free `p` if it is in use, else `false`""",
        "examples": [
            {"args": {"size": 5, "base": 30000, "ops": [["reserve", 30001], ["allocate"], ["allocate"], ["release", 30001], ["allocate"]]},
             "explanation": "30001 is pinned, so the watermark hands out 30000 and then skips to 30002. After 30001 is released it is the lowest free port again.",
             "why": {"t": "Skip a pinned port", "d": "The watermark jumps over a reservation."}},
            {"args": {"size": 3, "base": 0, "ops": [["allocate"], ["release", 0], ["reserve", 0], ["allocate"], ["reserve", 7]]},
             "explanation": "Port 0 is released and pinned again, so its heap entry is stale; the next allocate gives 1. Port 7 is outside the range.",
             "why": {"t": "Stale heap entry · Out of range", "d": "A freed port taken by reserve must not be handed out twice."}},
        ],
        "constraints": ["0 ≤ size ≤ 10^6", "base is any integer", "1 ≤ ops.length ≤ 10^5"],
        "hints": [
            "Keep the set of ports in use; it is the only source of truth.",
            "When popping the heap or advancing the watermark, skip any offset that is already in use.",
            "Push an offset onto the heap on release only; reserve just marks it in use.",
        ],
        "tests": [
            {"args": {"size": 0, "base": 0, "ops": [["allocate"], ["reserve", 0], ["release", 0]]}, "why": {"t": "Empty range", "d": "Nothing to give, reserve or release."}},
            {"args": {"size": 1, "base": 9, "ops": [["reserve", 9], ["allocate"], ["reserve", 9], ["release", 9], ["allocate"]]}, "why": {"t": "Single port", "d": "Pinned, exhausted, double reserve, freed, handed out."}},
            {"args": {"size": 4, "base": 0, "ops": [["reserve", 0], ["reserve", 1], ["reserve", 2], ["reserve", 3], ["allocate"]]}, "why": {"t": "All pinned", "d": "The watermark skips everything: null."}},
            {"args": {"size": 4, "base": 0, "ops": [["release", 2], ["allocate"], ["release", 0], ["release", 0], ["allocate"]]}, "why": {"t": "Double release", "d": "Releasing a free port returns false and changes nothing."}},
            {"args": {"size": 6, "base": -3, "ops": [["reserve", 0], ["allocate"], ["allocate"], ["allocate"], ["allocate"], ["allocate"]]}, "why": {"t": "Negative base", "d": "A range below zero with a pin in the middle."}},
            {"args": {"size": 5, "base": 100, "ops": [["allocate"], ["allocate"], ["release", 100], ["release", 101], ["reserve", 101], ["allocate"], ["allocate"]]}, "why": {"t": "Ties in the heap", "d": "Two freed ports, one pinned again."}},
            {"args": _big_ports(), "why": {"t": "Large input", "d": "700 random operations on the Kubernetes NodePort range."}},
        ],
        "solutions": [
            {"name": "Watermark + min-heap with lazy skips (Optimal)",
             "description": "Offsets at or above the watermark have never been handed out by allocate. Released offsets go on a min-heap. On allocate, drop heap entries that are in use; if the heap is empty, advance the watermark past pinned offsets.",
             "time": "O(log r) amortized per call", "space": "O(k)",
             "keyPoints": ["The in-use set decides; the heap may hold stale entries", "The watermark only moves forward", "Every free offset below the watermark is in the heap"],
             "code": '''import heapq


def run_ports(size, base, ops):
    in_use, heap, nxt, out = set(), [], 0, []
    for op in ops:
        if op[0] == "allocate":
            while heap and heap[0] in in_use:
                heapq.heappop(heap)
            if heap:
                off = heapq.heappop(heap)
            else:
                while nxt < size and nxt in in_use:
                    nxt += 1
                if nxt == size:
                    out.append(None)
                    continue
                off = nxt
                nxt += 1
            in_use.add(off)
            out.append(base + off)
        elif op[0] == "reserve":
            off = op[1] - base
            if 0 <= off < size and off not in in_use:
                in_use.add(off)
                out.append(True)
            else:
                out.append(False)
        else:
            off = op[1] - base
            if off in in_use:
                in_use.remove(off)
                if off < nxt:
                    heapq.heappush(heap, off)
                out.append(True)
            else:
                out.append(False)
    return out
'''},
            {"name": "Scan for the smallest free", "slow": True,
             "description": "Keep the in-use set and scan the range from the bottom on every allocate.",
             "time": "O(size) per allocate", "space": "O(k)",
             "keyPoints": ["No watermark or heap to keep consistent", "Slow for large ranges"],
             "code": '''def run_ports(size, base, ops):
    in_use, out = set(), []
    for op in ops:
        if op[0] == "allocate":
            off = next((o for o in range(size) if o not in in_use), None)
            if off is None:
                out.append(None)
            else:
                in_use.add(off)
                out.append(base + off)
        elif op[0] == "reserve":
            off = op[1] - base
            ok = 0 <= off < size and off not in in_use
            if ok:
                in_use.add(off)
            out.append(ok)
        else:
            off = op[1] - base
            ok = off in in_use
            if ok:
                in_use.remove(off)
            out.append(ok)
    return out
'''},
        ],
        "starter": '''def run_ports(size: int, base: int, ops: list[list]) -> list:
    pass
''',
    },
    {
        "key": "dhcp-leases",
        "title": "DHCP leases that expire",
        "approach": "Expiry heap + free-ID heap + watermark · O(n log n) · O(size)",
        "spec": {"kind": "fn", "fn": "lease_addresses", "params": ["size", "ttl", "requests"], "ret": "value", "cmp": "exact"},
        "statement": """A DHCP server leases addresses. Nobody releases a lease: it simply expires.

### Input
- `size`: the addresses run from `0` to `size - 1`
- `ttl`: how long a lease holds its address
- `requests`: request times in non-decreasing order

### Output
- The address given to each request, or `-1` if every address is leased

### Rules
- Each request gets the **smallest** address free at that moment
- A lease granted at time `t` holds the address on `[t, t + ttl)`, so at time `t + ttl` it is free again""",
        "examples": [
            {"args": {"size": 2, "ttl": 10, "requests": [0, 1, 5, 10, 11]},
             "explanation": "0 and 1 are leased at times 0 and 1; at 5 both are taken (-1). At 10 address 0 expires and is reused; at 11 address 1 is.",
             "why": {"t": "Expiry frees an address", "d": "A lease ending at t is free for a request at t."}},
            {"args": {"size": 3, "ttl": 5, "requests": [0, 2, 5, 5]},
             "explanation": "At 5 only address 0 has expired: the two requests get 0 and 2 (1 is still leased until 7).",
             "why": {"t": "Same time", "d": "Two requests at one moment."}},
        ],
        "constraints": ["0 ≤ size ≤ 10^5", "1 ≤ ttl ≤ 10^9", "1 ≤ requests.length ≤ 10^5, non-decreasing, each in [0, 10^9]"],
        "hints": [
            "Keep active leases in a min-heap by expiry time.",
            "Before each request, pop every lease with expiry ≤ t and push its address onto a min-heap of free addresses.",
            "Addresses never leased yet come from a watermark, as in the main problem; freed ones are always below it.",
        ],
        "tests": [
            {"args": {"size": 0, "ttl": 5, "requests": [0]}, "why": {"t": "No addresses", "d": "An empty pool always answers -1."}},
            {"args": {"size": 1, "ttl": 1, "requests": [0, 0, 1, 1, 2]}, "why": {"t": "Single address", "d": "One lease per time step."}},
            {"args": {"size": 3, "ttl": 100, "requests": [0, 0, 0, 0]}, "why": {"t": "Exhausted", "d": "Burst at boot: the fourth request fails."}},
            {"args": {"size": 3, "ttl": 4, "requests": [0, 1, 2, 5, 5, 6]}, "why": {"t": "Out-of-order expiry", "d": "Addresses 0 and 1 free by 5, reused lowest first."}},
            {"args": {"size": 5, "ttl": 1000000000, "requests": [0, 999999999, 1000000000]}, "why": {"t": "Huge times", "d": "The first lease ends exactly at 10^9."}},
            {"args": {"size": 2, "ttl": 3, "requests": [3, 3, 3, 6, 6, 6]}, "why": {"t": "Ties at expiry", "d": "Both leases end together and are reused in order."}},
            {"args": _big_leases(), "why": {"t": "Large input", "d": "600 requests on a /24-sized pool with four-minute leases."}},
        ],
        "solutions": [
            {"name": "Expiry heap + free heap + watermark (Optimal)",
             "description": "Active leases sit in a heap of (expiry, address). Before each request, move expired addresses to a min-heap of free ones; take from it, else from the watermark, else answer -1.",
             "time": "O(n log n)", "space": "O(size)",
             "keyPoints": ["Expiry is inclusive: expiry ≤ t means free", "Freed addresses are below the watermark", "Each lease enters and leaves each heap once"],
             "code": '''import heapq


def lease_addresses(size, ttl, requests):
    active, free, nxt, out = [], [], 0, []
    for t in requests:
        while active and active[0][0] <= t:
            heapq.heappush(free, heapq.heappop(active)[1])
        if free:
            addr = heapq.heappop(free)
        elif nxt < size:
            addr = nxt
            nxt += 1
        else:
            out.append(-1)
            continue
        heapq.heappush(active, (t + ttl, addr))
        out.append(addr)
    return out
'''},
            {"name": "Scan lease end times", "slow": True,
             "description": "Store each address's lease end time and scan from address 0 for the first one that has ended.",
             "time": "O(n · size)", "space": "O(size)",
             "keyPoints": ["One array, no heaps", "Every request scans the pool"],
             "code": '''def lease_addresses(size, ttl, requests):
    ends = [0] * size
    used = [False] * size
    out = []
    for t in requests:
        for a in range(size):
            if not used[a] or ends[a] <= t:
                used[a] = True
                ends[a] = t + ttl
                out.append(a)
                break
        else:
            out.append(-1)
    return out
'''},
        ],
        "starter": '''def lease_addresses(size: int, ttl: int, requests: list[int]) -> list[int]:
    pass
''',
    },
]
