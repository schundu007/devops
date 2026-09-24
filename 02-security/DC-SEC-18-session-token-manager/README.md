Source: New

# DC-SEC-18 · Session Token Manager

## 1. Header
| | |
|---|---|
| Chip ID | DC-SEC-18 |
| Difficulty | Medium |
| Pattern | Hash map + expiry |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 1797 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
The internal auth service at `auth.internal:8443` hands out session tokens that live 3,600
seconds. Healthy workers renew their token every 30 minutes. A pod that crashed stops renewing,
and its token must quietly die an hour later. The capacity dashboard asks "how many sessions
are live right now?" every 15 seconds, so counting must stay cheap even with 200,000 tokens in memory.

## 3. Why This Is DevOps
**Production reality:** Short-lived credentials are the default for secure systems. A token
or lease has a time-to-live (TTL). A client that is still alive renews it before it expires, and
a dead client's credential expires by itself, so nothing has to clean it up by hand. The server
must reject renewals of already-expired tokens and must be able to count or list live ones for
quotas and dashboards.

**Where you see it:** HashiCorp Vault leases and tokens (TTL plus `renew`), OAuth 2.0 access
tokens with refresh tokens, Kubernetes `Lease` objects used for leader election, Consul
sessions with a TTL, AWS STS temporary credentials.

**Reality check:** Vault also enforces a **max TTL**: renewals cannot extend a lease past it, so
even a healthy client must re-authenticate eventually. OAuth access tokens are usually not renewed in
place. The client uses a refresh token to get a new one. This chip uses one fixed TTL and no max TTL.

**What breaks if you get it wrong:** If `renew` accepts expired tokens, a stolen token that
already timed out comes back to life, which is exactly what short TTLs were supposed to prevent.
If expiry is never enforced, the live-session count and the memory grow forever.

## 4. Problem Statement
Build a `TokenManager(ttl)`. Every token lives `ttl` seconds after it was last issued or renewed.
- `issue(token_id, now)`: create the token (or reset it, if the id already exists), expiring at `now + ttl`.
- `renew(token_id, now)`: if the token exists and has **not** expired, reset its expiry to
  `now + ttl`. Otherwise do nothing.
- `count_live(now)`: return how many tokens have an expiry **later** than `now`.

Expiry happens before anything else at the same moment: a token that expires at time 6 is
already dead for a `renew` or `count_live` at time 6. Across all calls, `now` never decreases.

## 5. Input / Output format and Constraints
- `TokenManager(ttl: int)`, `issue(str, int) -> None`, `renew(str, int) -> None`, `count_live(int) -> int`
- `1 <= ttl <= 10^8`, `1 <= now <= 10^8`, `now` is non-decreasing across calls.
- Up to `2 * 10^5` calls in total. Token ids are 1–64 characters.

## 6. Examples
**Example 1: issue, renew, count**
```
m = TokenManager(5)
m.issue("tok-a", 1)      # expires at 6
m.issue("tok-b", 2)      # expires at 7
m.count_live(3)  -> 2
m.renew("tok-a", 4)      # now expires at 9
m.count_live(7)  -> 1    # tok-b died at 7
```

**Example 2: renewing at the expiry moment (edge case)**
```
m = TokenManager(5); m.issue("tok", 1)   # expires at 6
m.renew("tok", 6)                        # ignored: already expired
m.count_live(7) -> 0
```

**Example 3: unknown token**
```
m = TokenManager(5); m.renew("ghost", 1); m.count_live(2) -> 0
```

## 7. Starter Code
See [`starter.py`](starter.py): the `TokenManager` class with the three methods, docstrings and type hints.

```bash
make try CHIP=02-security/DC-SEC-18-session-token-manager
```

## 8. Hints
1. **Nudge:** A dictionary from token id to expiry time makes `issue` and `renew` easy. What makes `count_live` slow?
2. **Pattern:** Every token has the same TTL, so tokens expire in the same order they were last
   touched. An ordered map, with the most recently touched at the end, keeps them in expiry order.
3. **Near-solution:** Use an `OrderedDict`. On every call, pop from the front while the front's
   expiry `<= now`. On `issue` and a successful `renew`, set the new expiry and `move_to_end`.
   `count_live` is then just `len()`.

## 9. Solution
**Approach**
1. Keep an `OrderedDict` of `token_id -> expiry`, ordered by last issue or renew.
2. Because all TTLs are equal, the front is always the next token to expire.
3. On every call, first evict from the front while `expiry <= now`.
4. `issue`: set the expiry and move to the end. `renew`: only if still present (so still live).
5. `count_live`: after evicting, the size is the answer.

**Brute force:** A plain dict, and `count_live` scans every token: O(n) per count. At 200,000
tokens and a count every 15 seconds that is fine for one dashboard, but not for per-request quota checks.

**Optimal code:** [`solution.py`](solution.py)

```python
class TokenManager:
    def __init__(self, ttl: int) -> None:
        self.ttl = ttl
        self.expiry: OrderedDict[str, int] = OrderedDict()   # oldest first

    def _evict(self, now: int) -> None:
        while self.expiry and next(iter(self.expiry.values())) <= now:
            self.expiry.popitem(last=False)

    def issue(self, token_id: str, now: int) -> None:
        self._evict(now)
        self.expiry[token_id] = now + self.ttl
        self.expiry.move_to_end(token_id)

    def renew(self, token_id: str, now: int) -> None:
        self._evict(now)
        if token_id in self.expiry:                          # live tokens only
            self.expiry[token_id] = now + self.ttl
            self.expiry.move_to_end(token_id)

    def count_live(self, now: int) -> int:
        self._evict(now)
        return len(self.expiry)
```

**Complexity**
- Time: O(1) amortised per call, because each token is evicted at most once per issue or renew.
- Space: O(live tokens), because expired ones are removed.

## 10. Tests
[`test_chip.py`](test_chip.py) has 7 cases: issue, renew and count; an empty manager; renewing
at the exact expiry moment; renewing an unknown token; re-issuing after expiry; a production Vault-style
lease where a crashed pod stops renewing; and 40,000 random operations checked against a plain dict scan.

## 11. Interview Talk Track
"Short-lived credentials need three operations: issue with a TTL, renew only if still alive,
and count what's live. A dict gives O(1) issue and renew, but counting would scan everything.
The key observation is that every token has the same TTL, so tokens expire in the order they were
last touched. An OrderedDict with move-to-end on each touch keeps them in expiry order, and I evict
from the front before every call. Everything is O(1) amortised. The edge case is expiry at exactly
now: it expires first, so a late renew can't revive it. Vault adds a max TTL on top, so even healthy
clients re-authenticate eventually."

## 12. Level Up
1. **"Tokens have different TTLs."** Expiry order no longer follows touch order. Use a min-heap
   of `(expiry, token_id)` with lazy deletion: on renew, push a new entry, and when popping, skip
   entries whose expiry no longer matches the dict. That is O(log n) per operation.
2. **"Add a max TTL, like Vault."** Store the issue time too. On renew, set the expiry to
   `min(now + ttl, issued_at + max_ttl)`. Once `now >= issued_at + max_ttl`, renewals stop
   working and the client must log in again.
3. **"Run it on 5 replicas behind a load balancer."** Keep tokens in a shared store with native
   TTLs (for example Redis `SET key value PX ttl`, where a renew is another `SET` or `PEXPIRE`).
   Or use self-contained signed tokens (JWTs), which trade instant revocation for no shared state.

## 13. Related Chips
- **DC-OBS-09 Log Flood Suppressor**: the same "last time we saw this key" map.
- **DC-PLAT-06 Image Cache with LRU Eviction**: move-to-end ordering for eviction.
- **DC-OBS-12 Late & Corrected Samples**: heaps with lazy deletion, as in Level Up 1.
