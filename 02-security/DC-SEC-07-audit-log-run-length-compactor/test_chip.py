"""Tests for DC-SEC-07 Audit Log Run-Length Compactor."""
from __future__ import annotations

import itertools
import random

from chip import load_impl

impl = load_impl(__file__)


def reference(text: str) -> str:
    """Independent reference built with itertools.groupby (not in place)."""
    out = []
    for ch, grp in itertools.groupby(text):
        run_len = len(list(grp))
        out.append(ch + (str(run_len) if run_len > 1 else ""))
    return "".join(out)


def run(text: str) -> str:
    buf = list(text)
    n = impl.compress(buf)
    assert len(buf) == len(text)   # in place: the buffer itself is not resized
    return "".join(buf[:n])


def test_normal_runs():
    assert run("aabbccc") == "a2b2c3"
    assert run("abc") == "abc"


def test_empty_and_single():
    assert run("") == ""
    assert run("x") == "x"


def test_multi_digit_boundaries():
    assert run("a" * 9) == "a9"
    assert run("a" * 10) == "a10"          # boundary: count needs two digits
    assert run("b" + "c" * 12) == "bc12"
    assert run("z" * 1000) == "z1000"


def test_never_longer_than_input():
    rng = random.Random(1)
    for _ in range(500):
        s = "".join(rng.choice("ab") for _ in range(rng.randint(0, 30)))
        assert len(run(s)) <= len(s)


def test_production_heartbeat_buffer():
    # An audit shipper on 10.0.7.21 buffers one status char per second:
    # "." = heartbeat ok, "W" = write event, "!" = auth failure.
    line = "." * 58 + "W" + "." * 3 + "!" * 5 + "." * 120
    assert run(line) == ".58W.3!5.120"


def test_large_random_matches_reference():
    rng = random.Random(443)
    for _ in range(300):
        s = "".join(rng.choice("aab.") * rng.randint(1, 15) for _ in range(rng.randint(0, 40)))
        assert run(s) == reference(s)
    big = "".join(rng.choice("xy") * rng.randint(1, 200) for _ in range(5_000))
    assert run(big) == reference(big)
