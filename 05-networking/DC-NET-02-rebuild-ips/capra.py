"""Capra Playground export for DC-NET-02 (see tools/export_capra.py)."""

SPEC = {"kind": "fn", "fn": "restore_addresses", "params": ["digits"], "types": {}, "ret": "value", "cmp": "unordered"}


def c(digits, t, d):
    return {"args": {"digits": digits}, "why": {"t": t, "d": d}}


EXAMPLES = [
    {"args": {"digits": "19216811"}, "explanation": "Nine ways to place three dots give a valid address; any order is accepted.",
     "why": {"t": "Log forensics", "d": "The anchor case: a log field lost its dots."}},
    {"args": {"digits": "0000"}, "explanation": "Only 0.0.0.0: a part may be '0' but never '00'.",
     "why": {"t": "All zeros", "d": "The leading-zero rule leaves one answer."}},
    {"args": {"digits": "101023"}, "explanation": "Five candidates; '1.0.10.23' is valid but '1.01.0.23' is not.",
     "why": {"t": "Zero inside", "d": "Zeros in the middle force single-digit parts."}},
]

TESTS = [
    c("", "Empty", "No digits: no address."),
    c("123", "Too short", "Fewer than 4 digits can never make 4 parts."),
    c("1111", "Minimum length", "Exactly 4 digits: one address."),
    c("255255255255", "Maximum length", "12 digits: every part must be 3 digits."),
    c("2552552552551", "Too long", "13 digits cannot fit."),
    c("256256256256", "All parts too big", "Every 3-digit split is above 255."),
    c("010010", "Leading zeros", "Parts like '01' and '010' are rejected."),
    c("1921680114", "Private range", "A 10-digit 192.168.x.x value."),
    c("100200", "Trailing zeros", "Zeros force some splits and forbid others."),
    c("12a4", "Non-digit", "A letter in the field: no address."),
    c("1000000", "One then zeros", "No valid reading: every split leaves a part like '00' or '000'."),
    c("25525511135", "Classic", "Two valid readings."),
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Backtracking with pruning (Optimal)",
     "description": "Choose a 1-3 digit part, recurse on the rest, then undo the choice. Skip parts with a leading zero or a value above 255, and prune when the digits left cannot fill the parts left.",
     "time": "O(1)", "space": "O(1)",
     "keyPoints": ["At most 3^4 = 81 leaves", "Prune on remaining digits vs remaining parts", "'0' is a valid part, '01' is not"]},
    {"name": "Try every dot placement", "slow": True,
     "description": "Try all choices of three cut positions and keep the ones where every part is valid.",
     "time": "O(1) (at most C(11,3) = 165 placements)", "space": "O(1)",
     "keyPoints": ["Three nested loops over cut positions", "Simple to write; no pruning"],
     "code": '''def restore_addresses(digits: str) -> list[str]:
    def ok(p: str) -> bool:
        return 1 <= len(p) <= 3 and p.isascii() and p.isdigit() and (p == "0" or p[0] != "0") and int(p) <= 255

    out = []
    n = len(digits)
    for i in range(1, n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                parts = [digits[:i], digits[i:j], digits[j:k], digits[k:]]
                if all(ok(p) for p in parts):
                    out.append(".".join(parts))
    return out
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Every dot placement", "idea": "Three nested loops over the cut positions; validate the four parts.",
     "time": "O(1)", "space": "O(1)", "use": "Fixed 4 parts: simplest correct answer."},
    {"name": "Backtracking", "idea": "Choose a part, recurse, un-choose; prune impossible lengths early.",
     "time": "O(1)", "space": "O(1)", "use": "Generalizes to any number of parts (e.g. IPv6 groups)."},
]

VARIANT_TITLE = "Restore every address"
VARIANT_APPROACH = "Backtracking with pruning · O(1) · O(1)"

_CIDR_FAST = '''def restore_in_cidr(digits: str, cidr: str) -> list[str]:
    base, plen = cidr.split("/")
    p = int(plen)
    mask = (0xFFFFFFFF << (32 - p)) & 0xFFFFFFFF
    net = 0
    for o in base.split("."):
        net = (net << 8) | int(o)
    net &= mask
    n = len(digits)
    out = []

    def go(pos: int, parts: list[str], value: int) -> None:
        k = len(parts)
        if k:
            top = (0xFFFFFFFF << (32 - 8 * k)) & 0xFFFFFFFF
            if ((value << (32 - 8 * k)) ^ net) & mask & top:
                return
        if k == 4:
            if pos == n:
                out.append(".".join(parts))
            return
        left = n - pos
        if left < 4 - k or left > 3 * (4 - k):
            return
        for size in (1, 2, 3):
            part = digits[pos:pos + size]
            if len(part) < size or not (part.isascii() and part.isdigit()):
                break
            if (size > 1 and part[0] == "0") or int(part) > 255:
                break
            go(pos + size, parts + [part], (value << 8) | int(part))

    go(0, [], 0)
    return sorted(out)
'''

_CIDR_SLOW = '''def restore_in_cidr(digits: str, cidr: str) -> list[str]:
    def ok(p: str) -> bool:
        return 1 <= len(p) <= 3 and p.isascii() and p.isdigit() and (p == "0" or p[0] != "0") and int(p) <= 255

    def to_int(parts: list[str]) -> int:
        v = 0
        for x in parts:
            v = (v << 8) | int(x)
        return v

    base, plen = cidr.split("/")
    p = int(plen)
    mask = (0xFFFFFFFF << (32 - p)) & 0xFFFFFFFF
    net = to_int(base.split(".")) & mask
    out = []
    n = len(digits)
    for i in range(1, n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                parts = [digits[:i], digits[i:j], digits[j:k], digits[k:]]
                if all(ok(x) for x in parts) and to_int(parts) & mask == net:
                    out.append(".".join(parts))
    return sorted(out)
'''

_SPLIT_FAST = '''def count_splits(digits: str) -> int:
    n = len(digits)
    if n == 0 or not (digits.isascii() and digits.isdigit()):
        return 0
    ways = [[0] * 4 for _ in range(n + 1)]
    ways[0][0] = 1
    for i in range(n):
        for r in range(4):
            w = ways[i][r]
            if not w:
                continue
            for size in (1, 2, 3):
                part = digits[i:i + size]
                if len(part) < size or (size > 1 and part[0] == "0") or int(part) > 255:
                    break
                ways[i + size][(r + 1) % 4] += w
    return ways[n][0]
'''

_SPLIT_SLOW = '''def count_splits(digits: str) -> int:
    if not digits or not (digits.isascii() and digits.isdigit()):
        return 0

    def ok(p: str) -> bool:
        return (p == "0" or p[0] != "0") and int(p) <= 255

    def go(pos: int, parts: int) -> int:
        if pos == len(digits):
            return 1 if parts % 4 == 0 else 0
        total = 0
        for size in (1, 2, 3):
            part = digits[pos:pos + size]
            if len(part) == size and ok(part):
                total += go(pos + size, parts + 1)
        return total

    return go(0, 0)
'''


def _cc(digits, cidr, t, d):
    return {"args": {"digits": digits, "cidr": cidr}, "why": {"t": t, "d": d}}


def _sc(digits, t, d):
    return {"args": {"digits": digits}, "why": {"t": t, "d": d}}


VARIANTS = [
    {
        "key": "restore-in-cidr",
        "title": "Restore inside a subnet",
        "approach": "Backtracking with a prefix-mask prune · O(1) · O(1)",
        "spec": {"kind": "fn", "fn": "restore_in_cidr", "params": ["digits", "cidr"], "cmp": "exact"},
        "statement": (
            "A firewall log stripped the dots from source addresses, but the incident is scoped: only traffic "
            "from one subnet matters. Given the digit string `digits` and a subnet `cidr` such as `10.0.0.0/8`, "
            "return every valid IPv4 reading of `digits` that falls **inside** the subnet.\n\n"
            "- Each of the four parts is 0-255 with no leading zeros (`0` is fine, `01` is not)\n"
            "- An address is inside `a.b.c.d/p` when its first `p` bits equal the subnet's first `p` bits\n"
            "- Host bits set in the `cidr` itself are ignored\n\n"
            "Return the addresses sorted as strings, ascending."
        ),
        "examples": [
            {"args": {"digits": "10010010", "cidr": "10.0.0.0/8"},
             "explanation": "Only readings that start with octet 10 can be in 10.0.0.0/8, and of those only 10.0.100.10 has no leading zero. 100.10.0.10 is valid but outside the subnet.",
             "why": {"t": "Private /8", "d": "The first octet is fixed by the subnet."}},
            {"args": {"digits": "19216811", "cidr": "192.168.1.0/24"},
             "explanation": "Nine readings exist, but only 192.168.1.1 has 192.168.1 as its first three octets.",
             "why": {"t": "One /24", "d": "Three octets are fixed; one reading survives."}},
        ],
        "constraints": [
            "0 ≤ digits.length ≤ 20",
            "cidr is `a.b.c.d/p` with 0 ≤ a, b, c, d ≤ 255 and 0 ≤ p ≤ 32",
            "digits may contain non-digit characters (no address then)",
        ],
        "hints": [
            "Build octets left to right as in the classic problem, carrying the numeric value so far.",
            "After k octets you already know the top 8k bits: compare them with the subnet under the mask and stop early on a mismatch.",
            "A /0 subnet accepts everything; a /32 accepts exactly one address.",
        ],
        "tests": [
            _cc("", "0.0.0.0/0", "Empty", "No digits: nothing to restore."),
            _cc("1111", "0.0.0.0/0", "Match-all subnet", "/0 keeps every reading."),
            _cc("1111", "1.1.1.1/32", "Single host", "/32 keeps only the exact address."),
            _cc("1111", "1.1.1.2/32", "No match", "The only reading is outside the /32."),
            _cc("172161005", "172.16.0.0/12", "Non-octet prefix", "A /12 fixes the first octet and half of the second."),
            _cc("25525511135", "255.255.0.0/16", "Classic digits", "Both classic readings sit inside 255.255/16."),
            _cc("10010010", "10.0.0.255/8", "Host bits in cidr", "The .255 in the subnet is ignored."),
            _cc("12a4", "0.0.0.0/0", "Non-digit", "A letter in the field: no address."),
            _cc("1011121314", "10.0.0.0/8", "Long field", "Many readings exist; only one starts with octet 10."),
        ],
        "solutions": [
            {"name": "Backtracking with a mask prune (Optimal)",
             "description": "Choose each octet as in the classic problem, keep the numeric value so far, and cut a branch as soon as its known top bits leave the subnet.",
             "time": "O(1)", "space": "O(1)",
             "keyPoints": ["After k octets the top 8k bits are fixed", "Compare (value ^ net) under mask and the known-bits mask", "Normalize the subnet with net & mask"],
             "code": _CIDR_FAST},
            {"name": "Restore all, then filter", "slow": True,
             "description": "Try every placement of three dots, keep valid readings, and test each full address against the subnet.",
             "time": "O(1) (at most 165 placements)", "space": "O(1)",
             "keyPoints": ["Reuses the classic answer unchanged", "Checks the subnet only on complete addresses"],
             "code": _CIDR_SLOW},
        ],
        "starter": "def restore_in_cidr(digits: str, cidr: str) -> list[str]:\n    pass\n",
    },
    {
        "key": "count-address-splits",
        "title": "Count merged address lists",
        "approach": "DP over position and octet count mod 4 · O(n) · O(n)",
        "spec": {"kind": "fn", "fn": "count_splits", "params": ["digits"], "cmp": "exact"},
        "statement": (
            "A broken exporter wrote a list of IPv4 addresses into one field with **every** separator removed: "
            "no dots and no commas. Before trying to repair the data, count how ambiguous it is.\n\n"
            "Return the number of ways to cut `digits` into a sequence of **one or more** valid IPv4 addresses. "
            "Each address is four parts of 0-255 with no leading zeros, and the parts are read in order.\n\n"
            "An empty string or a string with a non-digit has 0 readings."
        ),
        "examples": [
            {"args": {"digits": "1111"}, "explanation": "Only 1.1.1.1.",
             "why": {"t": "One address", "d": "Four digits: a single reading."}},
            {"args": {"digits": "11111111"},
             "explanation": "One reading is two addresses (1.1.1.1 then 1.1.1.1); the other 19 are a single address such as 11.11.11.11 or 1.1.111.111. 20 in total.",
             "why": {"t": "One or two addresses", "d": "The same digits can hold one address or two."}},
        ],
        "constraints": ["0 ≤ digits.length ≤ 24", "digits may contain non-digit characters"],
        "hints": [
            "Where an address ends does not matter, only how many parts have been read so far, modulo 4.",
            "Let ways[i][r] be the number of ways to read digits[:i] into parts with r = parts mod 4; each step adds a 1-3 digit part.",
            "The answer is ways[n][0] for a non-empty string.",
        ],
        "tests": [
            _sc("", "Empty", "No digits: 0 readings."),
            _sc("123", "Too short", "Fewer than 4 digits cannot hold one address."),
            _sc("0000", "All zeros", "Only 0.0.0.0."),
            _sc("00000", "Five zeros", "5 parts of '0' is not a multiple of 4, and '00' is invalid."),
            _sc("255255255255", "Twelve digits", "One, two or three addresses: many readings, not just 255.255.255.255."),
            _sc("1a11", "Non-digit", "A letter: 0 readings."),
            _sc("25525511135", "Classic digits", "11 digits: one address or two."),
            _sc("1921681110010", "Two addresses?", "13 digits could be one or two addresses."),
            _sc("123123123123123123123123", "Large input", "24 digits: up to six addresses."),
        ],
        "solutions": [
            {"name": "DP on parts mod 4 (Optimal)",
             "description": "ways[i][r] counts readings of the first i digits with r parts mod 4. From each state add a valid 1-3 digit part.",
             "time": "O(n)", "space": "O(n)",
             "keyPoints": ["Address boundaries are implied by the part count", "Each state has at most 3 transitions", "Leading zero and >255 stop the part from growing"],
             "code": _SPLIT_FAST},
            {"name": "Enumerate every reading", "slow": True,
             "description": "Recursively try a 1-3 digit part at each position and count complete readings whose part count is a multiple of 4.",
             "time": "O(3^n) worst case", "space": "O(n)",
             "keyPoints": ["Obviously correct", "Recomputes the same suffix many times"],
             "code": _SPLIT_SLOW},
        ],
        "starter": "def count_splits(digits: str) -> int:\n    pass\n",
    },
]
