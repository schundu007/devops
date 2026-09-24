"""Tests for DC-SEC-14 Identity Linker."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def brute(accounts: list[list[str]]) -> list[list[str]]:
    # Independent reference: merge email sets pairwise until nothing overlaps.
    groups = [(a[0], set(a[1:])) for a in accounts]
    merged = True
    while merged:
        merged = False
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                if groups[i][1] & groups[j][1]:
                    groups[i] = (groups[i][0], groups[i][1] | groups[j][1])
                    groups.pop(j)
                    merged = True
                    break
            if merged:
                break
    return sorted(([n, *sorted(e)] for n, e in groups), key=lambda r: (r[0], r[1]))


def test_normal_merge_through_shared_email():
    accounts = [
        ["priya", "priya@corp.example", "p.shah@corp.example"],
        ["priya", "priya@corp.example", "priya-gh@users.example"],
        ["tom", "tom@corp.example"],
    ]
    assert impl.link_identities(accounts) == [
        ["priya", "p.shah@corp.example", "priya-gh@users.example", "priya@corp.example"],
        ["tom", "tom@corp.example"],
    ]


def test_single_account_single_email():
    assert impl.link_identities([["sam", "sam@corp.example"]]) == [["sam", "sam@corp.example"]]


def test_same_name_different_people_stay_apart():
    accounts = [["alex", "alex1@corp.example"], ["alex", "alex2@corp.example"]]
    assert impl.link_identities(accounts) == [
        ["alex", "alex1@corp.example"],
        ["alex", "alex2@corp.example"],
    ]


def test_transitive_chain_links_all():
    # A-B share b, B-C share c: A and C are the same person with no direct overlap.
    accounts = [["kim", "a@x.example", "b@x.example"],
                ["kim", "c@x.example", "d@x.example"],
                ["kim", "b@x.example", "c@x.example"]]
    assert impl.link_identities(accounts) == [
        ["kim", "a@x.example", "b@x.example", "c@x.example", "d@x.example"]]


def test_duplicate_email_inside_one_account():
    accounts = [["lee", "lee@corp.example", "lee@corp.example"]]
    assert impl.link_identities(accounts) == [["lee", "lee@corp.example"]]


def test_production_offboarding():
    # Okta, AWS SSO and GitHub exports for a leaver: one person, three systems.
    accounts = [
        ["dana", "dana@acme.example"],                               # Okta
        ["dana", "dana@acme.example", "dana.ops@acme.example"],      # AWS SSO
        ["dana", "dana.ops@acme.example", "dana-dev@users.example"], # GitHub
        ["eve", "eve@acme.example"],
    ]
    rows = impl.link_identities(accounts)
    assert rows[0] == ["dana", "dana-dev@users.example", "dana.ops@acme.example", "dana@acme.example"]
    assert len(rows) == 2


def test_large_random_matches_brute_force():
    rng = random.Random(721)
    for _ in range(5):
        pool = [f"u{i}@x.example" for i in range(300)]
        accounts = []
        for _ in range(200):
            emails = rng.sample(pool, rng.randint(1, 3))
            accounts.append([f"n{int(emails[0][1:].split('@')[0]) % 7}", *emails])
        # Random names may disagree inside a merged group, so compare the email groups only.
        rows = impl.link_identities(accounts)
        assert sorted(sorted(r[1:]) for r in rows) == sorted(sorted(r[1:]) for r in brute(accounts))
