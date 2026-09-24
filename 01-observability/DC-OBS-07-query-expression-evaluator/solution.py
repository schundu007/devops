"""DC-OBS-07 Query Expression Evaluator — reference solution."""
from __future__ import annotations


def evaluate(expr: str, values: dict[str, int]) -> int:
    """Evaluate +, -, parentheses, integers and metric names looked up in `values`."""
    result = 0   # running total of the current parenthesis level
    sign = 1     # sign to apply to the next operand
    stack: list[tuple[int, int]] = []  # (total before '(', sign in front of '(')
    i, n = 0, len(expr)
    while i < n:
        ch = expr[i]
        if ch.isdigit() or ch.isalpha() or ch == "_":
            j = i
            if ch.isdigit():
                while j < n and expr[j].isdigit():
                    j += 1
                operand = int(expr[i:j])
            else:
                while j < n and (expr[j].isalnum() or expr[j] == "_"):
                    j += 1
                operand = values[expr[i:j]]  # unknown metric -> KeyError
            result += sign * operand
            i = j
            continue
        if ch == "+":
            sign = 1
        elif ch == "-":
            sign = -1
        elif ch == "(":
            # Save this level and start a fresh one inside the parentheses.
            stack.append((result, sign))
            result, sign = 0, 1
        elif ch == ")":
            outer, outer_sign = stack.pop()
            result = outer + outer_sign * result
        elif ch != " ":
            raise ValueError(f"unexpected character {ch!r} at {i}")
        i += 1
    return result
