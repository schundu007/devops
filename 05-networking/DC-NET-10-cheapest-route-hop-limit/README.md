Source: New

# DC-NET-10 · Cheapest Route Within Hop Limit

## 1. Header
| | |
|---|---|
| Chip ID | DC-NET-10 |
| Difficulty | Medium |
| Pattern | Bellman-Ford / level BFS |
| Track | Networking, Service Mesh & Resilience (NET) |
| Classic pattern | LeetCode 787 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
The data team must copy a nightly 40 TB export from `us-east-1` to `ap-south-1`. The direct
transfer is expensive. Relaying through `eu-central-1`, or through `us-west-2` and then
`eu-central-1`, costs less. But every relay adds a staging bucket, a copy job and another failure
point, so the platform team caps it: **at most one transit region**. Find the cheapest route that
respects the cap.

## 3. Why This Is DevOps
**Production reality:** Moving data between regions or clouds costs money per GB, and prices
differ by route. The cheapest path is often not direct. Every hop still adds latency,
operational risk and something to monitor, so teams cap the number of hops. "Cheapest path with
at most k hops" is shortest path with a constraint. Plain Dijkstra fails here, because the
cheapest way to reach a region may use too many hops. Bellman-Ford solves it naturally: after
round r, it knows the cheapest cost using at most r hops.

**Where you see it:** planning cross-region replication and data transfer routes on AWS, GCP or
Azure, CDN origin shielding tiers, IP TTL and hop limits (a similar idea), BGP paths where a
shorter AS path is preferred (a similar idea).

**Reality check:** Real transfer pricing depends on the source region, destination, service and
monthly volume tier. It is not one number per link. Transit hops also need storage and add time,
which this chip ignores.

**What breaks if you get it wrong:** Run Dijkstra and then check the hop count, and you can
wrongly report "no route". Or, if you update costs in place within a round, one round can chain
several hops. Either way the pipeline breaks the relay limit, or overpays by thousands of dollars a month.

## 4. Problem Statement
There are `n` regions, numbered `0` to `n - 1`. Each `routes[i] = [a, b, price]` is a one-way
transfer from region `a` to region `b` with that cost.

Find the lowest total cost to get from `src` to `dst` passing through **at most `max_transit`**
regions in between (so at most `max_transit + 1` transfers). Return `-1` if no such route exists.

## 5. Input / Output format and Constraints
- Returns an integer cost, or `-1`.
- `2 <= n <= 100`, `0 <= len(routes) <= n * (n - 1)`.
- `0 <= a, b < n`, `a != b`, `1 <= price <= 10^4`, and there is at most one route per ordered pair.
- `0 <= src, dst < n`, `src != dst`, and `0 <= max_transit < n`.

## 6. Examples
**Example 1: the cheapest path is too long**
```
routes = [[0,1,100],[1,2,100],[2,3,100],[0,3,800],[1,3,600]], src = 0, dst = 3
max_transit = 1  ->  700   # 0->1->3; the 300 path needs 2 transit regions
max_transit = 2  ->  300   # 0->1->2->3
```

**Example 2: zero transit means direct only**
```
routes = [[0,1,100],[1,2,100],[0,2,500]], src = 0, dst = 2, max_transit = 0  ->  500
```

**Example 3: unreachable (edge case)**
```
routes = [[0,1,5]], src = 0, dst = 2, max_transit = 5  ->  -1
```

## 7. Starter Code
See [`starter.py`](starter.py): the `cheapest_route(n, routes, src, dst, max_transit)` signature,
docstring and type hints. The body is TODO.

```bash
make try CHIP=05-networking/DC-NET-10-cheapest-route-hop-limit
```

## 8. Hints
1. **Nudge:** Why does plain Dijkstra fail? A region's cheapest arrival may use too many hops,
   while a slightly dearer arrival with fewer hops could still continue.
2. **Pattern:** Bellman-Ford with a fixed number of rounds: round r allows paths with at most
   r transfers. Run `max_transit + 1` rounds.
3. **Near-solution:** Each round, copy `cost` to `prev` and relax every route using only
   `prev[a] + price`. Reading from `prev` stops one round from chaining two hops.

## 9. Solution
**Approach**
1. `cost[src] = 0`, and every other region is infinity.
2. Repeat `max_transit + 1` times: snapshot `prev = cost[:]`, and for each route relax
   `cost[b] = min(cost[b], prev[a] + price)`.
3. Return `cost[dst]`, or `-1` if it is still infinity.

**Brute force:** Enumerate every walk with up to `max_transit + 1` transfers using DFS. That is
exponential in the hop limit: with 100 regions and 3 hops, already about 10^6 walks.

**Optimal code:** [`solution.py`](solution.py)

```python
def cheapest_route(n, routes, src, dst, max_transit):
    INF = float("inf")
    cost = [INF] * n
    cost[src] = 0
    for _ in range(max_transit + 1):        # round r: paths with at most r hops
        prev = cost[:]                      # snapshot: one extra hop per round
        for a, b, price in routes:
            if prev[a] + price < cost[b]:
                cost[b] = prev[a] + price
    return -1 if cost[dst] == INF else int(cost[dst])
```

**Complexity**
- Time: O((k + 1) · R), where k is `max_transit` and R is the number of routes: each of the
  k + 1 rounds scans every route once.
- Space: O(n), for the two cost arrays.

## 10. Tests
[`test_chip.py`](test_chip.py) has 8 cases: the cheaper path being too long, zero transit,
unreachable and no routes, one-way routes, the exact hop-limit boundary, a four-region egress case,
200 random graphs checked against DFS enumeration, and a dense 100-region graph (9,900 routes).

## 11. Interview Talk Track
"We want the cheapest data transfer route, but ops caps the number of relays. Dijkstra alone
doesn't work, because it keeps only the cheapest arrival at each region, and that might have used
up the hop budget. Bellman-Ford fits naturally: after round r, it holds the cheapest cost using at
most r transfers. So I run max_transit plus one rounds. The one subtle bug is updating in place,
because then a single round can chain several hops. Snapshotting the previous round's costs fixes
that. That's O(k times routes). An alternative is Dijkstra over (region, hops used) states.
In a real cloud plan, I'd also weigh latency and the extra failure point each relay adds."

## 12. Level Up
1. **"Minimise cost, but break ties on fewer hops."** Store `(cost, hops)` pairs and compare them
   as tuples. Or run the rounds and remember the first round in which `dst` reaches its final cost.
2. **"10,000 regions and 1 million routes, with k = 3."** Bellman-Ford does 4 × 1M relaxations,
   which is fine. If k is large, run Dijkstra on states `(region, hops)`, pruning any state whose
   cost is no better than a state with fewer hops at the same region.
3. **"Prices change hourly, and you need routes for 500 region pairs."** Run the k-round relaxation
   once per distinct source (each run gives every destination), which is far fewer runs than 500 pairs.
   Cache results by price-table version, and recompute only when prices change.

## 13. Related Chips
- **DC-NET-04 Network Delay Time**: shortest path without a hop cap (Dijkstra).
- **DC-NET-09 Most Reliable Path**: Dijkstra on multiplied probabilities.
- **DC-NET-11 Cheapest Full Connectivity**: connect all regions for the least total cost.
