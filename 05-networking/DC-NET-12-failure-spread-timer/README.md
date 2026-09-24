Source: Handbook #95 Rotting Oranges — `apps/camora/src/data/capra/top100/95.json` (copied unchanged as `handbook.json`)

# DC-NET-12 · Failure Spread Timer

## 1. Header `DevOps layer`
| | |
|---|---|
| Chip ID | DC-NET-12 |
| Difficulty | Medium |
| Pattern | Multi-source BFS |
| Track | Networking, Service Mesh & Resilience (NET) |
| Classic pattern | LeetCode 994 |
| Premium | No |
| Time box | 25 min |
| Source | Handbook #95 Rotting Oranges |

## 2. The Scenario `DevOps layer`
It is a game day in the `dc-east-2` lab. You lay out three racks as a grid: each slot is empty,
a healthy node, or a node you have just failed. The chaos rule is simple. Every minute, a
failed node overloads its direct neighbours (up, down, left, right) and they fail too. The
exercise lead asks two questions: "How many minutes until every node is down?" and "Is any
segment safe because empty slots or firewall gaps cut it off?"

**Mapping: DevOps term → handbook name**

| DevOps term | Handbook name |
|---|---|
| empty slot / firewall gap | `0` (empty) |
| healthy node | `1` (fresh orange) |
| failed node | `2` (rotten orange) |
| one minute of cascading failure | one BFS level |
| a segment the failure can never reach | the `-1` answer |

## 3. Why This Is DevOps `DevOps layer`
**Production reality:** Failures spread through dependencies. An overloaded node sheds its
traffic onto its neighbours, a retry storm hits the next tier, and a worm moves from host to
host. When several things fail at once, they all spread at the same time. The question "how
long until everything is affected?" is the distance from the nearest failure to the farthest
healthy node. That is multi-source BFS. The answer tells you how much time you have to react,
and the `-1` case shows which segments your isolation actually protects.

**Where you see it:** chaos-engineering game days (Gremlin, AWS Fault Injection Service,
Chaos Mesh), network segmentation reviews, worm-propagation models in security teams,
blast-radius planning for circuit breakers.

**Reality check:** Real failures do not spread one grid step per minute. Links have
different delays, and a circuit breaker stops the spread once it opens. For uneven delays,
use Dijkstra (DC-NET-04). The grid is the simple, same-speed version of a failure graph.

**What breaks if you get it wrong:** Run a single-source BFS once per failed node and take
the maximum, and you overestimate the time to full impact. The runbook then says "you have 6
minutes" when you really have 2.

## 4. Problem Statement `From handbook`
You are given an `m × n` grid where each cell is `0` (empty), `1` (a fresh orange) or `2` (a rotten orange). Every minute, each fresh orange that is directly up, down, left or right of a rotten orange becomes rotten.

Return the **minimum number of minutes** until no fresh orange remains. If some fresh orange can never be reached, return `-1`. If there are no fresh oranges at the start, the answer is `0`.

## 5. Input / Output format and Constraints
**Input / Output format `(added)`:** `Solution().orangesRotting(grid: List[List[int]]) -> int`.

**Constraints `From handbook`**
- m == grid.length
- n == grid[i].length
- 1 ≤ m, n ≤ 10
- grid[i][j] is 0, 1, or 2

## 6. Examples `From handbook`
**Example 1 — 3×3 grid**
```
Input:  grid = [[2, 1, 1], [1, 1, 0], [0, 1, 1]]
Output: 4
```
The rot spreads outward from the top-left corner and reaches the bottom-right orange at minute `4`.

**Example 2 — Impossible case · 3×3 grid**
```
Input:  grid = [[2, 1, 1], [0, 1, 1], [1, 0, 1]]
Output: -1
```
The orange in the bottom-left corner has no rotten neighbor path, so it never rots.

**Example 3 — Single row/column · Zero answer**
```
Input:  grid = [[0, 2]]
Output: 0
```
There is nothing fresh to rot.

## 7. Starter Code `(added)`
The handbook builds its starter from the problem's function signature and stores no starter file. See
[`starter.py`](starter.py): the same `orangesRotting` signature, with a TODO body.

```bash
make try CHIP=05-networking/DC-NET-12-failure-spread-timer
```

## 8. Hints `From handbook`
1. All rotten oranges spread simultaneously, so the answer is the farthest any fresh orange is from its nearest rotten source.
2. Run a multi-source BFS: enqueue every initially rotten cell together, and process the queue one level (minute) at a time.
3. Count fresh oranges first; decrement as each is rotted and enqueued. When the queue empties, return the number of levels that rotted something if the count is `0`, else `-1`.

## 9. Solution `From handbook`
#### Minute-by-Minute Simulation
Each minute, scan the whole grid for fresh oranges next to rotten ones and rot them all at once; stop when nothing changes.

- Collect newly rotten cells before applying
- Each round is one minute
- Leftover fresh oranges mean -1

Time: O((m·n)²) · Space: O(m·n)

```python
class Solution:
    def orangesRotting(self, grid):
        grid = [row[:] for row in grid]
        m, n = len(grid), len(grid[0])
        minutes = 0
        while True:
            to_rot = []
            for r in range(m):
                for c in range(n):
                    if grid[r][c] != 1:
                        continue
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < m and 0 <= nc < n and grid[nr][nc] == 2:
                            to_rot.append((r, c))
                            break
            if not to_rot:
                break
            for r, c in to_rot:
                grid[r][c] = 2
            minutes += 1
        if any(1 in row for row in grid):
            return -1
        return minutes
```

#### Multi-Source BFS (Optimal)
Seed a queue with every rotten orange and expand level by level; each BFS level is one minute, and fresh oranges left over at the end are unreachable.

- All rotten cells start in the queue
- One BFS layer = one minute
- Count fresh oranges to detect -1

Time: O(m·n) · Space: O(m·n)

```python
from collections import deque

class Solution:
    def orangesRotting(self, grid):
        grid = [row[:] for row in grid]
        m, n = len(grid), len(grid[0])
        q = deque()
        fresh = 0
        for r in range(m):
            for c in range(n):
                if grid[r][c] == 2:
                    q.append((r, c))
                elif grid[r][c] == 1:
                    fresh += 1
        minutes = 0
        while q and fresh:
            for _ in range(len(q)):
                r, c = q.popleft()
                for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                    if 0 <= nr < m and 0 <= nc < n and grid[nr][nc] == 1:
                        grid[nr][nc] = 2
                        fresh -= 1
                        q.append((nr, nc))
            minutes += 1
        return -1 if fresh else minutes
```

`solution.py` is the handbook's optimal Python solution (Multi-Source BFS), copied unchanged.
The handbook's Java, C++, Go and JavaScript versions are in `handbook.json` → `solutions[].code`.

## 10. Tests
**From handbook:** 30 cases in `handbook.json` → `tests`, run unchanged by `test_chip.py`.

**`(added)`** [`test_chip.py`](test_chip.py) wraps those cases in pytest (deep-copying each
grid so no run can change a shared case). It also runs **every** Python solution from the
handbook against them (the Step 3 check), and adds two DevOps-layer cases: the rack scenario (an
isolated column returns `-1`, and 6 minutes once the gap is closed), and 300 random grids checked
against a minute-by-minute simulation.

## 11. Interview Talk Track `DevOps layer`
"This models a cascading failure. Every failed node spreads to its neighbours each minute,
and all failures spread at the same time. So I don't run a BFS from each failure; I put
every failed node in the queue at minute zero and run one BFS, level by level. Each level is
one minute. I count the healthy nodes up front and decrement as each one fails, so at the end,
if any are left, some segment is unreachable and I return -1. Every cell enters the queue at
most once, so it's O(rows times columns). In a real system that -1 is the good news: it is the
segment your isolation protects. With uneven link delays I'd switch to Dijkstra."

## 12. Level Up `DevOps layer`
1. **"The network is a graph with 1 million hosts, not a grid."** The same algorithm works
   on an adjacency list: enqueue every failed host, then BFS over edges. It is O(V + E) time and
   O(V) memory. Store the graph compactly (CSR arrays) instead of Python dicts.
2. **"Some links are slower, or some hosts take 3 minutes to fall over."** Levels no longer
   equal minutes. Use Dijkstra from a virtual source connected to every failed host with
   weight 0. The answer is the largest shortest distance.
3. **"Which single firewall rule would cut the spread the most?"** Find the chokepoints: the
   bridges or articulation points between the failed area and the rest (DC-NET-06). Blocking a
   bridge splits the graph, and the BFS then returns -1 for the protected side.

## 13. Related Chips `DevOps layer`
- **DC-NET-04 Network Delay Time**: the same spreading question with weighted links (Dijkstra).
- **DC-SEC-12 Blast Radius of a Leaked Credential**: reachability from one compromise point.
- **DC-NET-06 Single-Point-of-Failure Links**: where to cut the graph to stop the spread.
