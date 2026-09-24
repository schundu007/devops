"""DC-SEC-18 Session Token Manager — reference solution."""
from __future__ import annotations

from collections import OrderedDict


class TokenManager:
    def __init__(self, ttl: int) -> None:
        self.ttl = ttl
        # token id -> expiry time. Every token gets the same TTL, so the order of
        # the last issue/renew is also the order of expiry: oldest first.
        self.expiry: OrderedDict[str, int] = OrderedDict()

    def _evict(self, now: int) -> None:
        # A token whose expiry == now is already expired (expiry happens first).
        while self.expiry and next(iter(self.expiry.values())) <= now:
            self.expiry.popitem(last=False)

    def issue(self, token_id: str, now: int) -> None:
        self._evict(now)
        self.expiry[token_id] = now + self.ttl
        self.expiry.move_to_end(token_id)

    def renew(self, token_id: str, now: int) -> None:
        self._evict(now)
        if token_id in self.expiry:  # only live tokens can be renewed
            self.expiry[token_id] = now + self.ttl
            self.expiry.move_to_end(token_id)

    def count_live(self, now: int) -> int:
        self._evict(now)
        return len(self.expiry)
