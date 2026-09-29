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

VARIANT_TITLE = "Depth-capped parser"
VARIANT_APPROACH = "Stack of open lists · O(n) · O(depth)"

VARIANTS = [
    {
        "key": "measure-depth",
        "title": "Measure depth before parsing",
        "approach": "One pass with a bracket stack, skipping strings · O(n) · O(depth)",
        "spec": {"kind": "fn", "fn": "max_depth", "params": ["payload"]},
        "statement": (
            "An API gateway rejects deeply nested JSON bodies before handing them to the real parser. It needs the "
            "nesting depth of a raw payload, cheaply.\n\n"
            "- `[` / `]` and `{` / `}` open and close a level. Depth is the most levels open at once.\n"
            "- Text inside double-quoted strings does not count. Inside a string, `\\` escapes the next "
            "character, so `\\\"` does not end the string.\n"
            "- Everything else (numbers, commas, colons, spaces) is ignored.\n\n"
            "Return the depth, or `-1` if the brackets are mismatched, unclosed or closed too often."
        ),
        "examples": [
            {"args": {"payload": '{"a": [1, {"b": []}]}'},
             "explanation": "Object, list, object, list: 4 levels open at the deepest point.",
             "why": {"t": "Mixed brackets", "d": "Objects and lists both count."}},
            {"args": {"payload": '["[[[", "]"]'},
             "explanation": "The brackets inside the strings are text, so the depth is 1.",
             "why": {"t": "Brackets in strings", "d": "String contents are skipped."}},
            {"args": {"payload": "[{]}"},
             "explanation": "] closes while { is still open: mismatched, -1.",
             "why": {"t": "Mismatch", "d": "Each closer must match the last opener."}},
        ],
        "constraints": ["0 ≤ len(payload) ≤ 10^5", "Strings are always closed", "Characters are printable ASCII"],
        "hints": [
            "Walk the characters with a flag for 'inside a string' and skip the character after a backslash there.",
            "Push each opener on a stack; a closer must match the top. The largest stack size is the depth.",
            "At the end the stack must be empty.",
        ],
        "tests": [
            {"args": {"payload": ""}, "why": {"t": "Empty", "d": "No brackets: depth 0."}},
            {"args": {"payload": "42"}, "why": {"t": "Scalar", "d": "A bare value has depth 0."}},
            {"args": {"payload": "[]"}, "why": {"t": "Minimal list", "d": "Depth 1."}},
            {"args": {"payload": '{"k": "a\\"]b"}'}, "why": {"t": "Escaped quote", "d": "An escaped quote keeps the string open over the ]."}},
            {"args": {"payload": "[[]"}, "why": {"t": "Unclosed", "d": "An opener is left on the stack: -1."}},
            {"args": {"payload": "[]]"}, "why": {"t": "Extra closer", "d": "Closing with an empty stack: -1."}},
            {"args": {"payload": "[[],[[]],{}]"}, "why": {"t": "Siblings", "d": "The deepest branch decides: 3."}},
            {"args": {"payload": "[" * 150 + "]" * 150}, "why": {"t": "Deep payload", "d": "150 levels, the kind of body the gateway blocks."}},
            {"args": {"payload": "[" + ",".join('{"id": %d, "tags": ["x", "]"]}' % i for i in range(300)) + "]"}, "why": {"t": "Large input", "d": "300 objects with bracket characters in strings."}},
        ],
        "solutions": [
            {"name": "Bracket stack (Optimal)",
             "description": "Scan once, tracking string state. Push openers, pop on a matching closer, fail on a mismatch, and track the largest stack size.",
             "time": "O(n)", "space": "O(depth)",
             "keyPoints": ["String and escape handling come first", "The stack size is the current depth", "A non-empty stack at the end is an error"],
             "code": '''def max_depth(payload):
    pairs = {"]": "[", "}": "{"}
    stack = []
    deepest = 0
    in_str = False
    escape = False
    for ch in payload:
        if in_str:
            if escape:
                escape = False
            elif ch == "\\\\":
                escape = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "[{":
            stack.append(ch)
            deepest = max(deepest, len(stack))
        elif ch in "]}":
            if not stack or stack.pop() != pairs[ch]:
                return -1
    return deepest if not stack else -1
'''},
            {"name": "Peel innermost pairs", "slow": True,
             "description": "Drop string contents and non-bracket characters, then repeatedly delete every empty [] and {} pair. Each round peels one level; leftovers mean a mismatch.",
             "time": "O(n · depth)", "space": "O(n)",
             "keyPoints": ["Each round removes all innermost pairs at once", "Rounds needed = depth", "Rebuilds the string every round"],
             "code": '''import re


def max_depth(payload):
    kept = []
    in_str = False
    escape = False
    for ch in payload:
        if in_str:
            if escape:
                escape = False
            elif ch == "\\\\":
                escape = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "[]{}":
            kept.append(ch)
    s = "".join(kept)
    rounds = 0
    while s:
        t = re.sub(r"\\[\\]|\\{\\}", "", s)
        if t == s:
            return -1
        s = t
        rounds += 1
    return rounds
'''},
        ],
        "starter": '''def max_depth(payload: str) -> int:
    """Deepest bracket nesting outside strings, or -1 if mismatched."""
    raise NotImplementedError
''',
    },
    {
        "key": "truncate-deep",
        "title": "Truncate instead of refusing",
        "approach": "Stack parse, skip deep lists by bracket count · O(n) · O(min(depth, cap))",
        "spec": {"kind": "fn", "fn": "truncate", "params": ["s", "max_depth"]},
        "statement": (
            "A structured logger must never drop an event, so instead of refusing deep values it truncates them, the "
            "way many log libraries print `...` for deep objects.\n\n"
            "`s` uses the main problem's format (integers and lists, no spaces). A list's depth is the number of lists "
            "open when it opens, counting itself, so the outermost list has depth 1.\n\n"
            "Return the parsed value, with every list deeper than `max_depth` replaced by the string `\"...\"`."
        ),
        "examples": [
            {"args": {"s": "[1,[2,[3,[4]]]]", "max_depth": 2},
             "explanation": "The lists at depth 1 and 2 are kept; [3,[4]] opens at depth 3 and becomes \"...\".",
             "why": {"t": "Cut at the cap", "d": "Everything below the cap is replaced by one marker."}},
            {"args": {"s": "[[]]", "max_depth": 0},
             "explanation": "With a cap of 0, even the outermost list is replaced.",
             "why": {"t": "Cap 0", "d": "The whole value becomes the marker."}},
        ],
        "constraints": ["1 ≤ len(s) ≤ 5 · 10^5", "s is valid: digits, -, [, ] and , only", "0 ≤ max_depth ≤ 10^5"],
        "hints": [
            "Parse with a stack of open lists, as in the main problem.",
            "When a '[' would exceed the cap, append \"...\" and skip ahead to its matching ']' by counting brackets.",
            "Skipped text is never turned into values, so a hostile payload costs only a scan.",
        ],
        "tests": [
            {"args": {"s": "-7", "max_depth": 0}, "why": {"t": "Scalar", "d": "Integers are never truncated."}},
            {"args": {"s": "[]", "max_depth": 1}, "why": {"t": "Exactly at the cap", "d": "Depth equal to the cap is kept."}},
            {"args": {"s": "[1,[],2,[[3]],4]", "max_depth": 1}, "why": {"t": "Siblings keep their place", "d": "Each deep list becomes one marker in position."}},
            {"args": {"s": "[[[1]],[2],[[[3]]]]", "max_depth": 2}, "why": {"t": "Mixed depths", "d": "Only the lists opening past depth 2 are cut."}},
            {"args": {"s": "[0,-1000000000,1000000000]", "max_depth": 5}, "why": {"t": "Nothing to cut", "d": "A flat list passes through."}},
            {"args": {"s": "[" * 300 + "]" * 300, "max_depth": 3}, "why": {"t": "Deep payload", "d": "300 levels shrink to 3 plus a marker."}},
            {"args": {"s": "[" + ",".join("[%d,[%d]]" % (i, -i) for i in range(1500)) + "]", "max_depth": 2}, "why": {"t": "Large input", "d": "1,500 pairs, each with a list cut at depth 3."}},
        ],
        "solutions": [
            {"name": "Stack parse with skipping (Optimal)",
             "description": "Walk with a stack of open lists. On '[' past the cap, append \"...\" and advance to the matching ']' by counting brackets. Numbers are flushed on ',' or ']'.",
             "time": "O(n)", "space": "O(min(depth, max_depth)) stack",
             "keyPoints": ["Deep parts are scanned, never built", "No recursion", "The marker keeps the list's position"],
             "code": '''def truncate(s, max_depth):
    if s[0] != "[":
        return int(s)
    stack = []
    root = None
    i, n = 0, len(s)
    while i < n:
        ch = s[i]
        if ch == "[":
            if len(stack) == max_depth:
                bal = 0
                while True:
                    if s[i] == "[":
                        bal += 1
                    elif s[i] == "]":
                        bal -= 1
                        if bal == 0:
                            break
                    i += 1
                if stack:
                    stack[-1].append("...")
                else:
                    return "..."
            else:
                new = []
                if stack:
                    stack[-1].append(new)
                else:
                    root = new
                stack.append(new)
            i += 1
        elif ch == "]":
            stack.pop()
            i += 1
        elif ch == ",":
            i += 1
        else:
            j = i + 1
            while j < n and s[j].isdigit():
                j += 1
            stack[-1].append(int(s[i:j]))
            i = j
    return root
'''},
            {"name": "Parse fully, then prune", "slow": True,
             "description": "Parse the whole value with recursive descent, then walk it again replacing lists below the cap.",
             "time": "O(n)", "space": "O(n) values plus O(depth) call stack",
             "keyPoints": ["Builds every deep list only to throw it away", "Recursion depth follows the input, not the cap"],
             "code": '''def truncate(s, max_depth):
    pos = 0

    def value():
        nonlocal pos
        if s[pos] != "[":
            start = pos
            pos += 1
            while pos < len(s) and s[pos].isdigit():
                pos += 1
            return int(s[start:pos])
        pos += 1
        out = []
        while s[pos] != "]":
            out.append(value())
            if s[pos] == ",":
                pos += 1
        pos += 1
        return out

    def prune(v, depth):
        if not isinstance(v, list):
            return v
        if depth > max_depth:
            return "..."
        return [prune(x, depth + 1) for x in v]

    return prune(value(), 1)
'''},
        ],
        "starter": '''def truncate(s: str, max_depth: int):
    """Parse s, replacing lists deeper than max_depth with "..."."""
    raise NotImplementedError
''',
    },
]
