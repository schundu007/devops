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
     "description": "Emit one /32 per address, then repeatedly merge two neighboring blocks of the same size whose first block is aligned to the doubled size. Stop when nothing merges.",
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

VARIANT_TITLE = "Range to CIDR blocks"
VARIANT_APPROACH = "Lowest set bit · O(1) for IPv4 · O(1)"

_CIDR_HELPERS = '''
def _to_int(ip):
    a, b, c, d = (int(x) for x in ip.split("."))
    return (a << 24) | (b << 16) | (c << 8) | d


def _to_ip(x):
    return ".".join(str((x >> s) & 0xFF) for s in (24, 16, 8, 0))


def _parse(cidr):
    ip, n = cidr.split("/")
    return _to_int(ip), 1 << (32 - int(n))
'''

_GREEDY = '''

def _cover(x, count, out):
    while count > 0:
        step = x & -x if x else 1 << 32
        while step > count:
            step >>= 1
        out.append(f"{_to_ip(x)}/{32 - (step.bit_length() - 1)}")
        x += step
        count -= step
'''

_MERGE32 = '''

def _merge_addresses(addrs):
    blocks = [(a, 1) for a in sorted(addrs)]
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
    return [f"{_to_ip(s)}/{32 - (n.bit_length() - 1)}" for s, n in blocks]
'''

VARIANTS = [
    {
        "key": "carve-out",
        "title": "Carve a block out of an allowlist",
        "approach": "Split into two ranges, lowest set bit on each · O(32) · O(1)",
        "spec": {"kind": "fn", "fn": "carve_out", "params": ["parent", "excluded"], "cmp": "exact"},
        "statement": (
            "A security group allows `parent`, say `10.0.0.0/24`, but one subnet inside it must now be denied. "
            "Most firewalls cannot express \"allow except\", so the rule has to be rewritten as plain CIDRs.\n\n"
            "Given two valid, aligned CIDR blocks `parent` and `excluded`, return the **fewest** CIDR blocks that "
            "cover exactly the addresses of `parent` that are **not** in `excluded`, in address order.\n\n"
            "- If they do not overlap, the answer is `[parent]`.\n"
            "- If `excluded` covers all of `parent`, the answer is `[]`.\n\n"
            "Don't use the `ipaddress` module."
        ),
        "examples": [
            {"args": {"parent": "10.0.0.0/24", "excluded": "10.0.0.64/26"},
             "explanation": "Left of the hole: 10.0.0.0/26. Right of it: 10.0.0.128 to .255, which is one /25.",
             "why": {"t": "Hole in the middle", "d": "Both sides of the excluded block are re-covered."}},
            {"args": {"parent": "10.0.0.0/28", "excluded": "10.0.0.5/32"},
             "explanation": "0-4 needs a /30 and a /32; 6-15 needs a /31 and a /29.",
             "why": {"t": "Single address removed", "d": "Removing one address splits into a staircase."}},
        ],
        "constraints": ["parent and excluded are valid CIDRs whose address is a multiple of the block size",
                        "Prefix lengths 20 to 32 for parent, 0 to 32 for excluded"],
        "hints": [
            "Two aligned CIDR blocks are either disjoint or one contains the other.",
            "What remains is at most two ranges: before the hole and after it.",
            "Cover each range with the main problem's greedy: the largest aligned block at x is `x & -x`.",
        ],
        "tests": [
            {"args": {"parent": "10.0.0.0/24", "excluded": "10.0.1.0/24"}, "why": {"t": "Disjoint", "d": "Nothing to remove: [parent]."}},
            {"args": {"parent": "10.0.0.0/24", "excluded": "10.0.0.0/24"}, "why": {"t": "Same block", "d": "Everything removed: []."}},
            {"args": {"parent": "10.0.0.128/25", "excluded": "10.0.0.0/16"}, "why": {"t": "Excluded is larger", "d": "The parent sits inside the excluded block: []."}},
            {"args": {"parent": "10.0.0.0/24", "excluded": "10.0.0.0/25"}, "why": {"t": "Hole at the start", "d": "Only the upper half remains."}},
            {"args": {"parent": "10.0.0.0/24", "excluded": "10.0.0.255/32"}, "why": {"t": "Hole at the end", "d": "Removing the last address leaves 8 blocks."}},
            {"args": {"parent": "192.168.16.0/20", "excluded": "192.168.21.37/32"}, "why": {"t": "Large input", "d": "A /20 with one address carved out of the middle."}},
            {"args": {"parent": "255.255.255.252/30", "excluded": "255.255.255.254/31"}, "why": {"t": "Top of the space", "d": "The last block of IPv4 with its top half removed."}},
        ],
        "solutions": [
            {"name": "Two ranges + lowest set bit (Optimal)",
             "description": "Convert both blocks to [start, end) intervals. If they overlap, what remains is [p_start, e_start) and [e_end, p_end); cover each with the greedy from the main problem.",
             "time": "O(32)", "space": "O(1) besides the output",
             "keyPoints": ["Aligned blocks nest or are disjoint", "At most two leftover ranges", "Reuse range_to_cidrs on each range"],
             "code": _CIDR_HELPERS + _GREEDY + '''

def carve_out(parent, excluded):
    ps, pn = _parse(parent)
    es, en = _parse(excluded)
    pe, ee = ps + pn, es + en
    if ee <= ps or pe <= es:
        return [f"{_to_ip(ps)}/{32 - (pn.bit_length() - 1)}"]
    out = []
    if es > ps:
        _cover(ps, es - ps, out)
    if ee < pe:
        _cover(ee, pe - ee, out)
    return out
'''},
            {"name": "Enumerate and merge /32s", "slow": True,
             "description": "List every address of parent that is not in excluded, then merge aligned sibling blocks until nothing merges.",
             "time": "O(size · 32)", "space": "O(size)",
             "keyPoints": ["Obviously exact", "Memory grows with the size of the parent"],
             "code": _CIDR_HELPERS + _MERGE32 + '''

def carve_out(parent, excluded):
    ps, pn = _parse(parent)
    es, en = _parse(excluded)
    return _merge_addresses(a for a in range(ps, ps + pn) if not es <= a < es + en)
'''},
        ],
        "starter": '''def carve_out(parent: str, excluded: str) -> list[str]:
    pass
''',
    },
    {
        "key": "merge-allowlist",
        "title": "Compact an allowlist",
        "approach": "Sort + merge intervals, then lowest set bit · O(m log m) · O(m)",
        "spec": {"kind": "fn", "fn": "merge_cidrs", "params": ["cidrs"], "cmp": "exact"},
        "statement": (
            "An allowlist grew by copy and paste: `cidrs` holds CIDR blocks that may overlap, repeat or sit "
            "right next to each other. Cloud security groups cap the number of rules, so compact it.\n\n"
            "Return the **fewest** CIDR blocks that cover exactly the union of all addresses in `cidrs`, in "
            "address order. Each input block is valid and aligned. An empty list gives `[]`.\n\n"
            "Don't use the `ipaddress` module."
        ),
        "examples": [
            {"args": {"cidrs": ["10.0.0.0/25", "10.0.0.128/25", "10.0.1.0/24"]},
             "explanation": "The two /25s form 10.0.0.0/24, which with 10.0.1.0/24 forms one /23.",
             "why": {"t": "Adjacent blocks", "d": "Neighbors merge into a larger aligned block."}},
            {"args": {"cidrs": ["10.0.0.0/24", "10.0.0.16/28", "10.0.0.0/24"]},
             "explanation": "The /28 is inside the /24 and the /24 repeats: one block.",
             "why": {"t": "Nested and duplicate", "d": "Overlaps collapse into the enclosing block."}},
        ],
        "constraints": ["0 ≤ len(cidrs) ≤ 10^4", "Every block is a valid CIDR with an aligned address"],
        "hints": [
            "Turn every block into an interval `[start, end)` and merge overlapping or touching intervals.",
            "No CIDR block can span a gap between merged intervals, so each merged interval can be covered on its own.",
            "Cover each interval with the greedy from the main problem.",
        ],
        "tests": [
            {"args": {"cidrs": []}, "why": {"t": "Empty list", "d": "No blocks: []."}},
            {"args": {"cidrs": ["0.0.0.0/0"]}, "why": {"t": "Whole space", "d": "One /0 stays one /0."}},
            {"args": {"cidrs": ["10.0.0.1/32", "10.0.0.2/32"]}, "why": {"t": "Touching but misaligned", "d": "Adjacent /32s that cannot form a /31."}},
            {"args": {"cidrs": ["10.0.2.0/24", "10.0.0.0/24", "10.0.1.0/24", "10.0.3.0/24"]}, "why": {"t": "Unsorted input", "d": "Four /24s in any order make one /22."}},
            {"args": {"cidrs": ["10.0.0.0/24", "10.0.2.0/24"]}, "why": {"t": "Gap", "d": "A gap keeps the blocks apart."}},
            {"args": {"cidrs": ["172.16.0.0/22", "172.16.2.0/23", "172.16.4.0/24", "172.16.5.0/24", "172.16.6.0/23", "172.16.9.0/24", "172.16.10.0/23"]},
             "why": {"t": "Large input", "d": "Overlapping and adjacent blocks over about 2,800 addresses."}},
        ],
        "solutions": [
            {"name": "Merge intervals + lowest set bit (Optimal)",
             "description": "Sort the blocks as intervals, merge overlapping or touching ones, and cover each merged interval greedily with the largest aligned block at each point.",
             "time": "O(m log m + 32 · m)", "space": "O(m)",
             "keyPoints": ["Touching intervals (end == next start) merge too", "Gaps separate independent problems", "Reuse the greedy per interval"],
             "code": _CIDR_HELPERS + _GREEDY + '''

def merge_cidrs(cidrs):
    spans = sorted((s, s + n) for s, n in map(_parse, cidrs))
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    out = []
    for s, e in merged:
        _cover(s, e - s, out)
    return out
'''},
            {"name": "Set of addresses + merge /32s", "slow": True,
             "description": "Put every address of every block into a set, then merge aligned sibling blocks until nothing changes.",
             "time": "O(total addresses · 32)", "space": "O(total addresses)",
             "keyPoints": ["Duplicates and overlaps vanish in the set", "Unusable for large blocks such as a /8"],
             "code": _CIDR_HELPERS + _MERGE32 + '''

def merge_cidrs(cidrs):
    blocks = [_parse(c) for c in cidrs]
    if any(n == 1 << 32 for _, n in blocks):
        return ["0.0.0.0/0"]
    addrs = set()
    for s, n in blocks:
        addrs.update(range(s, s + n))
    return _merge_addresses(addrs)
'''},
        ],
        "starter": '''def merge_cidrs(cidrs: list[str]) -> list[str]:
    pass
''',
    },
]
