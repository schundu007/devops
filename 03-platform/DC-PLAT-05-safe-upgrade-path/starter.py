"""DC-PLAT-05 Shortest Safe Upgrade Path — your attempt.

Run your code against the tests:
    make try CHIP=03-platform/DC-PLAT-05-safe-upgrade-path
"""
from __future__ import annotations

from typing import Sequence


def min_upgrade_steps(start: Sequence[str], target: Sequence[str], approved: list[Sequence[str]]) -> int:
    """Fewest steps from `start` to `target`.

    A state is a tuple of component versions, for example
    ("1.28", "1.27", "3.5") for (control plane, kubelet, etcd).
    One step changes exactly one component. Every state after `start`
    must appear in `approved`. Return -1 if `target` cannot be reached,
    and 0 if `start == target`.
    """
    # TODO
    raise NotImplementedError
