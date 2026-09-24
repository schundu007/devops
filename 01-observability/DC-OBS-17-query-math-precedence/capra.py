"""Capra Playground export for DC-OBS-17 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "evaluate", "params": ["expr"], "types": {}, "ret": "value", "cmp": "exact"}


def case(expr):
    return {"expr": expr}


EXAMPLES = [
    {"args": case("3+2*2"),
     "explanation": "* binds tighter than +, so this is 3 + (2 * 2) = 7.",
     "why": {"t": "Precedence", "d": "Multiplication happens before addition."}},
    {"args": case(" 3/2 "),
     "explanation": "Integer division truncates toward zero: 3 / 2 = 1. Spaces are ignored.",
     "why": {"t": "Division · Spaces", "d": "Truncating division, with spaces around the expression."}},
    {"args": case("500 * 100 / 2000"),
     "explanation": "errors * 100 / total, evaluated left to right: 50000 / 2000 = 25 (percent).",
     "why": {"t": "Error percentage", "d": "The production query from the scenario."}},
]


def _large():
    rng = random.Random(227)
    parts = [str(rng.randint(0, 999))]
    for _ in range(400):
        op = rng.choice("+-*/")
        parts.append(op)
        parts.append(str(rng.randint(1, 999)))
    return case(" ".join(parts))


TESTS = [
    {"args": case("42"), "why": {"t": "Single number", "d": "No operators at all."}},
    {"args": case("0"), "why": {"t": "Zero", "d": "The smallest number."}},
    {"args": case("2-7/2"), "why": {"t": "Truncate toward zero", "d": "-7 / 2 is -3 (toward zero), not -4 (floor)."}},
    {"args": case("14-3/2"), "why": {"t": "Division after minus", "d": "3 / 2 = 1 is applied before the subtraction."}},
    {"args": case("1 + 2 * 3 - 4 / 2 * 5 + 6"), "why": {"t": "Mixed chain", "d": "Several * and / terms between + and -."}},
    {"args": case("2147483647*1"), "why": {"t": "32-bit max", "d": "The largest number the constraints allow."}},
    {"args": case("  7  "), "why": {"t": "Spaces only around", "d": "Leading and trailing spaces around one number."}},
    {"args": case("100/3/3*9"), "why": {"t": "Left to right", "d": "Operators of equal precedence apply left to right."}},
    {"args": _large(), "why": {"t": "Large input", "d": "A random expression of about 400 operators."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Stack of terms (Optimal)",
     "description": "Scan once, building each number. When a number ends, apply the operator in front of it: push it, push its negative, or combine it with the top term for * and /. The answer is the sum of the stack.",
     "time": "O(n)", "space": "O(n)",
     "keyPoints": ["Remember the operator before the current number", "* and / act on the previous term immediately", "Truncate toward zero with integer math, not floats"]},
    {"name": "Two passes over tokens", "slow": True,
     "description": "Tokenize, then fold every * and / into its left neighbour in one pass, then add and subtract the remaining terms in a second pass.",
     "time": "O(n²) with list deletes", "space": "O(n)",
     "keyPoints": ["Mirrors how you'd do it by hand", "Rebuilding the token list costs extra time"],
     "code": '''from __future__ import annotations

import re


def evaluate(expr: str) -> int:
    tokens = re.findall(r"\\d+|[+\\-*/]", expr)
    items = [int(t) if t.isdigit() else t for t in tokens]
    i = 1
    while i < len(items):
        if items[i] in ("*", "/"):
            a, b = items[i - 1], items[i + 1]
            if items[i] == "*":
                v = a * b
            else:
                v = abs(a) // b
                v = v if a >= 0 else -v
            items[i - 1:i + 2] = [v]
        else:
            i += 2
    total = items[0]
    for j in range(1, len(items), 2):
        total = total + items[j + 1] if items[j] == "+" else total - items[j + 1]
    return total
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Two passes over tokens", "idea": "Fold * and / first, then + and -.",
     "time": "O(n²) with list deletes", "space": "O(n)", "use": "Short queries; mirrors the precedence rules directly."},
    {"name": "One pass with a stack", "idea": "Push signed terms; combine the top term for * and /.",
     "time": "O(n)", "space": "O(n)", "use": "Long expressions; the standard interview answer."},
]
