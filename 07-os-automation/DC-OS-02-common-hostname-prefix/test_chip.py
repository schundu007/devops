"""Tests for DC-OS-02 Common Hostname Prefix."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def _brute(hosts: list[str]) -> str:
    # Independent reference: the longest length L where every host shares hosts[0][:L].
    if not hosts:
        return ""
    best = ""
    for length in range(len(hosts[0]) + 1):
        cand = hosts[0][:length]
        if all(h.startswith(cand) for h in hosts):
            best = cand
    return best


def test_two_hosts():
    hosts = ["us-east-prod-api-01", "us-east-prod-worker-02"]
    assert impl.common_prefix(hosts) == "us-east-prod-"


def test_no_common_prefix():
    assert impl.common_prefix(["web-01", "api-01", "db-01"]) == ""


def test_empty_list_and_single_host():
    assert impl.common_prefix([]) == ""
    assert impl.common_prefix(["bastion-01"]) == "bastion-01"


def test_one_host_is_prefix_of_another():
    # Boundary: the whole shorter host is the answer.
    assert impl.common_prefix(["cache", "cache-01", "cache-02"]) == "cache"


def test_empty_hostname_in_list():
    assert impl.common_prefix(["api-01", "", "api-02"]) == ""


def test_prefix_can_cut_mid_token():
    # Production flavour: the character prefix is "eu-west-prod-k", which is not a
    # clean name segment. Level Up 1 covers segment-aware prefixes.
    hosts = ["eu-west-prod-kafka-01", "eu-west-prod-kube-node-7", "eu-west-prod-kafka-02"]
    assert impl.common_prefix(hosts) == "eu-west-prod-k"


def test_random_matches_brute_force():
    rng = random.Random(14)
    alphabet = "ab-"
    for _ in range(300):
        stem = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 6)))
        hosts = [stem + "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 5)))
                 for _ in range(rng.randint(1, 8))]
        assert impl.common_prefix(hosts) == _brute(hosts)


def test_large_inventory():
    hosts = [f"ap-south-1-prod-node-{i:05d}" for i in range(10_000)]
    # Numbers 00000-09999 all start with "0", so the prefix runs one character past the dash.
    assert impl.common_prefix(hosts) == "ap-south-1-prod-node-0"
    hosts.append("ap-south-1-prod-node-10000")
    assert impl.common_prefix(hosts) == "ap-south-1-prod-node-"
