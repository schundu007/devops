"""DC-SEC-15 Impossible Travel Detector — reference solution."""
from __future__ import annotations

from collections import Counter, defaultdict

RISK_LIMIT = 1000
WINDOW_MIN = 60


def flag_events(events: list[str]) -> list[str]:
    """Return the suspicious events, in input order.

    Each event is "user,minute,risk,city".
    """
    parsed = []
    by_user: dict[str, list[int]] = defaultdict(list)
    for i, e in enumerate(events):
        user, minute, risk, city = e.split(",")
        parsed.append((user, int(minute), int(risk), city))
        by_user[user].append(i)

    flagged = [False] * len(events)
    for idxs in by_user.values():
        idxs.sort(key=lambda i: parsed[i][1])
        # Sweep a window [t - 60, t + 60] around each event, counting cities inside.
        cities: Counter[str] = Counter()
        lo = hi = 0
        for i in idxs:
            t = parsed[i][1]
            while hi < len(idxs) and parsed[idxs[hi]][1] <= t + WINDOW_MIN:
                cities[parsed[idxs[hi]][3]] += 1
                hi += 1
            while parsed[idxs[lo]][1] < t - WINDOW_MIN:
                c = parsed[idxs[lo]][3]
                cities[c] -= 1
                if cities[c] == 0:
                    del cities[c]
                lo += 1
            # The event itself is in the window, so 2+ cities means another city is nearby.
            if len(cities) > 1:
                flagged[i] = True

    return [
        e for i, e in enumerate(events)
        if flagged[i] or parsed[i][2] > RISK_LIMIT
    ]
