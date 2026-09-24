"""DC-SEC-11 Redundant Prefix Grant Cleaner — reference solution."""
from __future__ import annotations


def remove_covered(grants: list[str]) -> list[str]:
    """Drop every grant that sits under another grant; return the rest sorted."""
    kept: list[str] = []
    # Sort by path segments, not raw text. Raw text puts "/logs/app-old" between
    # "/logs/app" and "/logs/app/2026" because "-" sorts before "/". Segment order
    # keeps every parent directly in front of all of its children.
    for path in sorted(grants, key=lambda p: p.split("/")):
        # The "/" matters: /logs/app covers /logs/app/2026 but not /logs/apple.
        if kept and path.startswith(kept[-1] + "/"):
            continue
        kept.append(path)
    return sorted(kept)
