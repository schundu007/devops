Source: New

# DC-NET-08 · Find the Loop Link

## 1. Header
| | |
|---|---|
| Chip ID | DC-NET-08 |
| Difficulty | Medium |
| Pattern | Union-find |
| Track | Networking, Service Mesh & Resilience (NET) |
| Classic pattern | LeetCode 684 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
At 09:40 the monitoring on the `bldg-3` access network shows every switch port at 100%
broadcast traffic, and VoIP calls start dropping. The night before, a technician added one
patch cable between `sw7` and `sw4` "for redundancy". The layer-2 network was a tree
(`sw1` core, `sw2`/`sw3` distribution, `sw4`–`sw7` access), and now it has a loop. You have
the cabling list in the order the links were added. Find the link to disable.

## 3. Why This Is DevOps
**Production reality:** An Ethernet frame has no time-to-live field. When a layer-2 network
contains a loop, broadcast frames circle forever and multiply: a broadcast storm that can
take down a whole building. A tree network plus one extra link has exactly one loop, and
removing any link on that loop restores a tree. Union-find reads the links one at a time and
spots the first link whose two ends are already connected. That link closes the loop.

**Where you see it:** the Spanning Tree Protocol (IEEE 802.1D) and its faster versions
(RSTP, MSTP), which block redundant switch ports so the active topology is a tree. You also see
it in network-as-code validation before a cabling change, and in Kruskal's minimum spanning
tree (DC-NET-11).

**Reality check:** STP does not delete links. It keeps the redundant link in a blocking
state and brings it back if another link fails. It also picks which port to block from bridge
priorities and path costs, not from the order links were added. The chip only finds the link
that closes the loop.

**What breaks if you get it wrong:** Disable a link that is not on the loop and you cut a
switch off the network while the storm continues. Two problems instead of one.

## 4. Problem Statement
A network of `n` switches, numbered `1` to `n`, was a tree: every switch was connected and there
were no loops. Then exactly one extra link was added. You get all links in `links`, in the order
they were added, where `links[i] = [a, b]` is a cable between switches `a` and `b`.

Return the link that you can disable so the network becomes a tree again. If several links
would work, return the one that appears **last** in `links`.

## 5. Input / Output format and Constraints
- `n`: the number of switches. `links`: a list of `[a, b]` pairs.
- Returns one `[a, b]` pair, exactly as it appears in `links`.
- `3 <= n <= 1000` and `len(links) == n`.
- `1 <= a, b <= n` and `a != b`.
- Without the extra link, the network is a connected tree. Two cables may connect the same
  pair of switches; that is the shortest possible loop.

## 6. Examples
**Example 1: the smallest loop**
```
n = 3, links = [[1,2], [1,3], [2,3]]   ->  [2,3]
```
All three links are on the loop 1-2-3. `[2,3]` is listed last.

**Example 2: the loop is not at the end**
```
n = 4, links = [[1,2], [2,3], [3,1], [3,4]]   ->  [3,1]
```
`[3,4]` is last, but removing it would cut off switch 4. Only links on the loop count.

**Example 3: parallel cables (edge case)**
```
n = 3, links = [[1,2], [2,3], [2,1]]   ->  [2,1]
```
The second cable between switches 1 and 2 is the loop.

## 7. Starter Code
See [`starter.py`](starter.py): the `find_loop_link(n, links)` signature, docstring and type hints.
The body is TODO.

```bash
make try CHIP=05-networking/DC-NET-08-find-the-loop-link
```

## 8. Hints
1. **Nudge:** Add links one at a time. When does a new link create a loop?
2. **Pattern:** A link creates a loop exactly when its two switches are already connected.
   Union-find answers "already connected?" in near-constant time.
3. **Near-solution:** For each `[a, b]` in order: if `find(a) == find(b)`, return `[a, b]`.
   Otherwise `union(a, b)`. The first link that closes the loop is the last loop link listed,
   because the other loop links all came before it.

## 9. Solution
**Approach**
1. Start with every switch in its own group.
2. Read the links in order. If both ends are already in the same group, this link closes the
   loop: return it.
3. Otherwise merge the two groups (union by size, with path halving in `find`).
4. Why this is "the last one listed": the loop is complete only once all of its links have
   been read, so the link that completes it is the loop link that comes last.

**Brute force:** Remove each link in turn (from the last one backwards), then BFS to check
whether the rest is a connected tree. That is O(n) checks of O(n) each, so O(n²). Fine for
1,000 switches, but too slow for a 100,000-link data-centre fabric.

**Optimal code:** [`solution.py`](solution.py)

```python
def find_loop_link(n: int, links: list[list[int]]) -> list[int]:
    parent = list(range(n + 1))
    size = [1] * (n + 1)

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]   # path halving
            x = parent[x]
        return x

    for a, b in links:
        ra, rb = find(a), find(b)
        if ra == rb:
            return [a, b]                   # already connected: this link closes the loop
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra                     # union by size
        size[ra] += size[rb]
    return []
```

**Complexity**
- Time: O(n · α(n)), which is effectively linear. Each link does two `find` calls, and with
  union by size plus path halving each call costs the inverse Ackermann function α(n), which is below 5 for any real size.
- Space: O(n), for the parent and size arrays.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: the smallest triangle, a loop that is not at
the end, "last listed wins", parallel cables, a production mis-cabling case (`sw7`–`sw4`),
150 random networks checked against a remove-and-BFS brute force, and a 1,000-switch ring.

## 11. Interview Talk Track
"A layer-2 tree with one extra cable has exactly one loop, and loops are dangerous because
Ethernet frames have no TTL, so broadcasts circle forever. To find the link to disable, I read
the links in order and keep connected groups in a union-find. If a new link joins two switches
that are already in the same group, that link closes the loop, so I return it. Because the
loop only completes at its last link, that's also the last loop link in the input, which is
the tie-break asked for. With union by size and path compression it's effectively linear.
In production, STP solves this continuously: it keeps the redundant link but blocks the port,
chosen by bridge priority, and unblocks it if the main path fails."

## 12. Level Up
1. **"Two extra links were added, not one."** Keep reading after the first loop link. Every
   link whose ends are already connected is redundant, so collect them all. To choose *which*
   ones to block, use costs: that is a minimum spanning tree (DC-NET-11), which is what STP
   approximates using path costs.
2. **"The links are directed (for example, routing adjacencies with one parent each)."** Now
   a node can also have two parents. You need to handle three cases: a node with two parents, a
   cycle, or both. That is LeetCode 685, a harder version of this chip.
3. **"Cables are added live, and you must reject a loop the moment it is proposed."** Keep
   the union-find in memory and run `find(a) == find(b)` as an admission check in CI for
   network-as-code changes. Each check is near O(1). Removing links is the hard part, because
   union-find cannot split groups: rebuild the structure, or use a dynamic-connectivity structure.

## 13. Related Chips
- **DC-NET-07 Heal a Network Partition**: union-find counting groups and spare links.
- **DC-NET-11 Cheapest Full Connectivity**: Kruskal uses the same "already connected?" check.
- **DC-NET-06 Single-Point-of-Failure Links**: the opposite question, links with no backup.
