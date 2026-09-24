"""DC-NET-01 IP Address Validator — reference solution."""
from __future__ import annotations

HEX_DIGITS = set("0123456789abcdefABCDEF")


def _is_ipv4(addr: str) -> bool:
    parts = addr.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        # Only ASCII digits, 1-3 of them. str.isdigit() alone would accept "²" or "٣".
        if not (1 <= len(part) <= 3) or not all("0" <= ch <= "9" for ch in part):
            return False
        # A leading zero is ambiguous: some parsers read "0127" as octal (= 87).
        if len(part) > 1 and part[0] == "0":
            return False
        if int(part) > 255:
            return False
    return True


def _is_ipv6(addr: str) -> bool:
    groups = addr.split(":")
    if len(groups) != 8:  # full form only; "::" shortening is not accepted here
        return False
    return all(1 <= len(g) <= 4 and all(ch in HEX_DIGITS for ch in g) for g in groups)


def classify_address(addr: str) -> str:
    """Return "IPv4", "IPv6" or "Neither" for one address string."""
    if addr.count(".") == 3 and _is_ipv4(addr):
        return "IPv4"
    if addr.count(":") == 7 and _is_ipv6(addr):
        return "IPv6"
    return "Neither"
