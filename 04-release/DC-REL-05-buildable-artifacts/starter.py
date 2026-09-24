"""DC-REL-05 Buildable Artifacts — your attempt.

Run your code against the tests:
    make try CHIP=04-release/DC-REL-05-buildable-artifacts
"""
from __future__ import annotations


def buildable(artifacts: list[str], inputs: list[list[str]], available: list[str]) -> list[str]:
    """Return every artifact that can be built, in any order.

    artifacts[i] needs every name in inputs[i]. An input is either something in
    `available` (base images, pinned packages) or another artifact that is itself
    buildable. Names in `available` and in `artifacts` never overlap.
    """
    # TODO
    raise NotImplementedError
