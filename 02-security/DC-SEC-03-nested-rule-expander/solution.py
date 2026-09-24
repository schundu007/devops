"""DC-SEC-03 Nested Rule Expander — reference solution."""
from __future__ import annotations


def expand(template: str, max_output: int = 100_000) -> str:
    """Expand every `k[body]` block into `body` repeated k times.

    Raises ValueError if the expanded text would exceed `max_output` characters,
    so a tiny template cannot blow up memory (an "expansion bomb").
    """
    # Each stack frame: (text built before this block opened, repeat count).
    stack: list[tuple[list[str], int]] = []
    current: list[str] = []
    length = 0          # length of `current`, tracked so the cap check is O(1)
    lengths: list[int] = []
    count = 0
    for ch in template:
        if ch.isdigit():
            count = count * 10 + int(ch)   # counts can have several digits
        elif ch == "[":
            stack.append((current, count))
            lengths.append(length)
            current, length, count = [], 0, 0
        elif ch == "]":
            outer, k = stack.pop()
            outer_len = lengths.pop()
            body = "".join(current)
            new_len = outer_len + k * len(body)
            if new_len > max_output:
                raise ValueError("expanded output exceeds max_output")
            outer.append(body * k)
            current, length = outer, new_len
        else:
            current.append(ch)
            length += 1
            if length > max_output:
                raise ValueError("expanded output exceeds max_output")
    return "".join(current)
