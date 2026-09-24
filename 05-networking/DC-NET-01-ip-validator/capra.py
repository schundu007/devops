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
