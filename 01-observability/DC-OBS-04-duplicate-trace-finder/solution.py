"""DC-OBS-04 Duplicate Stack Trace Finder — reference solution."""
from __future__ import annotations


class Frame:
    """One node of a call tree: a function name and the calls it made, in order."""

    def __init__(self, name: str, children: list[Frame] | None = None) -> None:
        self.name = name
        self.children: list[Frame] = children if children is not None else []


def render(frame: Frame) -> str:
    """Canonical text form: `name` for a leaf, `name(child1,child2,...)` otherwise."""
    if not frame.children:
        return frame.name
    return f"{frame.name}({','.join(render(c) for c in frame.children)})"


def find_duplicate_subtrees(root: Frame | None) -> list[str]:
    """Canonical form of every subtree shape that appears two or more times, sorted."""
    if root is None:
        return []

    shape_id: dict[tuple[str, tuple[int, ...]], int] = {}  # (name, child ids) -> id
    count: dict[int, int] = {}                               # id -> occurrences
    first: dict[int, Frame] = {}                             # id -> one frame with it
    ids: dict[int, int] = {}                                 # id(frame) -> shape id

    # Iterative post-order so a 10,000-frame-deep trace cannot hit the recursion limit.
    stack: list[tuple[Frame, bool]] = [(root, False)]
    while stack:
        node, children_done = stack.pop()
        if not children_done:
            stack.append((node, True))
            for child in reversed(node.children):
                stack.append((child, False))
            continue
        # Children already have ids, so a subtree is identified by a small tuple,
        # not by its full text. Equal tuples mean equal shapes.
        key = (node.name, tuple(ids[id(c)] for c in node.children))
        sid = shape_id.setdefault(key, len(shape_id))
        ids[id(node)] = sid
        count[sid] = count.get(sid, 0) + 1
        first.setdefault(sid, node)

    # Render text only for the duplicates we report.
    return sorted(render(first[sid]) for sid, n in count.items() if n >= 2)
