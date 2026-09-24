"""Capra Playground export for DC-SEC-09 (see tools/export_capra.py)."""

SPEC = {"kind": "fn", "fn": "range_to_cidrs", "params": ["start_ip", "count"], "types": {}, "ret": "value", "cmp": "exact"}


def case(start_ip, count):
    return {"start_ip": start_ip, "count": count}


EXAMPLES = [
    {"args": case("10.0.0.8", 20),
     "explanation": "10.0.0.8 can start a /29 (8 addresses), then 10.0.0.16/29 (8 more), then 10.0.0.24/30 (4): 20 in total.",
     "why": {"t": "Anchor case", "d": "The range from the scenario: start at 10.0.0.8, 20 addresses."}},
    {"args": case("10.0.0.7", 1),
     "explanation": "A single address is a /32.",
     "why": {"t": "Single address", "d": "One address needs one /32 block."}},
    {"args": case("10.0.0.0", 0),
     "explanation": "No addresses, no blocks.",
     "why": {"t": "Empty range", "d": "count = 0 returns []."}},
]

TESTS = [
    {"args": case("10.0.0.0", 256), "why": {"t": "Aligned block", "d": "An aligned /24 is a single block."}},
    {"args": case("10.0.0.1", 255), "why": {"t": "Unaligned start", "d": "Starting at .1 forces a staircase of blocks."}},
    {"args": case("10.0.0.255", 2), "why": {"t": "Octet carry", "d": "The range crosses from .0.255 into .1.0."}},
    {"args": case("0.0.0.0", 1), "why": {"t": "Address zero", "d": "0 is aligned to every block size."}},
    {"args": case("255.255.255.254", 2), "why": {"t": "Top of the space", "d": "The last two IPv4 addresses."}},
    {"args": case("192.0.2.5", 7), "why": {"t": "Odd start, odd count", "d": "Blocks grow, then shrink to fit the end."}},
    {"args": case("10.20.30.40", 1000), "why": {"t": "Mid-size range", "d": "About a thousand addresses from an odd start."}},
    {"args": case("10.0.0.0", 65536), "why": {"t": "Whole /16", "d": "Exactly one /16."}},
    {"args": case("10.0.3.17", 5000), "why": {"t": "Large input", "d": "5,000 addresses from an unaligned start."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Lowest set bit (Optimal)",
     "description": "Convert the start address to an integer x. The largest block that may start at x is its lowest set bit, x & -x. Halve it until it fits in the addresses left, emit it, move past it and repeat.",
     "time": "O(1) for IPv4 (at most about 64 blocks, 32 halvings each)", "space": "O(1) besides the output",
     "keyPoints": ["A /n block must start on a multiple of its size", "x & -x is the biggest aligned block starting at x", "Address 0 is aligned to everything"]},
    {"name": "Merge /32s into their parents", "slow": True,
     "description": "Emit one /32 per address, then repeatedly merge two neighbouring blocks of the same size whose first block is aligned to the doubled size. Stop when nothing merges.",
     "time": "O(count · 32)", "space": "O(count)",
     "keyPoints": ["Easy to trust: every merge keeps the cover exact", "Memory grows with the number of addresses"],
     "code": '''from __future__ import annotations


def range_to_cidrs(start_ip: str, count: int) -> list[str]:
    a, b, c, d = (int(x) for x in start_ip.split("."))
    x = (a << 24) | (b << 16) | (c << 8) | d
    blocks = [(x + i, 1) for i in range(count)]
    changed = True
    while changed:
        changed = False
        merged, i = [], 0
        while i < len(blocks):
            if i + 1 < len(blocks):
                (s1, n1), (s2, n2) = blocks[i], blocks[i + 1]
                if n1 == n2 and s1 % (2 * n1) == 0 and s2 == s1 + n1:
                    merged.append((s1, 2 * n1))
                    i += 2
                    changed = True
                    continue
            merged.append(blocks[i])
            i += 1
        blocks = merged
    ip = lambda v: ".".join(str((v >> s) & 0xFF) for s in (24, 16, 8, 0))
    return [f"{ip(s)}/{32 - (n.bit_length() - 1)}" for s, n in blocks]
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Merge /32s", "idea": "One /32 per address, then merge aligned sibling pairs until nothing changes.",
     "time": "O(count · 32)", "space": "O(count)", "use": "Small ranges; obviously correct."},
    {"name": "Lowest set bit", "idea": "Take the biggest aligned block at the start, shrink to fit, repeat.",
     "time": "O(1) for IPv4", "space": "O(1)", "use": "Any range size, including millions of addresses."},
]
