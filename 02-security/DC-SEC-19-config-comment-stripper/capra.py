"""Capra Playground export for DC-SEC-19 (see tools/export_capra.py)."""
import random

SPEC = {"kind": "fn", "fn": "strip_comments", "params": ["lines"], "types": {}, "ret": "value", "cmp": "exact"}

EXAMPLES = [
    {"args": {"lines": ['resource "aws_s3_bucket" "logs" { // audit bucket',
                        '  /* versioning is',
                        '     required by policy */',
                        '  versioning = true',
                        '}']},
     "explanation": "The // comment ends its line. The two-line block comment removes those lines entirely.",
     "why": {"t": "Line and block comments", "d": "Both comment styles in one HCL-style block."}},
    {"args": {"lines": ["port = 80/* old: 8080", "*/80"]},
     "explanation": "A block comment spanning lines joins the text before it with the text after it: 'port = 8080'.",
     "why": {"t": "Joined lines", "d": "Text around a multi-line block comment becomes one line."}},
]


def _large():
    rng = random.Random(722)
    lines = []
    for i in range(1500):
        r = rng.random()
        if r < 0.2:
            lines.append(f"key_{i} = {i} // note {i}")
        elif r < 0.3:
            lines.append(f"/* block {i} */ key_{i} = true")
        elif r < 0.35:
            lines.append(f"x_{i} = 1 /* open")
            lines.append("still comment */")
        else:
            lines.append(f"key_{i} = \"v{i}\"".replace('"', ""))
    return {"lines": lines}


TESTS = [
    {"args": {"lines": []}, "why": {"t": "Empty", "d": "No lines in, no lines out."}},
    {"args": {"lines": ["a = 1", "b = 2"]}, "why": {"t": "No comments", "d": "Lines pass through unchanged."}},
    {"args": {"lines": ["   ", "// only comment", ""]},
     "why": {"t": "Spaces kept", "d": "A line of spaces is not empty and is kept; a comment-only line is dropped."}},
    {"args": {"lines": ["a/*/b*/c"]}, "why": {"t": "/*/ trap", "d": "'/*/' opens a comment; it does not close itself."}},
    {"args": {"lines": ["/* // inside */x = 1"]}, "why": {"t": "// inside a block", "d": "A // inside a block comment is ignored."}},
    {"args": {"lines": ["x = 1 // a /* b", "y = 2"]}, "why": {"t": "/* after //", "d": "A /* after // is part of the line comment."}},
    {"args": {"lines": ["/*", "", "*/"]}, "why": {"t": "Whole block", "d": "Everything inside the block, blank lines too, disappears."}},
    {"args": _large(), "why": {"t": "Large input", "d": "About 1,600 lines mixing both comment styles."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Character state machine (Optimal)",
     "description": "Carry an in_block flag and a line buffer across lines. Outside a block, /* enters it and // ends the line; inside, skip to */. Emit the buffer at a line end only when outside a block, which joins text around multi-line comments.",
     "time": "O(total characters)", "space": "O(total characters)",
     "keyPoints": ["Skip 2 characters after /* so /*/ stays open", "Emit only outside a block", "Drop lines left empty"]},
]
