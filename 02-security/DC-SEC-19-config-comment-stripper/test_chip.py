"""Tests for DC-SEC-19 Config Comment Stripper."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def brute(lines: list[str]) -> list[str]:
    # Independent reference: work on the whole text with str.find.
    text = "\n".join(lines)
    out, pos = [], 0
    while pos < len(text):
        a, b = text.find("//", pos), text.find("/*", pos)
        cands = [x for x in (a, b) if x != -1]
        if not cands:
            out.append(text[pos:])
            break
        first = min(cands)
        out.append(text[pos:first])
        if first == a:
            nl = text.find("\n", first)
            pos = len(text) if nl == -1 else nl       # keep the newline itself
        else:
            pos = text.find("*/", first + 2) + 2      # newlines inside are removed
    return [ln for ln in "".join(out).split("\n") if ln]


def test_normal_line_and_block_comments():
    src = ["a = 1 // set a", "/* header */", "b = 2"]
    assert impl.strip_comments(src) == ["a = 1 ", "b = 2"]


def test_empty_and_single():
    assert impl.strip_comments([]) == []
    assert impl.strip_comments(["x"]) == ["x"]
    assert impl.strip_comments(["// only a comment"]) == []


def test_multiline_block_joins_lines():
    assert impl.strip_comments(["a/*comment", "line", "more*/b"]) == ["ab"]


def test_block_open_does_not_close_itself():
    # "/*/" opens a block; the "/" right after "/*" is not the end.
    assert impl.strip_comments(["x/*/y*/z"]) == ["xz"]


def test_first_marker_wins():
    assert impl.strip_comments(["a // b /* c"]) == ["a "]
    assert impl.strip_comments(["a /* b // c */ d"]) == ["a  d"]


def test_production_jsonc_settings():
    src = [
        "{",
        '  // region for the fake staging cluster',
        '  "region": "eu-west-1", /* was us-east-1 */',
        "  /* disabled until INC-2231 is closed",
        '  "debug": true,',
        "  */",
        '  "replicas": 3',
        "}",
    ]
    # Whitespace-only leftovers ("  ") are not empty, so they stay: only "" is dropped.
    assert impl.strip_comments(src) == [
        "{",
        "  ",
        '  "region": "eu-west-1", ',
        "  ",
        '  "replicas": 3',
        "}",
    ]


def test_large_random_matches_brute_force():
    rng = random.Random(722)
    alphabet = "ab /*"
    for _ in range(300):
        lines = ["".join(rng.choice(alphabet) for _ in range(rng.randint(0, 12)))
                 for _ in range(rng.randint(1, 8))]
        # Make sure any open block is closed at the end, as the problem promises.
        lines.append("*/")
        assert impl.strip_comments(lines) == brute(lines), lines
    # Scale: 20,000 lines of config with scattered comments.
    big = ["key = value // note" if i % 3 else "/* a */ x = 1 /* b" if i % 2 else "c */ y = 2"
           for i in range(20_000)] + ["*/"]
    assert impl.strip_comments(big) == brute(big)
