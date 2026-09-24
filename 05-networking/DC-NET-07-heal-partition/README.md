Source: New

# DC-NET-07 · Heal a Network Partition

## 1. Header
| | |
|---|---|
| Chip ID | DC-NET-07 |
| Difficulty | Medium |
| Pattern | Union-find |
| Track | Networking, Service Mesh & Resilience (NET) |
| Classic pattern | LeetCode 1319 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
At 03:40 the core switch in `dc-west-2` reboots after a firmware bug and does not come back.
The 12 access switches in row B are left in three isolated segments. Remote hands are on
site, but there is no spare cable: they can only unplug an existing redundant cable and
re-patch it somewhere else. The incident commander asks two questions: "Can we join all 12
switches with the cables we already have? If so, what is the minimum number of re-patches?"

## 3. Why This Is DevOps
**Production reality:** During a partition, the first question is "how many isolated pieces
are there?", and the second is "do we have the spare capacity to join them?". Every segment
with more links than it needs to stay connected has spare links: links that only close a loop.
Moving one spare joins two segments. So with enough links overall (at least n − 1), healing
takes exactly (segments − 1) moves. Union-find counts the segments in one pass over the links,
which also works while link-up events stream in.

**Where you see it:** incident runbooks for split-brain and partitioned clusters, network
topology checks after maintenance, cluster-membership tools that count islands of nodes that
can still see each other, and capacity checks ("do we have enough uplinks to survive losing X?").

**Reality check:** Real re-patching is limited by physical reach, port speeds and which
devices share a rack, so not any cable can go anywhere. The count here is the lower bound a
real plan starts from. Clusters split by a partition also need a quorum decision (which side
keeps serving), which this chip does not model.

**What breaks if you get it wrong:** If you promise the commander "one re-patch" when the
network really has three segments, there are two more rounds of calls to remote hands while
the outage continues. If you don't notice there are too few links, people spend an hour on a
plan that can never work instead of ordering cables right away.

## 4. Problem Statement
There are `n` devices numbered `0` to `n - 1`, and a list of undirected cables `(a, b)`. In one
**move**, you may unplug any existing cable and plug it in between any two devices. You cannot
add new cables.

Return the minimum number of moves needed so that every device can reach every other device.
If that is impossible with the cables available, return `-1`.

## 5. Input / Output format and Constraints
- `n: int`, `links: list[tuple[int, int]]`. Returns `int`.
- `1 <= n <= 10^5`, `0 <= len(links) <= 2 * 10^5`, `0 <= a, b < n`, `a != b`.
- The same pair may be linked more than once. An extra copy is a spare cable.

## 6. Examples
**Example 1: one re-patch**
```
min_link_moves(4, [(0, 1), (0, 2), (1, 2)])  -> 1
```
Devices 0, 1, 2 form a loop, so one of their links is spare. Move it to device 3.

**Example 2: not enough cables (edge case)**
```
min_link_moves(6, [(0, 1), (0, 2), (0, 3), (1, 2)])  -> -1
```
Six devices need at least 5 cables, and there are only 4.

**Example 3: already connected**
```
min_link_moves(3, [(0, 1), (1, 2)])  -> 0
```

## 7. Starter Code
See [`starter.py`](starter.py): `min_link_moves(n, links) -> int` with a docstring. The body is TODO.

```bash
make try CHIP=05-networking/DC-NET-07-heal-partition
```

## 8. Hints
1. **Nudge:** How many cables does it take to connect n devices at all? What can you say straight away if there are fewer?
2. **Pattern:** Count the connected pieces. Union-find merges the two sides of each cable and tells you when a cable joins devices that are already connected (a spare).
3. **Near-solution:** If `len(links) < n - 1`, return `-1`. Otherwise start with `segments = n` and subtract 1 for every cable whose ends are in different sets. The answer is `segments - 1`.

## 9. Solution
**Approach**
1. If there are fewer than `n - 1` cables, no plan can connect all `n` devices, so return `-1`.
2. Start with every device as its own segment in a union-find structure.
3. For each cable, find the roots of both ends. Different roots: merge them and reduce the
   segment count. Same root: the cable is spare.
4. With at least `n - 1` cables, there are always at least `segments - 1` spares, and each move
   joins two segments. So the answer is `segments - 1`.

**Why the spare count works out:** A forest joining `n` devices into `s` segments uses `n - s`
cables. The rest, `len(links) - (n - s) >= (n - 1) - (n - s) = s - 1`, are spares.

**Brute force:** Try re-patching cables one at a time and search over the resulting networks.
That is exponential. It also misses the point: the answer depends only on the segment count.

**Optimal code:** [`solution.py`](solution.py)

```python
def min_link_moves(n, links):
    if len(links) < n - 1:
        return -1
    parent, size = list(range(n)), [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]   # path halving
            x = parent[x]
        return x

    segments = n
    for a, b in links:
        ra, rb = find(a), find(b)
        if ra == rb:
            continue                         # spare cable
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra                      # union by size
        size[ra] += size[rb]
        segments -= 1
    return segments - 1
```

**Complexity**
- Time: O(n + E · α(n)), where α is the inverse Ackermann function, which is at most 4 for any real input. Each cable does two finds, and path halving with union by size keeps them near-constant.
- Space: O(n) for the `parent` and `size` arrays.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases:
- one move;
- not enough cables;
- a single device, and a network that is already connected;
- the boundary of exactly `n - 1` cables (a loop plus an isolated device, and a tree);
- duplicate cables counted as spares;
- the production-style switch-reboot partition, with and without spare uplinks;
- random networks up to 100,000 devices checked against an independent BFS component count.

## 11. Interview Talk Track
"First a quick check: n devices need at least n minus 1 cables, so with fewer I return -1
immediately. Otherwise the answer is just the number of isolated segments minus one, because
each re-patch joins two segments, and with at least n minus 1 cables there are always enough
spares. A spare is a cable that only closes a loop inside a segment. I count segments with
union-find: every cable joining two different sets reduces the count by one. With path halving
and union by size that's near-linear. In an incident, the segment count is also what I'd report
first: how many islands we have, and whether we have the cables to fix it without a delivery."

## 12. Level Up
1. **"Tell remote hands *which* cables to move and where."** Keep the spare cables found during
   the union pass, plus one representative device per segment. Pair spare `k` with joining
   segment `k` to segment `k + 1`. It is still O(n + E), and it gives a concrete re-patch list.
2. **"Links come up one by one as the switch recovers. Report the segment count live."**
   Union-find is incremental: process each link-up event as it arrives, and the count is always
   current. Links going **down** are harder, because union-find cannot split sets. Rebuild it
   periodically, or use an offline dynamic-connectivity approach for replays.
3. **"Cables can only be re-patched within the same row."** The problem becomes constrained:
   spares in row B can only join segments that have a device in row B. Model it as matching
   spares to the gaps they can reach. It is no longer a simple count, but the union-find pass is
   still the first step.

## 13. Related Chips
- **DC-NET-08 Find the Loop Link**: the same union-find, stopping at the first link that closes a loop.
- **DC-NET-13 Reachability Check**: "are these two in the same segment?" as a single query.
- **DC-NET-06 Single-Point-of-Failure Links**: the next question once the network is joined: which links are its SPOFs.
