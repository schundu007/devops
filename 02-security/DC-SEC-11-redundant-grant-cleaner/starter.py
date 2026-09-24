"""DC-SEC-11 Redundant Prefix Grant Cleaner — your attempt.

Run your code against the tests:
    make try CHIP=02-security/DC-SEC-11-redundant-grant-cleaner
"""
from __future__ import annotations


def remove_covered(grants: list[str]) -> list[str]:
    """Return the grants that are not covered by another grant, sorted ascending.

    A grant covers another if the other path starts with it followed by "/".
    Example: "/logs/app" covers "/logs/app/2026" but not "/logs/apple".
    """
    # TODO
    raise NotImplementedError
