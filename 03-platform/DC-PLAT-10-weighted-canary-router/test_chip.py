"""Tests for DC-PLAT-10 Weighted Canary Router.

Randomness is injected, so every test is deterministic: scripted tickets check
the exact mapping, and a seeded Random checks the traffic split.
"""
from __future__ import annotations

import random

import pytest
from chip import load_impl

impl = load_impl(__file__)


class ScriptedRng:
    """Stands in for random.Random: returns preset tickets, checks the range asked for."""

    def __init__(self, tickets: list[int]) -> None:
        self._tickets = iter(tickets)
        self.totals: list[int] = []

    def randrange(self, stop: int) -> int:
        self.totals.append(stop)
        t = next(self._tickets)
        assert 0 <= t < stop
        return t


def brute_pick(weights: list[int], ticket: int) -> int:
    """Independent reference: walk the backends until the ticket falls inside one."""
    for i, w in enumerate(weights):
        if ticket < w:
            return i
        ticket -= w
    raise AssertionError("ticket out of range")


def test_ticket_boundaries_90_10():
    rng = ScriptedRng([0, 8, 89, 90, 99])
    r = impl.WeightedRouter([90, 10], rng)
    assert [r.pick() for _ in range(5)] == [0, 0, 0, 1, 1]
    assert rng.totals == [100] * 5  # one draw per pick, over the total weight


def test_single_backend_always_wins():
    r = impl.WeightedRouter([7], ScriptedRng([0, 3, 6]))
    assert [r.pick() for _ in range(3)] == [0, 0, 0]


def test_drained_backend_never_picked():
    # Boundary: weight 0 = drained (Argo Rollouts setWeight: 0, say).
    r = impl.WeightedRouter([5, 0, 5], ScriptedRng(list(range(10))))
    assert [r.pick() for _ in range(10)] == [0] * 5 + [2] * 5


@pytest.mark.parametrize("weights", [[], [0, 0], [3, -1]])
def test_invalid_weights_rejected(weights):
    with pytest.raises(ValueError):
        impl.WeightedRouter(weights, random.Random(1))


def test_canary_rollout_steps_split_traffic():
    # Production flavour: Argo-Rollouts-style steps 5% -> 25% -> 50% canary.
    # Seeded, so this is deterministic; the tolerance is far wider than the noise
    # (std. dev. of the share over 200,000 picks is at most ~0.11 percentage points).
    for canary in (5, 25, 50):
        r = impl.WeightedRouter([100 - canary, canary], random.Random(528 + canary))
        n = 200_000
        hits = sum(r.pick() for _ in range(n))  # backend 1 is the canary
        assert abs(hits / n * 100 - canary) < 1.0


def test_large_input_matches_brute_force():
    rng = random.Random(7)
    weights = [rng.randint(0, 50) for _ in range(5_000)] + [1]
    total = sum(weights)
    tickets = [rng.randrange(total) for _ in range(3_000)] + [0, total - 1]
    r = impl.WeightedRouter(weights, ScriptedRng(tickets))
    assert [r.pick() for _ in tickets] == [brute_pick(weights, t) for t in tickets]
