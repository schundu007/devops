"""DC-SEC-01 Path Traversal Guard — reference solution."""
from __future__ import annotations


def normalize_path(path: str) -> str:
    """Canonical absolute form of a Unix-style path, using text rules only.

    "." is dropped, ".." removes the previous name (and stays at "/" at the top),
    repeated slashes collapse, and any other name (even "...") is kept.
    """
    stack: list[str] = []
    for part in path.split("/"):
        if part == "" or part == ".":
            continue  # "//" and "/./" add nothing
        if part == "..":
            if stack:
                stack.pop()  # go up one level; at "/" there is nowhere to go
            continue
        stack.append(part)
    return "/" + "/".join(stack)


def is_within_root(root: str, requested: str) -> bool:
    """True if `requested` (absolute, or relative to `root`) stays inside `root`.

    Text-only check. In production, also resolve symlinks (os.path.realpath)
    before comparing, or a link inside root can still point outside it.
    """
    base = normalize_path(root)
    target = normalize_path(requested if requested.startswith("/") else base + "/" + requested)
    if base == "/":
        return True
    # Compare whole path segments: "/srv/app2" must not pass for root "/srv/app".
    return target == base or target.startswith(base + "/")
