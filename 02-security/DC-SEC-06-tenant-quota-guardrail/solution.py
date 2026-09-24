"""DC-SEC-06 Tenant Quota Guardrail — reference solution."""
from __future__ import annotations


def peak_usage(jobs: list[tuple[int, int, int]]) -> int:
    """Highest total vCPU in use at any moment. Each job is (vcpus, start, end), active on [start, end)."""
    # Difference map: +vcpus when a job starts, -vcpus when it ends.
    # A dict instead of an array, because times can be as large as 10^9.
    delta: dict[int, int] = {}
    for vcpus, start, end in jobs:
        if start >= end:
            continue  # a zero-length job never runs
        delta[start] = delta.get(start, 0) + vcpus
        delta[end] = delta.get(end, 0) - vcpus
    peak = running = 0
    for t in sorted(delta):
        # Ends and starts at the same time are already netted in delta[t],
        # so a job ending at t frees its vCPUs for a job starting at t.
        running += delta[t]
        peak = max(peak, running)
    return peak


def fits_quota(jobs: list[tuple[int, int, int]], quota: int) -> bool:
    """True if total vCPU in use never goes above `quota`."""
    return peak_usage(jobs) <= quota
