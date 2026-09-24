"""DC-SEC-20 Nested Config Parser — reference solution."""
from __future__ import annotations

Nested = int | list  # an int, or a list of Nested


def parse(s: str, max_depth: int = 64) -> Nested:
    """Parse "123" or "[1,[2,[3]],[]]" into ints and lists.

    Raises ValueError if lists nest deeper than max_depth.
    """
    if s[0] != "[":
        return int(s)
    stack: list[list] = []   # open lists, innermost last; its length is the depth
    num = ""                 # digits (and a leading "-") of the number being read
    result: list = []
    for ch in s:
        if ch == "[":
            if len(stack) == max_depth:
                # Refuse before allocating more: this is the DoS guard.
                raise ValueError(f"nesting deeper than {max_depth}")
            new: list = []
            if stack:
                stack[-1].append(new)
            stack.append(new)
        elif ch == "-" or ch.isdigit():
            num += ch
        else:  # "," or "]" ends any number in progress
            if num:
                stack[-1].append(int(num))
                num = ""
            if ch == "]":
                result = stack.pop()
    return result
