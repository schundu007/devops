"""Capra Playground export for DC-OBS-07 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "evaluate", "params": ["expr", "values"], "types": {}, "ret": "value", "cmp": "exact"}

V = {"errors": 42, "timeouts": 8, "retries": 11}

EXAMPLES = [
    {"args": {"expr": "(errors + timeouts) - retries", "values": V},
     "explanation": "(42 + 8) - 11 = 39.",
     "why": {"t": "Parentheses", "d": "Metric names inside parentheses."}},
    {"args": {"expr": "100 - (errors - timeouts + retries)", "values": V},
     "explanation": "The minus flips every term inside: 100 − 42 + 8 − 11 = 55.",
     "why": {"t": "Minus before parentheses", "d": "A leading minus negates the whole group."}},
    {"args": {"expr": "-(2 + 3)", "values": {}},
     "explanation": "A unary minus in front of a group.",
     "why": {"t": "Unary minus", "d": "An expression that starts with minus."}},
]


def _large():
    rng = random.Random(224)
    names = [f"m{i}" for i in range(20)]
    values = {n: rng.randint(0, 1000) for n in names}

    def expr(depth):
        parts = []
        for i in range(rng.randint(2, 4)):
            op = "" if i == 0 else rng.choice([" + ", " - "])
            if depth and rng.random() < 0.35:
                term = ("-" if i == 0 and rng.random() < 0.3 else "") + "(" + expr(depth - 1) + ")"  # unary minus only first
            else:
                term = rng.choice(names) if rng.random() < 0.6 else str(rng.randint(0, 99))
            parts.append(op + term)
        return "".join(parts)

    return {"expr": " + ".join(expr(4) for _ in range(40)), "values": values}


TESTS = [
    {"args": {"expr": "   ", "values": {}},
     "why": {"t": "Only spaces", "d": "An empty expression evaluates to 0."}},
    {"args": {"expr": "7", "values": {}},
     "why": {"t": "Single number", "d": "A lone integer."}},
    {"args": {"expr": "http_5xx_total", "values": {"http_5xx_total": 17}},
     "why": {"t": "Single metric", "d": "A lone name with underscores and digits."}},
    {"args": {"expr": "1-(2-(3-(4-5)))", "values": {}},
     "why": {"t": "Deep nesting, no spaces", "d": "Signs alternate through four levels: 1-2+3-4+5 = 3."}},
    {"args": {"expr": "((((errors))))", "values": V},
     "why": {"t": "Redundant parentheses", "d": "Parentheses around a single operand change nothing."}},
    {"args": {"expr": "1000 - 999", "values": {}},
     "why": {"t": "Multi-digit", "d": "Numbers with several digits are read whole."}},
    {"args": {"expr": "(requests - (errors_5xx + errors_4xx)) - (canary_errors - canary_retries)",
              "values": {"requests": 12000, "errors_5xx": 140, "errors_4xx": 310, "canary_errors": 45, "canary_retries": 30}},
     "why": {"t": "Dashboard query", "d": "Good requests minus the net canary errors."}},
    {"args": _large(),
     "why": {"t": "Large input", "d": "A long random expression with nested groups."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "One pass with a stack (Optimal)",
     "description": "Keep a running result and the sign of the next operand. On '(' push (result, sign) and start fresh; on ')' pop and combine: outer + outer_sign * inner.",
     "time": "O(n)", "space": "O(d) for nesting depth d",
     "keyPoints": ["Only + and -, so a running total and a sign are enough", "The stack saves the outer total and the sign in front of each group", "Metric names are looked up in values"]},
    {"name": "Innermost group first", "slow": True,
     "description": "Repeatedly find an innermost ( ... ), evaluate that flat expression, and splice its value back into the text.",
     "time": "O(n²)", "space": "O(n)",
     "keyPoints": ["Simple string rewriting", "Rescans the text once per group"],
     "code": '''from __future__ import annotations
import re


def _flat(expr: str, values: dict[str, int]) -> int:
    """Evaluate an expression with no parentheses. Signs multiply, so 1--5 is 6."""
    total, sign = 0, 1
    for tok in re.findall(r"\\d+|[A-Za-z_][A-Za-z0-9_]*|[+-]", expr):
        if tok == "-":
            sign = -sign
        elif tok != "+":
            total += sign * (int(tok) if tok.isdigit() else values[tok])
            sign = 1
    return total


def evaluate(expr: str, values: dict[str, int]) -> int:
    expr = expr.replace(" ", "")
    while "(" in expr:
        m = re.search(r"\\(([^()]*)\\)", expr)   # an innermost group
        expr = expr[:m.start()] + str(_flat(m.group(1), values)) + expr[m.end():]
    return _flat(expr, values)
'''},
]
