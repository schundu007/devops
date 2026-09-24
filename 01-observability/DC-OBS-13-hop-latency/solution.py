"""DC-OBS-13 Hop-to-Hop Average Latency — reference solution."""
from __future__ import annotations


class HopLatency:
    def __init__(self) -> None:
        # request id -> (service where it entered, entry time); removed on exit
        self._open: dict[str, tuple[str, int]] = {}
        # (from service, to service) -> [total duration, completed requests]
        self._stats: dict[tuple[str, str], list[int]] = {}

    def enter(self, request_id: str, service: str, t: int) -> None:
        """The request starts its hop at `service` at time t."""
        self._open[request_id] = (service, t)

    def exit(self, request_id: str, service: str, t: int) -> None:
        """The request finishes its hop at `service` at time t."""
        start_service, start_t = self._open.pop(request_id)
        stat = self._stats.setdefault((start_service, service), [0, 0])
        stat[0] += t - start_t
        stat[1] += 1

    def average(self, from_service: str, to_service: str) -> float:
        """Mean duration of all completed hops from `from_service` to `to_service`."""
        total, count = self._stats[(from_service, to_service)]
        return total / count
