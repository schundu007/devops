"""DC-SEC-04 Domain Suffix Compactor — your attempt.

Run your code against the tests:
    make try CHIP=02-security/DC-SEC-04-domain-suffix-compactor
"""
from __future__ import annotations


def compact(hostnames: list[str]) -> list[str]:
    """Return, sorted, the hostnames that are not a label-suffix of another one.

    Compare names in lowercase, without a trailing dot, and ignore duplicates
    and empty names. "prod.example.com" is covered by "api.prod.example.com";
    "ample.com" is NOT covered by "example.com" (whole labels only).
    """
    # TODO
    raise NotImplementedError


def encoded_length(hostnames: list[str]) -> int:
    """Length of one string holding every kept name, each followed by '#'."""
    # TODO
    raise NotImplementedError
