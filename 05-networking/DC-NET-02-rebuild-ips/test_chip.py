"""Tests for DC-NET-02 Rebuild IPs from Broken Logs."""
from __future__ import annotations

import ipaddress
import random
from itertools import combinations

from chip import load_impl

impl = load_impl(__file__)


def solve(s: str) -> list[str]:
    return sorted(impl.restore_addresses(s))


def brute(s: str) -> list[str]:
    # Independent reference: try every choice of 3 dot positions, then validate
    # with the standard library (which rejects leading zeros).
    out = []
    for a, b, c in combinations(range(1, len(s)), 3):
        cand = f"{s[:a]}.{s[a:b]}.{s[b:c]}.{s[c:]}"
        try:
            ipaddress.IPv4Address(cand)
        except ValueError:
            continue
        out.append(cand)
    return sorted(out)


def test_normal_log_field():
    assert solve("19216811") == sorted([
        "1.92.168.11", "19.2.168.11", "19.21.68.11", "19.216.8.11", "19.216.81.1",
        "192.1.68.11", "192.16.8.11", "192.16.81.1", "192.168.1.1",
    ])


def test_empty_and_too_short():
    assert solve("") == []
    assert solve("1") == []
    assert solve("123") == []


def test_boundary_lengths():
    assert solve("0000") == ["0.0.0.0"]                 # shortest: 4 digits
    assert solve("255255255255") == ["255.255.255.255"]  # longest: 12 digits
    assert solve("2552552552551") == []                 # 13 digits: impossible


def test_leading_zeros_are_never_produced():
    assert solve("010010") == ["0.10.0.10", "0.100.1.0"]
    for ip in solve("1001001"):
        assert all(p == "0" or not p.startswith("0") for p in ip.split("."))


def test_non_digit_input():
    assert solve("10.0.0.1") == []
    assert solve("1a2b3c4d") == []


def test_forensics_match_against_known_hosts():
    # Production flavour: a log field "1001317" lost its dots. The inventory knows
    # these hosts; which could it have been? More than one match means the log
    # alone cannot name the host.
    inventory = {"10.0.13.17", "10.0.3.17", "100.1.31.7", "10.1.1.1"}
    candidates = set(solve("1001317"))
    assert candidates & inventory == {"10.0.13.17", "100.1.31.7"}


def test_random_matches_brute_force():
    rng = random.Random(93)
    for _ in range(3_000):
        n = rng.randint(0, 13)
        s = "".join(rng.choice("0012559") for _ in range(n))
        assert solve(s) == brute(s), s
