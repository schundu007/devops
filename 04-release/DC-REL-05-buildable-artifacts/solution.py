"""DC-REL-05 Buildable Artifacts — reference solution."""
from __future__ import annotations

from collections import defaultdict, deque


def buildable(artifacts: list[str], inputs: list[list[str]], available: list[str]) -> list[str]:
    """Every artifact that can be built from `available`, in the order it becomes buildable."""
    missing = [len(ins) for ins in inputs]             # inputs not yet in hand, per artifact
    used_by: dict[str, list[int]] = defaultdict(list)  # input name -> artifacts that need it
    for i, ins in enumerate(inputs):
        for name in ins:
            used_by[name].append(i)

    built = [a for a, m in zip(artifacts, missing) if m == 0]  # no inputs: build at once
    ready = deque(available)                           # everything we currently have
    ready.extend(built)
    while ready:
        name = ready.popleft()
        for i in used_by[name]:
            missing[i] -= 1
            if missing[i] == 0:                        # last input arrived: build it
                built.append(artifacts[i])
                ready.append(artifacts[i])             # it can now feed other artifacts
    return built
