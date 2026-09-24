"""Tests for DC-SEC-08 IAM Wildcard Matcher."""
from __future__ import annotations

import fnmatch
import random

import pytest
from chip import load_impl

impl = load_impl(__file__)


@pytest.mark.parametrize(
    "pattern,value,expected",
    [
        ("s3:Get*", "s3:GetObject", True),
        ("s3:Get*", "s3:PutObject", False),
        ("ec2:Describe?nstances", "ec2:DescribeInstances", True),
        ("a*b*c", "aXXbYYc", True),
        ("a*b*c", "aXXbYY", False),
    ],
)
def test_normal(pattern, value, expected):
    assert impl.matches(pattern, value) is expected


def test_empty_and_single():
    assert impl.matches("", "") is True
    assert impl.matches("*", "") is True
    assert impl.matches("?", "") is False
    assert impl.matches("", "a") is False
    assert impl.matches("?", "a") is True
    assert impl.matches("***", "abc") is True


def test_whole_string_boundaries():
    # The match must cover the whole value, not just a prefix or substring.
    assert impl.matches("s3:Get", "s3:GetObject") is False
    assert impl.matches("Object", "s3:GetObject") is False
    assert impl.matches("*Object", "s3:GetObject") is True
    assert impl.matches("s3:GetObject?", "s3:GetObject") is False


def test_production_s3_log_bucket_policy():
    resource = "arn:aws:s3:::logs-*/2026/*"
    assert impl.matches(resource, "arn:aws:s3:::logs-prod/2026/03/14/app.log") is True  # '*' spans '/'
    assert impl.matches(resource, "arn:aws:s3:::logs-prod/2025/12/31/app.log") is False
    assert impl.matches(resource, "arn:aws:s3:::logs-/2026/x") is True                  # '*' may be empty
    assert impl.matches(resource, "arn:aws:s3:::billing-logs-prod/2026/x") is False     # anchored at start
    # Action names are case-insensitive in IAM, so the caller lowercases both sides.
    action = "s3:Get*".lower()
    assert impl.matches(action, "S3:GetObjectVersion".lower()) is True
    assert impl.matches(action, "s3:PutObject".lower()) is False


def test_large_random_matches_fnmatch():
    rng = random.Random(44)
    for _ in range(3_000):
        pat = "".join(rng.choice("ab*?:") for _ in range(rng.randint(0, 10)))
        val = "".join(rng.choice("ab:") for _ in range(rng.randint(0, 12)))
        # Independent reference: fnmatch has the same '*' and '?' rules
        # (the alphabet has no '[' so its character classes never apply).
        assert impl.matches(pat, val) is fnmatch.fnmatchcase(val, pat), (pat, val)


def test_worst_case_is_polynomial():
    # Many stars and a value that almost matches: exponential backtracking would hang here.
    pattern = "*" + "a*" * 400 + "b"
    assert impl.matches(pattern, "a" * 2_000) is False
    assert impl.matches(pattern, "a" * 2_000 + "b") is True
