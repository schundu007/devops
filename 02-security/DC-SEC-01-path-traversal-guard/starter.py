"""DC-SEC-01 Path Traversal Guard — your attempt.

Run your code against the tests:
    make try CHIP=02-security/DC-SEC-01-path-traversal-guard
"""
from __future__ import annotations


def normalize_path(path: str) -> str:
    """Return the canonical absolute form of a Unix-style path.

    - "." means "this directory" and is dropped.
    - ".." removes the previous name; at "/" it stays at "/".
    - Repeated slashes count as one. A trailing slash is removed (except for "/").
    - Any other name, including "...", is an ordinary name.
    An empty string means "/".
    """
    # TODO
    raise NotImplementedError


def is_within_root(root: str, requested: str) -> bool:
    """Return True if `requested` stays inside `root` after normalizing.

    `requested` is absolute (starts with "/") or relative to `root`.
    "/srv/app2" is NOT inside "/srv/app".
    """
    # TODO
    raise NotImplementedError
