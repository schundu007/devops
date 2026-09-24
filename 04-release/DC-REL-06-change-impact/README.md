Source: New

# DC-REL-06 · Change Impact Query

## 1. Header
| | |
|---|---|
| Chip ID | DC-REL-06 |
| Difficulty | Medium |
| Pattern | Transitive closure (BFS / Floyd-Warshall) |
| Track | Release & CI/CD (REL) |
| Classic pattern | LeetCode 1462 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
A pull request changes the Terraform module `vpc`. The change-review bot must answer
questions like "does `orders-api` depend on `vpc`?" and "does `rds-orders` depend on
`dns`?" for every pair of stacks the reviewers care about. That is thousands of questions per
PR across 400 stacks. A plain graph search per question is too slow for a bot that must
comment within a minute, so you precompute who depends on whom once and answer each question instantly.

## 3. Why This Is DevOps
**Production reality:** Before changing a shared module, VPC, base image or library, you
need its blast radius: everything that uses it directly *or* through a chain. `orders-api`
never mentions the VPC, but it runs on a cluster that sits in subnets carved from that VPC.
That "depends on, even indirectly" relation is the transitive closure of the dependency
graph. Computing it once turns every later question into a constant-time lookup.

**Where you see it:** `bazel query 'rdeps(//..., //lib:foo)'` (reverse dependencies),
`nx affected` and similar "affected projects" commands in monorepos, `terraform graph`
reviews, and base-image rebuild pipelines that find every image built on an updated base.

**Reality check:** Real tools usually answer one question at a time with a reverse graph
search, because their graphs are huge and change on every commit. Precomputing a full
closure pays off when the graph is fixed and the questions are many, like one review with
thousands of pair checks. Bitmasks make the closure compact for up to a few thousand nodes.

**What breaks if you get it wrong:** A reviewer sees "no impact" on a VPC change because the
tool checked only direct users. The change merges, and three hops away the payment service
loses its database route during checkout.

## 4. Problem Statement
There are `n` components numbered `0..n-1`. Each pair `(u, v)` in `deps` means component `v`
directly uses component `u`, so a change to `u` can affect `v`. The graph has no cycles.

For each query `(u, v)`, return `True` if `v` depends on `u` directly or through a chain of
other components, and `False` otherwise. A component does not count as depending on itself.

## 5. Input / Output format and Constraints
- `impacts(n: int, deps: list[tuple[int, int]], queries: list[tuple[int, int]]) -> list[bool]`
- `1 <= n <= 2,000`, `0 <= len(deps) <= n·(n-1)/2`, `0 <= len(queries) <= 10^5`.
- All pairs in `deps` are distinct. `u != v` in every dependency, and the graph is acyclic.
- One answer per query, in query order.

## 6. Examples
**Example 1**
```
n = 4, deps = [(0,1), (1,2)]
queries = [(0,1), (0,2), (2,0), (3,2), (1,2)]
impacts(...) -> [True, True, False, False, True]
```
`2` depends on `0` through `1`. Nothing depends on the isolated component `3`, and direction matters.

**Example 2: no edges (edge case)**
```
n = 3, deps = [], queries = [(0,1), (1,2), (2,0)]
impacts(...) -> [False, False, False]
```

**Example 3: a component and itself**
```
n = 1, deps = [], queries = [(0,0)]
impacts(...) -> [False]
```

## 7. Starter Code
See [`starter.py`](starter.py): `impacts(n, deps, queries)` with a docstring and type hints.

```bash
make try CHIP=04-release/DC-REL-06-change-impact
```

## 8. Hints
1. **Nudge:** You could run a BFS for every query. With 10^5 queries, what gets repeated?
2. **Pattern:** Precompute the full "reaches" relation once (the transitive closure), then
   answer each query with a lookup.
3. **Near-solution:** Topologically sort the graph. Walk it in reverse and set
   `reach[u] = OR over children w of (bit w | reach[w])`, using Python ints as bitsets. The
   answer to a query is `reach[u] >> v & 1`.

## 9. Solution
**Approach**
1. Build child lists and topologically sort the components with Kahn's algorithm.
2. Walk the order in reverse, so every child is finished before its parents.
3. For each component `u`, its downstream set is each child plus that child's downstream
   set. Keep it as a bitmask in a Python int.
4. Answer each query by checking bit `v` of `reach[u]`.

**Brute force:** Run a BFS from `u` for every query. That is O(Q·(n + E)): with 10^5 queries
on a dense graph it runs too slowly for the review bot. Floyd–Warshall builds the same table in O(n³).

**Optimal code:** [`solution.py`](solution.py)

```python
def impacts(n, deps, queries):
    children = [[] for _ in range(n)]
    indegree = [0] * n
    for up, down in deps:
        children[up].append(down)
        indegree[down] += 1
    order = []
    ready = deque(v for v in range(n) if indegree[v] == 0)
    while ready:                                  # Kahn's topological order
        v = ready.popleft()
        order.append(v)
        for w in children[v]:
            indegree[w] -= 1
            if indegree[w] == 0:
                ready.append(w)
    reach = [0] * n                               # reach[u]: bitmask of downstream components
    for u in reversed(order):
        for w in children[u]:
            reach[u] |= (1 << w) | reach[w]
    return [bool(reach[u] >> v & 1) for u, v in queries]
```

**Complexity**
- Time: O(n + E·n/64 + Q). Each dependency ORs one bitmask of n bits, which takes about
  n/64 machine words. Each query is O(1).
- Space: O(n²/64) for the bitmasks, plus O(n + E) for the graph.

## 10. Tests
[`test_chip.py`](test_chip.py) has 6 tests: direct and indirect dependencies, a single
component and an empty query list, no edges, direction, the VPC blast radius over eight
Terraform stacks, and a 120-node random DAG with 5,000 queries checked against Floyd–Warshall.

## 11. Interview Talk Track
"Before merging a change to a shared module, I want its blast radius, including indirect
users, and here I have thousands of pair questions per review. A BFS per question repeats
the same work, so I precompute the transitive closure once. I topologically sort the
dependency graph, then walk it backward. Each component's downstream set is the union of its
children and their downstream sets, and I store it as a bitmask, so a union is one OR over
n/64 words. After that every query is a single bit check. For monorepo-scale graphs that
change on every commit, tools like `bazel query rdeps` search on demand instead. Precomputing
wins when the graph is fixed and the questions are many."

## 12. Level Up
1. **"The graph has 2 million nodes."** A full closure needs n² bits, about 500 GB, so it
   no longer fits. Answer each question with a reverse BFS from the changed node, and cache
   the results for hot nodes such as base images. You can also compress with interval
   labelling on a spanning tree (the idea behind GRAIL-style reachability indexes).
2. **"Dependencies change during the day."** Adding an edge `u → v` means OR-ing
   `reach[v] | bit(v)` into `u` and into everything that already reaches `u`. Removing edges is
   the hard case, and usually means recomputing the affected part. Many teams simply rebuild
   the index on each merge to main.
3. **"Show the path, not just yes or no."** Store one parent pointer per (source, reached)
   pair during a BFS, or re-run a single BFS for the pair when a reviewer asks. Reviewers
   trust "vpc → subnets → eks-cluster → orders-api" more than a bare "True".

## 13. Related Chips
- **DC-SEC-12 Blast Radius of a Leaked Credential**: reachability from a single source.
- **DC-REL-05 Buildable Artifacts**: the same graph, walked forward from what is available.
- **DC-NET-13 Reachability Check**: a single yes/no reachability question with BFS or union-find.
