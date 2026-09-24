Source: New

# DC-SEC-09 · IP Range to CIDR Blocks

## 1. Header
| | |
|---|---|
| Chip ID | DC-SEC-09 |
| Difficulty | Medium |
| Pattern | Bit manipulation |
| Track | Cloud Security & IAM (SEC) |
| Classic pattern | LeetCode 751 |
| Premium | Yes (P). Free alternative: LeetCode 231 Power of Two (Easy), which practises the same lowest-set-bit trick (`x & -x`, `x & (x - 1)`). |
| Time box | 25 min |
| Source | New |

## 2. The Scenario
A payments vendor emails: "Please allow our egress NAT range, 192.0.2.3 to 192.0.2.60
(58 addresses), on port 443." Your security group `sg-vendor-callbacks` only takes CIDR
blocks, and it is close to its inbound rule limit. Allowing `192.0.2.0/26` would be one rule,
but it would also let in 6 addresses the vendor doesn't own. You need the **fewest** CIDR
blocks that cover **exactly** the vendor's 58 addresses.

## 3. Why This Is DevOps
**Production reality:** Firewalls, security groups and network ACLs speak CIDR, but people
and vendors hand you ranges ("start here, this many addresses"). A CIDR block of size 2^k must
start on a multiple of 2^k, so the largest block that can begin at an address is given by its
lowest set bit. Take the biggest block that both starts here and fits in what is left, then
move on. Each step is a couple of bit operations, and the result is the shortest exact rule set.

**Where you see it:** AWS security groups and managed prefix lists, GCP firewall source
ranges, `ipset` with `hash:net` on Linux, Python's `ipaddress.summarize_address_range`, and
Go's `net/netip`.

**Reality check:** In production, use the standard library (`ipaddress`, `net/netip`)
instead of hand-written bit code. This chip teaches what those functions do. Real rule sets also
merge ranges from several sources first (DC-SEC-05) and handle IPv6, where the same trick works
on 128-bit numbers.

**What breaks if you get it wrong:** Rounding out to one big block (`/26`) grants access to
addresses someone else may own, which is a real exposure. Emitting one `/32` per address uses
58 rules, runs into the security group's rule limit, and makes the next review unreadable.

## 4. Problem Statement
Write `range_to_cidrs(start_ip, count)`.

- The range starts at IPv4 address `start_ip` and covers `count` addresses in a row.
- Return the **fewest** CIDR blocks that together cover **exactly** those addresses (no more,
  no fewer), in address order, as strings like `"10.0.0.8/29"`.
- A block `a.b.c.d/n` covers `2^(32-n)` addresses, and its first address must be a multiple of that size.
- Return `[]` when `count` is 0. Don't use the `ipaddress` module in your answer.

## 5. Input / Output format and Constraints
- `range_to_cidrs(start_ip: str, count: int) -> list[str]`.
- `start_ip` is a valid dotted IPv4 address. `0 <= count`, and the range does not go past
  `255.255.255.255`.
- `count` can be as large as `2^32`.

## 6. Examples
**Example 1: the anchor case**
```
range_to_cidrs("10.0.0.8", 20) -> ["10.0.0.8/29", "10.0.0.16/29", "10.0.0.24/30"]
# 8 + 8 + 4 = 20. 10.0.0.16 could start a /28 (16 addresses), but only 12 are left.
```

**Example 2: aligned range**
```
range_to_cidrs("10.1.0.0", 65536) -> ["10.1.0.0/16"]
```

**Example 3: edges (edge case)**
```
range_to_cidrs("192.0.2.77", 1)   -> ["192.0.2.77/32"]
range_to_cidrs("0.0.0.0", 2**32)  -> ["0.0.0.0/0"]
range_to_cidrs("10.0.0.8", 0)     -> []
```

## 7. Starter Code
See [`starter.py`](starter.py): `range_to_cidrs` with a docstring and type hints. The body is TODO.

```bash
make try CHIP=02-security/DC-SEC-09-ip-range-to-cidr-blocks
```

## 8. Hints
1. **Nudge:** Turn the address into one 32-bit integer. Which block sizes are allowed to start at, say, 10.0.0.8?
2. **Pattern:** A block of size 2^k must start on a multiple of 2^k, so the largest block that may start at `x` is
   `x & -x`, its lowest set bit. Then it's greedy.
3. **Near-solution:** `step = x & -x` (use 2^32 when x is 0). Halve `step` while it is bigger than `count`.
   Emit `x/(32 - log2(step))`, then `x += step`, `count -= step`. Repeat until `count` is 0.

## 9. Solution
**Approach**
1. Convert the start address to an integer `x`.
2. The largest block allowed to start at `x` is its lowest set bit, `x & -x`.
3. Shrink it (halve) until it is no bigger than the addresses left.
4. Emit that block, move `x` past it, subtract its size, and repeat.

Greedy is optimal here: taking the largest block that fits never blocks a better choice later,
because the next address becomes at least as aligned.

**Brute force:** Emit a `/32` per address, then repeatedly merge sibling pairs into their parent
block until nothing merges. That starts with O(count) blocks, and count can be 2^32.

**Optimal code:** [`solution.py`](solution.py)

```python
def _to_int(ip: str) -> int:
    a, b, c, d = (int(x) for x in ip.split("."))
    return (a << 24) | (b << 16) | (c << 8) | d


def _to_ip(x: int) -> str:
    return ".".join(str((x >> shift) & 0xFF) for shift in (24, 16, 8, 0))


def range_to_cidrs(start_ip: str, count: int) -> list[str]:
    x = _to_int(start_ip)
    out: list[str] = []
    while count > 0:
        step = x & -x if x else 1 << 32    # largest block allowed to START at x
        while step > count:
            step >>= 1                     # shrink until it fits in what's left
        prefix = 32 - (step.bit_length() - 1)
        out.append(f"{_to_ip(x)}/{prefix}")
        x += step
        count -= step
    return out
```

**Complexity**
- Time: O(32²) at most, so O(1) for IPv4: at most about 2 × 32 blocks, and each shrink loop is at most 32 steps.
- Space: O(1) besides the output, which has at most about 64 blocks.

## 10. Tests
[`test_chip.py`](test_chip.py) has 6 cases: the anchor example, empty and single ranges, an
aligned `/16` (and one address short of it), the edges of the address space (`0.0.0.0/0` and
`255.255.255.255`), a production vendor allow-list (checking exactly 58 addresses are covered),
and a large random check (2,000 random ranges up to 10^9 addresses against
`ipaddress.summarize_address_range`).

## 11. Interview Talk Track
"Vendors give you a range, but security groups want CIDR blocks, and rule counts are limited.
So I want the fewest blocks that cover exactly the range. The key fact is alignment: a block of
2^k addresses has to start on a multiple of 2^k. So the biggest block that can start at address
x is x's lowest set bit, `x & -x`. I take that, halve it until it fits in the addresses left,
emit it, and move on. Greedy is optimal because after each block the next address is at least as
aligned. For IPv4 it's at most about 64 blocks, so constant time. In real code I'd call
`ipaddress.summarize_address_range`, but I'd still want to explain why rounding out to one `/26`
is a security problem: it allows addresses the vendor doesn't own."

## 12. Level Up
1. **"The vendor sends 300 ranges, some overlapping."** Convert every range to integers, merge
   overlaps and adjacent ranges first (DC-SEC-05 with half-open ranges), then turn each merged
   range into CIDRs. Merging first can join blocks that neither range could form alone.
2. **"The group has a hard limit of 60 rules and exact coverage needs 75."** Now it's a
   trade-off: choose which blocks to widen so the extra, unowned address space is as small as
   possible. Widen the smallest gaps first, and send the result for security sign-off, since every
   extra address is a deliberate exposure. Or move the list into a managed prefix list.
3. **"Same for IPv6."** The algorithm is the same on 128-bit integers (Python integers have no
   size limit). Ranges are huge, but the block count stays at most about 2 × 128.

## 13. Related Chips
- **DC-SEC-05 Firewall Range Merger**: merge the integer ranges before turning them into CIDRs.
- **DC-SEC-10 Allow-List Range Tracker**: keep integer ranges up to date as rules change.
- **DC-NET-01 IP Address Validator**: validate the addresses before doing any arithmetic on them.
