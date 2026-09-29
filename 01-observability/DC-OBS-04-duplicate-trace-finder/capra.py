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

VARIANT_TITLE = "Duplicate call trees"
VARIANT_APPROACH = "Shape IDs, iterative post-order · O(n) · O(n)"


def _rand_forest(seed, names, count, depth):
    rng = random.Random(seed)

    def rand_tree(d):
        if d == 0 or rng.random() < 0.3:
            return leaf(rng.choice(names))
        return node(rng.choice(names), *[rand_tree(d - 1) for _ in range(rng.randint(1, 3))])

    return node("root", *[rand_tree(depth) for _ in range(count)])


_BLOCKS_IDS = '''from __future__ import annotations


def duplicate_blocks(root) -> list[str]:
    if root is None:
        return []
    shape_id: dict = {}
    shapes: list = []           # id -> (name, sorted child ids)
    count: dict[int, int] = {}
    stack = [(root, False)]
    done: list[int] = []        # ids of finished children, in post-order
    while stack:
        node, expanded = stack.pop()
        if not expanded:
            stack.append((node, True))
            for child in node[1]:
                stack.append((child, False))
            continue
        k = len(node[1])
        kids = tuple(sorted(done[len(done) - k:])) if k else ()
        del done[len(done) - k:]
        key = (node[0], kids)
        if key not in shape_id:
            shape_id[key] = len(shapes)
            shapes.append(key)
        sid = shape_id[key]
        count[sid] = count.get(sid, 0) + 1
        done.append(sid)

    memo: dict[int, str] = {}

    def render(sid):
        if sid not in memo:
            name, kids = shapes[sid]
            memo[sid] = name if not kids else name + "(" + ",".join(sorted(render(c) for c in kids)) + ")"
        return memo[sid]

    return sorted(render(sid) for sid, n in count.items() if n >= 2)
'''

_BLOCKS_RENDER = '''from __future__ import annotations


def duplicate_blocks(root) -> list[str]:
    def render(node):
        name, children = node
        if not children:
            return name
        return name + "(" + ",".join(sorted(render(c) for c in children)) + ")"

    if root is None:
        return []
    count: dict[str, int] = {}
    stack = [root]
    while stack:
        node = stack.pop()
        text = render(node)
        count[text] = count.get(text, 0) + 1
        stack.extend(node[1])
    return sorted(t for t, n in count.items() if n >= 2)
'''

_LARGEST_IDS = '''from __future__ import annotations


def largest_repeat(root) -> list[int]:
    if root is None:
        return [0, 0]
    shape_id: dict = {}
    size: list[int] = []
    count: list[int] = []
    stack = [(root, False)]
    done: list[int] = []
    while stack:
        node, expanded = stack.pop()
        if not expanded:
            stack.append((node, True))
            for child in reversed(node[1]):
                stack.append((child, False))
            continue
        k = len(node[1])
        kids = tuple(done[len(done) - k:]) if k else ()
        del done[len(done) - k:]
        key = (node[0], kids)
        if key not in shape_id:
            shape_id[key] = len(size)
            size.append(1 + sum(size[c] for c in kids))
            count.append(0)
        sid = shape_id[key]
        count[sid] += 1
        done.append(sid)
    best = [0, 0]
    for sid in range(len(size)):
        if count[sid] >= 2 and [size[sid], count[sid]] > best:
            best = [size[sid], count[sid]]
    return best
'''

_LARGEST_RENDER = '''from __future__ import annotations


def largest_repeat(root) -> list[int]:
    def render(node):
        name, children = node
        if not children:
            return name
        return name + "(" + ",".join(render(c) for c in children) + ")"

    def frames(node):
        return 1 + sum(frames(c) for c in node[1])

    if root is None:
        return [0, 0]
    count: dict[str, int] = {}
    sizes: dict[str, int] = {}
    stack = [root]
    while stack:
        node = stack.pop()
        text = render(node)
        count[text] = count.get(text, 0) + 1
        sizes[text] = frames(node)
        stack.extend(node[1])
    best = [0, 0]
    for text, n in count.items():
        if n >= 2 and [sizes[text], n] > best:
            best = [sizes[text], n]
    return best
'''

VARIANTS = [
    {
        "key": "unordered-config-blocks",
        "title": "Duplicate config blocks",
        "approach": "Shape IDs over sorted child IDs · O(n log n) · O(n)",
        "spec": {"kind": "fn", "fn": "duplicate_blocks", "params": ["root"], "cmp": "exact"},
        "statement": "A platform team wants to pull repeated blocks out of a large Kubernetes/Helm values tree into shared templates. The tree arrives as nested lists `[name, [child, child, ...]]` (or `null` for no tree). Unlike a call trace, **child order does not matter** here: two blocks with the same keys in a different order are the same block.\n\n- A block's canonical form is `name` for a leaf, otherwise `name(c1,c2,...)` with the children's canonical forms **sorted**\n- Report the canonical form of every block shape that appears two or more times, each once, sorted\n\nThe technique is the main problem's shape IDs, with one change to the key.",
        "examples": [
            {"args": {"root": node("values", node("probe", leaf("port"), leaf("path")), node("probe", leaf("path"), leaf("port")))},
             "explanation": "The two probes list the same keys in a different order, so they are the same block: probe(path,port). path and port each repeat too.",
             "why": {"t": "Order ignored", "d": "The main problem's order trap is now a match."}},
            {"args": {"root": node("values", node("a", leaf("x"), leaf("x")), node("a", leaf("x")))},
             "explanation": "a(x,x) and a(x) differ: duplicates among children count. Only the x leaf repeats.",
             "why": {"t": "Multiset of children", "d": "Sorting keeps repeated children, so counts still matter."}},
        ],
        "constraints": ["0 ≤ number of nodes ≤ 3 · 10³", "Tree depth ≤ 30", "Names are 1 to 20 characters from [a-z0-9._-]"],
        "hints": [
            "Process children before parents (post-order) and give every distinct shape a small integer ID.",
            "Key a shape by (name, sorted tuple of child IDs): sorting the IDs makes the order irrelevant.",
            "Render text only for the shapes that repeat, sorting the children's texts when you render.",
        ],
        "tests": [
            {"args": {"root": None}, "why": {"t": "No tree", "d": "No tree, no duplicates."}},
            {"args": {"root": leaf("values")}, "why": {"t": "Single node", "d": "One node cannot repeat."}},
            {"args": {"root": node("r", node("a", leaf("b"), leaf("c"), leaf("d")), node("a", leaf("d"), leaf("b"), leaf("c")), node("a", leaf("c"), leaf("d"), leaf("b")))},
             "why": {"t": "Three permutations", "d": "Three orderings of one block collapse to a single shape."}},
            {"args": {"root": node("r", node("x", node("y", leaf("z"))), node("x", leaf("y"), leaf("z")))},
             "why": {"t": "Same names, other nesting", "d": "x(y(z)) and x(y,z) hold the same names but are different blocks."}},
            {"args": {"root": node("r", node("m", node("p", leaf("q"), leaf("s")), leaf("t")), node("m", leaf("t"), node("p", leaf("s"), leaf("q"))))},
             "why": {"t": "Nested reorder", "d": "Order is ignored at every level, not just the top."}},
            {"args": {"root": node("r", leaf("a"), leaf("b"), leaf("c"))}, "why": {"t": "All distinct", "d": "No repeated block."}},
            {"args": {"root": _rand_forest(404, ["env", "port", "image", "limits", "probe"], 60, 4)},
             "why": {"t": "Large input", "d": "A random values tree with a few hundred nodes."}},
        ],
        "solutions": [
            {"name": "Shape IDs over sorted child IDs (Optimal)",
             "description": "Iterative post-order. Each node's key is (name, sorted child IDs), mapped to a small ID; count IDs. Render canonical text, with sorted children, only for IDs seen twice or more.",
             "time": "O(n log n)", "space": "O(n)",
             "keyPoints": ["Sort child IDs, not child text, when building the key", "Equal keys mean equal blocks at every level", "Render once per repeated shape, memoized"],
             "code": _BLOCKS_IDS},
            {"name": "Render every block", "slow": True,
             "description": "Build the full canonical text of every subtree, sorting the children's texts at each level, and count identical strings.",
             "time": "O(n² log n)", "space": "O(n²)",
             "keyPoints": ["Direct from the definition", "Every ancestor re-renders the whole subtree"],
             "code": _BLOCKS_RENDER},
        ],
        "starter": '''from __future__ import annotations


def duplicate_blocks(root) -> list[str]:
    """root is [name, [children]] or None. Return canonical forms (children sorted) seen 2+ times, sorted."""
    # TODO
    raise NotImplementedError
''',
    },
    {
        "key": "largest-repeat",
        "title": "Biggest repeated call tree",
        "approach": "Shape IDs with subtree sizes · O(n) · O(n)",
        "spec": {"kind": "fn", "fn": "largest_repeat", "params": ["root"], "cmp": "exact"},
        "statement": "A profiler wants to point at the **most expensive** repeated work, not list every repeat. Given a call tree as nested lists `[name, [child, ...]]` (or `null`), with child order mattering as in the main problem:\n\n- find the subtree shape with the **most frames** among shapes that appear two or more times\n- return `[frames, times]`: its frame count and how many times it appears\n- if two shapes have the same frame count, pick the one that appears more often\n- return `[0, 0]` when nothing repeats\n\nCaching that one call tree saves `frames · (times - 1)` calls per request.",
        "examples": [
            {"args": {"root": node("main", chain("retry", "http.get", "dns.resolve"), chain("retry", "http.get", "dns.resolve"), leaf("dns.resolve"))},
             "explanation": "The retry chain (3 frames) appears twice. dns.resolve appears three times, but it is only 1 frame.",
             "why": {"t": "Size beats count", "d": "The largest repeated shape wins even when a smaller one repeats more."}},
            {"args": {"root": node("main", node("a", leaf("x")), node("b", leaf("y")), node("b", leaf("y")), node("a", leaf("x")), node("a", leaf("x")))},
             "explanation": "a(x) and b(y) are both 2 frames. a(x) appears three times, so the answer is [2, 3].",
             "why": {"t": "Tie on size", "d": "Equal frame counts break on the number of appearances."}},
        ],
        "constraints": ["0 ≤ number of frames ≤ 3 · 10³", "Tree depth ≤ 30"],
        "hints": [
            "Reuse the shape IDs from the main problem: (name, tuple of child IDs) in post-order.",
            "A shape's frame count is 1 plus its children's frame counts, computed once per new ID.",
            "Compare candidates as [frames, times] pairs, which gives the tie rule for free.",
        ],
        "tests": [
            {"args": {"root": None}, "why": {"t": "No tree", "d": "Nothing repeats: [0, 0]."}},
            {"args": {"root": leaf("main")}, "why": {"t": "Single frame", "d": "One frame cannot repeat."}},
            {"args": {"root": node("main", leaf("db"), leaf("db"))}, "why": {"t": "Leaf repeat", "d": "The smallest repeat: one frame, twice."}},
            {"args": {"root": node("main", node("a", leaf("b"), leaf("c")), node("a", leaf("c"), leaf("b")))}, "why": {"t": "Order matters", "d": "The a subtrees differ, so only single frames repeat."}},
            {"args": {"root": node("m", node("s", node("t", leaf("u"), leaf("v"))), node("s", node("t", leaf("u"), leaf("v"))), leaf("u"), leaf("u"))},
             "why": {"t": "Nested repeat", "d": "The whole s subtree (4 frames) repeats; its parts repeat too but are smaller."}},
            {"args": {"root": chain(*["f"] * 8)}, "why": {"t": "Deep chain", "d": "Every depth of a straight chain is a new shape: [0, 0]."}},
            {"args": {"root": _rand_forest(405, ["db.query", "cache.get", "http.get", "json.parse"], 60, 4)},
             "why": {"t": "Large input", "d": "A random call tree with a few hundred frames."}},
        ],
        "solutions": [
            {"name": "Shape IDs with sizes (Optimal)",
             "description": "Iterative post-order assigns each (name, child IDs) key an ID and records its frame count when first seen. Count appearances, then take the largest [frames, times] among IDs seen twice or more.",
             "time": "O(n)", "space": "O(n)",
             "keyPoints": ["Size is computed once per distinct shape", "No text is built at all", "Pairs compare frames first, then times"],
             "code": _LARGEST_IDS},
            {"name": "Render and measure every subtree", "slow": True,
             "description": "Render every subtree to text, count identical strings, and count each subtree's frames separately.",
             "time": "O(n²)", "space": "O(n²)",
             "keyPoints": ["Simple to reason about", "Deep trees re-render and re-count at every level"],
             "code": _LARGEST_RENDER},
        ],
        "starter": '''from __future__ import annotations


def largest_repeat(root) -> list[int]:
    """root is [name, [children]] or None. Return [frames, times] of the biggest repeated shape."""
    # TODO
    raise NotImplementedError
''',
    },
]
