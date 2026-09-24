Source: New

# DC-NET-01 · IP Address Validator

## 1. Header
| | |
|---|---|
| Chip ID | DC-NET-01 |
| Difficulty | Medium |
| Pattern | String parsing |
| Track | Networking, Service Mesh & Resilience (NET) |
| Classic pattern | LeetCode 468 |
| Premium | No |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
A security review of the `edge-gateway` finds that its admin endpoint is allow-listed to
`10.0.0.0/8`, and the check runs on the client address taken from `X-Forwarded-For`. A tester
sends `X-Forwarded-For: 0177.0.0.1` and `2130706433`, and one of the libraries downstream reads
them as `127.0.0.1`. Your fix: before any allow-list or SSRF check runs, every address string
must be strictly classified as a well-formed IPv4, a well-formed IPv6, or rejected.

## 3. Why This Is DevOps
**Production reality:** Ingress controllers, WAFs, rate limiters and SSRF guards all turn an
address string into a decision. If the parser that validates the string and the library that
later connects to it disagree about what the string means, an attacker can pass the check and
still reach a blocked host. Leading zeros are the classic case: `0127.0.0.1` is "127.0.0.1" to a
strict parser, but `inet_aton`-style parsers read `0127` as octal, which is 87. Loose parsers
that accept leading zeros have caused real SSRF and allow-list bypass bugs, for example
CVE-2021-29921 (Python `ipaddress`), CVE-2021-29923 (Go `net`) and CVE-2021-28918 (the npm `netmask` package).

**Where you see it:** WAF and ingress allow-lists (`nginx` `allow`/`deny`, Envoy RBAC
`remote_ip`), cloud security-group APIs that reject malformed CIDRs, SSRF guards in webhook
and URL-fetch services, and log pipelines that parse client IPs.

**Reality check:** In production, use `ipaddress` / `net/netip`: Python's `ipaddress` module or Go's
`net/netip` package, not a hand-written parser. Both reject leading zeros in current versions.
They also accept forms this chip rejects: `::` shortening (`2001:db8::1`), IPv4-mapped IPv6
(`::ffff:10.0.0.1`) and, in Python, scope IDs (`fe80::1%eth0`). The chip is the strict core that
those libraries build on.

**What breaks if you get it wrong:** A webhook service validates `http://0177.0.0.1/` as
"not loopback", then fetches it. The fetch reaches the instance's local admin port, or a
metadata endpoint, and leaks credentials.

## 4. Problem Statement
Write `classify_address(addr)`, which takes one string and returns:

- `"IPv4"` if it is four decimal parts separated by dots, each part from 0 to 255, with **no
  leading zeros** (`"0"` on its own is fine, `"01"` is not).
- `"IPv6"` if it is exactly eight groups separated by colons, each group 1 to 4 hexadecimal
  digits (upper or lower case). Leading zeros inside a group are allowed. The `::` shorthand is
  **not** accepted.
- `"Neither"` for anything else: signs, spaces, empty parts, extra separators, non-ASCII digits.

## 5. Input / Output format and Constraints
- Input: `addr: str`, length 0 to 100, any printable characters.
- Output: exactly one of `"IPv4"`, `"IPv6"`, `"Neither"`.
- Use only string operations. `int()` is fine for a part that is already known to be 1–3 ASCII digits.

## 6. Examples
**Example 1: valid IPv4**
```
classify_address("10.0.3.17")  -> "IPv4"
```

**Example 2: leading zero (edge case)**
```
classify_address("0127.0.0.1") -> "Neither"   # would be 87.0.0.1 to an octal-aware parser
classify_address("256.0.0.1")  -> "Neither"   # one above the 255 limit
```

**Example 3: IPv6, full form only**
```
classify_address("2001:db8:85a3:0:0:8A2E:0370:7334") -> "IPv6"
classify_address("2001:db8::1")                      -> "Neither"   # "::" not accepted here
```

## 7. Starter Code
See [`starter.py`](starter.py): `classify_address(addr: str) -> str` with the rules in its
docstring. The body is TODO.

```bash
make try CHIP=05-networking/DC-NET-01-ip-validator
```

## 8. Hints
1. **Nudge:** Decide which family to try from the separators first. Three dots means only IPv4 is possible, and seven colons means only IPv6.
2. **Pattern:** Split on the separator, check the number of parts, then validate each part on its own with a short list of rules.
3. **Near-solution:** An IPv4 part must be 1–3 ASCII digits, must not start with `0` unless it is exactly `"0"`, and must be `<= 255`. An IPv6 group must be 1–4 characters, all in `0-9a-fA-F`.

## 9. Solution
**Approach**
1. Count the separators. Three dots means check IPv4, and seven colons means check IPv6.
   Anything else is `"Neither"`.
2. IPv4: split on `.` and require four parts. Check that each part is 1–3 ASCII digits, has no
   leading zero (unless it is `"0"`), and is `<= 255`.
3. IPv6: split on `:` and require eight groups, each 1–4 hex digits.
4. Check ASCII digits explicitly: Python's `str.isdigit()` also accepts `"²"` and `"٣"`.

**Brute force:** Build all 2³² IPv4 addresses as strings and look the input up. That takes
huge memory and still doesn't cover IPv6. It shows the problem is about rules, not search.

**Optimal code:** [`solution.py`](solution.py)

```python
HEX_DIGITS = set("0123456789abcdefABCDEF")


def _is_ipv4(addr: str) -> bool:
    parts = addr.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        if not (1 <= len(part) <= 3) or not all("0" <= ch <= "9" for ch in part):
            return False
        if len(part) > 1 and part[0] == "0":     # leading zero: octal ambiguity
            return False
        if int(part) > 255:
            return False
    return True


def _is_ipv6(addr: str) -> bool:
    groups = addr.split(":")
    if len(groups) != 8:
        return False
    return all(1 <= len(g) <= 4 and all(ch in HEX_DIGITS for ch in g) for g in groups)


def classify_address(addr: str) -> str:
    if addr.count(".") == 3 and _is_ipv4(addr):
        return "IPv4"
    if addr.count(":") == 7 and _is_ipv6(addr):
        return "IPv6"
    return "Neither"
```

**Complexity**
- Time: O(n) for a string of length n, because each character is looked at a constant number of times.
- Space: O(n) for the split parts. It could be O(1) with index scanning, but that is not worth the clarity cost.

## 10. Tests
[`test_chip.py`](test_chip.py) has 24 cases:
- valid IPv4 and IPv6, including the `0.0.0.0` and `255.255.255.255` boundaries;
- invalid IPv4: leading zeros, 256, too few parts, trailing dot, a non-ASCII digit;
- invalid IPv6: `::`, a 5-digit group, a non-hex group, an empty last group, nine groups;
- empty and single-character strings;
- a production-style `X-Forwarded-For` filter;
- a 20,000-string fuzz test against Python's `ipaddress`. The fuzz test runs only on shapes
  where the two sets of rules agree, and skips any string containing `::` or `%`.

## 11. Interview Talk Track
"This validator sits in front of every allow-list and SSRF check, so it has to be strict, not
forgiving. I pick the family from the separators: three dots means IPv4, seven colons means
IPv6. For IPv4 each part must be one to three ASCII digits, at most 255, and must not have a
leading zero, because some parsers read 0127 as octal 87. That mismatch is exactly how
allow-list bypasses like the 2021 CVEs in Python's ipaddress and Go's net package happened. For
IPv6 each of the eight groups is one to four hex digits. It's linear in the string length. In
production I wouldn't hand-roll this. I'd use ipaddress or net/netip, and make sure the same
parsed value is used for both the check and the connection."

## 12. Level Up
1. **"Accept real-world IPv6 with `::`."** Allow at most one `::`. Split on it, count the
   explicit groups on each side, and require the total to be at most 7, since `::` stands for one
   or more zero groups. Then handle an embedded IPv4 in the last 32 bits. At that point, use the
   standard library.
2. **"Validate and then connect: how do you stop time-of-check/time-of-use bugs?"** Parse once
   into an address object and pass that object, not the string, to both the policy check and the
   dialer. For hostnames, resolve once, check the resolved IP, and connect to that exact IP,
   which also blocks DNS rebinding.
3. **"Check 1 million `X-Forwarded-For` values per second."** This parser is already O(n) with
   no allocations beyond the split. The bigger cost is the allow-list lookup, so store CIDRs in a
   prefix trie (see DC-NET-05) keyed by address bits, and turn validated addresses into integers once.

## 13. Related Chips
- **DC-NET-02 Rebuild IPs from Broken Logs**: the same octet rules, used to generate candidates instead of checking one.
- **DC-SEC-09 IP Range to CIDR Blocks**: once an address is valid, turn ranges of addresses into CIDR rules.
- **DC-SEC-01 Path Traversal Guard**: another "normalise, then check" input guard where a parser mismatch leads to bypasses.
