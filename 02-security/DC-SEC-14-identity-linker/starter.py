"""DC-SEC-14 Identity Linker — your attempt.

Run your code against the tests:
    make try CHIP=02-security/DC-SEC-14-identity-linker
"""
from __future__ import annotations


def link_identities(accounts: list[list[str]]) -> list[list[str]]:
    """Merge accounts that belong to the same person.

    accounts[i] = [name, email1, email2, ...]. Two accounts are the same person
    if they share at least one email (directly or through a chain of accounts).
    Return one row per person: [name, *emails sorted ascending], with rows
    sorted by (name, first email).
    """
    # TODO
    raise NotImplementedError
