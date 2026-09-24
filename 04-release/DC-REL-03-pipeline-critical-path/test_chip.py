"""Tests for DC-REL-03 Pipeline Critical Path."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def reference(n: int, deps: list[tuple[int, int]], duration: list[int]) -> int:
    """Independent check: relax finish times until nothing changes (Bellman-Ford style)."""
    finish = list(duration)
    changed = True
    while changed:
        changed = False
        for a, b in deps:
            if finish[a] + duration[b] > finish[b]:
                finish[b] = finish[a] + duration[b]
                changed = True
    return max(finish, default=0)


def test_diamond_takes_the_longest_branch():
    # 0 -> {1, 2} -> 3 ; branch through 2 is longer
    assert impl.pipeline_time(4, [(0, 1), (0, 2), (1, 3), (2, 3)], [2, 3, 10, 1]) == 13


def test_empty_and_single_stage():
    assert impl.pipeline_time(0, [], []) == 0
    assert impl.pipeline_time(1, [], [7]) == 7


def test_no_dependencies_all_parallel():
    assert impl.pipeline_time(4, [], [5, 1, 9, 3]) == 9


def test_chain_is_the_sum():
    assert impl.pipeline_time(4, [(0, 1), (1, 2), (2, 3)], [1, 2, 3, 4]) == 10


def test_ci_pipeline_speeding_up_off_path_stage_does_not_help():
    # Production flavour: checkout(0) -> build(1) -> {unit(2), integration(3), lint(4)} -> deploy(5)
    names = ["checkout", "build", "unit", "integration", "lint", "deploy"]
    deps = [(0, 1), (1, 2), (1, 3), (1, 4), (2, 5), (3, 5), (4, 5)]
    minutes = [1, 6, 4, 14, 2, 3]
    assert len(names) == len(minutes)
    assert impl.pipeline_time(6, deps, minutes) == 1 + 6 + 14 + 3
    faster_unit = minutes[:2] + [1] + minutes[3:]            # unit tests: 4 -> 1 min
    assert impl.pipeline_time(6, deps, faster_unit) == 24    # no change: not on the critical path
    faster_integ = minutes[:3] + [8] + minutes[4:]            # integration: 14 -> 8 min
    assert impl.pipeline_time(6, deps, faster_integ) == 18


def test_large_random_dag_matches_reference():
    rng = random.Random(2050)
    for _ in range(5):
        n = 400
        labels = list(range(n))
        rng.shuffle(labels)                                  # hide the topological order
        deps = []
        for _ in range(2_000):
            i, j = sorted(rng.sample(range(n), 2))
            deps.append((labels[i], labels[j]))              # edges only go "forward": a DAG
        duration = [rng.randint(1, 100) for _ in range(n)]
        assert impl.pipeline_time(n, deps, duration) == reference(n, deps, duration)
