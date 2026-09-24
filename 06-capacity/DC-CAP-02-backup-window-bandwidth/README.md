Source: New

# DC-CAP-02 · Backup Window Bandwidth

## 1. Header
| | |
|---|---|
| Chip ID | DC-CAP-02 |
| Difficulty | Medium |
| Pattern | Binary search on the answer |
| Track | Capacity & Cost (CAP) |
| Classic pattern | LeetCode 1011 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
`orders-db` is moving to a disaster-recovery region. There are 8 nightly snapshots to copy
(220, 180, 950, 400, 310, 600, 120 and 880 GB), and they must arrive oldest-first, because the
restore job replays them in order. Copies run only in the 01:00–05:00 maintenance window, and a
snapshot is never split across two nights. The migration must finish in 4 nights. How much
nightly transfer capacity do you need to reserve on the Direct Connect link?

## 3. Why This Is DevOps
**Production reality:** Backups, migrations and replication jobs often run in fixed windows, and
the data has to move in order: snapshots, WAL segments, log files. "What is the smallest nightly
capacity that finishes by the deadline?" has the same shape as DC-CAP-01. If a capacity works,
any bigger capacity works too, so you binary search it. The difference here is order: you
cannot rearrange files to pack nights better, so the check is a single greedy pass in order.

**Where you see it:** planning backup windows and bandwidth commitments, database and storage
migrations to a new region or cloud (AWS DataSync, `rclone` jobs with bandwidth limits, a
similar idea), log shipping with ordered segments.

**Reality check:** Real transfers don't stop exactly at a byte limit. Throughput varies, and you
reserve headroom (often 20–30%). Tools also resume partial files, while this chip never splits a
file. The chip gives the minimum, and capacity planning adds headroom on top.

**What breaks if you get it wrong:** Size from the average (total ÷ nights = 915 GB) and night
two alone needs 950 GB, so the migration runs over. The restore can't start, and the cut-over
date slips, often past the change freeze.

## 4. Problem Statement
You have the file sizes `files[0..n-1]` in the order they must be copied, and a deadline of
`nights`. Each night you choose a capacity `C` (the same every night) and copy files **in order**
until the next file would push that night's total above `C`. That file then starts the next night.

Return the smallest `C` that copies every file within `nights` nights.

## 5. Input / Output format and Constraints
- Returns an integer (GB per night).
- `1 <= nights <= len(files) <= 5 * 10^4`.
- `1 <= files[i] <= 500`.

## 6. Examples
**Example 1: ten files, five nights**
```
files = [1,2,3,4,5,6,7,8,9,10], nights = 5  ->  15
```
The nights are [1..5]=15, [6,7]=13, [8]=8, [9]=9, [10]=10. With 14, you would need 6 nights.

**Example 2: order matters**
```
files = [3,2,2,4,1,4], nights = 3  ->  6
```
[3,2] [2,4] [1,4]. You can't move the 1 earlier to pack better.

**Example 3: a single file (edge case)**
```
files = [700], nights = 3  ->  700
```
Capacity can never be smaller than the largest file.

## 7. Starter Code
See [`starter.py`](starter.py): the `min_nightly_capacity(files, nights)` signature, docstring and
type hints. The body is TODO.

```bash
make try CHIP=06-capacity/DC-CAP-02-backup-window-bandwidth
```

## 8. Hints
1. **Nudge:** If capacity C finishes in time, does C + 1 also finish in time?
2. **Pattern:** Binary search on the answer. The lowest possible C is `max(files)` and the highest
   is `sum(files)`.
3. **Near-solution:** `nights_needed(C)`: walk the files, add each one to tonight, and start a new
   night when it would overflow. Binary search for the smallest C with `nights_needed(C) <= nights`.

## 9. Solution
**Approach**
1. The answer is between `max(files)` (no file can be split) and `sum(files)` (everything in one night).
2. For a candidate C, count nights greedily in order. Filling each night as much as possible is
   optimal when order is fixed.
3. Binary search for the smallest C that meets the deadline.

**Brute force:** Try C = max, max + 1, … until one works. That is O(n · (sum − max)), up to
about 25 million range steps × 50,000 files.

**Optimal code:** [`solution.py`](solution.py)

```python
def min_nightly_capacity(files, nights):
    def nights_needed(cap):
        used, count = 0, 1
        for size in files:
            if used + size > cap:     # tonight is full: start the next night
                count += 1
                used = 0
            used += size
        return count

    lo, hi = max(files), sum(files)
    while lo < hi:
        mid = (lo + hi) // 2
        if nights_needed(mid) <= nights:
            hi = mid
        else:
            lo = mid + 1
    return lo
```

**Complexity**
- Time: O(n · log(sum − max)). Each binary-search step runs one O(n) greedy pass.
- Space: O(1) extra.

## 10. Tests
[`test_chip.py`](test_chip.py) has 8 cases: ten files over five nights, a single file, one night
(the total), one night per file (the largest file), order mattering, the `orders-db` snapshot
migration (1,310 GB/night), 200 random inputs checked against a linear scan, and 50,000 files
checked as "meets the deadline, and C − 1 does not".

## 11. Interview Talk Track
"We need the smallest nightly capacity that copies every snapshot, in order, before the deadline.
Capacity is monotonic: if C works, anything bigger works. So I binary search C between the largest
file, since a file can't be split, and the total. The check is a greedy pass: fill tonight until
the next file would overflow, then start a new night. Because order is fixed, greedy filling is
optimal: finishing a night early never helps. That's O(n log sum). The classic mistake is total
divided by nights, which ignores both the order and the biggest file. In real planning, I'd add
20–30% headroom on top, because transfer rates vary."

## 12. Level Up
1. **"Each night has a different window length (a weekend night is longer)."** Give each night
   its own capacity, scaled from a base rate: `cap_i = rate × hours_i`. Binary search the rate. The
   greedy check fills night i up to `cap_i`, and monotonicity still holds.
2. **"Files may be split and resumed (as with rclone or DataSync)."** Order still matters, but
   now you can fill every night exactly. The answer becomes `ceil(sum / nights)`, with no search.
   So splittability changes the problem completely.
3. **"You can copy on 2 links in parallel, and each file goes to either link."** The order
   constraint usually applies per stream, so split the files into 2 ordered streams and solve each.
   If the files are unordered, it becomes a bin-packing / scheduling problem, which is NP-hard,
   and you need heuristics such as longest-first.

## 13. Related Chips
- **DC-CAP-01 Backlog Drain Rate**: binary search on a rate, where partitions are independent.
- **DC-CAP-03 Balanced Shard Split**: the same greedy check, but minimising the busiest worker.
- **DC-PLAT-03 Minimum CI Runners**: sizing capacity from job overlap instead of volume.
