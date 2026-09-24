"""DC-NET-01 IP Address Validator — your attempt.

Run your code against the tests:
    make try CHIP=05-networking/DC-NET-01-ip-validator
"""
from __future__ import annotations


def classify_address(addr: str) -> str:
    """Return "IPv4", "IPv6" or "Neither" for one address string.

    IPv4: four decimal parts 0-255 separated by ".", no leading zeros ("0" alone is fine).
    IPv6: eight groups of 1-4 hex digits separated by ":", upper or lower case,
          leading zeros allowed, no "::" shortening.
    Anything else is "Neither".
    """
    # TODO
    raise NotImplementedError
