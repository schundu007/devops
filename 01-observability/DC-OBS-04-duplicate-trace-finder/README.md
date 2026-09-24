Source: New

# DC-OBS-04 · Duplicate Stack Trace Finder

## 1. Header
| | |
|---|---|
| Chip ID | DC-OBS-04 |
| Difficulty | Medium |
| Pattern | Tree serialization + hashing |
| Track | Observability & SRE (OBS) |
| Classic pattern | LeetCode 652 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
03:40, and `payments-worker` is failing. The error tracker has received 18,000 events in ten
minutes, and each one carries a call tree: `payments-worker` called `charge`, which called
`stripe.client.post`, which called `socket.recv` and then raised `TimeoutError`. Nobody can read
18,000 trees. You need to collapse identical call paths into one fingerprint, so the incident
channel sees "1 issue, 17,400 events" plus a few rare ones, instead of a wall of noise.

## 3. Why This Is DevOps
**Production reality:** During an outage, the same failure produces thousands of identical
stack traces. Error trackers turn each trace into a canonical text form, hash it, and group
events with the same hash into one issue: this is the event's "fingerprint". Profilers do the
same thing to call trees: identical call paths are merged so a flame graph shows one bar with a
count instead of thousands of copies. Finding repeated subtrees is how you spot the hot or failing path.

**Where you see it:** Sentry issue grouping (fingerprints), pprof and flame graphs (merged call
paths), Grafana Pyroscope, and Alertmanager (it identifies an alert by a hash of its label set,
a similar idea for de-duplication).

**Reality check:** Sentry fingerprints a single trace, which is a list of frames. A list is a
tree where every node has one child, so it is a special case of this chip. Real grouping also
normalises frames first, for example by dropping frames that are not your own code, so
unrelated noise does not split one issue into many.

**What breaks if you get it wrong:** If the canonical form is ambiguous (for example
`a(b,c)` and `a(bc)` print the same), different failures merge into one issue and a second bug
hides inside the first. If it is too strict, one bug splits into 500 issues and the alert
floods the on-call channel.

## 4. Problem Statement
A call tree is made of `Frame` nodes. Each frame has a function `name` and an ordered list
of `children`: the calls it made, in order.

Two subtrees have the **same shape** if their roots have the same name and the same number of
children, and each pair of children, taken in order, also has the same shape.

Return the canonical text of every shape that appears **two or more times** anywhere in the
tree. Report each shape once, sorted. Canonical text is `name` for a leaf and
`name(child1,child2,...)` otherwise; `render(frame)` in the starter builds it.

## 5. Input / Output format and Constraints
- Input: `root: Frame | None`. `Frame(name: str, children: list[Frame])`.
- Output: `list[str]`, sorted ascending, no repeats.
- Up to `10^5` frames. The tree can be up to `10^5` frames deep (runaway recursion is a real
  trace shape), so avoid recursion in the main walk.
- Names are non-empty and contain no `(`, `)` or `,`.

## 6. Examples
**Example 1: repeated leaf**
```
handler
├── db.query
└── db.query
-> ["db.query"]
```

**Example 2: nested repeats**
```
main
├── retry ── http.get ── dns.resolve
├── retry ── http.get ── dns.resolve
└── retry ── http.get ── dns.resolve
-> ["dns.resolve", "http.get(dns.resolve)", "retry(http.get(dns.resolve))"]
```
Each shape is reported once, even though it appears three times.

**Example 3: order matters (edge case)**
```
main
├── a ── b, c
└── a ── c, b
-> ["b", "c"]
```
The two `a` subtrees contain the same frames but make the calls in a different order, so they are different traces.

## 7. Starter Code
See [`starter.py`](starter.py): the `Frame` class, a `render` helper, and
`find_duplicate_subtrees(root)` with a TODO body.

```bash
make try CHIP=01-observability/DC-OBS-04-duplicate-trace-finder
```

## 8. Hints
1. **Nudge:** You can only compare a subtree once you know what its children look like. Which
   traversal order gives you the children first?
2. **Pattern:** Post-order traversal, then a hash map from each subtree's canonical form to how
   many times it appears.
3. **Near-solution:** Building full strings costs O(n²) on deep trees. Instead, give each
   distinct shape a small integer ID: the key is `(name, tuple of child IDs)`. Count the IDs, and
   render text only for the IDs seen 2+ times.

## 9. Solution
**Approach**
1. Walk the tree in post-order using an explicit stack, so deep trees do not overflow.
2. For each frame, build the key `(name, (child_id_1, child_id_2, ...))`.
3. Look the key up in a map. A new key gets the next integer ID. Equal keys mean equal shapes.
4. Count each ID, and remember one frame per ID.
5. Render the canonical text for the IDs with count ≥ 2 and sort.

**Brute force:** Render every subtree in full and count the strings. Each render can be O(n)
long, so the total is O(n²) time and memory, which is too slow for a deep trace.

**Optimal code:** [`solution.py`](solution.py)

```python
def find_duplicate_subtrees(root: Frame | None) -> list[str]:
    if root is None:
        return []
    shape_id: dict[tuple[str, tuple[int, ...]], int] = {}
    count: dict[int, int] = {}
    first: dict[int, Frame] = {}
    ids: dict[int, int] = {}                      # id(frame) -> shape id

    stack = [(root, False)]                       # iterative post-order
    while stack:
        node, children_done = stack.pop()
        if not children_done:
            stack.append((node, True))
            for child in reversed(node.children):
                stack.append((child, False))
            continue
        key = (node.name, tuple(ids[id(c)] for c in node.children))
        sid = shape_id.setdefault(key, len(shape_id))
        ids[id(node)] = sid
        count[sid] = count.get(sid, 0) + 1
        first.setdefault(sid, node)

    return sorted(render(first[sid]) for sid, n in count.items() if n >= 2)
```

**Complexity**
- Time: O(n) to build IDs, because every frame's key has one entry per child, so the total
  key size is O(n). Rendering the answer adds the length of the output, plus O(d log d) to sort d duplicates.
- Space: O(n) for the ID maps and the explicit stack.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: an empty tree and a single frame, two identical
leaves, nested repeats, the same frames in a different order, a production-style outage
(three identical timeout traces and one different error), a 20,000-frame-deep trace (no
recursion overflow), and 50 random trees checked against a brute force that renders every subtree.

## 11. Interview Talk Track
"This is error grouping. Thousands of events share a call tree, and I want each distinct
shape once, with a count. A subtree is defined by its name and its children, so I walk
bottom-up in post-order. The naive way is to build a string for every subtree and put it in a
hash map, but on a deep trace those strings are O(n) each, so it's O(n²). Instead I intern
shapes: each distinct `(name, child IDs)` tuple gets a small integer. Equal tuples mean equal
shapes, so the whole thing is O(n). I use an explicit stack, because the traces you most need
to group, like runaway recursion, are exactly the ones that are deep enough to blow Python's
recursion limit. In production you'd hash the canonical form into a fingerprint and normalise frames first."

## 12. Level Up
1. **"Group events across 200 ingest servers."** Each server cannot share integer IDs, because they
   are only local. Hash the canonical form into a stable fingerprint (for example SHA-1 of the
   normalised frames), and use that hash as the grouping key in a shared store. Build the hash
   bottom-up, hashing each child's hash rather than its text, which works like a Merkle tree.
2. **"Line numbers change on every deploy and split the same bug into new issues."** Normalise
   before hashing: keep module and function name, drop line numbers and memory addresses, and
   collapse frames from third-party libraries. The grouping key is only as good as its normalisation.
3. **"Memory cap: 10 million events per hour."** Don't keep the trees. Keep `fingerprint ->
   (count, first_seen, last_seen, one sample event)`. The sample is enough to debug; the rest is just a counter.

## 13. Related Chips
- **DC-OBS-05 Top-K Noisy Pods Board**: once events are grouped, rank the top K issues.
- **DC-SEC-20 Nested Config Parser**: another walk over a nested structure without trusting its depth.
- Handbook #35 Serialize and Deserialize Binary Tree: the related canonical-form problem.
