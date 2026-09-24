"""Tests for DC-SEC-17 Streaming Secret Scanner."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def run(patterns: list[str], text: str) -> list[bool]:
    s = impl.SecretScanner(patterns)
    return [s.feed(c) for c in text]


def brute(patterns: list[str], text: str) -> list[bool]:
    # Independent reference: check every pattern against the text so far.
    return [any(text[: i + 1].endswith(p) for p in patterns) for i in range(len(text))]


def test_normal_match_at_last_char():
    assert run(["key"], "a key") == [False, False, False, False, True]


def test_single_char_pattern():
    assert run(["x"], "axbx") == [False, True, False, True]


def test_overlapping_and_nested_patterns():
    # "abc" and "bc" both end at 'c'; "ab" ends at 'b'.
    assert run(["abc", "bc", "ab"], "abc") == [False, True, True]


def test_match_only_on_the_final_character_of_pattern():
    assert run(["token"], "toke") == [False] * 4
    assert run(["token"], "tokens") == [False] * 4 + [True, False]


def test_first_character_and_long_quiet_stream():
    s = impl.SecretScanner(["abc"])
    assert s.feed("c") is False          # a pattern's last char alone is not a match
    assert not any(s.feed("z") for _ in range(10_000))
    assert [s.feed(c) for c in "abc"] == [False, False, True]


def test_production_ci_log_stream():
    # Fake credential prefixes streamed from a CI job log, one char at a time.
    patterns = ["AKIAFAKE", "ghp_FAKE", "-----BEGIN FAKE KEY"]
    log = "step 3: export AWS_KEY=AKIAFAKE123 && echo ok"
    hits = [i for i, v in enumerate(run(patterns, log)) if v]
    assert hits == [log.index("AKIAFAKE") + len("AKIAFAKE") - 1]


def test_large_random_matches_brute_force():
    rng = random.Random(1032)
    patterns = ["".join(rng.choice("ab") for _ in range(rng.randint(1, 8))) for _ in range(40)]
    text = "".join(rng.choice("abc") for _ in range(20_000))
    assert run(patterns, text) == brute(patterns, text)
