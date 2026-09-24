"""DC-SEC-09 IP Range to CIDR Blocks — your attempt.

Run your code against the tests:
    make try CHIP=02-security/DC-SEC-09-ip-range-to-cidr-blocks
"""
from __future__ import annotations


def range_to_cidrs(start_ip: str, count: int) -> list[str]:
    """Return the fewest CIDR blocks covering exactly `count` IPv4 addresses from `start_ip`.

    Blocks are listed in address order, as strings like "10.0.0.8/29".
    Return [] when count is 0. Do not use the ipaddress module here.
    """
    # TODO
    raise NotImplementedError
