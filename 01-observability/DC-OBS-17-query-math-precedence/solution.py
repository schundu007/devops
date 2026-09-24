"""DC-OBS-17 Query Math with Precedence — reference solution."""
from __future__ import annotations


def evaluate(expr: str) -> int:
    """Evaluate non-negative integers with + - * / and spaces, no parentheses.

    * and / bind tighter than + and -. Division truncates toward zero.
    """
    stack: list[int] = []  # terms that will be added together at the end
    num = 0
    op = "+"               # the operator in front of the number being read
    for i, ch in enumerate(expr):
        if ch.isdigit():
            num = num * 10 + int(ch)
        if (not ch.isdigit() and ch != " ") or i == len(expr) - 1:
            # The number is complete: apply the operator that came before it.
            if op == "+":
                stack.append(num)
            elif op == "-":
                stack.append(-num)
            elif op == "*":
                stack.append(stack.pop() * num)   # * and / act on the previous term now
            else:
                prev = stack.pop()
                q = abs(prev) // num                  # exact integer math, no float rounding
                stack.append(q if prev >= 0 else -q)  # truncate toward zero, not floor
            op, num = ch, 0
    return sum(stack)
