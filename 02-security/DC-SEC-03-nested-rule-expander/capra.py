"""Capra Playground export for DC-SEC-03 (see tools/export_capra.py).

Driver kind: expand() raises ValueError for an expansion bomb, and the
harness can only compare returned values, so the driver turns the error into
a JSON result.
"""

SPEC = {"kind": "driver", "fn": "expand", "params": ["template", "max_output"], "types": {}, "ret": "value", "cmp": "exact"}

DRIVER = '''
def __drive(args):
    try:
        return {"output": expand(args["template"], args["max_output"])}
    except ValueError:
        return {"error": "ValueError"}
'''


def case(template, max_output=100_000):
    return {"template": template, "max_output": max_output}


EXAMPLES = [
    {"args": case("3[a]2[bc]"),
     "explanation": "3[a] becomes aaa and 2[bc] becomes bcbc.",
     "why": {"t": "Two blocks", "d": "Side-by-side repeat blocks."}},
    {"args": case("3[a2[c]]"),
     "explanation": "The inner 2[c] becomes cc, so the outer block repeats acc three times.",
     "why": {"t": "Nested", "d": "A block inside a block expands from the inside out."}},
    {"args": case("9[9[9[9[x]]]]", 1000),
     "explanation": "The fully expanded text would be 6,561 characters, over the 1,000 cap, so expand raises ValueError.",
     "why": {"t": "Expansion bomb", "d": "A tiny template whose output exceeds the cap."}},
]

TESTS = [
    {"args": case(""), "why": {"t": "Empty", "d": "An empty template expands to nothing."}},
    {"args": case("allow:get,list"), "why": {"t": "No blocks", "d": "Plain text passes through unchanged."}},
    {"args": case("12[ab]"), "why": {"t": "Multi-digit count", "d": "Counts can have several digits."}},
    {"args": case("pre0[abc]post"), "why": {"t": "Zero count", "d": "k = 0 produces nothing."}},
    {"args": case("2[a2[b2[c]]]"), "why": {"t": "Deep nesting", "d": "Three levels of nesting."}},
    {"args": case("5[ab]", 10), "why": {"t": "Exactly at cap", "d": "Output length equals max_output, which is allowed."}},
    {"args": case("5[ab]c", 10), "why": {"t": "One over cap", "d": "One character over the cap raises ValueError."}},
    {"args": case("iam:2[get,put]/logs-2[a,b]", 100), "why": {"t": "Policy actions", "d": "An IAM-style action list flattened for review."}},
    {"args": case("50[ab20[c]]"), "why": {"t": "Large output", "d": "1,100 characters from a short template."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Stack with a running length (Optimal)",
     "description": "Scan once. Digits build the count, [ pushes the current text and count, ] pops and repeats the body. A running length checks the cap before building a too-long string.",
     "time": "O(n + L)", "space": "O(n + L)",
     "keyPoints": ["Counts can have several digits", "Check the cap before building the repeated string", "k = 0 produces nothing"]},
    {"name": "Recursive descent",
     "description": "A function parses a sequence until ']' or the end; on a count it recurses for the body, then checks the cap before repeating. The call stack plays the role of the explicit stack.",
     "time": "O(n + L)", "space": "O(n + L), plus O(depth) call stack",
     "keyPoints": ["Mirrors the grammar: seq = (char | k[seq])*", "Same cap checks as the stack version", "Deep nesting can hit Python's recursion limit"],
     "code": '''from __future__ import annotations


def expand(template: str, max_output: int = 100_000) -> str:
    pos = 0
    count = 0

    def seq() -> str:
        nonlocal pos, count
        out: list[str] = []
        length = 0
        while pos < len(template) and template[pos] != "]":
            ch = template[pos]
            pos += 1
            if ch.isdigit():
                count = count * 10 + int(ch)
            elif ch == "[":
                k, count = count, 0
                body = seq()
                pos += 1
                if length + k * len(body) > max_output:
                    raise ValueError("expanded output exceeds max_output")
                out.append(body * k)
                length += k * len(body)
            else:
                out.append(ch)
                length += 1
                if length > max_output:
                    raise ValueError("expanded output exceeds max_output")
        return "".join(out)

    return seq()
'''},
]

VARIANT_TITLE = "Expand with a size cap"
VARIANT_APPROACH = "Stack with a running length · O(n + L) · O(n + L)"


def _len_case(template):
    return {"template": template}


VARIANTS = [
    {
        "key": "expanded-length",
        "title": "Size the expansion first",
        "approach": "Stack of lengths, no strings built · O(n) · O(depth)",
        "spec": {"kind": "fn", "fn": "expanded_length", "params": ["template"]},
        "statement": (
            "An admission webhook wants the exact size of an expanded template, to reject expansion bombs without allocating anything.\n"
            "\n"
            "### Input\n"
            "- `template`: the main problem's syntax: `k[body]` is `body` repeated `k` times, blocks nest, and every other character is copied as is\n"
            "\n"
            "### Output\n"
            "- The length of the fully expanded text\n"
            "\n"
            "### Rules\n"
            "- The length may be far larger than memory"
        ),
        "examples": [
            {"args": _len_case("3[a2[c]]"),
             "explanation": "2[c] is 2 characters, a2[c] is 3, repeated 3 times: 9.",
             "why": {"t": "Nested", "d": "Lengths multiply from the inside out."}},
            {"args": _len_case("9[9[9[9[9[9[x]]]]]]"),
             "explanation": "Six levels of 9 give 9^6 = 531,441 characters from a 19-character template, computed without building them.",
             "why": {"t": "Expansion bomb", "d": "A tiny template with a huge result."}},
        ],
        "constraints": ["0 ≤ len(template) ≤ 10^4", "0 ≤ k ≤ 1000", "Brackets are balanced and every [ follows a count"],
        "hints": [
            "Replace the stack of strings with a stack of lengths.",
            "On ']', the block contributes k · (body length) to the enclosing length.",
        ],
        "tests": [
            {"args": _len_case(""), "why": {"t": "Empty", "d": "Length 0."}},
            {"args": _len_case("allow:get"), "why": {"t": "No blocks", "d": "Plain text length."}},
            {"args": _len_case("pre0[abc]post"), "why": {"t": "Zero count", "d": "k = 0 contributes nothing."}},
            {"args": _len_case("12[ab]c"), "why": {"t": "Multi-digit count", "d": "12 · 2 + 1."}},
            {"args": _len_case("2[a2[b2[c]]]x"), "why": {"t": "Deep nesting", "d": "Three levels plus a trailing literal."}},
            {"args": _len_case("iam:2[get,put]/logs-2[a,b]"), "why": {"t": "Policy actions", "d": "An IAM-style template."}},
            {"args": _len_case("50[ab20[c]]" * 20), "why": {"t": "Large input", "d": "Twenty repeated blocks, 22,000 characters."}},
        ],
        "solutions": [
            {"name": "Stack of lengths (Optimal)",
             "description": "Scan once. '[' pushes the current length and count; ']' pops and adds k times the body length to the outer length.",
             "time": "O(n)", "space": "O(depth)",
             "keyPoints": ["Never builds a string", "Handles results far bigger than memory", "Python ints do not overflow"],
             "code": '''def expanded_length(template):
    stack = []
    length = 0
    count = 0
    for ch in template:
        if ch.isdigit():
            count = count * 10 + int(ch)
        elif ch == "[":
            stack.append((length, count))
            length, count = 0, 0
        elif ch == "]":
            outer, k = stack.pop()
            length = outer + k * length
        else:
            length += 1
    return length
'''},
            {"name": "Expand, then measure", "slow": True,
             "description": "Build the expanded string with the stack method and return its length.",
             "time": "O(n + L)", "space": "O(L)",
             "keyPoints": ["Correct but allocates the whole result", "Exactly what a bomb exploits"],
             "code": '''def expanded_length(template):
    stack = []
    cur = []
    count = 0
    for ch in template:
        if ch.isdigit():
            count = count * 10 + int(ch)
        elif ch == "[":
            stack.append((cur, count))
            cur, count = [], 0
        elif ch == "]":
            outer, k = stack.pop()
            outer.append("".join(cur) * k)
            cur = outer
        else:
            cur.append(ch)
    return len("".join(cur))
'''},
        ],
        "starter": '''def expanded_length(template: str) -> int:
    """Length of the expanded template, without building it."""
    raise NotImplementedError
''',
    },
    {
        "key": "char-at",
        "title": "Read one character of a huge expansion",
        "approach": "Parse tree with sizes, descend with modulo · O(n) · O(n)",
        "spec": {"kind": "fn", "fn": "char_at", "params": ["template", "index"]},
        "statement": (
            "Find the character at one position of an expanded template, without building the full expansion (it is too big).\n"
            "\n"
            "### Input\n"
            "- `template`: the main problem's syntax\n"
            "- `index`: a **0-based** position in the expanded text\n"
            "\n"
            "### Output\n"
            "- The character at `index`, or `\"\"` if `index` is past the end"
        ),
        "examples": [
            {"args": {"template": "2[ab3[c]]", "index": 6},
             "explanation": "The expansion is abcccabccc; position 6 is b.",
             "why": {"t": "Inside a repeat", "d": "The index falls in the second copy of the body."}},
            {"args": {"template": "9[9[9[9[9[9[x]]]]]]y", "index": 531441},
             "explanation": "The block is 531,441 characters long, so this index is the trailing y.",
             "why": {"t": "Huge expansion", "d": "Answered without building the text."}},
        ],
        "constraints": ["0 ≤ len(template) ≤ 10^4", "0 ≤ index ≤ 10^18", "0 ≤ k ≤ 1000"],
        "hints": [
            "Parse the template into a tree: literal characters and (k, body) blocks, each with its expanded size.",
            "Walk the top level; skip whole items whose size is at most the remaining index.",
            "Inside a block, only index mod (body size) matters: every copy is identical.",
        ],
        "tests": [
            {"args": {"template": "", "index": 0}, "why": {"t": "Empty", "d": "Nothing to read."}},
            {"args": {"template": "abc", "index": 2}, "why": {"t": "Last literal", "d": "The final character, no blocks."}},
            {"args": {"template": "abc", "index": 3}, "why": {"t": "Just past the end", "d": "Returns an empty string."}},
            {"args": {"template": "x0[abc]y", "index": 1}, "why": {"t": "Zero count", "d": "The empty block is skipped."}},
            {"args": {"template": "3[a2[bc]]", "index": 14}, "why": {"t": "Nested modulo", "d": "Reduces the index at two levels."}},
            {"args": {"template": "iam:2[get,put]/logs", "index": 9}, "why": {"t": "Policy actions", "d": "A character inside the repeated action list."}},
            {"args": {"template": "40[ab30[c]de]" * 10, "index": 12345}, "why": {"t": "Large input", "d": "Ten blocks, 13,600 characters in total."}},
        ],
        "solutions": [
            {"name": "Sized parse tree (Optimal)",
             "description": "Parse with a stack into lists of items (a character, or [k, body, body_size]). Then descend from the top: skip items that end before the index, and inside a block take index mod body size.",
             "time": "O(n)", "space": "O(n)",
             "keyPoints": ["Sizes are computed while parsing", "Modulo jumps over identical copies", "Never builds the expanded text"],
             "code": '''def char_at(template, index):
    stack = []
    items, size, count = [], 0, 0
    for ch in template:
        if ch.isdigit():
            count = count * 10 + int(ch)
        elif ch == "[":
            stack.append((items, size, count))
            items, size, count = [], 0, 0
        elif ch == "]":
            outer, outer_size, k = stack.pop()
            outer.append((k, items, size))
            items, size = outer, outer_size + k * size
        else:
            items.append(ch)
            size += 1
    if index >= size:
        return ""
    while True:
        for item in items:
            if isinstance(item, str):
                if index == 0:
                    return item
                index -= 1
                continue
            k, body, body_size = item
            total = k * body_size
            if index < total:
                items, index = body, index % body_size
                break
            index -= total
'''},
            {"name": "Expand and index", "slow": True,
             "description": "Build the full expansion with the stack method and index into it.",
             "time": "O(n + L)", "space": "O(L)",
             "keyPoints": ["Simple and correct for small outputs", "Fails on bombs: memory grows with L"],
             "code": '''def char_at(template, index):
    stack = []
    cur = []
    count = 0
    for ch in template:
        if ch.isdigit():
            count = count * 10 + int(ch)
        elif ch == "[":
            stack.append((cur, count))
            cur, count = [], 0
        elif ch == "]":
            outer, k = stack.pop()
            outer.append("".join(cur) * k)
            cur = outer
        else:
            cur.append(ch)
    text = "".join(cur)
    return text[index] if index < len(text) else ""
'''},
        ],
        "starter": '''def char_at(template: str, index: int) -> str:
    """Character at index of the expansion, or "" past the end."""
    raise NotImplementedError
''',
    },
]
