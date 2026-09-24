"""Capra Playground export for DC-OBS-04 (see tools/export_capra.py).

Driver kind: the input is a call tree of Frame objects, which JSON cannot carry.
A tree travels as nested lists [name, [child, child, ...]] (null for no tree),
and the driver builds the user's Frame objects from it.
"""
import random

SPEC = {"kind": "driver", "fn": "find_duplicate_subtrees", "params": ["root"], "types": {}, "ret": "value", "cmp": "exact"}

DRIVER = '''
def __drive(args):
    def build(node):
        return Frame(node[0], [build(c) for c in node[1]])
    root = args["root"]
    return find_duplicate_subtrees(build(root) if root is not None else None)
'''


def leaf(name):
    return [name, []]


def node(name, *children):
    return [name, list(children)]


def chain(*names):
    """chain("retry", "http.get", "dns.resolve") -> retry -> http.get -> dns.resolve."""
    tree = leaf(names[-1])
    for name in reversed(names[:-1]):
        tree = node(name, tree)
    return tree


EXAMPLES = [
    {"args": {"root": node("handler", leaf("db.query"), leaf("db.query"))},
     "explanation": "The db.query leaf appears twice, so its shape is reported once.",
     "why": {"t": "Repeated leaf", "d": "The smallest duplicate: two identical leaves."}},
    {"args": {"root": node("main", *[chain("retry", "http.get", "dns.resolve") for _ in range(3)])},
     "explanation": "Three identical retry chains: each shape inside them is reported once, even though it appears three times.",
     "why": {"t": "Nested repeats", "d": "Every level of a repeated chain is its own duplicate shape."}},
    {"args": {"root": node("main", node("a", leaf("b"), leaf("c")), node("a", leaf("c"), leaf("b")))},
     "explanation": "The two a subtrees make the same calls in a different order, so they are different traces. Only b and c repeat.",
     "why": {"t": "Order matters", "d": "Children are ordered: the same frames in another order are another shape."}},
]


def _large():
    rng = random.Random(4)
    names = ["db.query", "cache.get", "http.get", "json.parse", "auth.check"]

    def rand_tree(depth):
        if depth == 0 or rng.random() < 0.3:
            return leaf(rng.choice(names))
        return node(rng.choice(names), *[rand_tree(depth - 1) for _ in range(rng.randint(1, 3))])

    return node("main", *[rand_tree(4) for _ in range(60)])


TESTS = [
    {"args": {"root": None},
     "why": {"t": "No tree", "d": "No trace at all returns an empty list."}},
    {"args": {"root": leaf("main")},
     "why": {"t": "Single frame", "d": "One frame has nothing to repeat."}},
    {"args": {"root": node("main", leaf("a"), leaf("b"), leaf("c"))},
     "why": {"t": "All distinct", "d": "Distinct leaves: no duplicates."}},
    {"args": {"root": node("x", leaf("x"))},
     "why": {"t": "Same name, different shape", "d": "A parent and its child share a name, but x and x(x) are different shapes."}},
    {"args": {"root": chain(*["f"] * 8)},
     "why": {"t": "Deep single chain", "d": "A straight chain f -> f -> ... has no repeated subtree: every depth is a new shape."}},
    {"args": {"root": node("main", node("a", leaf("b")), node("a", leaf("b")), node("a", leaf("b"), leaf("b")))},
     "why": {"t": "Duplicates", "d": "a(b) appears twice; b appears four times; a(b,b) once."}},
    {"args": {"root": node("checkout", *[chain("payment.charge", "stripe.post", "tls.handshake", "socket.timeout") for _ in range(5)],
                         chain("payment.charge", "stripe.post", "ok"))},
     "why": {"t": "Outage burst", "d": "Five identical timeout traces and one success: the timeout chain collapses into single issues."}},
    {"args": {"root": _large()},
     "why": {"t": "Large input", "d": "A random call tree with a few hundred frames and many repeats."}},
]

SOLUTIONS = [
    {"file": "solution.py", "name": "Shape IDs, post-order (Optimal)",
     "description": "Walk the tree bottom-up. Give each distinct (name, child IDs) key a small integer ID, count how often each ID appears, and render text only for IDs seen twice or more.",
     "time": "O(n)", "space": "O(n)",
     "keyPoints": ["Identify a subtree by (name, tuple of child IDs), not by its full text",
                   "Iterative post-order avoids the recursion limit on deep traces",
                   "Render only the duplicates, sorted"]},
    {"name": "Render every subtree", "slow": True,
     "description": "Render every subtree to its full text and count the strings. Each render can be O(n) long, so the total is O(n²).",
     "time": "O(n²)", "space": "O(n²)",
     "keyPoints": ["Simple and correct", "Text for deep subtrees is long and rebuilt at every level"],
     "code": '''from __future__ import annotations


class Frame:
    def __init__(self, name: str, children: list[Frame] | None = None) -> None:
        self.name = name
        self.children: list[Frame] = children if children is not None else []


def render(frame: Frame) -> str:
    if not frame.children:
        return frame.name
    return f"{frame.name}({','.join(render(c) for c in frame.children)})"


def find_duplicate_subtrees(root: Frame | None) -> list[str]:
    if root is None:
        return []
    count: dict[str, int] = {}
    stack = [root]
    while stack:
        node = stack.pop()
        text = render(node)
        count[text] = count.get(text, 0) + 1
        stack.extend(node.children)
    return sorted(t for t, n in count.items() if n >= 2)
'''},
]

WAYS_TO_SOLVE = [
    {"name": "Render every subtree", "idea": "Build each subtree's full text and count identical strings.",
     "time": "O(n²)", "space": "O(n²)", "use": "Small traces; easiest to explain."},
    {"name": "Shape IDs", "idea": "Hash (name, child IDs) to a small integer bottom-up; text only for duplicates.",
     "time": "O(n)", "space": "O(n)", "use": "Deep production traces with thousands of frames."},
]
