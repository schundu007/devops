"""DC-SEC-16 Brute-Force Burst Alert — reference solution."""
from __future__ import annotations

from collections import defaultdict

BURST = 3        # this many uses...
WINDOW_MIN = 60  # ...within this many minutes (inclusive) raises an alert


def burst_alerts(names: list[str], times: list[str]) -> list[str]:
    """Names used BURST+ times within WINDOW_MIN minutes, sorted ascending."""
    minutes: dict[str, list[int]] = defaultdict(list)
    for name, hhmm in zip(names, times):
        h, m = hhmm.split(":")
        minutes[name].append(int(h) * 60 + int(m))

    alerted = []
    for name, ts in minutes.items():
        ts.sort()
        # In sorted order, a burst of 3 exists iff some 3 consecutive uses fit the window.
        if any(ts[i] - ts[i - BURST + 1] <= WINDOW_MIN for i in range(BURST - 1, len(ts))):
            alerted.append(name)
    return sorted(alerted)
