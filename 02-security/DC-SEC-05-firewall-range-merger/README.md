Source: Handbook #61 Merge Intervals — `apps/camora/src/data/capra/top100/61.json` (copied unchanged as `handbook.json`)

# DC-SEC-05 · Firewall Range Merger

## 1. Header `DevOps layer`
| | |
|---|---|
| Chip ID | DC-SEC-05 |
| Difficulty | Medium |
| Pattern | Sort + merge |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 56 |
| Premium | No |
| Time box | 25 min |
| Source | Handbook #61 Merge Intervals |

## 2. The Scenario `DevOps layer`
A quarterly access review of security group `sg-web-prod` finds 40 inbound rules added by
six teams over two years: ports 80–443, 400–8080, 9000–9100, 9050–9200, and CIDRs
10.0.0.0/25, 10.0.0.128/25, 10.0.1.0/24 and 192.0.2.0/28. Nobody can say from the list what
is actually exposed. You want the true exposed ranges: sort the rules and merge the ones that
overlap. For CIDRs, first turn each block into an integer start and end.

**Mapping: DevOps term → handbook name**

| DevOps term | Handbook name |
|---|---|
| one port range or CIDR rule | one `[start, end]` in `intervals` |
| first / last port, or first / last address as an integer | `start` / `end` |
| the real exposed ranges | the merged list returned by `merge` |
| rules that overlap or share a boundary | "overlapping" intervals |

## 3. Why This Is DevOps `DevOps layer`
**Production reality:** Firewall rules, security groups and network ACLs pile up. Each rule
is a range of ports or addresses, and overlapping rules hide what is really open. Sorting the
ranges by start and merging overlaps in one pass gives the true exposed surface, which is what
an auditor or a rule-count cleanup needs. For CIDRs, convert each block to an integer range
(network address to broadcast address) and merge those numbers.

**Where you see it:** AWS security groups and network ACLs, GCP firewall rules, the Python
`ipaddress.collapse_addresses` function, and cloud security posture tools that report "effective
exposure".

**Reality check:** This merge treats `[1,4]` and `[4,5]` as overlapping, but `[80,443]` and
`[444,500]` as separate, even though no port lies between them. For integer ranges, use
half-open intervals (`[start, end + 1)`) or merge when `start <= end + 1`. Real rules also
carry protocol and source: only merge rules whose other fields match.

**What breaks if you get it wrong:** If you review rules one by one, 400–8080 hides behind the
"expected" 80–443 rule, and the database admin port inside that range stays open to the
whole VPC. Merging exposes the true 80–8080 range at a glance.

## 4. Problem Statement `From handbook`
Given an array `intervals` where `intervals[i] = [startᵢ, endᵢ]`, merge every group of overlapping intervals and return the list of non-overlapping intervals that together cover exactly the same points.

Intervals that share an endpoint, such as `[1,4]` and `[4,5]`, are considered overlapping. Return the merged intervals **sorted by start**.

## 5. Input / Output format and Constraints
**Input / Output format `(added)`:** `merge(intervals: List[List[int]]) -> List[List[int]]`, a plain function (the handbook's code has no `Solution` class).

**Constraints `From handbook`**
- 1 ≤ intervals.length ≤ 10⁴
- intervals[i].length == 2
- 0 ≤ startᵢ ≤ endᵢ ≤ 10⁴

## 6. Examples `From handbook`
**Example 1 — 4 intervals**
```
Input:  intervals = [[1, 3], [2, 6], [8, 10], [15, 18]]
Output: [[1, 6], [8, 10], [15, 18]]
```
`[1,3]` and `[2,6]` overlap and combine into `[1,6]`.

**Example 2 — 2 intervals**
```
Input:  intervals = [[1, 4], [4, 5]]
Output: [[1, 5]]
```
They touch at `4`, so they merge.

**Example 3 — 2 intervals**
```
Input:  intervals = [[4, 7], [1, 4]]
Output: [[1, 7]]
```
The input need not be sorted.

## 7. Starter Code `(added)`
The handbook builds its starter from the problem's function signature and stores no starter file. See
[`starter.py`](starter.py): the same `merge` signature, with a TODO body.

```bash
make try CHIP=02-security/DC-SEC-05-firewall-range-merger
```

## 8. Hints `From handbook`
1. Overlapping intervals are easy to spot once intervals with nearby starts sit next to each other.
2. Sort by start, then sweep once while keeping the last interval of the output as the one you are currently growing.
3. For each interval, if its start is `<=` the last output interval's end, extend that end to `max(end, current end)`; otherwise append it as a new interval.

## 9. Solution `From handbook`
#### Brute Force (Compare All Pairs)
Compare every pair of intervals and merge overlapping ones iteratively.

- Sort by start time first
- Merge if current start <= previous end
- This is already the optimal approach

Time: O(n log n) · Space: O(n)

```python
def merge(intervals):
    ivs = [list(iv) for iv in intervals]
    # Keep merging any overlapping pair until no pair overlaps
    changed = True
    while changed:
        changed = False
        for i in range(len(ivs)):
            for j in range(i + 1, len(ivs)):
                a, b = ivs[i], ivs[j]
                if a[0] <= b[1] and b[0] <= a[1]:
                    a[0], a[1] = min(a[0], b[0]), max(a[1], b[1])
                    ivs.pop(j)
                    changed = True
                    break
            if changed:
                break
    return sorted(ivs)
```

#### Sort and Merge (Optimal)
Sort intervals by start time, then iterate and merge overlapping intervals into the result.

- Sorting is the key insight
- After sorting, one pass suffices
- Update end of last merged interval

Time: O(n log n) · Space: O(n)

```python
def merge(intervals):
    if not intervals:
        return []
    intervals.sort(key=lambda x: x[0])
    result = [intervals[0]]
    for start, end in intervals[1:]:
        if start <= result[-1][1]:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    return result
```

`solution.py` is the handbook's optimal Python solution (Sort and Merge), copied unchanged.
The handbook's Java, C++, Go and JavaScript versions are in `handbook.json` → `solutions[].code`.

## 10. Tests
**From handbook:** 29 cases in `handbook.json` → `tests`, run unchanged by `test_chip.py`.

**`(added)`** [`test_chip.py`](test_chip.py) wraps those cases in pytest (passing deep copies,
see the Review note). It also runs **every** Python solution from the handbook against them (the
Step 3 check), and adds three DevOps-layer cases: security-group port rules (including touching
inclusive ranges that do not merge), CIDRs merged as half-open integer ranges and checked against
`ipaddress.collapse_addresses`, and 300 random interval sets checked against an independent
coverage sweep, plus a 15,000-interval chain.

## 11. Interview Talk Track `DevOps layer`
"To see what a security group really exposes, I treat every rule as a range and merge the
overlaps. Sorting by start puts any ranges that overlap next to each other, so one pass is
enough: if the next range starts at or before the end of the one I'm growing, I extend it,
otherwise I start a new one. That's O(n log n) for the sort and O(n) for the pass. For CIDRs I
convert each block to integers, network address to broadcast address, and merge the numbers. One
detail matters with integers: `/25` blocks that are next to each other don't overlap, so I use
half-open ranges, end plus one, so adjacent blocks merge into a `/24`. And I only merge rules
whose protocol and source are the same, or the merge claims access that no single rule grants."

## 12. Level Up `DevOps layer`
1. **"Merge 200,000 rules across every account in the organisation."** Group rules by
   (protocol, direction, source or destination) first, then merge each group separately. Sorting
   dominates the cost, and the groups can be merged in parallel.
2. **"Rules keep changing. Keep the merged view current."** Store the merged ranges in a sorted
   structure and handle add and remove as range updates instead of a full re-merge. That is the
   allow-list range tracker in DC-SEC-10.
3. **"Merge mixed IPv4 and IPv6."** Keep the two families apart (IPv4 and IPv6 integer spaces
   must not mix) and use Python's arbitrary-size integers for 128-bit IPv6 addresses. Then turn
   each merged range back into CIDRs with the fewest blocks (DC-SEC-09).

## 13. Related Chips `DevOps layer`
- **DC-SEC-10 Allow-List Range Tracker**: add and remove ranges live, splitting when needed.
- **DC-SEC-09 IP Range to CIDR Blocks**: turn merged integer ranges back into CIDR blocks.
- **DC-PLAT-15 On-Call Coverage Gaps**: the same sort and merge, then look at the gaps.

## Review note `DevOps layer`
**Issue:** The copied optimal `merge` changes its caller's data. `intervals.sort(...)` reorders the
caller's list, and `result[-1][1] = ...` writes into the caller's inner lists (they are shared, not
copied). Check: `x = [[8,10],[1,3],[2,6]]; merge(x)` leaves `x == [[1,6],[2,6],[8,10]]`. For a tool
that merges a list of rules it also displays or writes back, this silently corrupts the original rules.

**Suggested fix (not applied):** Copy first: `intervals = sorted(([s, e] for s, e in intervals), key=lambda x: x[0])`.
The copied code is left unchanged, and the tests pass it deep copies.
