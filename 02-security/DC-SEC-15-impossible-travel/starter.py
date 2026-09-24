"""DC-SEC-15 Impossible Travel Detector — your attempt.

Run your code against the tests:
    make try CHIP=02-security/DC-SEC-15-impossible-travel
"""
from __future__ import annotations

RISK_LIMIT = 1000
WINDOW_MIN = 60


def flag_events(events: list[str]) -> list[str]:
    """Return every suspicious event, in input order (duplicates kept).

    Each event is "user,minute,risk,city". An event is suspicious if:
      - its risk score is above RISK_LIMIT, or
      - the same user has another event in a different city within
        WINDOW_MIN minutes of it (inclusive, either direction).
    """
    # TODO
    raise NotImplementedError
