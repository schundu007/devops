"""Tests for DC-SEC-04 Domain Suffix Compactor."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def reference(hostnames: list[str]) -> list[str]:
    """Independent O(n^2) reference: keep names no other name ends with '.' + name."""
    names = {h.lower().rstrip(".") for h in hostnames} - {""}
    return sorted(h for h in names if not any(g != h and g.endswith("." + h) for g in names))


def test_normal_suffixes_collapse():
    hosts = ["api.prod.example.com", "prod.example.com", "example.com", "cdn.example.net"]
    assert impl.compact(hosts) == ["api.prod.example.com", "cdn.example.net"]
    assert impl.encoded_length(hosts) == len("api.prod.example.com#cdn.example.net#")


def test_empty_and_single():
    assert impl.compact([]) == []
    assert impl.encoded_length([]) == 0
    assert impl.compact(["example.com"]) == ["example.com"]
    assert impl.encoded_length(["example.com"]) == 12


def test_label_boundary_not_character_suffix():
    # Boundary: "ample.com" ends the text of "example.com" but is a different domain.
    assert impl.compact(["example.com", "ample.com"]) == ["ample.com", "example.com"]
    assert impl.compact(["a.b", "b"]) == ["a.b"]


def test_case_trailing_dot_and_duplicates():
    hosts = ["API.Example.COM.", "api.example.com", "example.com.", ""]
    assert impl.compact(hosts) == ["api.example.com"]


def test_production_egress_allow_list():
    # An egress proxy allow-list for the payments namespace.
    allow = [
        "hooks.slack.com", "slack.com", "api.stripe.com", "stripe.com",
        "files.stripe.com", "sts.us-east-1.amazonaws.com", "amazonaws.com",
        "ecr.us-east-1.amazonaws.com", "us-east-1.amazonaws.com",
    ]
    kept = impl.compact(allow)
    assert kept == sorted([
        "hooks.slack.com", "api.stripe.com", "files.stripe.com",
        "sts.us-east-1.amazonaws.com", "ecr.us-east-1.amazonaws.com",
    ])
    assert impl.encoded_length(allow) < sum(len(h) + 1 for h in allow)


def test_large_random_matches_reference():
    rng = random.Random(820)
    labels = ["a", "b", "api", "prod", "dev", "example", "com", "net"]
    for _ in range(200):
        hosts = [".".join(rng.choice(labels) for _ in range(rng.randint(1, 4))) for _ in range(rng.randint(0, 60))]
        assert impl.compact(hosts) == reference(hosts)
    many = [f"svc{i}.ns{i % 50}.cluster.local" for i in range(20_000)] + [f"ns{i}.cluster.local" for i in range(50)]
    kept = impl.compact(many)
    assert len(kept) == 20_000 and "cluster.local" not in kept
