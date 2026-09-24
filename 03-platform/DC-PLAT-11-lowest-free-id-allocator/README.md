Source: New

# DC-PLAT-11 · Lowest Free ID Allocator

## 1. Header
| | |
|---|---|
| Chip ID | DC-PLAT-11 |
| Difficulty | Medium |
| Pattern | Min-heap |
| Track | Platform Engineering, Scheduling & Allocation (PLAT) |
| Classic pattern | LeetCode 1845 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
A node agent on `ip-10-0-7-42` hands out host ports `30000`–`30009` to Envoy sidecars as
pods start. Pods come and go all day: `envoy-3` and `envoy-7` are terminated, and two new
pods ask for ports a minute later. The rule is "always hand out the lowest free port", so
the port map stays compact and easy to read in `ss -ltn`. The agent must also refuse a
second release of the same port, because a double release would later give one port to two pods.

## 3. Why This Is DevOps
**Production reality:** Many system resources are small numbered slots that are handed out,
returned and reused: file descriptors, loop devices, interface names such as `tun0`, `tun1`,
worker IDs, and port or address pools. When the rule is "give out the smallest free number",
the allocator needs the minimum of a changing set, and a min-heap of returned numbers plus a
"never used yet" counter does that in O(log n) per call. A double release is a classic
source of bugs where two owners share one ID.

**Where you see it:** Linux file descriptors (`open()` returns the lowest unused fd),
`losetup -f` (the first unused loop device), Linux interface names like `tun%d` (the lowest
free number), and worker or shard ID pools in job systems.

**Reality check:** Lowest-free is not always the goal. Kubernetes allocates Service ClusterIPs
and NodePorts from their ranges at random, not lowest-first. Reusing a just-freed ID at once
can let a stale client reach the new owner, so some allocators randomise or hold freed IDs
back for a while.

**What breaks if you get it wrong:** Accept a double release, and the same port goes into the
free pool twice. Two sidecars later bind "their" port, and one crashes with
`address already in use` in the middle of a rollout.

## 4. Problem Statement
Build an `IdAllocator` for the IDs `base, base + 1, …, base + size - 1`.

- `allocate()` returns the **smallest** ID not currently in use, or `None` if every ID is in use.
- `release(id)` returns an ID to the pool. If `id` is not currently allocated (a double
  release, or an ID outside the pool), raise `ValueError` and change nothing.

Aim for better than O(size) per call, and avoid building the whole free list up front when
`size` is large.

## 5. Input / Output format and Constraints
- `size`: `0 <= size <= 10^6`. `base`: any integer, default `0`.
- `allocate() -> int | None`. `release(id: int) -> None`, or it raises `ValueError`.
- Up to `10^5` calls in total.

## 6. Examples
**Example 1: reuse the lowest**
```
a = IdAllocator(5)
allocate(), allocate(), allocate()   -> 0, 1, 2
release(1); release(0)
allocate()                           -> 0     # lowest released ID first
allocate()                           -> 1
allocate()                           -> 3     # then IDs never used before
```

**Example 2: exhausted pool (edge case)**
```
a = IdAllocator(1)
allocate() -> 0
allocate() -> None
```

**Example 3: double release**
```
a = IdAllocator(3); x = allocate(); release(x)
release(x) -> ValueError
```

## 7. Starter Code
See [`starter.py`](starter.py): `IdAllocator(size, base=0)` with `allocate()` and `release(id_)`,
docstrings and type hints. Bodies are TODO.

```bash
make try CHIP=03-platform/DC-PLAT-11-lowest-free-id-allocator
```

## 8. Hints
1. **Nudge:** Split the free IDs into two groups: ones that were handed out and came back,
   and ones never handed out at all. What do you know about the second group?
2. **Pattern:** The never-used IDs are a contiguous tail, so a single counter describes them.
   The returned ones need "give me the smallest": a min-heap.
3. **Near-solution:** Every returned ID is below the counter, so check the heap first:
   `heappop` if it is non-empty, otherwise use the counter and increment it, otherwise return
   `None`. Keep an in-use set so `release` can reject bad IDs.

## 9. Solution
**Approach**
1. Work in offsets `0..size-1` and add `base` on the way out.
2. `_next` is the first offset never handed out. Everything at or above it is free.
3. `_released` is a min-heap of offsets that came back. All of them are below `_next`, so the
   heap top, when there is one, is always the smallest free offset.
4. `allocate`: pop the heap, or else take `_next`, or else return `None`. Record the offset as in use.
5. `release`: reject offsets that are not in use, otherwise move them from the in-use set to the heap.

**Brute force:** Keep a boolean array and scan from 0 for the first free slot, or keep a set
and take `min()`. Both are O(size) per allocation, and a pool of a million IDs makes each
call slow.

**Optimal code:** [`solution.py`](solution.py)

```python
import heapq


class IdAllocator:
    def __init__(self, size: int, base: int = 0) -> None:
        self._base, self._size = base, size
        self._next = 0                  # offsets >= _next were never handed out
        self._released: list[int] = []  # min-heap of returned offsets (all < _next)
        self._in_use: set[int] = set()

    def allocate(self) -> int | None:
        if self._released:
            offset = heapq.heappop(self._released)   # smallest returned offset
        elif self._next < self._size:
            offset = self._next
            self._next += 1
        else:
            return None
        self._in_use.add(offset)
        return self._base + offset

    def release(self, id_: int) -> None:
        offset = id_ - self._base
        if offset not in self._in_use:
            raise ValueError(f"id {id_} is not allocated")
        self._in_use.remove(offset)
        heapq.heappush(self._released, offset)
```

**Complexity**
- Time: O(log r) per call, where r is the number of returned IDs in the heap, for one heap
  push or pop. The set operations are O(1).
- Space: O(k), where k is the number of IDs ever handed out, never the full `size`. The pool is
  not built up front.

## 10. Tests
[`test_chip.py`](test_chip.py) has 6 cases: in-order allocation with lowest-first reuse, an
empty pool and a single-ID pool, double release and foreign IDs, an exhausted pool that frees
one ID (the boundary), a production-style sidecar port pool with `base=30000`, and a
10,000-operation random check against a set-and-`min()` brute force.

## 11. Interview Talk Track
"This is the allocator behind things like file descriptors and port pools: always hand out
the lowest free number. I split the free IDs into two groups. IDs never handed out form a
contiguous tail, so one counter covers them without allocating a million-entry list. IDs
that came back go into a min-heap. Every returned ID is below the counter, so the heap top is
always the global minimum when the heap isn't empty. Allocate pops the heap or bumps the
counter, and release pushes. Both are O(log n). I also keep an in-use set so a double release
raises instead of corrupting the pool, which is exactly the bug that puts two pods on one port.
In a real system I'd think about whether immediate reuse is safe. Kubernetes picks
ClusterIPs at random for that kind of reason."

## 12. Level Up
1. **"The pool is 16 million IDs and memory is tight."** Replace the heap and set with a
   bitmap of 2 MB, plus a small summary tree (one bit per 64-bit word that says "this word has
   a free bit"). Finding the first free ID is then a few word scans. The Linux kernel uses
   bitmaps with find-first-zero for similar ID spaces.
2. **"Don't reuse a freed ID for 60 seconds."** Put released IDs in a FIFO quarantine with
   their release time. Before each allocation, move every ID older than 60 s from the
   quarantine into the heap. This stops a stale client from reaching the new owner.
3. **"Several agents share one pool."** Store the pool in etcd or a database. Allocation is a
   compare-and-swap on a bitmap key or a unique-constraint insert, and each agent leases a
   small block of IDs so it doesn't hit the store on every call.

## 13. Related Chips
- **DC-PLAT-09 Runner Pool Allocation**: the same "lowest free number" heap, for runners.
- **DC-SEC-09 IP Range to CIDR Blocks**: address pools seen as bit patterns.
- **DC-PLAT-06 Image Cache with LRU Eviction**: which slot to give up, instead of which to hand out.
