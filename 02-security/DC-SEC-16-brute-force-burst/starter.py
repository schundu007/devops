"""DC-SEC-16 Brute-Force Burst Alert — your attempt.

Run your code against the tests:
    make try CHIP=02-security/DC-SEC-16-brute-force-burst
"""
from __future__ import annotations

BURST = 3
WINDOW_MIN = 60


def burst_alerts(names: list[str], times: list[str]) -> list[str]:
    """Return the names used BURST or more times within WINDOW_MIN minutes, sorted.

    names[i] was used at times[i] ("HH:MM", 24-hour, same day). "10:00" and
    "11:00" are within one hour of each other; "10:00" and "11:01" are not.
    """
    # TODO
    raise NotImplementedError
