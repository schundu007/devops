Source: Handbook #45 Course Schedule — `apps/camora/src/data/capra/top100/45.json` (copied unchanged as `handbook.json`)

# DC-PLAT-02 · Circular Dependency Detector

## 1. Header `DevOps layer`
| | |
|---|---|
| Chip ID | DC-PLAT-02 |
| Difficulty | Medium |
| Pattern | Cycle detection |
| Track | Platform Engineering, Scheduling & Allocation (PLAT) |
| Classic pattern | LeetCode 207 |
| Premium | No |
| Time box | 25 min |
| Source | Handbook #45 Course Schedule |

## 2. The Scenario `DevOps layer`
A CI check runs on every change to `.argo/release.yaml`, the Argo Workflows DAG for the `ledger`
service: `checkout → build → {unit-test, image-push} → deploy-staging → smoke-test`. A teammate
adds `build` depends on `smoke-test` "so the build can reuse the smoke-test cache". Now `build`
waits for `smoke-test`, which waits (through `deploy-staging` and `image-push`) for `build`, so nothing can ever start.
The check must catch this before merge, in milliseconds, for DAGs with thousands of steps.

**Mapping: DevOps term → handbook name**

| DevOps term | Handbook name |
|---|---|
| workflow step, Terraform resource, Airflow task | course |
| number of steps | `numCourses` |
| "step A depends on step B" | `prerequisites[i] = [A, B]` |
| the DAG is runnable (no cycle) | `true` |
| the DAG contains a cycle | `false` |

## 3. Why This Is DevOps `DevOps layer`
**Production reality:** Every system that runs dependent work has to refuse cycles, because a
cycle means every step in it waits forever. Terraform reports `Error: Cycle: …` during plan and
lists the resources involved. Airflow raises `AirflowDagCycleException` when it loads a DAG with a
cycle. Argo Workflows rejects DAG templates whose dependencies loop. Running the same check in CI
catches the mistake at review time instead of at 2 a.m.

**Where you see it:** Terraform plan, Airflow DAG parsing, Argo Workflows validation, Bazel and
Make (circular target dependencies), package managers resolving dependencies.

**Reality check:** Real tools report *which* nodes form the cycle, because "there is a cycle"
alone is hard to fix in a 3,000-step DAG. With Kahn's algorithm, the nodes never removed are the
ones on or behind a cycle. A DFS that finds a back edge can print the exact loop.

**What breaks if you get it wrong:** A missed cycle merges cleanly and then deadlocks in
production: the release workflow sits "Pending" forever, nothing fails loudly, and the fix
waits for someone to notice that no deploy has happened in a day.

## 4. Problem Statement `From handbook`
You must take `numCourses` courses, labelled `0` to `numCourses - 1`. Each entry `prerequisites[i] = [a, b]` means course `b` has to be completed before course `a` can be started.

Return `true` if there is some order in which all the courses can be finished, and `false` otherwise.

## 5. Input / Output format and Constraints
**Input / Output format `(added)`:** `canFinish(numCourses: int, prerequisites: List[List[int]]) -> bool`.
In the handbook this is a module-level function, not a `Solution` method.

**Constraints `From handbook`**
- 1 ≤ numCourses ≤ 2000
- 0 ≤ prerequisites.length ≤ 5000
- prerequisites[i].length == 2
- 0 ≤ a, b < numCourses
- All the pairs prerequisites[i] are unique.

## 6. Examples `From handbook`
**Example 1 — Single row/column · Answer exists**
```
Input:  numCourses = 2, prerequisites = [[1, 0]]
Output: true
```
Take course 0, then course 1.

**Example 2 — No answer · 2 prerequisites**
```
Input:  numCourses = 2, prerequisites = [[1, 0], [0, 1]]
Output: false
```
Each course requires the other first, so neither can ever be started.

## 7. Starter Code `(added)`
The handbook builds its starter from the problem's function signature and stores no starter file. See
[`starter.py`](starter.py): the same `canFinish` function, with a TODO body.

```bash
make try CHIP=03-platform/DC-PLAT-02-circular-dependency
```

## 8. Hints `From handbook`
1. Model the courses as a directed graph; the courses can all be finished exactly when that graph has no cycle.
2. Use Kahn's topological sort (BFS on in-degrees) or a DFS with three colours (unvisited / in progress / done).
3. With Kahn's algorithm, start from all courses with in-degree 0, repeatedly remove one and decrement its dependants' in-degrees, and check whether the number of removed courses equals numCourses.

## 9. Solution `From handbook`
#### DFS Cycle Detection
Build adjacency list and use DFS with 3 states (unvisited, visiting, visited) to detect cycles.

- Three states: unvisited, visiting (in current path), visited
- Cycle detected if we revisit a node in visiting state
- DFS explores all dependencies

Time: O(V + E) · Space: O(V + E)

```python
def canFinish(numCourses, prerequisites):
    graph = [[] for _ in range(numCourses)]
    for course, prereq in prerequisites:
        graph[course].append(prereq)
    # 0: unvisited, 1: visiting, 2: visited
    state = [0] * numCourses

    def dfs(node):
        if state[node] == 1:
            return False  # cycle
        if state[node] == 2:
            return True
        state[node] = 1
        for neighbor in graph[node]:
            if not dfs(neighbor):
                return False
        state[node] = 2
        return True

    for i in range(numCourses):
        if not dfs(i):
            return False
    return True
```

#### BFS Topological Sort (Kahn's Algorithm)
Use BFS with in-degree tracking. Process nodes with in-degree 0. If all nodes processed, no cycle exists.

- Kahn's algorithm for topological sort
- Start with nodes that have no prerequisites
- If count equals numCourses, no cycle
- BFS processes nodes level by level

Time: O(V + E) · Space: O(V + E)

```python
from collections import deque

def canFinish(numCourses, prerequisites):
    graph = [[] for _ in range(numCourses)]
    in_degree = [0] * numCourses
    for course, prereq in prerequisites:
        graph[prereq].append(course)
        in_degree[course] += 1
    queue = deque(i for i in range(numCourses) if in_degree[i] == 0)
    count = 0
    while queue:
        node = queue.popleft()
        count += 1
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    return count == numCourses
```

`solution.py` is the handbook's **BFS Topological Sort (Kahn's Algorithm)** solution, copied
unchanged. Neither handbook solution is marked "Optimal" (both are O(V + E)), so the last one
listed was used. The handbook's Java, C++, Go and JavaScript versions are in `handbook.json` → `solutions[].code`.

## 10. Tests
**From handbook:** 29 cases in `handbook.json` → `tests`, run unchanged by `test_chip.py`.

**`(added)`** [`test_chip.py`](test_chip.py) wraps those cases in pytest (calling the
module-level `canFinish`). It runs **every** Python solution from the handbook (the Step 3
check). It adds DevOps-layer cases: the Argo DAG with and without the bad edge, 50 independent
steps, 150 random small graphs checked against a separate "peel off ready nodes" brute force,
and a 2,000-node DAG that turns cyclic when one edge is reversed.

## 11. Interview Talk Track `DevOps layer`
"This is the check Terraform, Airflow and Argo all run before they execute a graph: is there a
cycle? I use Kahn's algorithm. Count each step's unfinished dependencies, queue the ones at
zero, and keep removing them and decrementing their dependents. If every step gets removed,
the graph is a DAG. If some never reach zero, they're in a cycle or waiting behind one. It's
O(V + E), so it's cheap enough to run on every commit. The DFS version, with three colours,
finds a back edge instead, and has the bonus that it can print the exact loop, which is what you
want in the CI error message."

## 12. Level Up `DevOps layer`
1. **"Tell the author which steps form the cycle."** Run DFS with colours
   (unvisited / on the stack / done) and keep the current path. When you meet an "on the
   stack" node, the path from that node to the current one is the cycle. Print it the way
   Terraform does: `Cycle: build, image-push, deploy-staging, smoke-test`.
2. **"The graph is edited one edge at a time, and each edit must be checked quickly."**
   Adding edge `A depends on B` creates a cycle only if `A` can already reach `B` along the
   dependency direction, so one BFS from `A` answers it. That costs only the size of `A`'s
   reachable part, not the whole graph.
3. **"Steps come from 40 repos, each with its own file."** Build the combined graph in one
   place (a monorepo check or a central registry). A cycle can span repos even though each
   file is acyclic on its own.

## 13. Related Chips `DevOps layer`
- **DC-PLAT-01 IaC Apply Order**: the same walk, returning the order instead of yes/no.
- **DC-REL-07 Safe Services Finder**: find every node that can never be caught in a cycle.
- **DC-REL-06 Change Impact Query**: reachability queries on a dependency graph.
