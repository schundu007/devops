Source: New

# DC-NET-09 · Most Reliable Path

## 1. Header
| | |
|---|---|
| Chip ID | DC-NET-09 |
| Difficulty | Medium |
| Pattern | Dijkstra (max-product) |
| Track | Networking, Service Mesh & Resilience (NET) |
| Classic pattern | LeetCode 1514 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
Replication traffic from `us-east` to `eu-west` can go direct over a backup link that
succeeds 99.5% of the time, or through a transit region over two links at 99.9% each. The
architecture review asks: "Which path gives the highest end-to-end success, and what is it?"
There are 14 regions and 40 links in the full map, each with a measured success rate from last
quarter's probes. You need the best path from any region to any other.

## 3. Why This Is DevOps
**Production reality:** Availability multiplies across hops: 99.9% × 99.9% ≈ 99.8%. So the
"best" path is the one with the highest *product* of link success rates, not the fewest hops.
Dijkstra works here because multiplying by a number between 0 and 1 can never increase a
probability, just as adding a non-negative weight never shortens a distance. The same
calculation sets end-to-end SLOs for a chain of services, and it picks paths for replication
or failover.

**Where you see it:** availability math for serial dependencies in SLO documents, SD-WAN
path selection that uses measured loss (a similar idea), service-mesh locality and outlier
routing (a similar idea), multi-region replication design.

**Reality check:** Real links do not fail independently. Two links in the same conduit or the
same region fail together, which breaks the multiply rule. Measured loss also changes minute
to minute. The chip assumes independent, fixed probabilities.

**What breaks if you get it wrong:** Pick the fewest-hop path and replication runs over a
flaky link: you promise 99.9% in the SLO and deliver 99.5%. Over a month that is about 3.6
hours of extra failures instead of about 43 minutes.

## 4. Problem Statement
You have `n` network nodes numbered `0` to `n - 1`. Each `links[i] = [a, b]` is a two-way link
that works with probability `success[i]`. A path works only if every link on it works, so its
success is the product of its links' probabilities.

Return the highest success probability of any path from `src` to `dst`. If `dst` cannot be
reached, return `0.0`.

## 5. Input / Output format and Constraints
- Returns a float. Answers within `1e-9` relative error are accepted.
- `2 <= n <= 10^4`, `0 <= len(links) <= 2 * 10^4`, `len(success) == len(links)`.
- `0 <= a, b < n`, `a != b`, and `0 <= success[i] <= 1`.
- `src != dst`. There may be more than one link between the same two nodes.

## 6. Examples
**Example 1: two strong hops beat one weak link**
```
n = 3, links = [[0,1],[1,2],[0,2]], success = [0.5, 0.5, 0.2], src = 0, dst = 2  ->  0.25
```
The path 0→1→2 gives 0.5 × 0.5 = 0.25, which beats the direct 0.2.

**Example 2: the direct link wins**
```
same links, success = [0.5, 0.5, 0.3]  ->  0.3
```

**Example 3: unreachable (edge case)**
```
n = 3, links = [[0,1]], success = [0.9], src = 0, dst = 2  ->  0.0
```

## 7. Starter Code
See [`starter.py`](starter.py): the `most_reliable_path(n, links, success, src, dst)` signature,
docstring and type hints. The body is TODO.

```bash
make try CHIP=05-networking/DC-NET-09-most-reliable-path
```

## 8. Hints
1. **Nudge:** Adding a link to a path can only keep its probability the same or lower it. Which
   shortest-path algorithm relies on that kind of rule?
2. **Pattern:** Dijkstra, but maximise a product instead of minimising a sum. Use a max-heap
   (push negated probabilities onto `heapq`).
3. **Near-solution:** `best[src] = 1.0`. Pop the highest probability `p` at `node`, and skip it
   if it is stale. For each link, `cand = p * link_p`, and push it if `cand > best[next]`.
   The first time `dst` is popped, that value is final.

## 9. Solution
**Approach**
1. Build an adjacency list with both directions of every link.
2. `best[v]` = the best probability found so far to reach `v`, starting with `best[src] = 1`.
3. Pop the node with the highest probability from a max-heap. Its value is final, because every
   other path to it is already worse and can only get worse.
4. Relax neighbours by multiplying. Return `best` when `dst` is popped, or `0.0` if the heap empties.

**Brute force:** Try every simple path from `src` to `dst`, which is exponential. A safer
middle ground is Bellman-Ford (relax every link `n - 1` times), which is O(n · links).

**Optimal code:** [`solution.py`](solution.py)

```python
import heapq


def most_reliable_path(n, links, success, src, dst):
    adj = [[] for _ in range(n)]
    for (a, b), p in zip(links, success):
        adj[a].append((b, p))
        adj[b].append((a, p))
    best = [0.0] * n
    best[src] = 1.0
    heap = [(-1.0, src)]                 # max-heap via negation
    while heap:
        neg_p, node = heapq.heappop(heap)
        p = -neg_p
        if node == dst:
            return p                     # final the first time it is popped
        if p < best[node]:
            continue                     # stale entry
        for nxt, link_p in adj[node]:
            cand = p * link_p
            if cand > best[nxt]:
                best[nxt] = cand
                heapq.heappush(heap, (-cand, nxt))
    return 0.0
```

**Complexity**
- Time: O((n + L) log n), where L is the number of links. Each successful relaxation pushes
  once onto a heap, and each push or pop costs log of the heap size.
- Space: O(n + L), for the adjacency list, `best` and the heap.

## 10. Tests
[`test_chip.py`](test_chip.py) has 8 cases, all compared with a `1e-9` tolerance: two hops beating
one link, a direct link winning, unreachable, no links, boundary probabilities of 1.0 and 0.0,
the three-nines regions case, 200 random graphs checked against Bellman-Ford, and a 10,000-node chain.

## 11. Interview Talk Track
"Availability multiplies across hops, so the most reliable path maximises a product. Dijkstra
normally minimises a sum, and it's correct because extending a path never makes it shorter.
Here, multiplying by a probability never makes a path more reliable, so the same greedy rule
holds: the node with the highest probability in the heap is final. I use a max-heap of
negated probabilities, relax by multiplication, skip stale entries, and stop when I pop the
destination. That's O((V + E) log V). You could also take negative logs and run a normal
Dijkstra on sums, which avoids tiny floating-point numbers on long paths. The big caveat in
production is correlated failure: two links in the same conduit are not independent."

## 12. Level Up
1. **"Paths are 200 hops long and the product rounds to zero."** Work in log space: the weight
   is `-log(p)`, which is non-negative, and you run a normal min-sum Dijkstra. The answer is
   `exp(-distance)`. It is numerically stable and uses the textbook algorithm unchanged.
2. **"Two links share a fibre conduit and fail together."** The independence rule breaks. Model
   shared-risk link groups (SRLGs): treat the group as one failure event, and choose paths that
   avoid sharing a group. That turns the problem into disjoint-path routing, which is harder than
   plain Dijkstra.
3. **"Link probabilities change every minute from live probes."** Recompute from each source on
   a schedule. Dijkstra over 10,000 nodes takes milliseconds. For a full table between all pairs,
   run it from each source in parallel, or only recompute the paths that used a link that changed.

## 13. Related Chips
- **DC-NET-04 Network Delay Time**: the same Dijkstra, adding latencies instead of multiplying probabilities.
- **DC-NET-03 Capacity & Traffic Ratio Calculator**: multiplying ratios along a path.
- **DC-NET-10 Cheapest Route Within Hop Limit**: shortest paths when the number of hops is capped.
