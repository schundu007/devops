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
