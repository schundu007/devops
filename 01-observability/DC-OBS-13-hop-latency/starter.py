"""DC-OBS-13 Hop-to-Hop Average Latency — your attempt.

Run your code against the tests:
    make try CHIP=01-observability/DC-OBS-13-hop-latency
"""
from __future__ import annotations


class HopLatency:
    def __init__(self) -> None:
        # TODO
        pass

    def enter(self, request_id: str, service: str, t: int) -> None:
        """Request `request_id` starts a hop at `service` at time t.

        A request has at most one open hop at a time.
        """
        # TODO
        raise NotImplementedError

    def exit(self, request_id: str, service: str, t: int) -> None:
        """Request `request_id` ends its open hop at `service` at time t (t > entry time)."""
        # TODO
        raise NotImplementedError

    def average(self, from_service: str, to_service: str) -> float:
        """Mean duration of completed hops that entered at `from_service` and exited at `to_service`.

        Only called after at least one such hop has completed.
        """
        # TODO
        raise NotImplementedError
