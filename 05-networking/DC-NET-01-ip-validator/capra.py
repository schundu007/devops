"""Capra Playground export for DC-NET-01 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "classify_address", "params": ["addr"], "types": {}, "ret": "value", "cmp": "exact"}


def c(addr, t, d):
    return {"args": {"addr": addr}, "why": {"t": t, "d": d}}


EXAMPLES = [
    {"args": {"addr": "10.0.3.17"}, "explanation": "Four decimal parts, each 0-255 with no leading zero.",
     "why": {"t": "Valid IPv4", "d": "A normal private address."}},
    {"args": {"addr": "2001:0db8:85a3:0000:0000:8a2e:0370:7334"}, "explanation": "Eight groups of 1-4 hex digits.",
     "why": {"t": "Valid IPv6", "d": "Full-form IPv6 with leading zeros in groups (allowed in IPv6)."}},
    {"args": {"addr": "0127.0.0.1"}, "explanation": "A leading zero is rejected: some parsers read 0127 as octal, which is how SSRF filters get bypassed.",
     "why": {"t": "Leading zero", "d": "The classic allow-list bypass input."}},
]

TESTS = [
    c("", "Empty", "An empty string is neither."),
    c("0.0.0.0", "All zeros", "Single '0' parts are valid."),
    c("255.255.255.255", "Upper boundary", "255 is the largest octet."),
    c("256.1.1.1", "Octet too big", "256 is out of range."),
    c("10.0.0", "Three parts", "Missing an octet."),
    c("10.0.0.1.", "Trailing dot", "A trailing separator makes an empty part."),
    c("10..0.1", "Empty part", "Two dots in a row."),
    c("1e1.0.0.1", "Non-digit", "Letters are not allowed in IPv4."),
    c("10.0.0.²", "Unicode digit", "'²' passes str.isdigit() but is not an ASCII digit."),
    c("2001:db8:85a3:0:0:8A2E:0370:7334", "Mixed case IPv6", "Hex digits may be upper or lower case."),
    c("2001:0db8:85a3::8a2e:0370:7334", "Shortened IPv6", "'::' shortening is not accepted by this validator."),
    c("2001:0db8:85a3:00000:0:8a2e:0370:7334", "Group too long", "Five hex digits in one group."),
    c("02001:db8:85a3:0:0:8a2e:370:7334", "Leading-zero group", "A 5-character first group is too long."),
    c("1:2:3:4:5:6:7:g", "Bad hex", "'g' is not a hex digit."),
    c("192.0.2.1:8080", "Host and port", "An address with a port is not a bare address."),
    c(" 10.0.0.1", "Leading space", "Whitespace is not trimmed."),
    c("1.2.3.04", "Leading zero, last octet", "The leading-zero rule applies to every octet."),
]


def _large():
    rng = random.Random(468)
    out = []
    for _ in range(12):
        out.append(".".join(str(rng.randint(0, 255)) for _ in range(4)))
    return out


TESTS += [c(a, "Random IPv4", "A randomly generated valid address.") for a in _large()[:6]]

SOLUTIONS = [
    {"file": "solution.py", "name": "Split and check each part (Optimal)",
     "description": "Three dots means check IPv4 (four parts, 1-3 ASCII digits, no leading zero, at most 255). Seven colons means check IPv6 (eight groups of 1-4 hex digits). Anything else is Neither.",
     "time": "O(n)", "space": "O(n)",
     "keyPoints": ["Reject leading zeros: 0127 may be read as octal", "Check ASCII digits explicitly: str.isdigit() accepts '²'", "Full-form IPv6 only: no '::' shortening"]},
    {"name": "Regular expressions", "slow": True,
     "description": "Match the whole string against one pattern for IPv4 and one for IPv6. Correct, but the octet range and leading-zero rules make the IPv4 pattern long and easy to get wrong.",
     "time": "O(n)", "space": "O(1)",
     "keyPoints": ["fullmatch, not match, so trailing text is rejected", "The octet pattern encodes 0-255 without leading zeros"],
     "code": '''import re

_OCTET = r"(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])"
_V4 = re.compile(rf"{_OCTET}(?:\\.{_OCTET}){{3}}", re.ASCII)
_V6 = re.compile(r"[0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{1,4}){7}", re.ASCII)


def classify_address(addr: str) -> str:
    if _V4.fullmatch(addr):
        return "IPv4"
    if _V6.fullmatch(addr):
        return "IPv6"
    return "Neither"
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Split and check", "idea": "Split on the separator and validate each part by hand.",
     "time": "O(n)", "space": "O(n)", "use": "Interviews: every rule is explicit and easy to explain."},
    {"name": "Regular expressions", "idea": "One anchored pattern per address family.",
     "time": "O(n)", "space": "O(1)", "use": "Quick filters; the octet pattern is easy to get subtly wrong."},
    {"name": "Standard library", "idea": "ipaddress.ip_address / net/netip.ParseAddr.",
     "time": "O(n)", "space": "O(1)", "use": "Production code: use the library, not your own parser."},
]

VARIANT_TITLE = "IPv4 or IPv6"
VARIANT_APPROACH = "Split and check each part · O(n) · O(n)"

_CIDR_FAST = '''from __future__ import annotations


def _octets(addr: str) -> list[int] | None:
    parts = addr.split(".")
    if len(parts) != 4:
        return None
    out = []
    for p in parts:
        if not (1 <= len(p) <= 3) or not all("0" <= ch <= "9" for ch in p):
            return None
        if len(p) > 1 and p[0] == "0":
            return None
        v = int(p)
        if v > 255:
            return None
        out.append(v)
    return out


def valid_cidr(block: str) -> bool:
    if block.count("/") != 1:
        return False
    addr, plen = block.split("/")
    octs = _octets(addr)
    if octs is None:
        return False
    if not (1 <= len(plen) <= 2) or not all("0" <= ch <= "9" for ch in plen):
        return False
    if len(plen) > 1 and plen[0] == "0":
        return False
    prefix = int(plen)
    if prefix > 32:
        return False
    value = (octs[0] << 24) | (octs[1] << 16) | (octs[2] << 8) | octs[3]
    host_mask = (1 << (32 - prefix)) - 1
    return value & host_mask == 0
'''

_CIDR_SLOW = '''from __future__ import annotations

import re

_OCTET = r"(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])"
_BLOCK = re.compile(rf"({_OCTET}(?:\\.{_OCTET}){{3}})/(3[0-2]|[12][0-9]|[0-9])", re.ASCII)


def valid_cidr(block: str) -> bool:
    m = _BLOCK.fullmatch(block)
    if not m:
        return False
    bits = "".join(f"{int(o):08b}" for o in m.group(1).split("."))
    return "1" not in bits[int(m.group(2)):]
'''

_V6_FAST = '''from __future__ import annotations

HEX = set("0123456789abcdefABCDEF")


def _count(side: str) -> int:
    if side == "":
        return 0
    groups = side.split(":")
    for g in groups:
        if not (1 <= len(g) <= 4) or not all(ch in HEX for ch in g):
            return -1
    return len(groups)


def valid_ipv6(addr: str) -> bool:
    halves = addr.split("::")
    if len(halves) > 2:
        return False
    if len(halves) == 1:
        return _count(addr) == 8
    left, right = _count(halves[0]), _count(halves[1])
    if left < 0 or right < 0:
        return False
    return left + right <= 7
'''

_V6_SLOW = '''from __future__ import annotations

HEX = set("0123456789abcdefABCDEF")


def _full(addr: str) -> bool:
    groups = addr.split(":")
    return len(groups) == 8 and all(1 <= len(g) <= 4 and all(ch in HEX for ch in g) for g in groups)


def valid_ipv6(addr: str) -> bool:
    halves = addr.split("::")
    if len(halves) == 1:
        return _full(addr)
    if len(halves) != 2:
        return False
    left, right = halves
    for fill in range(1, 9):
        zeros = ":".join(["0"] * fill)
        candidate = left + (":" if left else "") + zeros + (":" if right else "") + right
        if _full(candidate):
            return True
    return False
'''


def _cidr(block, t, d):
    return {"args": {"block": block}, "why": {"t": t, "d": d}}


def _v6(addr, t, d):
    return {"args": {"addr": addr}, "why": {"t": t, "d": d}}


VARIANTS = [
    {
        "key": "cidr-block",
        "title": "CIDR block for a firewall rule",
        "approach": "Split, check, then mask the host bits · O(n) · O(1)",
        "spec": {"kind": "fn", "fn": "valid_cidr", "params": ["block"]},
        "statement": (
            "A firewall API takes allow rules as IPv4 CIDR blocks such as `10.0.0.0/8`. "
            "Return `True` only when `block` is a clean network block:\n\n"
            "- the address part follows the IPv4 rules (four parts, ASCII digits, 0-255, no leading zero)\n"
            "- exactly one `/` followed by a prefix length from 0 to 32, with no leading zero\n"
            "- every **host bit** (the bits after the prefix) is zero, so `10.0.0.1/8` is rejected\n\n"
            "A block with host bits set usually means someone pasted a host address and meant a /32; "
            "rejecting it stops a rule from quietly covering far more than intended."
        ),
        "examples": [
            {"args": {"block": "10.0.0.0/8"}, "explanation": "Only the first 8 bits are set, and they are all network bits.",
             "why": {"t": "Clean block", "d": "A normal private /8."}},
            {"args": {"block": "10.0.0.1/8"}, "explanation": "The last bit is a host bit, so this is a host address, not a network block.",
             "why": {"t": "Host bits set", "d": "The mistake the rule exists to catch."}},
        ],
        "constraints": ["0 ≤ block.length ≤ 40", "block is any printable string"],
        "hints": [
            "Split on `/` first; reuse the IPv4 part checks from the main problem on the left side.",
            "Pack the four octets into one 32-bit integer.",
            "The host mask is `(1 << (32 - prefix)) - 1`; the block is clean when `value & mask == 0`.",
        ],
        "tests": [
            _cidr("0.0.0.0/0", "Default route", "A /0 has no network bits, so the address must be all zeros."),
            _cidr("255.255.255.255/32", "Single host", "A /32 has no host bits."),
            _cidr("192.168.1.128/25", "Upper half", "The top half of a /24 split in two."),
            _cidr("192.168.1.64/25", "Mid-octet host bit", "64 sets a bit after the 25th."),
            _cidr("172.17.0.0/12", "Boundary inside an octet", "172.17 sets a host bit inside the second octet."),
            _cidr("172.16.0.0/12", "Clean /12", "The RFC 1918 172.16 block."),
            _cidr("10.0.0.0/33", "Prefix too long", "33 is past the 32 address bits."),
            _cidr("10.0.0.0/08", "Leading-zero prefix", "The prefix follows the no-leading-zero rule too."),
            _cidr("10.0.0.0", "No prefix", "A bare address is not a block."),
            _cidr("10.0.0.0/", "Empty prefix", "The slash needs digits after it."),
            _cidr("10.0.0.0/8/8", "Two slashes", "Only one prefix is allowed."),
            _cidr("010.0.0.0/8", "Leading-zero octet", "The address rules still apply."),
            _cidr("", "Empty", "An empty string is not a block."),
        ],
        "solutions": [
            {"name": "Split, check and mask (Optimal)",
             "description": "Validate the address and prefix by hand, pack the octets into a 32-bit integer, and check that the host mask selects only zero bits.",
             "time": "O(n)", "space": "O(1)",
             "keyPoints": ["Reuse the strict octet check", "Host mask = (1 << (32 - prefix)) - 1", "Prefix 0 means the whole address must be zero"],
             "code": _CIDR_FAST},
            {"name": "Regex and bit string", "slow": True,
             "description": "Match the block with one anchored pattern, write the address as a 32-character bit string, and check no '1' follows the prefix.",
             "time": "O(n)", "space": "O(1)",
             "keyPoints": ["fullmatch rejects trailing text", "Building the bit string is easy to read but allocates"],
             "code": _CIDR_SLOW},
        ],
        "starter": "def valid_cidr(block: str) -> bool:\n    pass\n",
    },
    {
        "key": "ipv6-shortened",
        "title": "IPv6 with :: shortening",
        "approach": "Split once on :: and count groups · O(n) · O(n)",
        "spec": {"kind": "fn", "fn": "valid_ipv6", "params": ["addr"]},
        "statement": (
            "Real IPv6 addresses in configs and logs are almost always shortened: `fe80::1`, `2001:db8::8a2e:370:7334`, `::`. "
            "Return `True` when `addr` is a valid IPv6 address, full or shortened:\n\n"
            "- every group is 1-4 hex digits (either case)\n"
            "- without `::` there must be exactly 8 groups\n"
            "- `::` may appear **at most once** and stands for **one or more** zero groups, so the written groups must number 7 or fewer\n\n"
            "Embedded IPv4 (`::ffff:1.2.3.4`) and zone IDs (`%eth0`) are not accepted."
        ),
        "examples": [
            {"args": {"addr": "2001:db8::8a2e:370:7334"}, "explanation": "Five written groups; :: fills in the other three.",
             "why": {"t": "Shortened", "d": "The common documentation-prefix form."}},
            {"args": {"addr": "1::2::3"}, "explanation": "With two :: nobody can tell how many zeros each one holds.",
             "why": {"t": "Two ::", "d": "Ambiguous, so invalid."}},
        ],
        "constraints": ["0 ≤ addr.length ≤ 45", "addr is any printable string"],
        "hints": [
            "Split on `::`. More than two pieces means more than one `::`.",
            "Each side of `::` is an ordinary colon-separated list of groups, or empty.",
            "`::` must replace at least one group, so the two sides together hold at most 7.",
        ],
        "tests": [
            _v6("::", "All zeros", "The unspecified address: :: alone is valid."),
            _v6("::1", "Loopback", "One written group after ::."),
            _v6("fe80::", "Trailing ::", "Nothing after the ::."),
            _v6("1:2:3:4:5:6:7::", "Seven plus ::", "The :: stands for exactly one group."),
            _v6("1:2:3:4:5:6:7:8::", "Eight plus ::", "No room left for :: to stand for anything."),
            _v6("1:2:3:4:5:6:7:8", "Full form", "Eight groups without :: is still valid."),
            _v6("1:2:3:4:5:6:7", "Seven without ::", "Too few groups when nothing is shortened."),
            _v6(":::", "Triple colon", "A stray colon next to ::."),
            _v6(":1:2:3:4:5:6:7", "Leading single colon", "A lone leading colon makes an empty group."),
            _v6("2001:DB8::AbCd", "Mixed case", "Hex digits may be upper or lower case."),
            _v6("::ffff:1.2.3.4", "Embedded IPv4", "The dotted tail is out of scope here."),
            _v6("12345::1", "Group too long", "Five hex digits in one group."),
            _v6("", "Empty", "An empty string is not an address."),
        ],
        "solutions": [
            {"name": "Split once and count (Optimal)",
             "description": "Split on '::'. With one piece, require 8 valid groups. With two, validate each side's groups and require at most 7 in total.",
             "time": "O(n)", "space": "O(n)",
             "keyPoints": ["More than two pieces means a second ::", "An empty side counts as zero groups", ":: must stand for at least one group"],
             "code": _V6_FAST},
            {"name": "Expand every possible fill", "slow": True,
             "description": "Replace '::' with 1 to 8 zero groups in turn and check whether any expansion is a valid full-form address.",
             "time": "O(8 · n)", "space": "O(n)",
             "keyPoints": ["Reuses the full-form checker", "Tries fills that can never fit"],
             "code": _V6_SLOW},
        ],
        "starter": "def valid_ipv6(addr: str) -> bool:\n    pass\n",
    },
]
