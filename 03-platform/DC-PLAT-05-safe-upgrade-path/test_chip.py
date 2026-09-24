"""Tests for DC-PLAT-05 Shortest Safe Upgrade Path."""
from __future__ import annotations

import random
from collections import deque

from chip import load_impl

impl = load_impl(__file__)
steps = impl.min_upgrade_steps

# (control plane, kubelet, etcd). Approved states follow a made-up support matrix.
K8S_APPROVED = [
    ("1.28", "1.27", "3.5"),
    ("1.28", "1.28", "3.5"),
    ("1.29", "1.28", "3.5"),
    ("1.29", "1.29", "3.5"),
    ("1.30", "1.29", "3.5"),
    ("1.30", "1.30", "3.5"),
    ("1.30", "1.30", "3.6"),
]


def bfs_brute_force(start, target, approved) -> int:
    """Independent check: compare every pair of states directly."""
    start, target = tuple(start), tuple(target)
    if start == target:
        return 0
    allowed = {tuple(s) for s in approved}
    if target not in allowed:
        return -1
    seen, q = {start}, deque([(start, 0)])
    while q:
        s, d = q.popleft()
        for t in allowed:
            if t not in seen and sum(a != b for a, b in zip(s, t)) == 1:
                if t == target:
                    return d + 1
                seen.add(t)
                q.append((t, d + 1))
    return -1


def test_kubernetes_minor_by_minor():
    # Control plane first, then kubelets, one minor at a time: 4 steps to reach 1.29.
    assert steps(("1.27", "1.27", "3.5"), ("1.29", "1.29", "3.5"), K8S_APPROVED) == 4


def test_no_skipping_minors():
    # ("1.29", "1.27", "3.5") is not approved, so the direct jump is illegal; the long way is taken.
    assert steps(("1.27", "1.27", "3.5"), ("1.30", "1.30", "3.6"), K8S_APPROVED) == 7


def test_already_there():
    assert steps(("1.29", "1.29", "3.5"), ("1.29", "1.29", "3.5"), []) == 0


def test_target_not_approved():
    assert steps(("1.27", "1.27", "3.5"), ("1.31", "1.31", "3.6"), K8S_APPROVED) == -1


def test_unreachable_and_empty():
    assert steps(("1.27",), ("1.29",), []) == -1
    # Approved states exist but no single change connects them to the start.
    assert steps(("a", "a"), ("b", "b"), [("b", "b")]) == -1


def test_start_need_not_be_approved():
    # The cluster may start in an unsupported state; only the states it moves into must be approved.
    assert steps(("x", "1"), ("y", "1"), [("y", "1")]) == 1


def test_large_random_matches_brute_force():
    rng = random.Random(433)
    alphabet = "abcd"
    for _ in range(20):
        length = rng.randint(1, 5)
        pool = {tuple(rng.choice(alphabet) for _ in range(length)) for _ in range(300)}
        approved = list(pool)
        start = tuple(rng.choice(alphabet) for _ in range(length))
        target = rng.choice(approved)
        assert steps(start, target, approved) == bfs_brute_force(start, target, approved)


def test_large_input_runs():
    # 10,000 approved states in a long chain: the answer is the chain length.
    chain = [(str(i), str(i + 1)) for i in range(5_000)] + [(str(i + 1), str(i + 1)) for i in range(5_000)]
    # Chain: (i, i) -> (i, i+1) -> (i+1, i+1) ...
    assert steps(("0", "0"), ("5000", "5000"), chain) == 10_000
