"""DC-CAP-03 Balanced Shard Split — reference solution (binary search on the answer)."""
from __future__ import annotations


def min_busiest_worker_load(loads: list[int], workers: int) -> int:
    """Split ordered shard loads into at most `workers` contiguous runs; minimise the largest run."""

    def fits(limit: int) -> bool:
        # Greedy: fill each worker up to `limit`, then start the next one.
        runs, current = 1, 0
        for load in loads:
            if current + load > limit:
                runs += 1
                current = 0
                if runs > workers:
                    return False
            current += load
        return True

    lo, hi = max(loads), sum(loads)  # one shard per worker ... all shards on one worker
    while lo < hi:
        mid = (lo + hi) // 2
        if fits(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo
