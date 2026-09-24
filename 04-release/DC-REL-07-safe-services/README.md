Source: New

# DC-REL-07 · Safe Services Finder

## 1. Header
| | |
|---|---|
| Chip ID | DC-REL-07 |
| Difficulty | Medium |
| Pattern | Reverse graph + topological sort |
| Track | Release & CI/CD (REL) |
| Classic pattern | LeetCode 802 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
After a refactor, the staging environment `stg-eu-1` won't come up. Each service waits for
the services it depends on before it starts, like init containers that block until a
dependency answers its health check. `billing` now waits for `ledger`, and `ledger` was
changed to wait for `billing`. `gateway` waits for `billing`, so it hangs too. Before the next
deploy you need the list of services that are guaranteed to start: those whose every chain of
waits ends cleanly.

## 3. Why This Is DevOps
**Production reality:** Startup ordering forms a directed graph, where an edge means "waits
for". A service that waits on nothing can start. A service can start once everything it waits
for can start. A cycle of waits never resolves, and neither does anything that waits on the
cycle, even if it is not part of it. Finding the services that are guaranteed to start is a
topological sort run backward from the services with no dependencies.

**Where you see it:** Kubernetes init containers that wait for a dependency, Docker Compose
`depends_on`, systemd unit ordering (`After=` / `Requires=`), and Helm charts with wait-for
jobs. Terraform and Argo reject cycles when validating the graph.

**Reality check:** Kubernetes has no built-in startup graph. Pods just crash-loop or wait
forever, so nobody sees the cycle. systemd detects ordering cycles at boot and breaks them by
deleting one job from the transaction, then logs it. Docker Compose refuses to start when
`depends_on` has a cycle. This chip finds both the cycle and everything stuck behind it,
before the deploy.

**What breaks if you get it wrong:** A release declares `gateway` healthy-by-design, but it
waits on the `billing` ⇄ `ledger` deadlock. The environment sits half up for an hour while
people look at crash-looping pods one by one.

## 4. Problem Statement
Services are numbered `0..n-1`. `waits_on[i]` lists the services that service `i` waits for
before it can start.

A service is **safe** if every chain of waits starting from it eventually reaches a service
that waits on nothing. In other words, no chain from it ever enters a cycle. Return all safe
services in ascending order.

## 5. Input / Output format and Constraints
- `safe_services(waits_on: list[list[int]]) -> list[int]`, sorted ascending.
- `0 <= n <= 10^4`, the total number of waits is at most `4 * 10^4`.
- Entries of `waits_on[i]` are distinct and in `0..n-1`. They may include `i` itself (a service waiting on itself).

## 6. Examples
**Example 1**
```
waits_on = [[1], [2], [0], [4], [], [1]]
safe_services(...) -> [3, 4]
```
`0 → 1 → 2 → 0` is a cycle. `5` is not in the cycle, but it waits on `1`, so it is stuck too.
`3 → 4` ends at `4`, which waits on nothing.

**Example 2: a service that waits on itself (edge case)**
```
waits_on = [[0]]
safe_services(...) -> []
```

**Example 3: one bad branch is enough**
```
waits_on = [[1, 2], [], [3], [2]]
safe_services(...) -> [1]
```
`0` waits on the safe `1`, but also on `2`, which is in a cycle with `3`.

## 7. Starter Code
See [`starter.py`](starter.py): `safe_services(waits_on)` with a docstring and type hints.

```bash
make try CHIP=04-release/DC-REL-07-safe-services
```

## 8. Hints
1. **Nudge:** Which services are safe without thinking at all? When does a service become safe after that?
2. **Pattern:** A service is safe once *all* of its dependencies are safe. Reverse the edges
   and run Kahn's algorithm, starting from the services that wait on nothing.
3. **Near-solution:** Set `pending[i] = len(waits_on[i])` and build `waited_by` lists. Queue
   every service with `pending == 0`. Pop one, mark it safe, and decrement each service that
   waits on it. Queue any that reach 0.

## 9. Solution
**Approach**
1. Count, for each service, how many of its dependencies are not yet proven safe:
   `pending[i] = len(waits_on[i])`.
2. Build the reverse graph: for every wait `i → d`, record that `d` is waited on by `i`.
3. Start a queue with every service that waits on nothing. They are safe.
4. Pop a safe service. For each service waiting on it, decrement `pending`. When `pending`
   hits 0, all of that service's dependencies are safe, so it is safe too: queue it.
5. Services never marked safe are in a cycle or lead into one.

**Brute force:** From each service, explore everything it can reach and check whether any of
it lies on a cycle. That is O(n·(n + E)): fine for 20 services, but too slow as a CI check on
thousands of workloads.

**Optimal code:** [`solution.py`](solution.py)

```python
def safe_services(waits_on):
    n = len(waits_on)
    pending = [len(deps) for deps in waits_on]
    waited_by = [[] for _ in range(n)]
    for s, deps in enumerate(waits_on):
        for d in deps:
            waited_by[d].append(s)
    ready = deque(s for s in range(n) if pending[s] == 0)
    safe = [False] * n
    while ready:
        d = ready.popleft()
        safe[d] = True
        for s in waited_by[d]:
            pending[s] -= 1
            if pending[s] == 0:        # every dependency of s is safe
                ready.append(s)
    return [s for s in range(n) if safe[s]]
```

A DFS with three colours (unvisited, in progress, done) solves it too: any service that
reaches an "in progress" service is unsafe.

**Complexity**
- Time: O(n + E), because each service is queued once and each wait is examined once.
- Space: O(n + E) for the reverse graph, counters and queue.

## 10. Tests
[`test_chip.py`](test_chip.py) has 6 tests: a graph with a cycle, a clean chain and a service
leading into the cycle, empty and single inputs (including waiting on itself), an acyclic
graph, one bad branch, an eight-service staging environment with a `billing` ⇄ `ledger`
deadlock, and five random 300-service graphs checked against a reachability-based method.

## 11. Interview Talk Track
"I'm modelling startup waits as a directed graph. A service is safe only if every chain of
waits from it ends at something that waits on nothing. The trick is working backward.
Services with no dependencies are safe right away. Then a service becomes safe exactly when
its last unproven dependency is proven safe. So I reverse the edges, count the pending
dependencies for each service, and run Kahn's algorithm from the no-dependency services.
Whatever never reaches zero is either in a cycle or waits on one. That second group matters:
`gateway` isn't in the deadlock, but it's stuck behind it. It's O(V + E), fast enough as a
pre-deploy check in CI."

## 12. Level Up
1. **"Tell the team *which* cycle to break."** Run Tarjan's or Kosaraju's strongly connected
   components on the unsafe services. Each component with more than one service (or a self-wait)
   is a cycle to report. The rest are just stuck behind one. Fixing one edge per cycle is
   enough.
2. **"Some waits are soft: a service can start degraded without that dependency."** Keep
   only the hard waits in this graph. Soft waits never block startup, so they cannot create a
   deadlock, but record them to report degraded starts.
3. **"Run this in CI across 3,000 Helm releases."** Pull the wait edges from manifests
   (init-container targets and chart annotations), build one graph for the whole environment,
   and fail the pipeline if any service is unsafe. It runs in linear time, well within a few seconds.

## 13. Related Chips
- **DC-PLAT-02 Circular Dependency Detector**: the yes/no version, "is there any cycle?".
- **DC-REL-05 Buildable Artifacts**: the same forward propagation from things that are already ready.
- **DC-PLAT-14 Deadlock-Free Lock Ordering**: preventing cycles of waits at runtime instead of detecting them.
