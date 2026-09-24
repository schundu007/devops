Source: Handbook #88 LRU Cache — `apps/camora/src/data/capra/top100/88.json` (copied unchanged as `handbook.json`)

# DC-PLAT-06 · Image Cache with LRU Eviction

## 1. Header `DevOps layer`
| | |
|---|---|
| Chip ID | DC-PLAT-06 |
| Difficulty | Medium |
| Pattern | Hash map + doubly linked list |
| Track | Platform Engineering, Scheduling & Allocation (PLAT) |
| Classic pattern | LeetCode 146 |
| Premium | No |
| Time box | 25 min |
| Source | Handbook #88 LRU Cache |

## 2. The Scenario `DevOps layer`
Node `ip-10-0-7-21` in the `batch` node group has a small disk that holds three container
images at a time: `nginx:1.27`, `redis:7.2` and `app:v142`. A pod restart just used
`nginx:1.27` again. Now the rollout of `app:v143` needs room. Which image should be deleted
so that the images most likely to be needed again stay on the node and don't have to be pulled again?

**Mapping: DevOps term → handbook name**

| DevOps term | Handbook name |
|---|---|
| image ID | `key` |
| image data (here, its size in MiB) | `value` |
| how many images fit on the node's disk | `capacity` |
| a container starts from the image (a use) | `get(key)` |
| pulling an image onto the node | `put(key, value)` |
| image garbage collection | eviction of the least recently used key |

## 3. Why This Is DevOps `DevOps layer`
**Production reality:** When the node's image disk passes a threshold, the kubelet deletes
unused images, the least recently used first, until usage drops below a lower threshold.
By default GC starts at 85% disk usage (`imageGCHighThresholdPercent`) and stops at 80%
(`imageGCLowThresholdPercent`). Least-recently-used is a good guess for "least likely to be
needed next", and a wrong guess costs a slow re-pull on the next pod start. The same eviction
rule runs in CDN edge caches, database buffer pools and DNS resolver caches.

**Where you see it:** kubelet image garbage collection, Redis
`maxmemory-policy allkeys-lru` (an approximate LRU), Nginx `proxy_cache` (its cache manager removes the least recently used data).

**Reality check:** The kubelet does not keep a linked list. It periodically lists the images,
sorts the unused ones by last-used time, and deletes them until enough bytes are free. It
never deletes an image a running container uses, and it skips images younger than
`imageMinimumGCAge`. Capacity is measured in disk bytes, not in number of images. Redis
samples a few keys and evicts the oldest one it sees, to avoid list overhead.

**What breaks if you get it wrong:** Evict the wrong image, for example the base image that
every pod restart needs, and each restart pulls hundreds of MiB again. During an incident
that means slow pod starts, registry rate limits (`429 Too Many Requests`), and pods stuck in
`ImagePullBackOff`.

## 4. Problem Statement `From handbook`
Design a key–value cache with a fixed capacity that evicts the **least recently used** entry when it overflows.

Implement the `LRUCache` class:
- `LRUCache(capacity)` sets the positive maximum number of entries.
- `get(key)` returns the value stored for `key`, or `-1` if the key is absent. A successful lookup counts as a use.
- `put(key, value)` inserts the pair or overwrites an existing key's value (also a use). If this pushes the number of keys above `capacity`, remove the key that has gone unused the longest.

Both `get` and `put` must run in `O(1)` average time.

## 5. Input / Output format and Constraints
**Input / Output format `(added)`:** a design problem. `LRUCache(capacity: int)`;
`get(key: int) -> int`; `put(key: int, value: int) -> None`.

**Constraints `From handbook`**
- 1 ≤ capacity ≤ 3000
- 0 ≤ key ≤ 10⁴
- 0 ≤ value ≤ 10⁵
- At most 2 × 10⁵ calls in total are made to get and put

## 6. Examples `From handbook`
**Example 1 — 9 operations**
```
Input:  ops = ["LRUCache", "put", "put", "get", "put", "get", "put", "get", "get", "get"], vals = [[2], [1, 1], [2, 2], [1], [3, 3], [2], [4, 4], [1], [3], [4]]
Output: [null, null, null, 1, null, -1, null, -1, 3, 4]
```
Reading key `1` makes key `2` the stalest, so inserting `3` evicts `2`. Inserting `4` then evicts `1`.

**Example 2 — 5 operations**
```
Input:  ops = ["LRUCache", "put", "put", "put", "get", "get"], vals = [[2], [1, 1], [1, 10], [2, 2], [1], [2]]
Output: [null, null, null, null, 10, 2]
```
Overwriting key `1` updates its value without consuming extra capacity.

## 7. Starter Code `(added)`
The handbook builds its starter from the problem's function signature and stores no starter file. See
[`starter.py`](starter.py): the same `LRUCache` signatures, with TODO bodies.

```bash
make try CHIP=03-platform/DC-PLAT-06-image-cache-lru
```

## 8. Hints `From handbook`
1. A hash map alone gives O(1) lookups but cannot tell you which key is least recently used; you also need an order that can be updated in O(1).
2. Pair the hash map with a doubly linked list ordered by recency, where the map stores each key's list node.
3. On every `get` hit or `put`, unlink the node and move it to the most-recent end; when the size exceeds `capacity`, remove the node at the least-recent end and delete its key from the map.

## 9. Solution `From handbook`
#### Hash Map + Recency List
Store values in a hash map and keep keys in an array ordered by use; touching a key moves it to the end and eviction removes the front.

- Map gives the value lookup
- Array tracks recency order
- Moving a key costs a linear removal

Time: O(capacity) per operation · Space: O(capacity)

```python
class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.values = {}
        self.order = []

    def _touch(self, key):
        if key in self.values:
            self.order.remove(key)
        self.order.append(key)

    def get(self, key):
        if key not in self.values:
            return -1
        self._touch(key)
        return self.values[key]

    def put(self, key, value):
        self._touch(key)
        self.values[key] = value
        if len(self.values) > self.capacity:
            oldest = self.order.pop(0)
            del self.values[oldest]
```

#### Hash Map + Doubly Linked List (Optimal)
The map points each key at a node in a doubly linked list ordered by recency, so moving a node to the front and evicting from the back are both constant time.

- Sentinel head and tail simplify edge cases
- Most recent sits next to head
- Evict the node just before tail

Time: O(1) per operation · Space: O(capacity)

```python
class _Node:
    def __init__(self, key=0, val=0):
        self.key, self.val = key, val
        self.prev = self.next = None

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.map = {}
        self.head, self.tail = _Node(), _Node()
        self.head.next, self.tail.prev = self.tail, self.head

    def _remove(self, node):
        node.prev.next, node.next.prev = node.next, node.prev

    def _add_front(self, node):
        node.prev, node.next = self.head, self.head.next
        self.head.next.prev = node
        self.head.next = node

    def get(self, key):
        if key not in self.map:
            return -1
        node = self.map[key]
        self._remove(node)
        self._add_front(node)
        return node.val

    def put(self, key, value):
        if key in self.map:
            self._remove(self.map[key])
        node = _Node(key, value)
        self.map[key] = node
        self._add_front(node)
        if len(self.map) > self.capacity:
            lru = self.tail.prev
            self._remove(lru)
            del self.map[lru.key]
```

`solution.py` is the handbook's optimal Python solution (Hash Map + Doubly Linked List),
copied unchanged. The handbook's Java, C++, Go and JavaScript versions are in
`handbook.json` → `solutions[].code`.

## 10. Tests
**From handbook:** 29 cases in `handbook.json` → `tests`, run unchanged by `test_chip.py`.

**`(added)`** [`test_chip.py`](test_chip.py) wraps those cases in pytest. It runs **every**
Python solution from the handbook (the Step 3 check). It adds DevOps-layer cases: the node
image cache above, capacity 1, a re-pull that refreshes recency, and 50,000 random operations
checked against a separate `OrderedDict` reference.

## 11. Interview Talk Track `DevOps layer`
"When a node's disk fills up, the kubelet deletes the images that haven't been used for the
longest time, which is LRU eviction. To make every operation O(1), I combine a hash map from
key to node with a doubly linked list in recency order. A get looks up the node and moves it to
the front. A put either updates and moves an existing node, or adds a new one at the front, and
if that goes over capacity, removes the node at the back, which is the least recently used.
Sentinel head and tail nodes remove the empty-list edge cases. In the real kubelet, capacity
is disk bytes, not an entry count, and it never evicts an image that a running container uses.
That second rule is a 'pinned' flag I'd add to this design."

## 12. Level Up `DevOps layer`
1. **"Capacity is bytes, not a count, and images differ in size."** Track `used_bytes`. After
   a put, evict from the tail until `used_bytes <= capacity`, which may remove several entries.
   Add hysteresis like the kubelet: start at the high threshold, stop at the low one, so the
   node doesn't evict on every pull.
2. **"Some images must never be evicted while a container uses them."** Keep a reference count
   per image. Skip pinned entries when evicting: walk from the tail to the first unpinned node,
   or keep pinned entries in a separate list so eviction stays O(1).
3. **"A one-off batch job pulls 50 images and pushes out the everyday ones."** Pure LRU
   suffers from this scan pollution. Use LFU (DC-PLAT-12) or a segmented LRU: new entries go into a
   probation segment and move to the protected segment only on a second use.

## 13. Related Chips `DevOps layer`
- **DC-PLAT-12 Hot-Object Cache (LFU)**: evict by frequency, with LRU to break ties.
- **DC-SEC-18 Session Token Manager**: expiry by time instead of by recency.
- **DC-OS-01 In-Memory File System**: another design problem that combines a hash map and a linked structure.
