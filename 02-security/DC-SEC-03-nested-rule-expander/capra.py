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
    {"args": case("s3:2[get,put]/logs-2[a,b]", 100), "why": {"t": "Policy actions", "d": "An IAM-style action list flattened for review."}},
    {"args": case("50[ab20[c]]"), "why": {"t": "Large output", "d": "1,100 characters from a short template."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Stack with a running length (Optimal)",
     "description": "Scan once. Digits build the count, [ pushes the current text and count, ] pops and repeats the body. A running length checks the cap before building a too-long string.",
     "time": "O(n + L)", "space": "O(n + L)",
     "keyPoints": ["Counts can have several digits", "Check the cap before building the repeated string", "k = 0 produces nothing"]},
]
