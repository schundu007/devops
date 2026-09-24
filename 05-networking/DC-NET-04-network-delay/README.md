Source: New

# DC-NET-04 · Network Delay Time

## 1. Header
| | |
|---|---|
| Chip ID | DC-NET-04 |
| Difficulty | Medium |
| Pattern | Dijkstra |
| Track | Networking, Service Mesh & Resilience (NET) |
| Classic pattern | LeetCode 743 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
The network team runs two sites joined by two WAN links: 18 ms through `wan-fra-1` and 25 ms
through `wan-ams-2`. Router `r1` at site A floods a routing update. After a change review, the
team asks: "How long until every router has the update? And what happens to that number if
`wan-fra-1` fails?" You have every link and its one-way delay. Some links are one-way, and one
router might not be reachable at all, which would be a partition you need to flag.

## 3. Why This Is DevOps
**Production reality:** A flooded signal travels down every link at once, so each router first
hears it along its **fastest** path. The time until the whole network knows is the largest of
those shortest-path times. Link-state routing protocols such as OSPF and IS-IS flood link-state
updates to every router, and each router then runs Dijkstra's shortest-path-first (SPF)
algorithm on the link-state database to build its routing table. If some router can never be
reached, the answer is not "slow", it is "partitioned".

**Where you see it:** OSPF and IS-IS SPF computation on routers (FRR, Cisco, Juniper), SD-WAN
path selection, service-mesh and CDN latency maps, and change reviews asking "what is our
convergence time if link X fails?"

**Reality check:** Real routers use link costs (often derived from bandwidth), not measured
delay. Their convergence time also includes failure detection (BFD or hello timers), SPF
throttling delays and route installation (FIB updates), not only propagation along links.
This chip models only the propagation part.

**What breaks if you get it wrong:** If you take the direct 10 ms link over a 3 ms two-hop
detour, the convergence estimate is too high and the SLO looks safe when it isn't. Worse, if you
treat an unreachable router as "reached eventually", a partition goes unreported and traffic is
blackholed.

## 4. Problem Statement
There are `n` routers numbered `1..n`. Each link `(u, v, ms)` carries a signal **one way**, from
`u` to `v`, and takes `ms` milliseconds (`ms >= 0`). A signal starts at router `source` at time 0
and is copied down every outgoing link as soon as it arrives.

Return the time at which the **last** router receives the signal. If any router never receives
it, return `-1`.

## 5. Input / Output format and Constraints
- `links: list[tuple[int, int, int]]`, `n: int`, `source: int`. Returns `int`.
- `1 <= n <= 10^4`, `0 <= len(links) <= 10^5`, `1 <= u, v, source <= n`, `0 <= ms <= 10^4`.
- There may be parallel links between the same pair, and self-loops.

## 6. Examples
**Example 1: tree-shaped flood**
```
links = [(2, 1, 1), (2, 3, 1), (3, 4, 1)], n = 4, source = 2   -> 2
```
Router 4 is reached last, at 2 ms, through router 3.

**Example 2: partition (edge case)**
```
links = [(1, 2, 1)], n = 2, source = 2   -> -1
```
The only link goes from 1 to 2, so a signal from router 2 never reaches router 1.

**Example 3: detour beats direct**
```
links = [(1, 4, 10), (1, 2, 1), (2, 3, 1), (3, 4, 1)], n = 4, source = 1   -> 3
```

## 7. Starter Code
See [`starter.py`](starter.py): `network_delay(links, n, source) -> int` with a docstring. The body is TODO.

```bash
make try CHIP=05-networking/DC-NET-04-network-delay
```

## 8. Hints
1. **Nudge:** Each router hears the signal at the time of its fastest path. You need all of those times, then the largest one.
2. **Pattern:** Single-source shortest paths with non-negative weights: Dijkstra with a min-heap.
3. **Near-solution:** Push `(0, source)`. Pop the smallest time. If the router is already finalised, skip it. Otherwise record it and push `(t + ms, v)` for each outgoing link. At the end, if fewer than `n` routers are finalised, return `-1`, else the max time.

## 9. Solution
**Approach**
1. Build an adjacency list of outgoing links.
2. Keep a min-heap of `(arrival time, router)`, starting with `(0, source)`.
3. Pop the earliest entry. If the router already has a final time, skip it (a stale entry). Otherwise, that time is final.
4. Push each neighbour with `time + delay`.
5. If every router got a final time, return the largest one. Otherwise, return `-1`.

**Brute force:** Bellman-Ford relaxes every link up to `n - 1` times: O(V·E), which is 10⁹
steps at the limits. It also handles negative weights, which delays never have. The tests use it
as the reference.

**Optimal code:** [`solution.py`](solution.py)

```python
import heapq


def network_delay(links, n, source):
    graph = [[] for _ in range(n + 1)]
    for u, v, ms in links:
        graph[u].append((v, ms))

    arrival = {}
    heap = [(0, source)]
    while heap:
        t, node = heapq.heappop(heap)
        if node in arrival:
            continue                      # stale entry
        arrival[node] = t                 # smallest time popped first = final
        for nxt, ms in graph[node]:
            if nxt not in arrival:
                heapq.heappush(heap, (t + ms, nxt))

    return max(arrival.values()) if len(arrival) == n else -1
```

**Complexity**
- Time: O(E log E), because each link pushes at most one heap entry and each push or pop is O(log E).
- Space: O(V + E) for the adjacency list, the heap and the arrival map.

## 10. Tests
[`test_chip.py`](test_chip.py) has 8 cases:
- a normal flood and a single router;
- unreachable routers (one-way links, an isolated router);
- a slow direct link that loses to a fast detour;
- zero-delay links and parallel links;
- a production-style two-site flood before and after a WAN link failure;
- a 3,000-router unit-weight graph checked against BFS levels;
- random graphs up to 2,000 routers and 12,000 links checked against Bellman-Ford.

## 11. Interview Talk Track
"A flooded update reaches each router along its fastest path, so this is single-source shortest
paths, and the network-wide answer is the largest shortest-path time. Delays are non-negative,
so I use Dijkstra: a min-heap of arrival times, always finalising the earliest router, skipping
stale heap entries. That's O(E log E). If some router is never finalised, I return -1, because
that's a partition, not a slow network. This is the same algorithm OSPF and IS-IS routers run
as SPF on their link-state database. In a real convergence estimate I'd add failure-detection
time, SPF throttle timers and FIB install time on top."

## 12. Level Up
1. **"The network has 50,000 routers, and links flap every few seconds."** Rerunning full SPF
   on every change is expensive. Routers throttle SPF runs (exponential back-off), and some use
   incremental SPF, which recomputes only the part of the tree below the changed link.
   Split the network into areas (OSPF) or levels (IS-IS) so each SPF runs on a smaller graph.
2. **"Which single link failure hurts convergence the most?"** For each link, remove it and
   rerun Dijkstra: O(E · E log E). That is fine for hundreds of links. For thousands, only test
   links on the current shortest-path tree, because removing a link outside the tree can't change
   any shortest time.
3. **"Return the path, not just the time."** Store `parent[v] = u` when `v` is finalised, then
   walk back from any router to the source. That is the routing table's next hop, read from the
   other end.

## 13. Related Chips
- **DC-NET-09 Most Reliable Path**: Dijkstra with multiplied probabilities instead of added delays.
- **DC-NET-10 Cheapest Route Within Hop Limit**: shortest path with a hop limit, where plain Dijkstra no longer works.
- **DC-NET-12 Failure Spread Timer**: the same "time until everything is reached" question when every step costs 1 (BFS).
