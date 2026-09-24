"""Tests for DC-REL-05 Buildable Artifacts. Order does not matter, so results are sorted."""
from __future__ import annotations

import random

from chip import load_impl

impl = load_impl(__file__)


def build(artifacts, inputs, available) -> list[str]:
    return sorted(impl.buildable(artifacts, inputs, available))


def reference(artifacts, inputs, available) -> list[str]:
    """Independent check: keep sweeping until no new artifact can be built."""
    have = set(available)
    built: set[str] = set()
    grew = True
    while grew:
        grew = False
        for a, ins in zip(artifacts, inputs):
            if a not in built and all(x in have for x in ins):
                built.add(a)
                have.add(a)
                grew = True
    return sorted(built)


def test_chain_of_artifacts():
    artifacts = ["app-image", "wheel-cache"]
    inputs = [["base-python", "wheel-cache"], ["requirements.lock", "pip"]]
    available = ["base-python", "requirements.lock", "pip"]
    assert build(artifacts, inputs, available) == ["app-image", "wheel-cache"]


def test_empty_and_single():
    assert build([], [], ["gcc"]) == []
    assert build(["hello-bin"], [["gcc"]], ["gcc"]) == ["hello-bin"]
    assert build(["hello-bin"], [["gcc"]], []) == []


def test_missing_input_blocks_everything_downstream():
    artifacts = ["lib", "svc", "img"]
    inputs = [["protoc"], ["lib"], ["svc", "distroless"]]
    assert build(artifacts, inputs, ["distroless"]) == []  # no protoc: nothing builds


def test_cycle_is_never_buildable():
    artifacts = ["a", "b", "c"]
    inputs = [["b"], ["a"], ["base"]]
    assert build(artifacts, inputs, ["base"]) == ["c"]


def test_artifact_with_no_inputs_is_always_buildable():
    assert build(["docs-site"], [[]], []) == ["docs-site"]


def test_monorepo_release_build():
    # Production flavour: which release artifacts can CI produce when the
    # internal mirror has lost "node-20"?
    artifacts = ["api-bin", "api-image", "web-bundle", "web-image", "helm-chart", "release-bundle"]
    inputs = [
        ["go-1.22", "api-src"],
        ["api-bin", "distroless-base"],
        ["node-20", "web-src"],
        ["web-bundle", "nginx-base"],
        ["chart-src"],
        ["api-image", "web-image", "helm-chart"],
    ]
    available = ["go-1.22", "api-src", "distroless-base", "web-src", "nginx-base", "chart-src"]
    assert build(artifacts, inputs, available) == ["api-bin", "api-image", "helm-chart"]


def test_large_random_matches_reference():
    rng = random.Random(2115)
    for _ in range(5):
        base = [f"base-{i}" for i in range(200)]
        artifacts = [f"art-{i}" for i in range(2_000)]
        pool = base + artifacts
        inputs = [rng.sample(pool, rng.randint(0, 4)) for _ in artifacts]
        for i, ins in enumerate(inputs):                  # no artifact needs itself
            if artifacts[i] in ins:
                ins.remove(artifacts[i])
        available = rng.sample(base, 150)
        assert build(artifacts, inputs, available) == reference(artifacts, inputs, available)
