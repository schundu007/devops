"""Tests for DC-REL-08 Versioned Config Store."""
from __future__ import annotations

import random

import pytest
from chip import load_impl

impl = load_impl(__file__)


@pytest.fixture
def store():
    return impl.ConfigStore()


def test_normal_history(store):
    store.set("replicas", "3")
    assert store.snapshot() == 0
    store.set("replicas", "5")
    assert store.snapshot() == 1
    assert store.get("replicas", 0) == "3"
    assert store.get("replicas", 1) == "5"


def test_unknown_key_and_empty_snapshot(store):
    assert store.snapshot() == 0
    assert store.get("replicas", 0) is None


def test_key_set_after_snapshot_is_not_visible_in_it(store):
    s0 = store.snapshot()
    store.set("log_level", "debug")
    s1 = store.snapshot()
    assert store.get("log_level", s0) is None      # boundary: set after s0 was taken
    assert store.get("log_level", s1) == "debug"


def test_last_write_before_snapshot_wins(store):
    store.set("image", "api:1.4.0")
    store.set("image", "api:1.4.1")
    s0 = store.snapshot()
    assert store.get("image", s0) == "api:1.4.1"


def test_unchanged_key_carries_across_snapshots(store):
    store.set("region", "eu-west-1")
    for _ in range(5):
        store.snapshot()
    assert all(store.get("region", s) == "eu-west-1" for s in range(5))


def test_rollback_reads_last_good_revision(store):
    # Production flavour: a feature flag rollout goes bad; roll back to the
    # config as of the last snapshot where checkout was healthy.
    store.set("flag.new_checkout", "off")
    store.set("checkout.timeout_ms", "800")
    healthy = store.snapshot()                        # rev 0: known good
    store.set("flag.new_checkout", "on")
    store.snapshot()                                  # rev 1: incident starts
    store.set("checkout.timeout_ms", "300")
    bad = store.snapshot()                            # rev 2: worse
    rollback = {k: store.get(k, healthy) for k in ("flag.new_checkout", "checkout.timeout_ms")}
    assert rollback == {"flag.new_checkout": "off", "checkout.timeout_ms": "800"}
    assert store.get("flag.new_checkout", bad) == "on"


def test_large_random_matches_full_copies(store):
    rng = random.Random(1146)
    working: dict[str, str] = {}
    copies: list[dict[str, str]] = []                 # brute force: a full copy per snapshot
    keys = [f"key-{i}" for i in range(300)]
    for _ in range(50_000):
        if rng.random() < 0.9:
            k, v = rng.choice(keys), str(rng.randrange(1_000))
            store.set(k, v)
            working[k] = v
        else:
            assert store.snapshot() == len(copies)
            copies.append(dict(working))
    for _ in range(20_000):
        if not copies:
            break
        s, k = rng.randrange(len(copies)), rng.choice(keys)
        assert store.get(k, s) == copies[s].get(k)
