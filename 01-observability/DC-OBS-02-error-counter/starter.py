"""DC-OBS-02 5-Minute Error Counter — your attempt.  (added: the handbook has no stored starter)

Signatures match Source: Handbook #102 Design Hit Counter.
Run your code against the tests:
    make try CHIP=01-observability/DC-OBS-02-error-counter
"""


class HitCounter:
    def __init__(self):
        # TODO
        pass

    def hit(self, timestamp: int) -> None:
        """Record one hit (one 5xx response) at this second."""
        # TODO
        raise NotImplementedError

    def getHits(self, timestamp: int) -> int:
        """Number of hits in the window (timestamp - 300, timestamp]."""
        # TODO
        raise NotImplementedError
