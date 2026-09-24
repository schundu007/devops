"""Tests for DC-NET-01 IP Address Validator."""
from __future__ import annotations

import ipaddress
import random

import pytest
from chip import load_impl

impl = load_impl(__file__)
classify = impl.classify_address


@pytest.mark.parametrize("addr", ["10.0.3.17", "192.0.2.1", "0.0.0.0", "255.255.255.255"])
def test_valid_ipv4(addr):
    assert classify(addr) == "IPv4"


@pytest.mark.parametrize(
    "addr",
    [
        "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        "2001:db8:85a3:0:0:8A2E:0370:7334",  # short groups and mixed case are fine
        "0:0:0:0:0:0:0:1",
    ],
)
def test_valid_ipv6(addr):
    assert classify(addr) == "IPv6"


@pytest.mark.parametrize(
    "addr",
    [
        "0127.0.0.1",   # leading zero: octal 0127 = 87 in some parsers (SSRF trick)
        "10.0.03.17",   # leading zero inside
        "256.0.0.1",    # boundary: one above 255
        "10.0.0",       # too few parts
        "10.0.0.1.",    # trailing dot
        "10..0.1",      # empty part
        "1e1.0.0.1",    # not decimal
        "-1.0.0.1",
        "10.0.0.٣",     # non-ASCII digit
    ],
)
def test_invalid_ipv4(addr):
    assert classify(addr) == "Neither"


@pytest.mark.parametrize(
    "addr",
    [
        "2001:db8::1",                            # "::" shortening is out of scope
        "2001:0db8:85a3:00000:0:8a2e:0370:7334",  # 5-digit group
        "2001:db8:85a3:0:0:8a2e:0370:733g",       # not hex
        "2001:db8:85a3:0:0:8a2e:0370:",           # empty last group
        "1:2:3:4:5:6:7:8:9",                      # nine groups
    ],
)
def test_invalid_ipv6(addr):
    assert classify(addr) == "Neither"


def test_empty_and_single_characters():
    for addr in ["", ".", ":", "1", "a"]:
        assert classify(addr) == "Neither"


def test_allow_list_input_filter():
    # Production flavour: an ingress reads X-Forwarded-For and only lets
    # well-formed addresses reach the allow-list check. The octal-looking and
    # decimal-integer forms must be rejected, not "normalised".
    header = "10.0.3.17, 0177.0.0.1, 2130706433, 192.0.2.44, 10.0.0.1:8080"
    kept = [a.strip() for a in header.split(",") if classify(a.strip()) != "Neither"]
    assert kept == ["10.0.3.17", "192.0.2.44"]


def _stdlib(addr: str) -> str:
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return "Neither"
    return "IPv4" if ip.version == 4 else "IPv6"


def test_fuzz_agrees_with_ipaddress_where_rules_match():
    # The chip's rules and Python's ipaddress agree on dotted IPv4 (both reject
    # leading zeros) and on full 8-group IPv6. They differ on "::" shortening,
    # embedded IPv4 ("::ffff:10.0.0.1") and scope IDs ("fe80::1%eth0"), which
    # ipaddress accepts and this chip rejects, so those shapes are filtered out.
    rng = random.Random(468)
    v4_parts = ["0", "1", "9", "10", "99", "255", "256", "00", "01", "007", "300", "1000", "", "a"]
    v6_groups = ["0", "1", "db8", "DB8", "0000", "ffff", "FFFF", "fffff", "g", "", "12345"]
    checked = 0
    for _ in range(20_000):
        if rng.random() < 0.5:
            addr = ".".join(rng.choice(v4_parts) for _ in range(rng.choice([3, 4, 4, 4, 5])))
        else:
            addr = ":".join(rng.choice(v6_groups) for _ in range(rng.choice([7, 8, 8, 8, 9])))
        if "::" in addr or "%" in addr:
            continue
        assert classify(addr) == _stdlib(addr), addr
        checked += 1
    assert checked > 10_000
