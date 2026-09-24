"""Tests for DC-REL-02 Version Comparator."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)
cmp = impl.compare_versions


def test_normal_patch_numbers_compare_as_numbers():
    assert "1.27.10" < "1.27.9"          # plain string compare gets it wrong...
    assert cmp("1.27.10", "1.27.9") == 1  # ...numeric compare gets it right
    assert cmp("1.27.9", "1.27.10") == -1


def test_single_part_and_equal():
    assert cmp("7", "7") == 0
    assert cmp("2", "10") == -1


def test_missing_parts_count_as_zero():
    assert cmp("1.2", "1.2.0") == 0
    assert cmp("1.2", "1.2.0.0.1") == -1
    assert cmp("1.2.0.0.1", "1.2") == 1


def test_leading_zeros_are_ignored():
    assert cmp("1.01", "1.001") == 0
    assert cmp("1.0.010", "1.0.9") == 1


def test_scanner_flags_packages_below_fixed_version():
    # Production flavour: a vulnerability scanner reports a package when
    # installed < fixed. Package names and versions are synthetic.
    inventory = {
        "libfoo": ("3.0.2", "3.0.13"),     # 2 < 13 numerically: vulnerable
        "libbar": ("1.27.10", "1.27.9"),   # already past the fix
        "libbaz": ("2.4", "2.4.0"),        # same release written two ways
        "libqux": ("0.9.99", "1.0"),       # major bump fixes it
    }
    vulnerable = sorted(p for p, (inst, fixed) in inventory.items() if cmp(inst, fixed) < 0)
    assert vulnerable == ["libfoo", "libqux"]


def test_large_random_matches_tuple_reference():
    rng = random.Random(165)

    def rand_version() -> str:
        return ".".join(str(rng.choice([0, 0, 1, 2, 9, 10, 99, 100])).zfill(rng.choice([1, 1, 2, 3]))
                        for _ in range(rng.randint(1, 6)))

    def reference(a: str, b: str) -> int:
        ta = [int(x) for x in a.split(".")]
        tb = [int(x) for x in b.split(".")]
        width = max(len(ta), len(tb))
        ta += [0] * (width - len(ta))
        tb += [0] * (width - len(tb))
        return (ta > tb) - (ta < tb)

    for _ in range(20_000):
        a, b = rand_version(), rand_version()
        assert cmp(a, b) == reference(a, b)
    long_a = ".".join(["1"] * 250)
    assert cmp(long_a, long_a + ".0") == 0
