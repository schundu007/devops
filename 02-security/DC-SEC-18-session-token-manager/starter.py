"""DC-SEC-18 Session Token Manager — your attempt.

Run your code against the tests:
    make try CHIP=02-security/DC-SEC-18-session-token-manager
"""
from __future__ import annotations


class TokenManager:
    def __init__(self, ttl: int) -> None:
        """Every token lives `ttl` seconds after it is issued or last renewed."""
        # TODO
        pass

    def issue(self, token_id: str, now: int) -> None:
        """Create a token that expires at now + ttl."""
        # TODO
        raise NotImplementedError

    def renew(self, token_id: str, now: int) -> None:
        """If the token exists and has not expired, reset its expiry to now + ttl.

        Otherwise do nothing. A token whose expiry equals `now` has already expired.
        """
        # TODO
        raise NotImplementedError

    def count_live(self, now: int) -> int:
        """Number of tokens whose expiry is later than `now`."""
        # TODO
        raise NotImplementedError
