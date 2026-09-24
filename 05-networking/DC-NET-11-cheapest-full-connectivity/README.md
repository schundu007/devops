Source: New

# DC-NET-11 · Cheapest Full Connectivity

## 1. Header
| | |
|---|---|
| Chip ID | DC-NET-11 |
| Difficulty | Medium |
| Pattern | Minimum spanning tree (Prim/Kruskal) |
| Track | Networking, Service Mesh & Resilience (NET) |
| Classic pattern | LeetCode 1584 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
Facilities is wiring a new campus: four office buildings and a data hall. Every building
needs a fibre path to every other, directly or through other buildings. Conduit runs along the
streets, so cable length is the Manhattan distance between sites on the site plan. The budget
line is "metres of fibre". Find the least total length that connects everything. (Adding
redundancy comes later, and is a separate decision.)

## 3. Why This Is DevOps
**Production reality:** Connecting every site, VPC or data centre at the lowest total link
cost is a minimum spanning tree. Any connected network with no loops uses exactly n − 1 links,
and the MST is the cheapest such network. Kruskal adds the cheapest links that don't form a loop;
Prim grows one connected area outward. Network and cloud architects use the result as the
cheapest baseline, then add redundant links where a single failure would hurt most.

**Where you see it:** campus and data-centre fibre planning, choosing peering links between VPCs
(a similar idea), STP building a loop-free tree at layer 2 (which picks the tree by bridge
priority and path cost, not total cost), clustering in network design tools.

**Reality check:** Real networks are not minimum trees on purpose. In a tree, every link is a
single point of failure (see DC-NET-06), so production designs add redundant links. Real
costs also include equipment, leases and right-of-way, not just distance.

**What breaks if you get it wrong:** Connect each new site to its nearest neighbour and you can
leave the network in separate islands, with two buildings unable to reach each other. Or you
overspend by laying a loop where a tree was enough.

## 4. Problem Statement
Each `sites[i] = [x, y]` is a location on the site plan. A cable between two sites costs
their Manhattan distance, `|x1 - x2| + |y1 - y2|`. Any site can be cabled to any other.

Return the lowest total cable cost so that every site can reach every other site. The network may
route through other sites. With zero or one site, the cost is 0.

## 5. Input / Output format and Constraints
- Returns an integer.
- `0 <= len(sites) <= 1000`.
- `-10^6 <= x, y <= 10^6`, and all sites are distinct.

## 6. Examples
**Example 1: five sites**
```
sites = [[0,0],[2,2],[3,10],[5,2],[7,0]]  ->  20
```
Links (0,0)-(2,2)=4, (2,2)-(5,2)=3, (5,2)-(7,0)=4, (2,2)-(3,10)=9. The total is 20.

**Example 2: two sites**
```
sites = [[3,12],[-2,5]]  ->  12
```

**Example 3: a single site (edge case)**
```
sites = [[4,4]]  ->  0
```

## 7. Starter Code
See [`starter.py`](starter.py): the `min_interconnect_cost(sites)` signature, docstring and type
hints. The body is TODO.

```bash
make try CHIP=05-networking/DC-NET-11-cheapest-full-connectivity
```

## 8. Hints
1. **Nudge:** The cheapest network connecting n sites has no loops. How many links does it need?
2. **Pattern:** Minimum spanning tree. Every pair can be linked, so there are about n²/2 edges:
   Prim with an array (O(n²)) avoids sorting them all.
3. **Near-solution:** Keep `dist[i]`, the cheapest link from site i into the tree. Each step, add the
   untouched site with the smallest `dist`, add that `dist` to the total, then lower `dist` for every
   remaining site using its distance to the new site.

## 9. Solution
**Approach (Prim, array version)**
1. Start the tree at site 0 (`dist[0] = 0`, and every other site is infinity).
2. Repeat n times: pick the site not yet in the tree with the smallest `dist`, add it, and add its
   `dist` to the total.
3. For every site still outside the tree, update `dist[v] = min(dist[v], distance(new, v))`.

**Brute force:** Try every set of n − 1 links and keep the cheapest one that connects all
sites. That grows exponentially. Kruskal (sort all n²/2 edges, O(n² log n)) is the reasonable
alternative, and the tests use it as the reference.

**Optimal code:** [`solution.py`](solution.py)

```python
def min_interconnect_cost(sites):
    n = len(sites)
    if n <= 1:
        return 0
    INF = float("inf")
    in_tree = [False] * n
    dist = [INF] * n
    dist[0] = 0
    total = 0
    for _ in range(n):
        u = min((i for i in range(n) if not in_tree[i]), key=dist.__getitem__)
        in_tree[u] = True
        total += dist[u]
        ux, uy = sites[u]
        for v in range(n):
            if not in_tree[v]:
                d = abs(ux - sites[v][0]) + abs(uy - sites[v][1])
                if d < dist[v]:
                    dist[v] = d
    return int(total)
```

**Complexity**
- Time: O(n²). There are n rounds, and each round scans n sites to pick the minimum and n
  sites to update. On a complete graph, that is as good as it gets, since there are n² edges anyway.
- Space: O(n), for `dist` and `in_tree`. The edges are never stored.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: five sites, a single site and an empty list, two
sites, sites in a line (the total is the span), the campus with a data hall, 150 random layouts
checked against Kruskal, and a 400-site layout with coordinates up to ±10^6.

## 11. Interview Talk Track
"Connecting every site for the least total cost is a minimum spanning tree. The cheapest
connected network has no loops, so it has exactly n − 1 links. Every site can link to every
other here, so the graph is complete with about n²/2 edges. Instead of sorting them all for
Kruskal, I use Prim with an array: keep the cheapest link from each outside site into the
tree, add the closest site, and update the others. That's O(n²) time with O(n) memory, and no edge list.
In production the MST is only the baseline: every link in a tree is a single point of
failure, so I'd then add redundant links on the critical bridges."

## 12. Level Up
1. **"Now make it survive any single link failure."** A tree can't. You need a 2-edge-connected
   network (no bridges). A practical approach: start from the MST, find the bridges (DC-NET-06), and
   add the cheapest extra link that puts each bridge on a loop. The exact minimum-cost version is NP-hard.
2. **"100,000 sites."** O(n²) is 10^10 operations, which is too slow. For Manhattan distance,
   you can build a sparse candidate graph with O(n) edges using a sweep over 4 directions, then
   run Kruskal on it, for O(n log n) total. Or you can cluster sites and wire each cluster separately.
3. **"Some links already exist (leased lines), so they are free."** Union their endpoints first
   (cost 0), then run Kruskal on the rest. Kruskal handles "must include" links naturally; Prim
   needs the free links added with weight 0.

## 13. Related Chips
- **DC-NET-06 Single-Point-of-Failure Links**: the bridges that an MST is full of.
- **DC-NET-08 Find the Loop Link**: the same union-find loop check Kruskal uses.
- **DC-NET-07 Heal a Network Partition**: connect separate groups with the fewest moves.
