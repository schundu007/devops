Source: New

# DC-PLAT-15 · On-Call Coverage Gaps

## 1. Header
| | |
|---|---|
| Chip ID | DC-PLAT-15 |
| Difficulty | Hard |
| Pattern | Merge intervals / heap |
| Track | Platform Engineering, Scheduling & Allocation (PLAT) |
| Classic pattern | LeetCode 759 |
| Premium | Yes (P). Free alternative: LeetCode 56 Merge Intervals. Merge everyone's shifts; the holes between merged blocks are the gaps. It is also Handbook #61. |
| Time box | 40 min |
| Source | New |

## 2. The Scenario
The payments team runs a follow-the-sun rota: APAC covers 00:00–08:00 UTC, EMEA 08:00–16:00
and US 16:00–24:00, Monday to Friday. Someone rebuilt the weekend layer last month, and on
Saturday at 03:40 a `checkout-api` page went unacknowledged for 47 minutes. Nobody was on
call. Before the next rota change ships, you want a check that reads every engineer's shifts
and lists every hour with nobody on call.

## 3. Why This Is DevOps
**Production reality:** An on-call schedule is a set of shifts per engineer, often layered
(primary, secondary, holiday overrides). The question that matters is "is someone on call at
every moment?". Merge all shifts across all engineers in time order and walk them with a
running "covered until" time. Any shift that starts after that time leaves a hole. Each
engineer's shifts are already sorted, so a k-way merge with a heap avoids re-sorting everything.

**Where you see it:** On-call tools such as PagerDuty and Opsgenie build a final schedule from
layers and overrides, and checking that result for holes is a similar idea. The same check
applies to maintenance-window calendars, backup windows ("is some backup always running?"),
and follow-the-sun support rotas.

**Reality check:** Real schedules have time zones, daylight-saving shifts, overrides and
escalation levels. A gap in the primary layer may be covered by a secondary. This chip uses
plain integer hours on one clock and treats every shift as equal cover.

**What breaks if you get it wrong:** A missed gap means a page goes to nobody. Treating a
handover at exactly 08:00 as a gap (an off-by-one) floods the team with false warnings, until
people stop reading them.

## 4. Problem Statement
You are given every engineer's on-call shifts. `schedules[p]` is engineer `p`'s list of shifts
`[start, end]` (end exclusive), sorted by `start` and not overlapping each other. Shifts of
different engineers may overlap freely.

Return every `[gap_start, gap_end]` where **nobody** is on call, in time order. Only count
time between the earliest shift start and the latest shift end. Before and after is out of
scope. A gap must have positive length: shifts that touch, like `[0, 8]` and `[8, 16]`, leave
no gap. With no shifts at all, return `[]`.

## 5. Input / Output format and Constraints
- `schedules`: `list[list[list[int]]]`, with up to 50 engineers and up to `10^4` shifts in total.
- `0 <= start < end <= 10^8` (hours, minutes or epoch seconds, as long as it is one clock).
- Each engineer's shifts are sorted by `start` and do not overlap each other. Lists may be empty.
- Returns `list[list[int]]` of `[gap_start, gap_end]` pairs, sorted by time.

## 6. Examples
**Example 1: a hole between engineers**
```
schedules = [[[0,8],[20,24]], [[6,12]]]   -> [[12,20]]
```
Coverage runs 0–12 (the shifts overlap at 6–8), then nobody is on call from 12 to 20.

**Example 2: a handover is not a gap (edge case)**
```
schedules = [[[0,8]], [[8,16]], [[16,24]]]  -> []
```

**Example 3: a long shift hides others**
```
schedules = [[[0,100]], [[10,20],[30,40]], [[101,110]]]  -> [[100,101]]
```
The running "covered until" stays at 100 while the short shifts pass. The last end seen would be wrong.

## 7. Starter Code
See [`starter.py`](starter.py): `coverage_gaps(schedules)` with the rules in the docstring.
The body is TODO.

```bash
make try CHIP=03-platform/DC-PLAT-15-on-call-coverage-gaps
```

## 8. Hints
1. **Nudge:** Forget who is on call. You only care whether *anyone* is. What if all shifts were in one list, sorted by start?
2. **Pattern:** Merge intervals. Walk the shifts by start time, keeping `covered_until`, the
   furthest end seen so far. Each engineer's list is already sorted, so a heap-based k-way merge
   gives the global order.
3. **Near-solution:** For each shift `[s, e]` from `heapq.merge(*schedules)`: if
   `s > covered_until`, record `[covered_until, s]`. Then set `covered_until = max(covered_until, e)`.

## 9. Solution
**Approach**
1. Merge all engineers' sorted shift lists into one stream sorted by start, using a k-way
   merge (`heapq.merge`).
2. Keep `covered_until`, the latest end among the shifts seen so far.
3. A shift starting strictly after `covered_until` means a gap `[covered_until, start]`.
4. Extend `covered_until` with `max`, so a long shift keeps covering later short ones.

**Brute force:** Mark every hour (or minute) on a timeline and read off the unmarked runs.
It costs time proportional to the time span, not the number of shifts. A year of minutes is
525,600 cells per check, and epoch-second schedules make it impossible.

**Optimal code:** [`solution.py`](solution.py)

```python
import heapq


def coverage_gaps(schedules: list[list[list[int]]]) -> list[list[int]]:
    gaps: list[list[int]] = []
    covered_until: int | None = None
    for start, end in heapq.merge(*schedules):          # all shifts, by start
        if covered_until is not None and start > covered_until:
            gaps.append([covered_until, start])         # nobody on call in between
        covered_until = end if covered_until is None else max(covered_until, end)
    return gaps
```

**Complexity**
- Time: O(N log k) for N shifts and k engineers, because each shift passes through a heap of
  size k once. Sorting everything would be O(N log N).
- Space: O(k) for the merge heap, plus the output.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: a normal gap, empty inputs, a single engineer,
touching shifts versus a one-hour hole (the boundary), a long shift hiding later ones, a
production-style follow-the-sun week with a forgotten weekend (`[[120, 156]]`), and a random
check (40 rounds, up to 30 engineers) against a mark-every-hour brute force.

## 11. Interview Talk Track
"I want every moment when nobody is on call. Who is on call doesn't matter, only whether
anyone is, so this is merge intervals across all engineers. Each engineer's shifts are
already sorted, so I k-way merge them with a heap, which is O(N log k) instead of re-sorting
everything. I walk the shifts by start time with one number, 'covered until', the furthest
end seen so far. If a shift starts after that, the gap between them is a hole in the rota.
Then I extend covered-until with max, not with the last end, because a 24-hour shift can
cover several short ones. Touching shifts, like a handover at 08:00, aren't a gap because I
compare with strictly greater. In real tools I'd run this on the final layered schedule,
after overrides, and in UTC so daylight-saving changes don't hide a gap."

## 12. Level Up
1. **"We need two people on call at all times (primary and secondary)."** Turn the shifts into
   events: `+1` at each start and `-1` at each end. Sort them with ends before starts at the
   same time, and sweep, reporting every stretch where the count is below 2. The sweep
   generalises "anyone" to "at least k".
2. **"Check the next 90 days as the schedule is edited, on every save."** Keep the merged
   coverage in a balanced interval tree or a sorted list of blocks. An edit only changes the
   blocks around the edited shift, so update those and re-check locally instead of rebuilding.
3. **"Engineers are in different time zones and shifts are written in local time."** Convert
   everything to UTC instants before merging. Around daylight-saving changes, an 08:00–16:00
   local shift is 7 or 9 real hours, and gaps or double cover appear exactly on those nights.

## 13. Related Chips
- **DC-SEC-05 Firewall Range Merger**: the same merge, keeping the covered blocks instead of the holes.
- **DC-OBS-14 Multi-Node Log Timeline Merge**: the k-way heap merge of sorted streams.
- **DC-PLAT-03 Minimum CI Runners**: overlapping intervals again, counting peak overlap.
