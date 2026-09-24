"""Tests for DC-CAP-02 Backup Window Bandwidth."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def _nights(files: list[int], cap: int) -> int:
    used, count = 0, 1
    for f in files:
        if used + f > cap:
            count, used = count + 1, 0
        used += f
    return count


def _brute(files: list[int], nights: int) -> int:
    # Independent reference: try every capacity upward from the largest file.
    cap = max(files)
    while _nights(files, cap) > nights:
        cap += 1
    return cap


def test_ten_files_five_nights():
    assert impl.min_nightly_capacity([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5) == 15


def test_single_file():
    assert impl.min_nightly_capacity([700], 3) == 700


def test_one_night_means_total():
    assert impl.min_nightly_capacity([3, 2, 2, 4, 1, 4], 1) == 16


def test_one_night_per_file_means_largest():
    # Boundary: as many nights as files, so the largest file sets the capacity.
    assert impl.min_nightly_capacity([3, 2, 2, 4, 1, 4], 6) == 4


def test_order_matters():
    # Same sizes in a different order need different capacity.
    assert impl.min_nightly_capacity([1, 2, 3, 1, 1], 4) == 3
    assert impl.min_nightly_capacity([3, 2, 2, 4, 1, 4], 3) == 6


def test_db_snapshot_migration():
    # Production flavour: nightly snapshots (GB) of the orders-db, oldest first,
    # to be copied to the DR region over 4 nights.
    snapshots = [220, 180, 950, 400, 310, 600, 120, 880]
    cap = impl.min_nightly_capacity(snapshots, 4)
    assert _nights(snapshots, cap) <= 4 and _nights(snapshots, cap - 1) > 4
    assert cap == 1310


def test_random_matches_brute_force():
    rng = random.Random(1011)
    for _ in range(200):
        files = [rng.randint(1, 60) for _ in range(rng.randint(1, 30))]
        nights = rng.randint(1, len(files))
        assert impl.min_nightly_capacity(files, nights) == _brute(files, nights)


def test_large_input():
    rng = random.Random(3)
    files = [rng.randint(1, 500) for _ in range(50_000)]
    cap = impl.min_nightly_capacity(files, 300)
    assert _nights(files, cap) <= 300 < _nights(files, cap - 1)
