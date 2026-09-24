"""DC-SEC-12 Blast Radius of a Leaked Credential — your attempt.

Run your code against the tests:
    make try CHIP=02-security/DC-SEC-12-credential-blast-radius
"""
from __future__ import annotations


def blast_radius(holds: list[list[int]], leaked: int) -> list[int]:
    """Return every resource an attacker can reach, sorted ascending.

    holds[i] lists the resources whose credentials are stored in resource i.
    The attacker starts with `leaked` (included in the answer).
    """
    # TODO
    raise NotImplementedError
