"""Capra Playground export for DC-SEC-20 (see tools/export_capra.py).

Driver kind: a too-deep input must raise ValueError, and the harness would
report a raised exception as a failed case. The driver turns it into a value.
"""

SPEC = {"kind": "driver", "fn": "parse", "params": ["s", "max_depth"], "types": {}, "ret": "value", "cmp": "exact"}

DRIVER = '''def __drive(args):
    try:
        return parse(args["s"], args["max_depth"])
    except ValueError:
        return "ValueError: too deep"
'''

EXAMPLES = [
    {"args": {"s": "324", "max_depth": 64}, "explanation": "A plain integer is returned as an int.",
     "why": {"t": "Plain integer", "d": "No brackets at all."}},
    {"args": {"s": "[123,[456,[789]]]", "max_depth": 64}, "explanation": "Lists nest three deep, well under the cap.",
     "why": {"t": "Nested lists", "d": "The normal case."}},
    {"args": {"s": "[[[1]]]", "max_depth": 2},
     "explanation": "Three levels of nesting with a cap of 2: the parser refuses with ValueError.",
     "why": {"t": "Depth cap", "d": "The denial-of-service guard: refuse input nested deeper than max_depth."}},
]

TESTS = [
    {"args": {"s": "[]", "max_depth": 64}, "why": {"t": "Empty list", "d": "The smallest list."}},
    {"args": {"s": "-5", "max_depth": 64}, "why": {"t": "Negative", "d": "A leading minus sign."}},
    {"args": {"s": "[-1,[],[[]],0]", "max_depth": 64}, "why": {"t": "Empty inner lists", "d": "Empty lists at several depths, plus zero."}},
    {"args": {"s": "[[[1]]]", "max_depth": 3}, "why": {"t": "Exactly at the cap", "d": "Depth equal to max_depth is allowed."}},
    {"args": {"s": "7", "max_depth": 0}, "why": {"t": "Cap 0, integer", "d": "A plain integer has depth 0, so it passes."}},
    {"args": {"s": "[]", "max_depth": 0}, "why": {"t": "Cap 0, list", "d": "Any list is too deep when the cap is 0."}},
    {"args": {"s": "[1000000000,-1000000000]", "max_depth": 64}, "why": {"t": "Integer limits", "d": "The largest and smallest allowed values."}},
    {"args": {"s": "[" * 300 + "]" * 300, "max_depth": 64}, "why": {"t": "Deep payload", "d": "300 levels against a cap of 64: refused."}},
    {"args": {"s": "[" * 90 + "]" * 90, "max_depth": 90}, "why": {"t": "Deep but allowed", "d": "90 levels with a cap of 90 parse without recursion."}},
    {"args": {"s": "[" + ",".join(str(i * 37 % 1000 - 500) for i in range(2000)) + "]", "max_depth": 64},
     "why": {"t": "Large input", "d": "A flat list of 2,000 numbers."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Stack of open lists (Optimal)",
     "description": "Walk the characters with a stack of open lists. '[' pushes (refusing past max_depth), digits and '-' build a number, ',' and ']' flush it, ']' pops.",
     "time": "O(n)", "space": "O(n) result, O(min(depth, max_depth)) stack",
     "keyPoints": ["The stack length is the current depth", "Refuse before allocating the next level", "No recursion, so deep input cannot crash the parser"]},
    {"name": "Recursive descent with a depth check",
     "description": "Parse a value; on '[' recurse for each element. The call stack holds the depth, so it needs the same explicit max_depth check.",
     "time": "O(n)", "space": "O(depth) call stack",
     "keyPoints": ["Natural first attempt", "Without the depth check, very deep input hits RecursionError"],
     "code": '''from __future__ import annotations


def parse(s: str, max_depth: int = 64):
    pos = 0

    def value(depth: int):
        nonlocal pos
        if s[pos] != "[":
            start = pos
            while pos < len(s) and (s[pos] == "-" or s[pos].isdigit()):
                pos += 1
            return int(s[start:pos])
        if depth == max_depth:
            raise ValueError(f"nesting deeper than {max_depth}")
        pos += 1
        out = []
        while s[pos] != "]":
            out.append(value(depth + 1))
            if s[pos] == ",":
                pos += 1
        pos += 1
        return out

    return value(0)
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Recursive descent", "idea": "Recurse on each '['; the call stack tracks depth.", "time": "O(n)",
     "space": "O(depth)", "use": "Readable; needs a depth cap and a recursion limit."},
    {"name": "Explicit stack", "idea": "Push on '[', pop on ']'; the stack length is the depth.", "time": "O(n)",
     "space": "O(depth)", "use": "Untrusted input: no recursion limit to hit."},
]
