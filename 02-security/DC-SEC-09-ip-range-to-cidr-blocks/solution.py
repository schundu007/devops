"""DC-SEC-09 IP Range to CIDR Blocks — reference solution."""
from __future__ import annotations


def _to_int(ip: str) -> int:
    a, b, c, d = (int(x) for x in ip.split("."))
    return (a << 24) | (b << 16) | (c << 8) | d


def _to_ip(x: int) -> str:
    return ".".join(str((x >> shift) & 0xFF) for shift in (24, 16, 8, 0))


def range_to_cidrs(start_ip: str, count: int) -> list[str]:
    """Fewest CIDR blocks that cover exactly `count` addresses from `start_ip`, in order."""
    x = _to_int(start_ip)
    out: list[str] = []
    while count > 0:
        # x & -x is the lowest set bit: the largest block that can START at x
        # (a /n block must begin on a multiple of its size). 0 can start anything.
        step = x & -x if x else 1 << 32
        while step > count:
            step >>= 1          # shrink until the block fits in what is left
        prefix = 32 - (step.bit_length() - 1)
        out.append(f"{_to_ip(x)}/{prefix}")
        x += step
        count -= step
    return out
