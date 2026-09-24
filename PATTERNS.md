# Pattern Cheat Sheet

Two lines per pattern: **When you see X in DevOps, think Y**, and where it shows up in this book.

| Pattern | When you see… | …think | Chips |
|---|---|---|---|
| **Stack** | Nested brackets, `..` in paths, expressions with parentheses, undo-style "go back one level". | Push when you open a level, pop when you close it. What is on top is "where you are now". | OBS-07, OBS-17, SEC-01, SEC-02, SEC-03, SEC-20 |
| **Sliding window** | "In the last N seconds", "longest stretch where…", "at most k failures". | Two pointers mark the window. Grow the right edge, shrink the left edge when a rule breaks. Each item enters and leaves once. | OBS-02, OBS-16, SEC-16 |
| **Monotonic deque** | "Max (or min) over the last N samples", updated every tick. | Keep a deque in sorted order. Drop values that can never win again from the back, and expired ones from the front. | OBS-03, OBS-06 |
| **Two heaps** | A running median or percentile over a stream. | A max-heap holds the low half and a min-heap the high half. The answer sits on top of one or both. | OBS-08 |
| **Heap with lazy deletion** | A max/min that must survive late corrections or removals. | Push new values. When the top is stale (it no longer matches the source of truth), pop it and look again. | OBS-12 |
| **K-way merge** | Many streams, each already sorted (per-node logs, per-shard results). | Put the head of each stream in a min-heap. Pop the smallest, then push the next item from that stream. | OBS-14, OBS-15 |
| **Binary search** | Sorted history, "first bad commit", "value as of time T". | Halve the range each step. Decide carefully whether you want the first `>=` or the last `<=`. | OBS-01, REL-01, REL-08, PLAT-10 |
| **Binary search on the answer** | "Smallest rate / capacity / bandwidth that still finishes in time." | If a guess works, every bigger guess works too. Binary search the guess and write a `feasible(x)` check. | CAP-01, CAP-02, CAP-03 |
| **Topological sort** | Dependencies: apply order, build order, release order. | Kahn's algorithm: start with zero-dependency nodes, remove them, repeat. Nodes that are left over sit in a cycle. | PLAT-01, REL-03, REL-04, REL-05, REL-07 |
| **Cycle detection** | "A waits on B waits on A." Circular module or DAG references. | DFS with three colours (new / in progress / done). Reaching an "in progress" node means a cycle. Or: Kahn's sort visits fewer nodes than there are. | PLAT-02, REL-07 |
| **Transitive closure** | Many "does A depend on B, even indirectly?" questions. | Precompute reachability once (BFS from each node, or Floyd-Warshall). Each query is then a lookup. | REL-06 |
| **BFS** | Fewest hops, fewest steps, shortest path when every edge costs the same. | Explore level by level with a queue, and mark nodes visited when you enqueue them. | PLAT-05, SEC-12, NET-13 |
| **Multi-source BFS** | Several failure points spreading at the same time. | Put every source in the queue at step 0. The number of levels is the time to reach everything. | NET-12 |
| **Dijkstra** | Weighted shortest path: latency, cost, or best probability. | A min-heap of (distance, node). Finalise the smallest one first. It needs non-negative weights (for probabilities, maximise the product). | NET-04, NET-09 |
| **Bellman-Ford** | Shortest path with a hop or TTL limit. | Relax every edge k+1 times, using a copy of the previous round so each round adds at most one hop. | NET-10 |
| **Minimum spanning tree** | Connect every site for the least total cost. | Kruskal: sort edges and add each one unless union-find says it makes a loop. Prim: grow from one node with a heap. | NET-11 |
| **Tarjan's bridges** | "Which single link failure splits the network?" | DFS with discovery time and low-link. Edge u–v is a bridge if `low[v] > disc[u]`. | NET-06 |
| **Union-find** | Merging groups: linked identities, network segments, redundant links. | `find` with path compression and `union` by size or rank. "Already in the same set" means the new edge makes a loop. | SEC-13, SEC-14, NET-07, NET-08, NET-11, NET-13 |
| **Trie** | Matching request paths or keys by prefix, autocomplete, route tables. | One node per character or path segment. Lookup cost depends on the key's length, not on how many keys are stored. | NET-05, SEC-11 |
| **Reverse trie** | Shared suffixes (domains), or matching a pattern that ends at the newest character of a stream. | Insert words reversed, then walk backward from the newest character. | SEC-04, SEC-17 |
| **Backtracking** | "List every valid way to split or rebuild this." | Choose, recurse, un-choose. Prune a branch as soon as it cannot be valid. | NET-02 |
| **Dynamic programming** | Wildcard matching, longest chains, best split with overlapping sub-problems. | Define `dp[state]`, write the recurrence, fill it in dependency order. | SEC-08, REL-03, CAP-03 |
| **Difference array** | Many intervals adding load; "is capacity ever exceeded?" | +load at start and −load at end, then a running sum over the timeline. | SEC-06 |
| **Prefix sums** | Weighted random choice, range totals. | Cumulative totals make any range sum O(1). Binary search the prefix array to pick by weight. | PLAT-10 |
| **Two pointers** | In-place compaction, comparing two sequences, merging sorted data. | A read pointer and a write pointer (or one pointer per input) move forward and never go back. | SEC-07, REL-02, SEC-05 |
| **Bit manipulation** | CIDR blocks, subnet masks, alignment. | `x & -x` gives the largest power-of-two block that starts at x. Masks select the network bits. | SEC-09 |
| **Hash map + linked list** | LRU and LFU caches, eviction order. | The map gives O(1) lookup. A doubly linked list (one per frequency, for LFU) keeps eviction order with O(1) moves. | PLAT-06, PLAT-12 |
| **Locks and condition variables** | Producers faster than consumers, shared resources, deadlocks. | Wait on a condition in a `while` loop and notify when state changes. Always take locks in one global order. | PLAT-13, PLAT-14 |

Other patterns used once: hash map + expiry (SEC-18), bucketing (OBS-11), tree
serialization + hashing (OBS-04), string state machine (SEC-19), string parsing (NET-01),
directory tree design (OS-01), string scan (OS-02).
