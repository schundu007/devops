Source: New

# DC-REL-05 · Buildable Artifacts

## 1. Header
| | |
|---|---|
| Chip ID | DC-REL-05 |
| Difficulty | Medium |
| Pattern | Topological sort |
| Track | Release & CI/CD (REL) |
| Classic pattern | LeetCode 2115 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
At 09:40 the internal package mirror loses its `node-20` toolchain, and the release job for
`shop-monorepo` has to go out today. The release is built from six artifacts: `api-bin`,
`api-image`, `web-bundle`, `web-image`, `helm-chart` and `release-bundle`. Some need base
images or toolchains, and some need other artifacts. Before anyone starts a 40-minute build,
work out which artifacts can still be produced with what is available right now.

## 3. Why This Is DevOps
**Production reality:** Build systems see targets as a dependency graph. A target can be
built once all its inputs exist, and each new output can unlock more targets. Starting from
what is available (base images, pinned packages, source trees) and following that chain
forward is a topological sort. A target whose inputs never all appear, because one is
missing or the target is part of a cycle, is never built.

**Where you see it:** Make (a target's prerequisites are built first), Bazel's target and
action graph, Nix derivations, Docker multi-stage builds, and CI release jobs that assemble
images, charts and bundles.

**Reality check:** Real build tools usually work backward from the target you ask for, not
forward from everything available, and they cache outputs by a hash of the inputs. This chip
works forward to answer "what can I build right now?", which is the question during an outage.

**What breaks if you get it wrong:** The pipeline starts a long build, fails 35 minutes in on
a missing base image, and the release window closes. A missed cycle is worse: it can make a
build hang, or make the tool report "up to date" when nothing was built.

## 4. Problem Statement
You get a list of artifact names. `inputs[i]` lists everything `artifacts[i]` needs. You also
get `available`: things you already have, such as base images and toolchains.

An artifact can be built when every one of its inputs is available or is another artifact
that can be built. Return all artifacts that can be built, in any order.

## 5. Input / Output format and Constraints
- `buildable(artifacts: list[str], inputs: list[list[str]], available: list[str]) -> list[str]`
- `0 <= len(artifacts) == len(inputs) <= 10^4`, `0 <= len(inputs[i]) <= 100`, `len(available) <= 10^4`.
- Names in `artifacts` are distinct, and names in `available` are distinct. The two lists never share a name.
- `inputs[i]` holds distinct names and never contains `artifacts[i]` itself.
- The output may be in any order.

## 6. Examples
**Example 1: a chain**
```
artifacts = ["app-image", "wheel-cache"]
inputs    = [["base-python", "wheel-cache"], ["requirements.lock", "pip"]]
available = ["base-python", "requirements.lock", "pip"]
buildable(...) -> ["wheel-cache", "app-image"]
```
`wheel-cache` is built first, and that unlocks `app-image`.

**Example 2: a cycle (edge case)**
```
artifacts = ["a", "b", "c"], inputs = [["b"], ["a"], ["base"]], available = ["base"]
buildable(...) -> ["c"]
```
`a` and `b` each wait for the other, so neither is ever built.

**Example 3: no inputs**
```
artifacts = ["docs-site"], inputs = [[]], available = []
buildable(...) -> ["docs-site"]
```

## 7. Starter Code
See [`starter.py`](starter.py): `buildable(artifacts, inputs, available)` with a docstring and type hints.

```bash
make try CHIP=04-release/DC-REL-05-buildable-artifacts
```

## 8. Hints
1. **Nudge:** Which artifacts can you build right now, using only `available`? What changes once you have built them?
2. **Pattern:** For each artifact, count the inputs it is still missing. When a name becomes
   available, decrease the count of everything that needs it. Kahn's algorithm with names as nodes.
3. **Near-solution:** Map each name to the artifacts that use it, and start a queue with
   `available` plus any artifact that has no inputs. Pop a name and decrement `missing[i]` for each user `i`. When a count reaches
   0, record `artifacts[i]` and push it onto the queue.

## 9. Solution
**Approach**
1. For every artifact, count its inputs: `missing[i]`.
2. Build a reverse index: input name → the artifacts that need it.
3. Put everything in `available` on a queue, plus any artifact with no inputs (it is buildable at once).
4. Pop a name. For each artifact that needs it, decrement `missing`. When `missing` hits 0,
   the artifact is buildable: record it and push its name, because it may feed others.
5. Artifacts whose count never reaches 0 are missing an input or sit in a cycle.

**Brute force:** Sweep all artifacts again and again, adding any whose inputs are all present,
until a sweep adds nothing. That can take O(A) sweeps of O(total inputs) each, so it is quadratic.

**Optimal code:** [`solution.py`](solution.py)

```python
def buildable(artifacts, inputs, available):
    missing = [len(ins) for ins in inputs]
    used_by = defaultdict(list)                 # input name -> artifacts that need it
    for i, ins in enumerate(inputs):
        for name in ins:
            used_by[name].append(i)
    built = [a for a, m in zip(artifacts, missing) if m == 0]  # no inputs: build at once
    ready = deque(available)
    ready.extend(built)
    while ready:
        name = ready.popleft()
        for i in used_by[name]:
            missing[i] -= 1
            if missing[i] == 0:                 # last input arrived: build it
                built.append(artifacts[i])
                ready.append(artifacts[i])      # it can now feed other artifacts
    return built
```

An artifact with no inputs is never decremented, because no name points to it. That is why
such artifacts go straight into `built` and `ready` at the start. Forgetting this is the
most common bug here.

**Complexity**
- Time: O(A + I + V), where A is the number of artifacts, I the total number of inputs and V
  the number of available names. Every name is queued at most once and every input edge is used once.
- Space: O(A + I + V) for the reverse index, the counters and the queue.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 tests: a chain, empty and single inputs, a missing input
that blocks everything downstream, a cycle, an artifact with no inputs, the monorepo release
after the mirror loses `node-20`, and five random 2,000-artifact graphs checked against a
repeated-sweep method.

## 11. Interview Talk Track
"The question is: given what's on the mirror right now, what can the release job still build?
It's a topological sort where the starting nodes are the available things. For each artifact
I count its missing inputs, and I keep a reverse index from each name to the artifacts that
need it. I start a queue with everything available. Each time a name comes off, I decrement
its users, and when one reaches zero it's buildable, so it joins the queue and can unlock
others. Anything whose count never reaches zero is missing an input or stuck in a cycle.
That's linear in the size of the graph. Make and Bazel think in the same graph terms, but
they work backward from the target you ask for and cache outputs by input hash."

## 12. Level Up
1. **"Also explain *why* `web-image` can't be built."** For each unbuildable artifact, list its
   inputs that are neither available nor buildable. Follow those back to the first missing
   leaves (here `node-20`). That is the error message the release manager actually needs.
2. **"Build them as fast as possible on 16 workers."** The queue already gives the order in
   which artifacts become buildable. Hand each ready artifact to a free worker, and run the
   longest remaining chain first. DC-REL-03 computes the critical path this needs.
3. **"Rebuild only what changed after a commit."** Hash each artifact's inputs, and skip an
   artifact whose input hash matches the cached output. Only artifacts downstream of a
   change get rebuilt. This is the core idea of content-addressed build caches.

## 13. Related Chips
- **DC-PLAT-01 IaC Apply Order**: Kahn's algorithm over resources.
- **DC-REL-06 Change Impact Query**: the reverse question, what depends on a changed input.
- **DC-REL-07 Safe Services Finder**: nodes stuck because they depend on a cycle.
