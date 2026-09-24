"""DC-OBS-09 Log Flood Suppressor — your attempt.

Run your code against the tests:
    make try CHIP=01-observability/DC-OBS-09-log-flood-suppressor
"""
from __future__ import annotations


class LogSuppressor:
    def __init__(self, window: int = 10) -> None:
        # TODO
        pass

    def should_print(self, timestamp: int, message: str) -> bool:
        """Return True and remember the print if `message` was not printed in the
        last `window` seconds; otherwise return False.

        A message printed at time t may print again at t + window or later.
        Suppressed calls do not restart the quiet period.
        Timestamps never go backwards.
        """
        # TODO
        raise NotImplementedError
