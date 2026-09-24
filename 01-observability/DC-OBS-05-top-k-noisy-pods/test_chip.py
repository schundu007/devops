"""Tests for DC-OBS-05 Top-K Noisy Pods Board."""
from __future__ import annotations

import random

import pytest
from chip import load_impl

impl = load_impl(__file__)


@pytest.fixture
def board():
    return impl.NoisyBoard()


def test_normal_ranking(board):
    board.add("checkout-7d9f4-x2kqp", 900)
    board.add("search-5c8b7-q1wzt", 300)
    board.add("cart-6f5d2-m8hvn", 600)
    assert board.top(2) == [("checkout-7d9f4-x2kqp", 900), ("cart-6f5d2-m8hvn", 600)]
    assert board.top_total(2) == 1500


def test_empty_board_and_k_larger_than_keys(board):
    assert board.top(3) == []
    assert board.top_total(3) == 0
    board.add("only-pod", 5)
    assert board.top(3) == [("only-pod", 5)]


def test_adds_accumulate_and_reset_forgets(board):
    board.add("api-key-7f3a", 10)
    board.add("api-key-7f3a", 15)
    board.add("api-key-91bc", 20)
    assert board.top(1) == [("api-key-7f3a", 25)]
    board.reset("api-key-7f3a")
    assert board.top(5) == [("api-key-91bc", 20)]
    board.reset("never-seen")          # unknown key: no error
    board.add("api-key-7f3a", 1)       # comes back from zero
    assert board.top(5) == [("api-key-91bc", 20), ("api-key-7f3a", 1)]


def test_ties_break_by_key(board):
    # Boundary: equal totals must give a stable, readable order.
    for key in ("pod-c", "pod-a", "pod-b"):
        board.add(key, 7)
    assert board.top(2) == [("pod-a", 7), ("pod-b", 7)]


def test_rate_limit_board_scenario(board):
    # Production flavour: 429s per API key over one window, then the window rolls
    # and the worst offender's counter is reset after it is blocked.
    events = [("key-a", 120), ("key-b", 30), ("key-c", 450), ("key-a", 400), ("key-d", 5)]
    for key, n in events:
        board.add(key, n)
    assert [k for k, _ in board.top(3)] == ["key-a", "key-c", "key-b"]
    board.reset("key-a")
    assert [k for k, _ in board.top(3)] == ["key-c", "key-b", "key-d"]


def test_large_random_matches_full_sort(board):
    rng = random.Random(1244)
    truth: dict[str, int] = {}
    for step in range(50_000):
        key = f"pod-{rng.randint(0, 2_000)}"
        if rng.random() < 0.02:
            board.reset(key)
            truth.pop(key, None)
        else:
            n = rng.randint(1, 100)
            board.add(key, n)
            truth[key] = truth.get(key, 0) + n
        if step % 5_000 == 0:
            k = rng.randint(1, 50)
            expected = sorted(truth.items(), key=lambda kv: (-kv[1], kv[0]))[:k]
            assert board.top(k) == expected
            assert board.top_total(k) == sum(v for _, v in expected)
