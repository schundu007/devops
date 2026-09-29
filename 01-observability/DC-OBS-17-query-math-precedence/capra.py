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
     "description": "Tokenize, then fold every * and / into its left neighbor in one pass, then add and subtract the remaining terms in a second pass.",
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

VARIANT_TITLE = "Precedence without parentheses"
VARIANT_APPROACH = "Stack of terms · O(n) · O(n)"


def _big_paren():
    rng = random.Random(772)

    def expr(depth):
        out = []
        for i in range(rng.randint(2, 5)):
            op = "" if i == 0 else rng.choice("+-*/")
            if op in "*/":
                out.append(op + str(rng.randint(1, 9)))
            elif depth and rng.random() < 0.4:
                out.append(op + "(" + expr(depth - 1) + ")")
            else:
                out.append(op + str(rng.randint(0, 99)))
        return "".join(out)

    return {"expr": " + ".join(expr(3) for _ in range(30))}


def _big_rpn():
    rng = random.Random(150)

    def tree(depth):
        if depth == 0 or rng.random() < 0.2:
            return [str(rng.randint(-50, 50))]
        op = rng.choice("+-+-*/")
        if op in "*/":
            return tree(depth - 1) + [str(rng.choice([-3, -2, 2, 3, 4, 5, 7]))] + [op]
        return tree(depth - 1) + tree(depth - 1) + [op]

    toks = tree(6)
    for _ in range(40):
        toks = toks + tree(6) + ["+"]
    return {"tokens": toks}


VARIANTS = [
    {
        "key": "with-parentheses",
        "title": "Query math with parentheses",
        "approach": "Stack of terms, one frame per group · O(n) · O(n)",
        "spec": {"kind": "fn", "fn": "evaluate", "params": ["expr"], "ret": "value", "cmp": "exact"},
        "statement": """The dashboard query language now allows parentheses, so `(errors + timeouts) * 100 / total` can be written directly.

### Input
- `expr`: non-negative integers, `+ - * /`, parentheses and spaces; there is no unary minus

### Output
- The value as an `int`

### Rules
- `*` and `/` bind tighter than `+` and `-`; equal levels go left to right
- Division truncates toward zero, and a group can be negative, so `7 / (2 - 4)` is `-3`""",
        "examples": [
            {"args": {"expr": "(40 + 10) * 100 / 2000"},
             "explanation": "50 * 100 = 5000, then 5000 / 2000 = 2 (truncated).",
             "why": {"t": "Group first", "d": "The parentheses override precedence."}},
            {"args": {"expr": "2*(5+5*2)/3+(6/2+8)"},
             "explanation": "2 * 15 = 30, 30 / 3 = 10, plus (3 + 8) = 21.",
             "why": {"t": "Mixed", "d": "Groups on both sides of + with * and / around them."}},
        ],
        "constraints": ["1 ≤ expr.length ≤ 10^4", "The expression is valid and never divides by zero", "Numbers are non-negative integers; Python ints do not overflow"],
        "hints": [
            "Inside one group, the main problem's stack of terms works unchanged.",
            "On '(' save (stack, operator) and start empty; on ')' the group's value is sum(stack) and becomes the current number.",
            "Truncate toward zero with signs handled by hand: the divisor can be negative now.",
        ],
        "tests": [
            {"args": {"expr": "7"}, "why": {"t": "Single number", "d": "No operators."}},
            {"args": {"expr": "(((7)))"}, "why": {"t": "Redundant groups", "d": "Parentheses around one number."}},
            {"args": {"expr": "7/(2-4)"}, "why": {"t": "Negative divisor", "d": "-3.5 truncates to -3."}},
            {"args": {"expr": "(1-8)/2"}, "why": {"t": "Negative numerator", "d": "-7 / 2 truncates to -3, not -4."}},
            {"args": {"expr": "0*(5+5)"}, "why": {"t": "Zero", "d": "A zero factor."}},
            {"args": {"expr": "10 - (2 - (3 - (4 - 5)))"}, "why": {"t": "Deep nesting", "d": "Signs alternate through three levels."}},
            {"args": {"expr": "(500 - (120 + 30)) * 100 / (500 + 0)"}, "why": {"t": "Success ratio", "d": "Good requests as a percentage of all."}},
            {"args": _big_paren(), "why": {"t": "Large input", "d": "Thirty random expressions with nested groups."}},
        ],
        "solutions": [
            {"name": "Stack of terms per group (Optimal)",
             "description": "Tokenize. Keep a stack of signed terms and the pending operator. '(' saves both and starts fresh; ')' closes the group, whose sum becomes the current number.",
             "time": "O(n)", "space": "O(n)",
             "keyPoints": ["Same term stack as the main problem", "One saved frame per open group", "Division truncates toward zero for any signs"],
             "code": '''import re


def evaluate(expr):
    def push(stack, op, num):
        if op == "+":
            stack.append(num)
        elif op == "-":
            stack.append(-num)
        elif op == "*":
            stack.append(stack.pop() * num)
        else:
            p = stack.pop()
            q = abs(p) // abs(num)
            stack.append(-q if (p < 0) != (num < 0) else q)

    stack, op, num, saved = [], "+", 0, []
    for tok in re.findall(r"\\d+|[-+*/()]", expr):
        if tok.isdigit():
            num = int(tok)
        elif tok == "(":
            saved.append((stack, op))
            stack, op, num = [], "+", 0
        elif tok == ")":
            push(stack, op, num)
            num = sum(stack)
            stack, op = saved.pop()
        else:
            push(stack, op, num)
            op, num = tok, 0
    push(stack, op, num)
    return sum(stack)
'''},
            {"name": "Reduce the innermost group", "slow": True,
             "description": "Tokenize into a list, then repeatedly take the last '(' and its matching ')', evaluate the flat tokens between them with two passes, and splice in the value.",
             "time": "O(n²)", "space": "O(n)",
             "keyPoints": ["Values replace groups in the token list, so negatives need no parsing", "Rebuilds the list once per group"],
             "code": '''import re


def _div(a, b):
    q = abs(a) // abs(b)
    return -q if (a < 0) != (b < 0) else q


def _flat(items):
    out = [items[0]]
    for i in range(1, len(items), 2):
        op, v = items[i], items[i + 1]
        if op == "*":
            out[-1] = out[-1] * v
        elif op == "/":
            out[-1] = _div(out[-1], v)
        else:
            out += [op, v]
    total = out[0]
    for i in range(1, len(out), 2):
        total = total + out[i + 1] if out[i] == "+" else total - out[i + 1]
    return total


def evaluate(expr):
    items = [int(t) if t.isdigit() else t for t in re.findall(r"\\d+|[-+*/()]", expr)]
    while "(" in items:
        i = len(items) - 1 - items[::-1].index("(")
        j = items.index(")", i)
        items[i:j + 1] = [_flat(items[i + 1:j])]
    return _flat(items)
'''},
        ],
        "starter": '''def evaluate(expr: str) -> int:
    pass
''',
    },
    {
        "key": "rpn",
        "title": "Rules stored in reverse Polish notation",
        "approach": "Operand stack · O(n) · O(n)",
        "spec": {"kind": "fn", "fn": "eval_rpn", "params": ["tokens"], "ret": "value", "cmp": "exact"},
        "statement": """An alerting backend compiles every rule to reverse Polish notation once, so evaluating it on each scrape needs no parsing.

### Input
- `tokens`: the compiled rule: integers (possibly negative, such as `"-3"`) and the operators `+ - * /`

### Output
- The value as an `int`

### Rules
- Each operator takes the two most recent values, **left** operand first
- Division truncates toward zero""",
        "examples": [
            {"args": {"tokens": ["500", "100", "*", "2000", "/"]},
             "explanation": "500 * 100 = 50000, then 50000 / 2000 = 25.",
             "why": {"t": "Error percentage", "d": "errors * 100 / total, compiled."}},
            {"args": {"tokens": ["4", "13", "5", "/", "+"]},
             "explanation": "13 / 5 = 2, then 4 + 2 = 6.",
             "why": {"t": "Operand order", "d": "The second-from-top value is the left operand."}},
        ],
        "constraints": ["1 ≤ tokens.length ≤ 10^4", "The tokens always form a valid expression that never divides by zero", "Numbers are in [-200, 200]"],
        "hints": [
            "Push numbers. An operator pops b, then a, and pushes a op b.",
            "Watch the sign of a negative number: '-3' is a number, '-' alone is an operator.",
            "Truncate toward zero by hand, not with //, which floors.",
        ],
        "tests": [
            {"args": {"tokens": ["42"]}, "why": {"t": "Single number", "d": "No operators."}},
            {"args": {"tokens": ["-7"]}, "why": {"t": "Negative literal", "d": "A lone negative number."}},
            {"args": {"tokens": ["-7", "2", "/"]}, "why": {"t": "Truncate toward zero", "d": "-7 / 2 is -3, not -4."}},
            {"args": {"tokens": ["3", "10", "-"]}, "why": {"t": "Order of operands", "d": "3 - 10, not 10 - 3."}},
            {"args": {"tokens": ["2", "3", "4", "*", "+", "5", "-"]}, "why": {"t": "Mixed", "d": "2 + 3 * 4 - 5 compiled."}},
            {"args": {"tokens": ["0", "5", "/", "9", "*"]}, "why": {"t": "Zero numerator", "d": "0 / 5 is 0."}},
            {"args": _big_rpn(), "why": {"t": "Large input", "d": "Forty-one random compiled rules summed together."}},
        ],
        "solutions": [
            {"name": "Operand stack (Optimal)",
             "description": "Scan left to right. Push numbers; for an operator pop two values, apply it and push the result.",
             "time": "O(n)", "space": "O(n)",
             "keyPoints": ["Every token is handled once", "Pop b before a", "Integer truncation toward zero"],
             "code": '''def eval_rpn(tokens):
    stack = []
    for t in tokens:
        if t in ("+", "-", "*", "/"):
            b = stack.pop()
            a = stack.pop()
            if t == "+":
                stack.append(a + b)
            elif t == "-":
                stack.append(a - b)
            elif t == "*":
                stack.append(a * b)
            else:
                q = abs(a) // abs(b)
                stack.append(-q if (a < 0) != (b < 0) else q)
        else:
            stack.append(int(t))
    return stack[0]
'''},
            {"name": "Collapse the first operator", "slow": True,
             "description": "Repeatedly find the first operator in the list, replace it and the two values before it with the result, until one value remains.",
             "time": "O(n²)", "space": "O(n)",
             "keyPoints": ["No explicit stack", "Rescans from the start every time"],
             "code": '''def eval_rpn(tokens):
    items = list(tokens)
    ops = {"+", "-", "*", "/"}
    while len(items) > 1:
        i = next(k for k, t in enumerate(items) if t in ops)
        a, b, op = int(items[i - 2]), int(items[i - 1]), items[i]
        if op == "+":
            v = a + b
        elif op == "-":
            v = a - b
        elif op == "*":
            v = a * b
        else:
            q = abs(a) // abs(b)
            v = -q if (a < 0) != (b < 0) else q
        items[i - 2:i + 1] = [str(v)]
    return int(items[0])
'''},
        ],
        "starter": '''def eval_rpn(tokens: list[str]) -> int:
    pass
''',
    },
]
