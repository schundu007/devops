"""DC-CAP-03 Balanced Shard Split — your attempt.

Run your code against the tests:
    make try CHIP=06-capacity/DC-CAP-03-balanced-shard-split
"""
from __future__ import annotations


def min_busiest_worker_load(loads: list[int], workers: int) -> int:
    """Return the smallest possible load on the busiest worker.

    `loads` are the loads of key-range shards in key order. Each worker takes one
    contiguous run of shards (key ranges stay together). At most `workers` workers are used.
    """
    # TODO
    raise NotImplementedError
