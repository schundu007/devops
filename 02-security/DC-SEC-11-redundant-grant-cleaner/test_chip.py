"""Tests for DC-SEC-11 Redundant Prefix Grant Cleaner."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def brute(grants: list[str]) -> list[str]:
    # Independent reference: compare every pair.
    return sorted(
        g for g in grants
        if not any(o != g and g.startswith(o + "/") for o in grants)
    )


def test_normal_parent_and_children():
    grants = ["/logs/app", "/logs/app/2026", "/logs/app/2026/09", "/metrics"]
    assert impl.remove_covered(grants) == ["/logs/app", "/metrics"]


def test_empty_and_single():
    assert impl.remove_covered([]) == []
    assert impl.remove_covered(["/logs"]) == ["/logs"]


def test_segment_boundary_not_string_prefix():
    # "/logs/app" is a text prefix of "/logs/apple", but not a path parent.
    assert impl.remove_covered(["/logs/apple", "/logs/app"]) == ["/logs/app", "/logs/apple"]


def test_input_order_does_not_matter():
    grants = ["/a/b/c", "/a/b", "/a"]
    assert impl.remove_covered(grants) == ["/a"]
    assert impl.remove_covered(list(reversed(grants))) == ["/a"]


def test_siblings_with_dash_sort_before_slash():
    # "-" (0x2d) sorts before "/" (0x2f): "/logs/app-old" lands between
    # "/logs/app" and "/logs/app/2026" after sorting. It must not break coverage.
    grants = ["/logs/app", "/logs/app-old", "/logs/app/2026"]
    assert impl.remove_covered(grants) == brute(grants)


def test_production_bucket_policy():
    # Role data-reader in a fake account: three grants, one already covered.
    grants = [
        "/acme-logs-prod/app",
        "/acme-logs-prod/app/2026",
        "/acme-logs-prod/audit",
        "/acme-logs-prod/app/2026/09/23",
        "/acme-backups/db",
    ]
    assert impl.remove_covered(grants) == [
        "/acme-backups/db",
        "/acme-logs-prod/app",
        "/acme-logs-prod/audit",
    ]


def test_large_random_matches_brute_force():
    rng = random.Random(1233)
    parts = ["a", "b", "ab", "a-b", "c"]
    grants = sorted({
        "/" + "/".join(rng.choice(parts) for _ in range(rng.randint(1, 5)))
        for _ in range(1_500)
    })
    rng.shuffle(grants)
    assert impl.remove_covered(grants) == brute(grants)
