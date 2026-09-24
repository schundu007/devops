Source: Handbook #36 Implement Trie (Prefix Tree) — `apps/camora/src/data/capra/top100/36.json` (copied unchanged as `handbook.json`)

# DC-NET-05 · Route Prefix Trie

## 1. Header `DevOps layer`
| | |
|---|---|
| Chip ID | DC-NET-05 |
| Difficulty | Medium |
| Pattern | Trie |
| Track | Networking, Service Mesh & Resilience (NET) |
| Classic pattern | LeetCode 208 |
| Premium | No |
| Time box | 25 min |
| Source | Handbook #36 Implement Trie (Prefix Tree) |

## 2. The Scenario `DevOps layer`
The `edge-gateway` in front of 40 microservices holds 3,000 routes such as `/api/v1/orders`,
`/api/v1/orders/refunds` and `/healthz`. Before a deploy, a config check has to answer two
questions quickly for every new route: "Is this exact route already registered?" and "Does any
registered route live under this prefix?" (for example, before someone deletes `/api/v1/`).
Scanning 3,000 strings for each check is too slow for a CI gate that runs on every PR, so the
table needs a structure whose lookups depend on the path length, not on the number of routes.

**Mapping: DevOps term → handbook name**

| DevOps term | Handbook name |
|---|---|
| a route path, such as `/api/v1/orders` | `word` |
| register a route | `insert(word)` |
| "is this exact route registered?" | `search(word)` |
| "is anything registered under this prefix?" | `startsWith(prefix)` |
| the route table | `Trie` |

## 3. Why This Is DevOps `DevOps layer`
**Production reality:** API gateways and HTTP routers match request paths by prefix, and
network routers match destination addresses by the longest prefix. Both keep their tables in
a trie: each step down the tree consumes the next part of the key, so a lookup costs the length
of the path, not the size of the table. That is why a router with a million routes still forwards
at line rate.

**Where you see it:** the Linux kernel's IPv4 routing table (`fib_trie`, an LC-trie), the BSD
radix tree used for routing tables, and Go HTTP routers such as `httprouter` and `chi`, which
match paths with radix trees.

**Reality check:** Production tries are **compressed** (radix or Patricia): a chain of
single-child nodes is stored as one edge, so `/api/v1/` is one hop, not eight. IP routers
branch on bits of the address, not characters. They also answer a third question this chip
does not: the **longest** registered prefix of a key (see Level Up). Some proxies, such as
Envoy, check routes in order instead.

**What breaks if you get it wrong:** If `search` returns true for a mere prefix,
`/api/v1/order` is treated as a registered route. The CI gate then allows a duplicate or a
shadowing route, and traffic for `/api/v1/orders` quietly goes to the wrong service after the deploy.

## 4. Problem Statement `From handbook`
A **trie** (prefix tree) stores strings so that lookups by whole word or by prefix are fast. Implement the `Trie` class:

- `Trie()` creates an empty trie.
- `insert(word)` adds the string `word`.
- `search(word)` returns `true` if `word` has been inserted before, and `false` otherwise.
- `startsWith(prefix)` returns `true` if at least one inserted word begins with `prefix`, and `false` otherwise.

Input is given as parallel lists `ops` (method names) and `vals` (argument lists). The output lists each call's return value, with `null` for the constructor and for `insert`.

## 5. Input / Output format and Constraints
**Input / Output format `(added)`:** a design problem. `Trie()` builds the table;
`insert(word: str) -> None`; `search(word: str) -> bool`; `startsWith(prefix: str) -> bool`.

**Constraints `From handbook`**
- 1 ≤ word.length, prefix.length ≤ 2000
- word and prefix consist only of lowercase English letters.
- At most 3 * 10⁴ calls in total will be made to insert, search, and startsWith.

The handbook's constraint is lowercase letters. Both handbook solutions store characters in a
dict, so the DevOps-layer tests also pass route paths containing `/`.

## 6. Examples
**From handbook**

**Example 1 — 6 operations**
```
Input:  ops = ["Trie", "insert", "search", "search", "startsWith", "insert", "search"], vals = [[], ["apple"], ["apple"], ["app"], ["app"], ["app"], ["app"]]
Output: [null, null, true, false, true, null, true]
```
`app` is only a prefix until it is inserted as a word itself.

**Example 2 — Prefix is not a word `(added)`**
```
Input:  ops = ["Trie", "insert", "search", "startsWith", "startsWith"], vals = [[], ["orders"], ["order"], ["order"], ["ordersx"]]
Output: [null, null, false, true, false]
```
`order` is only a prefix of the inserted word, so `search` is false but `startsWith` is true. A prefix longer than any word is false.

## 7. Starter Code `(added)`
The handbook builds its starter from the problem's function signature and stores no starter file. See
[`starter.py`](starter.py): the same `Trie` signatures, with TODO bodies.

```bash
make try CHIP=05-networking/DC-NET-05-route-prefix-trie
```

## 8. Hints `From handbook`
1. `search` and `startsWith` walk the same path of characters; they only differ in what they require at the end of the walk.
2. Give each node a map (or 26-slot array) from character to child node, plus a boolean that marks the end of a complete word.
3. insert creates missing children along the path and sets the end flag on the last node; search requires the path to exist and the flag to be set; startsWith requires only that the path exists.

## 9. Solution `From handbook`
#### Hash Map Based Trie
Each node uses a hash map to store children. Simple but slightly slower due to hash overhead.

- Each node is a hash map of children
- Special marker # indicates end of word
- Search checks for end marker, startsWith does not
- Hash map approach is concise and flexible

Time: O(m) per operation · Space: O(total characters)

```python
class Trie:
    def __init__(self):
        self.root = {}

    def insert(self, word):
        node = self.root
        for ch in word:
            if ch not in node:
                node[ch] = {}
            node = node[ch]
        node['#'] = True

    def search(self, word):
        node = self.root
        for ch in word:
            if ch not in node:
                return False
            node = node[ch]
        return '#' in node

    def startsWith(self, prefix):
        node = self.root
        for ch in prefix:
            if ch not in node:
                return False
            node = node[ch]
        return True
```

#### TrieNode Class (Optimal)
Use dedicated TrieNode objects with a children array and an isEnd flag for clean structure.

- Dedicated TrieNode class is cleaner
- Helper _find method avoids code duplication
- isEnd flag distinguishes complete words from prefixes
- m is the length of the word/prefix

Time: O(m) per operation · Space: O(total characters)

```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True

    def search(self, word):
        node = self._find(word)
        return node is not None and node.is_end

    def startsWith(self, prefix):
        return self._find(prefix) is not None

    def _find(self, prefix):
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node
```

**Follow-up (from handbook):** _(none in handbook)_

`solution.py` is the handbook's optimal Python solution (TrieNode Class), copied unchanged. The
handbook's Java, C++, Go and JavaScript versions are in `handbook.json` → `solutions[].code`.

## 10. Tests
**From handbook:** 29 cases in `handbook.json` → `tests`, run unchanged by `test_chip.py`.

**`(added)`** [`test_chip.py`](test_chip.py) wraps those cases in pytest. It also runs
**every** Python solution from the handbook against them (the Step 3 check), and adds two
DevOps-layer cases: the gateway route table from the scenario (exact route vs prefix, a
missing version, a deeper path) and a 5,000-operation random cross-check against a set-based brute force.

## 11. Interview Talk Track `DevOps layer`
"A route table needs two questions answered fast: is this exact route registered, and is
anything registered under this prefix. A trie answers both in time proportional to the key
length, not the number of routes. Each node maps the next character to a child and has an end
flag. Insert walks and creates nodes and sets the flag. Search walks and needs the flag at the
end. startsWith only needs the walk to succeed. That's O(m) per operation and O(total
characters) memory. In production I'd compress single-child chains into one edge (a radix trie),
branch on path segments or on address bits, and add a longest-prefix-match query. That's what
Linux's fib_trie and Go routers like httprouter do."

## 12. Level Up `DevOps layer`
1. **"Route `/api/v1/orders/42` to the most specific registered prefix."** That is
   longest-prefix match. Walk the path and remember the last node whose end flag was set; when the
   walk stops, that node is the answer. It is still O(m), and it is exactly what an IP router does
   with a destination address and its CIDR routes.
2. **"One million routes, and memory is tight."** One Python object per character is huge.
   Compress chains of single-child nodes into one edge that holds a substring (radix / Patricia
   trie), which cuts the node count to roughly the number of routes. For IP routes, branch on bits,
   and use level compression (as the Linux LC-trie does) so the tree is shallow.
3. **"Routes have `{id}` wildcards, like `/users/{id}/orders`."** Branch on path segments instead
   of characters, give each node one optional "parameter" child, and try exact children before the
   parameter child. That is how segment-based HTTP routers resolve a path without backtracking in the common case.

## 13. Related Chips `DevOps layer`
- **DC-SEC-04 Domain Suffix Compactor**: the same structure built on reversed hostnames.
- **DC-SEC-17 Streaming Secret Scanner**: a reverse trie matched against a live stream.
- **DC-SEC-11 Redundant Prefix Grant Cleaner**: "is this path covered by a parent prefix?" in a policy.
