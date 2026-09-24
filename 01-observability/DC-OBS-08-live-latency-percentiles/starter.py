"""DC-OBS-08 Live Latency Percentiles — your attempt.  (added: the handbook has no stored starter)

Signatures match Source: Handbook #39 Find Median from Data Stream.
Run your code against the tests:
    make try CHIP=01-observability/DC-OBS-08-live-latency-percentiles
"""


class MedianFinder:
    def __init__(self):
        # TODO
        pass

    def addNum(self, num: int) -> None:
        """Add one latency sample (ms) to the stream."""
        # TODO
        raise NotImplementedError

    def findMedian(self) -> float:
        """Median (p50) of all samples so far. Called only after at least one addNum."""
        # TODO
        raise NotImplementedError
