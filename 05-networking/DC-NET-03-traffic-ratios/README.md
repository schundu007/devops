Source: New

# DC-NET-03 · Capacity & Traffic Ratio Calculator

## 1. Header
| | |
|---|---|
| Chip ID | DC-NET-03 |
| Difficulty | Medium |
| Pattern | Weighted graph + DFS/BFS |
| Track | Networking, Service Mesh & Resilience (NET) |
| Classic pattern | LeetCode 399 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
Capacity planning for Q3. The platform wiki records a handful of facts: one `prod-eu`
cluster holds 20 nodes, one node holds 30 pods, and one pod handles 150 requests per second.
In the mesh, 50% of ingress traffic goes to `checkout`, and 20% of `checkout` goes to
`checkout-canary`. Finance asks how many pods one cluster holds. The release manager asks what
fraction of ingress traffic reaches the canary. Nobody wrote those numbers down, but they can be
derived by chaining the facts you have.

## 3. Why This Is DevOps
**Production reality:** Capacity numbers come as local ratios: pods per node, nodes per
cluster, requests per pod. Planning questions ask about the ends of the chain. Traffic splits
work the same way. A VirtualService sends 50% to one subset, and inside it another rule sends
20% to a canary, so the canary gets 0.5 × 0.2 = 10% of the total. Every answer is a product
along a path, and every reversed fact is a reciprocal (30 pods per node means 1/30 of a node
per pod).

**Where you see it:** capacity spreadsheets and FinOps unit-cost models (cost per request =
cost per node ÷ requests per node), Istio `VirtualService` weights and Argo Rollouts canary
steps, Kubernetes cluster sizing (max pods per node × nodes).

**Reality check:** Ratios multiply, but latency adds, so this chip does not compute end-to-end
latency. Real facts also carry uncertainty and ranges, and a spreadsheet usually holds a fixed
tree, not a graph with query-time search. The graph matters when facts come from many teams
and nobody owns the whole chain.

**What breaks if you get it wrong:** Invert one ratio (use 30 instead of 1/30) and the plan is
off by a factor of 900. You either buy 900 times too many nodes, or run a canary on 10 times
more traffic than you meant and turn a small bad release into an outage.

## 4. Problem Statement
You get a list of facts. Fact `i` is a pair `(a, b)` with a positive number `values[i] = v`,
meaning "one `a` holds `v` of `b`". Facts can be used backwards: one `b` holds `1/v` of `a`.

For each query `(x, y)`, return how many `y` one `x` holds, by chaining facts. Return `-1.0`
if `x` or `y` does not appear in any fact, or if no chain of facts connects them. A query
`(x, x)` is `1.0` when `x` is known.

The facts never contradict each other.

## 5. Input / Output format and Constraints
- `facts: list[tuple[str, str]]`, `values: list[float]` (same length), `queries: list[tuple[str, str]]`.
- Output: `list[float]`, one answer per query, in order.
- `0 <= len(facts) <= 2000`, `0 <= len(queries) <= 2000`, `0 < values[i] <= 10^6`.
- Names are non-empty strings of up to 30 characters.

## 6. Examples
**Example 1: chain and inverse**
```
facts   = [("cluster", "node"), ("node", "pod")],  values = [20.0, 30.0]
queries = [("cluster", "pod"), ("pod", "cluster")]
-> [600.0, 0.0016666…]            # 20 × 30, and 1 / 600
```

**Example 2: unknown and self (edge case)**
```
facts = [("cluster", "node")], values = [20.0]
queries = [("node", "node"), ("vm", "vm"), ("vm", "node")]
-> [1.0, -1.0, -1.0]              # "vm" was never mentioned
```

**Example 3: traffic split**
```
facts = [("ingress", "checkout"), ("checkout", "checkout-canary")], values = [0.5, 0.2]
queries = [("ingress", "checkout-canary")]  -> [0.1]
```

## 7. Starter Code
See [`starter.py`](starter.py): `calc_ratios(facts, values, queries) -> list[float]` with a docstring. The body is TODO.

```bash
make try CHIP=05-networking/DC-NET-03-traffic-ratios
```

## 8. Hints
1. **Nudge:** Draw each unit as a dot and each fact as an arrow with a number on it. What does a query look like in that drawing?
2. **Pattern:** A weighted graph. Add an edge `a→b` with weight `v` and `b→a` with `1/v`. A query is a path search that multiplies weights along the way.
3. **Near-solution:** For each query, if either end is unknown return `-1.0`. Otherwise BFS from `x` carrying `(node, product)`, and when you pop `y` return the product. If the BFS runs out, return `-1.0`.

## 9. Solution
**Approach**
1. Build an adjacency list. Each fact adds two edges: forward with `v`, backward with `1/v`.
2. For each query, return `-1.0` if either unit is missing from the graph.
3. BFS from `x`, carrying the product of weights on the path taken.
4. When `y` is reached, return the product. If the BFS ends without reaching `y`, return `-1.0`.
5. Because facts are consistent, any path gives the same product, so the first one found is correct.

**Brute force:** Enumerate every simple path from `x` to `y`. That is exponential, and pointless
because consistent facts make every path give the same answer.

**Optimal code:** [`solution.py`](solution.py)

```python
from collections import defaultdict, deque


def calc_ratios(facts, values, queries):
    graph = defaultdict(list)
    for (a, b), v in zip(facts, values):
        graph[a].append((b, v))
        graph[b].append((a, 1.0 / v))

    def ratio(x, y):
        if x not in graph or y not in graph:
            return -1.0
        seen, queue = {x}, deque([(x, 1.0)])
        while queue:
            node, acc = queue.popleft()
            if node == y:
                return acc
            for nxt, w in graph[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, acc * w))   # ratios multiply along a chain
        return -1.0

    return [ratio(x, y) for x, y in queries]
```

**Complexity**
- Time: O(Q · (V + E)) for Q queries, because each query is one BFS over at most V units and 2E edges.
- Space: O(V + E) for the graph, plus O(V) for one BFS's queue and seen set.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases:
- a capacity chain with inverses;
- unknown units and self queries;
- empty facts and empty queries;
- groups with no link between them;
- the production-style mesh traffic split (50% × 20% = 10%);
- a single fact used in both directions;
- a 2,000-unit random forest with 300 queries, checked against independent per-unit potentials computed in one DFS.

## 11. Interview Talk Track
"Each fact is a ratio between two units, like pods per node, so I model units as nodes and
facts as weighted edges, with the reciprocal on the reverse edge. A question like 'pods per
cluster' is a path from cluster to pod, and the answer is the product of the weights along
it. I run a BFS per query, carrying the running product. Unknown units or a disconnected pair
give -1. The facts are consistent, so any path gives the same answer. That is O(V plus E) per
query. For many queries I'd precompute: give each unit a potential relative to its component's
root, or use weighted union-find, and each query becomes O(1). One caution: ratios multiply,
latency adds. Don't use this to add up latency across hops."

## 12. Level Up
1. **"100,000 queries per second from a planning API."** Precompute once. Use weighted
   union-find (each node stores its ratio to its parent, and path compression multiplies them),
   or one BFS per component that stores each unit's potential relative to the root.
   A query is then `pot[y] / pot[x]` in O(1) after an O(α) find.
2. **"Two teams wrote contradictory facts."** During the build, when an edge connects two units
   already in the same component, compare the implied ratio with the new one. If they differ by
   more than a tolerance, reject the fact and name both sources, instead of silently picking a path.
3. **"Traffic weights change during a canary rollout."** Recompute only the affected component.
   With union-find, a changed weight can't be patched in place, so rebuild that component, or keep
   the tree small by modelling each route as its own subgraph. Weights change about once per rollout
   step, so this is cheap.

## 13. Related Chips
- **DC-NET-09 Most Reliable Path**: another multiply-along-the-path problem, where you choose the best path instead of the only answer.
- **DC-PLAT-10 Weighted Canary Router**: turns a traffic split into per-request routing.
- **DC-SEC-14 Identity Linker**: union-find grouping, the base of the weighted union-find follow-up.
