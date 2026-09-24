"""DC-OBS-04 Duplicate Stack Trace Finder — your attempt.

Run your code against the tests:
    make try CHIP=01-observability/DC-OBS-04-duplicate-trace-finder
"""
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
    """Return render(subtree) for every subtree shape that appears 2+ times.

    Two subtrees have the same shape when they have the same name and the same
    children in the same order, recursively. Report each shape once, sorted.
    """
    # TODO
    raise NotImplementedError
