"""DC-NET-02 Rebuild IPs from Broken Logs — reference solution."""
from __future__ import annotations


def _valid_octet(s: str) -> bool:
    # 1-3 digits, no leading zero (except "0" itself), value <= 255.
    return 1 <= len(s) <= 3 and (s == "0" or s[0] != "0") and int(s) <= 255


def restore_addresses(digits: str) -> list[str]:
    """Every valid dotted IPv4 address that `digits` could have been before the dots were lost."""
    out: list[str] = []
    if not digits.isascii() or not digits.isdigit() or not 4 <= len(digits) <= 12:
        return out  # fewer than 4 or more than 12 digits can never form an IPv4

    parts: list[str] = []

    def place(start: int) -> None:
        left_parts = 4 - len(parts)
        left_chars = len(digits) - start
        # Prune: each remaining octet needs 1-3 digits.
        if not left_parts <= left_chars <= 3 * left_parts:
            return
        if left_parts == 0:
            out.append(".".join(parts))
            return
        for size in (1, 2, 3):
            octet = digits[start:start + size]
            if len(octet) == size and _valid_octet(octet):
                parts.append(octet)       # choose
                place(start + size)       # explore
                parts.pop()               # un-choose

    place(0)
    return out
