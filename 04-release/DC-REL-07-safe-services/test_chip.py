"""Tests for DC-REL-07 Safe Services Finder."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def reference(waits_on: list[list[int]]) -> list[int]:
    """Independent check: a service is unsafe iff it can reach a node that lies on a cycle."""
    n = len(waits_on)

    def reachable(src: int) -> set[int]:
        seen, stack = set(), list(waits_on[src])
        while stack:
            v = stack.pop()
            if v not in seen:
                seen.add(v)
                stack.extend(waits_on[v])
        return seen

    reach = [reachable(s) for s in range(n)]
    on_cycle = {s for s in range(n) if s in reach[s]}
    return [s for s in range(n) if s not in on_cycle and not (reach[s] & on_cycle)]


def test_normal_mixed_graph():
    # 0 -> 1 -> 2 -> 0 is a cycle; 3 -> 4 ends cleanly; 5 -> 1 leads into the cycle
    waits_on = [[1], [2], [0], [4], [], [1]]
    assert impl.safe_services(waits_on) == [3, 4]


def test_empty_and_single():
    assert impl.safe_services([]) == []
    assert impl.safe_services([[]]) == [0]
    assert impl.safe_services([[0]]) == []          # waits on itself


def test_all_safe_when_acyclic():
    assert impl.safe_services([[1, 2], [2], []]) == [0, 1, 2]


def test_one_bad_branch_makes_a_service_unsafe():
    # 0 waits on 1 (safe) and on 2, which is in a cycle with 3
    assert impl.safe_services([[1, 2], [], [3], [2]]) == [1]


def test_compose_startup_graph():
    # Production flavour: service startup waits (like depends_on / init containers).
    names = ["postgres", "redis", "auth", "orders", "billing", "ledger", "gateway", "metrics"]
    i = {n: k for k, n in enumerate(names)}
    waits = {
        "postgres": [], "redis": [], "metrics": [],
        "auth": ["postgres", "redis"],
        "orders": ["auth", "postgres"],
        "billing": ["ledger"], "ledger": ["billing"],        # mutual wait: deadlock
        "gateway": ["orders", "billing"],                   # blocked behind billing
    }
    waits_on = [[i[d] for d in waits[n]] for n in names]
    safe = [names[s] for s in impl.safe_services(waits_on)]
    assert safe == ["postgres", "redis", "auth", "orders", "metrics"]


def test_large_random_matches_reference():
    rng = random.Random(802)
    for _ in range(5):
        n = 300
        waits_on = [[rng.randrange(n) for _ in range(rng.choice([0, 0, 1, 1, 2, 3]))] for _ in range(n)]
        waits_on = [sorted(set(d)) for d in waits_on]
        assert impl.safe_services(waits_on) == reference(waits_on)
