"""Tests for DC-SEC-09 IP Range to CIDR Blocks."""
from __future__ import annotations

import ipaddress
import random

from chip import load_impl

impl = load_impl(__file__)


def reference(start_ip: str, count: int) -> list[str]:
    """Independent reference: the standard library's minimal summarization."""
    if count == 0:
        return []
    first = ipaddress.IPv4Address(start_ip)
    last = ipaddress.IPv4Address(int(first) + count - 1)
    return [str(n) for n in ipaddress.summarize_address_range(first, last)]


def test_anchor_example():
    assert impl.range_to_cidrs("10.0.0.8", 20) == ["10.0.0.8/29", "10.0.0.16/29", "10.0.0.24/30"]


def test_empty_and_single():
    assert impl.range_to_cidrs("10.0.0.8", 0) == []
    assert impl.range_to_cidrs("192.0.2.77", 1) == ["192.0.2.77/32"]


def test_aligned_block_is_one_rule():
    assert impl.range_to_cidrs("10.1.0.0", 65_536) == ["10.1.0.0/16"]
    assert impl.range_to_cidrs("10.1.0.0", 65_535)[-1] == "10.1.255.254/32"


def test_boundaries_of_the_address_space():
    assert impl.range_to_cidrs("0.0.0.0", 2**32) == ["0.0.0.0/0"]
    assert impl.range_to_cidrs("255.255.255.255", 1) == ["255.255.255.255/32"]
    assert impl.range_to_cidrs("255.255.255.254", 2) == ["255.255.255.254/31"]


def test_production_vendor_allow_list():
    # A vendor says: "our egress NAT uses 192.0.2.3 to 192.0.2.60 (58 addresses)".
    rules = impl.range_to_cidrs("192.0.2.3", 58)
    assert rules == ["192.0.2.3/32", "192.0.2.4/30", "192.0.2.8/29", "192.0.2.16/28",
                     "192.0.2.32/28", "192.0.2.48/29", "192.0.2.56/30", "192.0.2.60/32"]
    covered = sum(ipaddress.ip_network(r).num_addresses for r in rules)
    assert covered == 58   # exactly the vendor's range: not one address more


def test_large_random_matches_ipaddress():
    rng = random.Random(751)
    for _ in range(2_000):
        start = rng.randint(0, 2**32 - 1)
        count = rng.randint(1, min(2**32 - start, rng.choice([10, 1_000, 10**6, 10**9])))
        ip = str(ipaddress.IPv4Address(start))
        assert impl.range_to_cidrs(ip, count) == reference(ip, count), (ip, count)
