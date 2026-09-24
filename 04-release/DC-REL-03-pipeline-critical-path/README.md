Source: New

# DC-REL-03 · Pipeline Critical Path ★

## 1. Header
| | |
|---|---|
| Chip ID | DC-REL-03 ★ (start here) |
| Difficulty | Hard |
| Pattern | Topological sort + DP |
| Track | Release & CI/CD (REL) |
| Classic pattern | LeetCode 2050 |
| Premium | No |
| Time box | 40 min |
| Source | New |

## 2. The Scenario
The `web-monorepo` pipeline takes 24 minutes, and the team wants it under 20. It runs
`checkout` (1 min) → `build` (6) → then `unit` (4), `integration` (14) and `lint` (2) in
parallel → `deploy` (3). Someone spent a week cutting unit tests from 4 minutes to 1, and the
pipeline still takes 24. You need to compute the real minimum time and show which stages
decide it.

## 3. Why This Is DevOps
**Production reality:** A CI/CD pipeline is a dependency graph of stages. A stage starts as
soon as all its dependencies finish, and independent stages run in parallel. So the total
time is not the sum of all stages: it is the longest dependency chain, the **critical path**.
Making a stage faster helps only if that stage is on the critical path. Everything else
already has slack.

**Where you see it:** GitHub Actions jobs with `needs:`, GitLab CI `needs:` (DAG pipelines),
Argo Workflows DAG templates, Tekton pipelines with `runAfter`, and build systems that run
independent actions in parallel.

**Reality check:** This chip assumes unlimited runners. Real pipelines queue when the runner
pool is full, so the actual time can be longer than the critical path (see DC-PLAT-03 for
runner sizing). Stage times also vary from run to run, so teams track p50 and p90 per stage.

**What breaks if you get it wrong:** Teams spend weeks speeding up stages that are not on the
critical path. The pipeline does not get faster, and the real bottleneck stays unfixed.

## 4. Problem Statement
A pipeline has `n` stages numbered `0..n-1`. Stage `i` takes `duration[i]` minutes. Each pair
`(a, b)` in `deps` means stage `b` cannot start until stage `a` has finished. Any number of
stages can run at the same time, and the dependencies contain no cycles.

Return the minimum number of minutes needed to finish every stage.

## 5. Input / Output format and Constraints
- `pipeline_time(n: int, deps: list[tuple[int, int]], duration: list[int]) -> int`
- `0 <= n <= 5 * 10^4`, `len(duration) == n`, `1 <= duration[i] <= 10^4`.
- `0 <= len(deps) <= 5 * 10^4`, with `0 <= a, b < n` and `a != b`.
- The dependency graph is a DAG (no cycles).

## 6. Examples
**Example 1: a diamond**
```
n = 4, deps = [(0,1), (0,2), (1,3), (2,3)], duration = [2, 3, 10, 1]
pipeline_time(...) -> 13
```
The path 0 → 2 → 3 takes 2 + 10 + 1 = 13. The path through stage 1 takes only 6.

**Example 2: no dependencies (edge case)**
```
n = 4, deps = [], duration = [5, 1, 9, 3]
pipeline_time(...) -> 9
```
Everything runs in parallel, so the slowest stage decides.

**Example 3: the scenario**
```
checkout 1 -> build 6 -> {unit 4, integration 14, lint 2} -> deploy 3
pipeline_time(...) -> 24        # 1 + 6 + 14 + 3
```
Cutting `unit` to 1 minute still gives 24. Cutting `integration` to 8 minutes gives 18.

## 7. Starter Code
See [`starter.py`](starter.py): `pipeline_time(n, deps, duration)` with a docstring and type hints.

```bash
make try CHIP=04-release/DC-REL-03-pipeline-critical-path
```

## 8. Hints
1. **Nudge:** When can a stage start at the earliest? What does that depend on?
2. **Pattern:** `earliest_start(b) = max(finish(a))` over its dependencies. Compute stages in an
   order where every dependency comes first: a topological sort.
3. **Near-solution:** Run Kahn's algorithm. When you take stage `s` off the queue, set
   `finish = start[s] + duration[s]`, and for each child set `start[child] = max(start[child], finish)`.
   The answer is the largest `finish`.

## 9. Solution
**Approach**
1. Build the child lists and count each stage's unfinished dependencies.
2. Put every stage with no dependencies in a queue. Its earliest start is 0.
3. Take a stage off the queue. Its finish time is its start plus its duration.
4. Push that finish time to each child: `start[child] = max(start[child], finish)`. When a
   child has no unfinished dependencies left, add it to the queue.
5. The answer is the largest finish time seen.

**Brute force:** Try every path from a stage with no dependencies to a final stage and take
the longest. The number of paths can grow exponentially in a dense DAG.

**Optimal code:** [`solution.py`](solution.py)

```python
def pipeline_time(n, deps, duration):
    children = [[] for _ in range(n)]
    waiting = [0] * n
    for a, b in deps:
        children[a].append(b)
        waiting[b] += 1
    start = [0] * n
    ready = deque(i for i in range(n) if waiting[i] == 0)
    total = 0
    while ready:
        s = ready.popleft()
        finish = start[s] + duration[s]
        total = max(total, finish)
        for nxt in children[s]:
            start[nxt] = max(start[nxt], finish)   # wait for the slowest dependency
            waiting[nxt] -= 1
            if waiting[nxt] == 0:
                ready.append(nxt)
    return total
```

**Complexity**
- Time: O(n + E), because each stage is queued once and each dependency is relaxed once.
- Space: O(n + E) for the child lists, counters and queue.

## 10. Tests
[`test_chip.py`](test_chip.py) has 6 tests: a diamond, an empty pipeline and a single stage,
all stages in parallel, a chain, the CI scenario (speeding up a stage off the critical path
changes nothing, and speeding up one on it does), and five random 400-stage DAGs with
shuffled labels checked against a separate relaxation method.

## 11. Interview Talk Track
"A pipeline is a DAG of stages, and with enough runners the total time is the longest path
through that DAG, the critical path. A stage can start only when its slowest dependency
finishes, so earliest start equals the max finish time among its dependencies. That's a DP,
and I need to evaluate it in dependency order, which a topological sort gives me. I run
Kahn's algorithm, and when a stage comes off the queue I compute its finish time and push it
to its children. The answer is the largest finish time. It's O(V + E). In practice this is how
I'd decide where to spend optimisation effort: only critical-path stages matter. Cutting unit
tests from four minutes to one changed nothing here, while cutting integration tests saved six minutes."

## 12. Level Up
1. **"Also return which stages are on the critical path."** For each stage, remember which
   dependency set its start time (the argmax). Walk back from the stage with the largest
   finish time. That chain is the critical path to show on the dashboard.
2. **"Only 3 runners are available."** Now it is a scheduling problem, and the exact answer is
   NP-hard in general. List scheduling is the practical choice: when a runner frees up, start
   the ready stage with the longest remaining path to the end. That is a strong heuristic.
3. **"Stage durations vary: integration is 14 minutes at p50 and 25 at p90."** Compute the
   critical path with p90 durations to plan for bad days, or run a Monte Carlo simulation over
   sampled durations. Different stages can be critical at p50 and at p90.

## 13. Related Chips
- **DC-PLAT-01 IaC Apply Order**: the same topological sort, returning an order instead of a time.
- **DC-REL-04 Grouped Release Order**: topological sorting at two levels.
- **DC-PLAT-03 Minimum CI Runners**: how many runners the parallelism actually needs.
