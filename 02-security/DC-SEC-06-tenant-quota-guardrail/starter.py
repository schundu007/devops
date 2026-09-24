"""DC-SEC-06 Tenant Quota Guardrail — your attempt.

Run your code against the tests:
    make try CHIP=02-security/DC-SEC-06-tenant-quota-guardrail
"""
from __future__ import annotations


def peak_usage(jobs: list[tuple[int, int, int]]) -> int:
    """Return the highest total vCPU in use at any moment.

    Each job is (vcpus, start, end) and holds its vCPUs on [start, end):
    from `start` up to, but not including, `end`. Return 0 for no jobs.
    """
    # TODO
    raise NotImplementedError


def fits_quota(jobs: list[tuple[int, int, int]], quota: int) -> bool:
    """Return True if total vCPU in use never goes above `quota`."""
    # TODO
    raise NotImplementedError
