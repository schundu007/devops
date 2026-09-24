Source: Handbook #24 Merge K Sorted Lists — `apps/camora/src/data/capra/top100/24.json` (copied unchanged as `handbook.json`)

# DC-OBS-14 · Multi-Node Log Timeline Merge

## 1. Header `DevOps layer`
| | |
|---|---|
| Chip ID | DC-OBS-14 ★ |
| Difficulty | Hard |
| Pattern | Min-heap (k-way merge) |
| Track | Observability & SRE (OBS) |
| Classic pattern | LeetCode 23 |
| Premium | No |
| Time box | 40 min |
| Source | Handbook #24 Merge K Sorted Lists |

## 2. The Scenario `DevOps layer`
At 03:40 the `orders` database failed over, and 40 app nodes (`ip-10-0-1-11` to
`ip-10-0-4-50`) logged connection errors. Each node's log file is already sorted by time,
because a node writes lines as they happen. The incident commander wants **one** timeline
across all 40 nodes to see which node failed first, and whether the errors started before
or after the failover. Some nodes logged nothing at all.

**Mapping: DevOps term → handbook name**

| DevOps term | Handbook name |
|---|---|
| one node's log stream, sorted by time | one linked list `lists[i]` |
| one log line's timestamp | `node.val` |
| a node that logged nothing | an empty list (`None`) |
| the merged incident timeline | the returned list |
| number of nodes | `k` |

## 3. Why This Is DevOps `DevOps layer`
**Production reality:** Each node ships logs that are already in time order. Building one
timeline does not need a full sort: at every step the next line is the earliest among the
*heads* of the k streams. A min-heap holds those k heads, so each output line costs O(log k).
The same k-way merge runs whenever sorted pieces are combined: merging per-shard query
results, merging sorted runs in a database's external sort, and LSM-tree compaction.

**Where you see it:** `sort -m` (merges files that are already sorted), Loki and Elasticsearch
queriers merging results from many streams or shards, LSM compaction in RocksDB and Cassandra,
`kubectl logs` with `--prefix` across pods (the output is interleaved as lines arrive, *not*
merged by timestamp, which is exactly why you need this).

**Reality check:** Real node clocks drift, so "sorted by timestamp" across nodes is only as
good as NTP. Aggregators often sort within a small time window rather than trusting exact
order. Log timestamps also tie often, so a stable tie-breaker (node ID, then line number)
keeps the timeline repeatable.

**What breaks if you get it wrong:** Concatenate the node logs instead of merging them, and
the timeline says node 1 failed "first" just because it is listed first. The postmortem then
blames the wrong service for the cascade.

## 4. Problem Statement `From handbook`
You are given an array `lists` of `k` linked lists, each sorted in ascending order.

Merge all of them into a single sorted linked list and return its head. If there are no nodes at all, return an empty list.

## 5. Input / Output format and Constraints
**Input / Output format `(added)`:** `mergeKLists(lists)` takes a list of linked-list heads
(`ListNode` with `val` and `next`, where an empty list is `None`) and returns the head of the
merged list. Tests store each linked list as an array, and the runner converts it.

**Constraints `From handbook`**
- k == lists.length
- 0 ≤ k ≤ 10⁴
- 0 ≤ lists[i].length ≤ 500
- -10⁴ ≤ lists[i][j] ≤ 10⁴
- lists[i] is sorted in ascending order.
- The sum of lists[i].length will not exceed 10⁴.

## 6. Examples `From handbook`
**Example 1 — 3 lists**
```
Input:  lists = [[1, 4, 5], [1, 3, 4], [2, 6]]
Output: [1, 1, 2, 3, 4, 4, 5, 6]
```
All eight values, taken together in sorted order.

**Example 2 — Empty input · Empty result**
```
Input:  lists = []
Output: []
```
There are no lists.

**Example 3 — 1 list · Empty result**
```
Input:  lists = [[]]
Output: []
```
There is one list, and it is empty.

## 7. Starter Code `(added)`
The handbook builds its starter from the problem's function signature and stores no starter file. See
[`starter.py`](starter.py): a top-level `mergeKLists(lists)`, the same form as the handbook's
code, with a TODO body. The runner provides `ListNode`.

```bash
make try CHIP=01-observability/DC-OBS-14-log-timeline-merge
```

## 8. Hints `From handbook`
1. The next output node is always the smallest among the current heads of the `k` lists.
2. A min-heap keyed by node value gives that smallest head in O(log k); alternatively merge lists pairwise, divide-and-conquer style.
3. Push every non-empty head into the heap; repeatedly pop the minimum, append it to the result, and push its `next` if it exists.

## 9. Solution `From handbook`
#### Compare All Lists
At each step, find the minimum head across all k lists and append it to the result.

- Scan all k heads to find minimum each time
- n is total number of nodes
- Simple but slow for large k

Time: O(n * k) · Space: O(1)

```python
def mergeKLists(lists):
    dummy = curr = ListNode(0)
    while True:
        min_idx = -1
        min_val = float('inf')
        for i, node in enumerate(lists):
            if node and node.val < min_val:
                min_val = node.val
                min_idx = i
        if min_idx == -1:
            break
        curr.next = lists[min_idx]
        lists[min_idx] = lists[min_idx].next
        curr = curr.next
    return dummy.next
```

#### Divide and Conquer (Optimal)
Merge lists pairwise, reducing k lists to k/2, then k/4, etc. Like merge sort.

- Merge pairs like merge sort
- log k rounds of merging
- Each round processes all n nodes once
- Reuses the merge two sorted lists subroutine

Time: O(n log k) · Space: O(log k)

```python
def mergeKLists(lists):
    if not lists:
        return None
    def merge2(l1, l2):
        dummy = curr = ListNode(0)
        while l1 and l2:
            if l1.val <= l2.val:
                curr.next = l1
                l1 = l1.next
            else:
                curr.next = l2
                l2 = l2.next
            curr = curr.next
        curr.next = l1 or l2
        return dummy.next
    while len(lists) > 1:
        merged = []
        for i in range(0, len(lists), 2):
            l1 = lists[i]
            l2 = lists[i + 1] if i + 1 < len(lists) else None
            merged.append(merge2(l1, l2))
        lists = merged
    return lists[0]
```

`solution.py` is the handbook's optimal Python solution (Divide and Conquer), copied
unchanged. The handbook's Java, C++, Go and JavaScript versions are in `handbook.json` →
`solutions[].code`.

**`(added)` Min-heap k-way merge.** This is the chip's pattern, and the handbook's hints 2 and
3 describe it, but the handbook stores no heap solution. See
[`solution_heap.py`](solution_heap.py). It is also O(n log k) time, with O(k) space for the heap:

```python
import heapq


def mergeKLists(lists):
    heap = []
    for i, node in enumerate(lists):
        if node:
            heap.append((node.val, i, node))  # i breaks ties so nodes are never compared
    heapq.heapify(heap)
    dummy = tail = ListNode(0)
    while heap:
        _, i, node = heapq.heappop(heap)
        tail.next = node
        tail = node
        if node.next:
            heapq.heappush(heap, (node.next.val, i, node.next))
    return dummy.next
```

## 10. Tests
**From handbook:** 29 cases in `handbook.json` → `tests`, run unchanged by `test_chip.py`.

**`(added)`** [`test_chip.py`](test_chip.py) wraps those cases in pytest. A local adapter
defines `ListNode` and converts arrays to linked lists and back, doing the job of the handbook's
own runner. It runs **every** Python solution from the handbook against the cases (the Step 3
check), runs the added heap solution too, and adds two DevOps-layer cases: a three-node
incident timeline with a tie and a silent node, and a 300-list random check against `sorted()` and `heapq.merge`.

## 11. Interview Talk Track `DevOps layer`
"Every node's log is already sorted by time, so I don't sort everything again. The next
line of the combined timeline is always the smallest among the k stream heads. I keep those
k heads in a min-heap. I pop the smallest, append it, and push that stream's next line.
Each of the n lines goes in and out of the heap once, so it's O(n log k) time and O(k) memory.
That matters because k is small, say 40 nodes, while n is millions of lines, and it works
on streams too, since I only ever hold one line per node. Divide and conquer, merging pairs
like merge sort, has the same bound. The production catches are clock skew between nodes and
ties, so I break ties by node ID to keep the output stable."

## 12. Level Up `DevOps layer`
1. **"10,000 nodes, streaming live, and new lines keep arriving."** A heap of 10,000 heads is
   still tiny. The real question is when you may emit: a line is safe to output only once every
   stream has sent something later, or a watermark timeout has passed. This is how streaming
   systems handle late data.
2. **"The streams are 50 GB files on disk."** Read each file in buffered chunks and keep only
   the current line per file in the heap, so memory stays O(k × buffer). This is an external
   merge sort's final pass, and it is what `sort -m` does with sorted files.
3. **"Clocks on nodes drift by up to 2 seconds."** Exact order across nodes is not knowable.
   Merge by timestamp anyway, but mark lines within the skew bound as concurrent, or use a
   causal ID (a trace ID, or a request's hop order) to order related events.

## 13. Related Chips `DevOps layer`
- **DC-OBS-15 Incident Correlation Window**: the same k-heads-in-a-heap idea, used to find the tightest window.
- **DC-OBS-10 Log Time-Range Query**: pick the time range before merging.
- **DC-OBS-08 Live Latency Percentiles**: heaps over a stream.

## Review note `DevOps layer`
- **Hints and solutions don't match.** Handbook hints 2 and 3 describe a min-heap, but the
  stored solutions are "Compare All Lists" and "Divide and Conquer". Nothing is wrong with
  either one; all handbook cases pass on both. Suggested fix: add the heap solution
  (as in `solution_heap.py`) to the handbook entry, so the hints lead to a solution the reader can see.
- **The handbook code depends on `ListNode` from the runner.** `solution.py` does not run on
  its own because `ListNode` is not defined in it. This is by design in the handbook, so the
  copied code is left unchanged, and the test adapter provides the class.
