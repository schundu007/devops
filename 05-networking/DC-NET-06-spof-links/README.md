Source: New

# DC-NET-06 · Single-Point-of-Failure Links ★

## 1. Header
| | |
|---|---|
| Chip ID | DC-NET-06 |
| Difficulty | Hard |
| Start here | ★ |
| Pattern | Tarjan's bridges |
| Track | Networking, Service Mesh & Resilience (NET) |
| Classic pattern | LeetCode 1192 |
| Premium | No |
| Time box | 40 min |
| Source | New |

## 2. The Scenario
The data-center team is planning next year's budget. They export the physical topology from
NetBox: 8 switches in two leaf-spine pods, fully meshed inside each pod, plus the inter-pod
cabling. The CTO asks: "Which single cable, if a technician unplugs it by mistake, cuts part
of the network off from the rest?" Those cables get a second, redundant path first. The export
also shows two parallel cables between some pairs, and those should **not** be flagged.

## 3. Why This Is DevOps
**Production reality:** A link is a single point of failure (SPOF) when it is the only path
between two parts of the network. In graph terms, it is a bridge. Tarjan's algorithm finds all
of them in one DFS by tracking, for each device, the earliest point in the DFS that its subtree
can reach without using the link to its parent. If a subtree can't reach above its parent, the
parent link is the only way out. Reliability reviews use this to rank where to buy redundancy
first.

**Where you see it:** topology audits of NetBox or CMDB exports, network design reviews ("N+1
on every path"), and resilience checks in SD-WAN and cloud network planning (VPC peering and
Transit Gateway attachments). The same bridge check works on service dependency graphs.

**Reality check:** Real SPOF analysis also looks at **nodes** (a single core switch whose
failure splits the network is an articulation point, found by the same DFS with a slightly
different test) and at shared-risk groups: two "redundant" fibres in the same conduit fail
together, and a graph cannot see that. Links are also directional in capacity, even when they
are up in both directions.

**What breaks if you get it wrong:** If a parallel cable is treated as a SPOF, budget goes to
links that are already redundant. Worse, if a real bridge is missed, the one cable between
pods is unplugged during maintenance and half the fleet is unreachable, with every
"redundant" top-of-rack pair still shown healthy.

## 4. Problem Statement
The network has `n` devices, numbered `0` to `n - 1`, and a list of undirected links
`(a, b)`. The same pair may be linked more than once. A link is **critical** if removing it
leaves at least one pair of devices, previously connected, with no path between them.

Return every critical link, in any order. Each link may be written as `(a, b)` or `(b, a)`.
The network does not have to be connected.

## 5. Input / Output format and Constraints
- `n: int`, `links: list[tuple[int, int]]`. Returns `list[tuple[int, int]]`.
- `1 <= n <= 10^5`, `0 <= len(links) <= 2 * 10^5`, `0 <= a, b < n`, `a != b`.
- Parallel links between the same pair are allowed.
- Your solution must handle a path of 100,000 devices without hitting a recursion limit.

## 6. Examples
**Example 1: ring with a tail**
```
critical_links(4, [(0, 1), (1, 2), (2, 0), (1, 3)])  -> [(1, 3)]
```
Devices 0, 1, 2 form a ring, and any single ring link can fail safely. Link 1–3 is the only way to reach device 3.

**Example 2: parallel cables (edge case)**
```
critical_links(3, [(0, 1), (0, 1), (1, 2)])  -> [(1, 2)]
```
The two 0–1 cables back each other up.

**Example 3: a full ring**
```
critical_links(6, [(0,1), (1,2), (2,3), (3,4), (4,5), (5,0)])  -> []
```

## 7. Starter Code
See [`starter.py`](starter.py): `critical_links(n, links) -> list[tuple[int, int]]` with a docstring. The body is TODO.

```bash
make try CHIP=05-networking/DC-NET-06-spof-links
```

## 8. Hints
1. **Nudge:** A link u–v is critical exactly when it is not on any cycle. How could one DFS tell whether a subtree has another way back up?
2. **Pattern:** Tarjan's bridges. Record `disc[u]` (when u was first visited) and `low[u]` (the smallest `disc` reachable from u's subtree using at most one non-tree link).
3. **Near-solution:** For a tree link parent → child, after the child finishes, set `low[parent] = min(low[parent], low[child])`. If `low[child] > disc[parent]`, the link is a bridge. Skip the exact link you came in on, by link id, not by parent device, so parallel links count as a cycle.

## 9. Solution
**Approach**
1. Build an adjacency list that stores `(neighbour, link id)`.
2. Run DFS from every unvisited device, giving each device a discovery time `disc` and setting `low = disc`.
3. Seeing an already-visited device through a link other than the one you entered by is a back link: `low[u] = min(low[u], disc[v])`.
4. When a child finishes, pass its `low` up to its parent. If `low[child] > disc[parent]`, nothing under the child can get around the parent link, so it is a bridge.
5. Use an explicit stack of `(device, entry link, neighbour iterator)` instead of recursion, so
   deep networks don't overflow the call stack.

**Brute force:** Remove each link in turn and count the connected components with BFS: O(E · (V + E)).
With 200,000 links that is about 10¹¹ steps. The tests use it on small graphs as the reference.

**Optimal code:** [`solution.py`](solution.py)

```python
def critical_links(n, links):
    adj = [[] for _ in range(n)]
    for eid, (a, b) in enumerate(links):
        adj[a].append((b, eid))
        adj[b].append((a, eid))

    disc, low, timer, bridges = [-1] * n, [0] * n, 0, []
    for root in range(n):
        if disc[root] != -1:
            continue
        disc[root] = low[root] = timer
        timer += 1
        stack = [(root, -1, iter(adj[root]))]          # no recursion
        while stack:
            u, parent_link, neighbours = stack[-1]
            descended = False
            for v, eid in neighbours:
                if eid == parent_link:
                    continue                            # skip only the link we came in on
                if disc[v] == -1:                       # tree link: go deeper
                    disc[v] = low[v] = timer
                    timer += 1
                    stack.append((v, eid, iter(adj[v])))
                    descended = True
                    break
                low[u] = min(low[u], disc[v])           # back link
            if descended:
                continue
            stack.pop()
            if stack:
                p = stack[-1][0]
                low[p] = min(low[p], low[u])
                if low[u] > disc[p]:
                    bridges.append((p, u))
    return bridges
```

**Complexity**
- Time: O(V + E), because each device is pushed once and each link is examined twice (once from each end).
- Space: O(V + E) for the adjacency list, plus O(V) for `disc`, `low` and the explicit stack.

## 10. Tests
[`test_chip.py`](test_chip.py) has 8 cases:
- a ring with a tail;
- a single link and a single device;
- a full ring;
- parallel links;
- a production-style pair of leaf-spine pods joined by one uplink, then made redundant;
- a network in separate pieces;
- a 100,000-device chain and ring (checks there is no recursion limit);
- 150 random graphs checked against an independent remove-and-BFS brute force.

## 11. Interview Talk Track
"A cable is a single point of failure exactly when it isn't on any cycle. Removing each link and
rerunning BFS is quadratic, so I use Tarjan's bridge-finding in one DFS. Each device gets a
discovery time and a low value: the earliest discovery time its subtree can reach with one back
link. When a child finishes, if its low is still greater than the parent's discovery time,
nothing under it can get around the parent link, so that link is a bridge. Two details matter in
production. I skip the incoming link by id, not by parent, so doubled cables count as redundant.
And I make the DFS iterative, because a long chain of devices would overflow Python's recursion
limit. It's O(V plus E). For node failures I'd use the same DFS to find articulation points."

## 12. Level Up
1. **"Also find the single **switches** whose failure splits the network."** Those are
   articulation points. It's the same DFS: a non-root device u is one if some child has
   `low[child] >= disc[u]`, and the root is one if it has two or more DFS children. The result is
   the device list to double up.
2. **"Two 'redundant' fibres run through the same conduit."** Model shared-risk link groups
   (SRLGs): merge links in the same group into one failure unit, and ask whether removing the
   whole group disconnects the network. Bridges tell you about single links. SRLGs need the
   group-level check (at worst, remove each group and run BFS).
3. **"The topology changes every few minutes (VPC peerings added and removed)."** Recompute on
   change. O(V + E) on a 100,000-link graph is about a second in Python, so it is cheap. Only
   look at a dynamic-connectivity structure if changes arrive faster than that.

## 13. Related Chips
- **DC-NET-11 Cheapest Full Connectivity**: builds a minimum spanning tree, where every link is a bridge, which shows why real networks add links on purpose.
- **DC-NET-08 Find the Loop Link**: the opposite question, the link that closes a cycle.
- **DC-SEC-12 Blast Radius of a Leaked Credential**: DFS over a dependency graph for a different kind of reach.
