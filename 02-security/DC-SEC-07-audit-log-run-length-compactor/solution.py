"""DC-SEC-07 Audit Log Run-Length Compactor — reference solution."""
from __future__ import annotations


def compress(buf: list[str]) -> int:
    """Run-length encode `buf` in place and return the new length.

    Each run becomes the character, followed by the run length in decimal
    if the run is longer than 1. `buf[:returned]` holds the result.
    """
    write = 0   # next slot to write; never passes `read`, so no data is lost
    read = 0
    n = len(buf)
    while read < n:
        ch = buf[read]
        run_start = read
        while read < n and buf[read] == ch:
            read += 1
        buf[write] = ch
        write += 1
        run = read - run_start
        if run > 1:
            # A run of length r writes 1 + len(str(r)) <= r slots, so writing
            # the digits in place never overwrites unread input.
            for digit in str(run):
                buf[write] = digit
                write += 1
    return write
