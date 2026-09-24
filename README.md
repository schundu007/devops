# DevOps Chip

**LeetCode patterns inside real infrastructure**

*Small problems. Real infrastructure.*

78 practice problems ("chips") in 7 tracks. Each one is a classic coding-interview pattern
told as a real DevOps, SRE or cloud-security situation. Every chip explains where the same
logic runs in production and works like a playground: starter code, hints, a full solution
and runnable tests.

Written for senior engineers preparing for Staff or Principal DevOps, SRE and Platform
interviews. Code is Python 3.11, standard library only.

14 chips reuse problems from the Capra Handbook as-is and add only the DevOps layer.
See [REUSE_MAP.md](REUSE_MAP.md).

---

## How to use: the playground loop

1. **Read the scenario** in the chip's `README.md` (sections 1–3). Know *why* it matters first.
2. **Try the starter.** Fill in `starter.py`, then run the tests against it:
   ```bash
   make try CHIP=01-observability/DC-OBS-01-metric-lookup
   ```
3. **Open hints one at a time** (section 8). Stop as soon as you are unstuck.
4. **Run the tests** until they pass. `make test` runs every chip against the reference solutions.
5. **Read the solution** (`solution.py` and section 9), even if you passed. Compare approaches.
6. **Say the talk track out loud** (section 11). Time yourself: about 60 seconds.

Section tags in chip READMEs:
- **From handbook**: copied unchanged from the Capra Handbook (REUSE chips only).
- **DevOps layer**: written for this book.
- **(added)**: a section the handbook entry did not have.

## Layout

```
devops-chip/
  README.md  PATTERNS.md  REUSE_MAP.md  Makefile  pytest.ini
  tools/chip.py                 shared test helpers
  tools/fill_handbook.py        fills REUSE READMEs with handbook text, verbatim
  01-observability/  02-security/  03-platform/  04-release/
  05-networking/  06-capacity/  07-os-automation/
    DC-<TRACK>-<NN>-<slug>/
      README.md       chip sections 1-8 and 11-13
      starter.py      your attempt
      solution.py     reference solution
      test_chip.py    pytest
      handbook.json   REUSE chips only: unchanged copy of the handbook entry
```

## Track map

| # | Track | Code | Chips | Folder |
|---|---|---|---|---|
| 1 | Observability & SRE | OBS | 17 | `01-observability/` |
| 2 | Cloud Security & IAM | SEC | 20 | `02-security/` |
| 3 | Platform Engineering, Scheduling & Allocation | PLAT | 15 | `03-platform/` |
| 4 | Release & CI/CD | REL | 8 | `04-release/` |
| 5 | Networking, Service Mesh & Resilience | NET | 13 | `05-networking/` |
| 6 | Capacity & Cost | CAP | 3 | `06-capacity/` |
| 7 | OS & Automation | OS | 2 | `07-os-automation/` |
| | **Total** | | **78** | |

## Master matrix

★ = start here. P = LeetCode Premium (the chip names a free alternative).

| Chip ID | LC # | Difficulty | ★ | Premium | Source | Pattern | Track | Production subsystem |
|---|---|---|---|---|---|---|---|---|
| DC-OBS-01 | 981 | Medium | | | New | Hash map + binary search | OBS | TSDB point-in-time sample lookup |
| DC-OBS-02 | 362 | Medium | | P | Handbook #102 | Queue / sliding window | OBS | Error-rate and SLO alerting |
| DC-OBS-03 | 239 | Hard | | | Handbook #83 | Monotonic deque | OBS | HPA scale-down stabilization window |
| DC-OBS-04 | 652 | Medium | | | New | Tree serialization + hashing | OBS | Error fingerprinting and grouping |
| DC-OBS-05 | 1244 | Medium | | P | New | Hash map + heap/sort | OBS | Top-K dashboards (topk) |
| DC-OBS-06 | 1438 | Medium | | | New | Sliding window + two monotonic deques | OBS | Latency stability and SLO review |
| DC-OBS-07 | 224 | Hard | | | New | Stack | OBS | Query expression evaluation |
| DC-OBS-08 | 295 | Hard | ★ | | Handbook #39 | Two heaps | OBS | Streaming latency percentiles |
| DC-OBS-09 | 359 | Easy | | P | New | Hash map + timestamps | OBS | Log and alert de-duplication |
| DC-OBS-10 | 635 | Medium | | P | New | Timestamp truncation + range scan | OBS | Log time-range queries |
| DC-OBS-11 | 1348 | Medium | | | New | Hash map + bucketing | OBS | Downsampling and step alignment |
| DC-OBS-12 | 2034 | Medium | | | New | Hash map + heaps with lazy deletion | OBS | Out-of-order and corrected samples |
| DC-OBS-13 | 1396 | Medium | | | New | Hash maps | OBS | Distributed tracing span latency |
| DC-OBS-14 | 23 | Hard | ★ | | Handbook #24 | Min-heap (k-way merge) | OBS | Multi-node log aggregation |
| DC-OBS-15 | 632 | Hard | | | New | Min-heap + sliding window | OBS | Incident correlation |
| DC-OBS-16 | 1004 | Medium | | | New | Sliding window | OBS | Error budgets |
| DC-OBS-17 | 227 | Medium | | | New | Stack | OBS | Query operator precedence |
| DC-SEC-01 | 71 | Medium | | | New | Stack | SEC | Path traversal defense |
| DC-SEC-02 | 20 | Easy | | | Handbook #16 | Stack | SEC | CI config lint |
| DC-SEC-03 | 394 | Medium | | | New | Stack | SEC | Policy and template expansion |
| DC-SEC-04 | 820 | Medium | | | New | Reverse trie | SEC | DNS name compression, domain allow-lists |
| DC-SEC-05 | 56 | Medium | | | Handbook #61 | Sort + merge | SEC | Firewall and security-group rules |
| DC-SEC-06 | 1094 | Medium | | | New | Difference array / prefix sum | SEC | Tenant quota guardrails |
| DC-SEC-07 | 443 | Medium | | | New | Two pointers (in place) | SEC | Log compaction |
| DC-SEC-08 | 44 | Hard | ★ | | New | DP / greedy two pointers | SEC | IAM action and ARN matching |
| DC-SEC-09 | 751 | Medium | | P | New | Bit manipulation | SEC | CIDR block planning |
| DC-SEC-10 | 715 | Hard | | | New | Sorted intervals | SEC | Live IP/port allow-lists |
| DC-SEC-11 | 1233 | Medium | | | New | Sort + prefix check (or trie) | SEC | Policy grant cleanup |
| DC-SEC-12 | 841 | Medium | ★ | | New | Graph DFS/BFS | SEC | Attack-path / blast-radius analysis |
| DC-SEC-13 | 2092 | Hard | | | New | Union-find per time group / BFS | SEC | Credential exposure and rotation |
| DC-SEC-14 | 721 | Medium | | | New | Union-find | SEC | Identity resolution (SSO, offboarding) |
| DC-SEC-15 | 1169 | Medium | ★ | | New | Sort + group by user | SEC | Identity threat detection |
| DC-SEC-16 | 1604 | Medium | | | New | Sort + sliding window | SEC | Brute-force and abuse detection |
| DC-SEC-17 | 1032 | Hard | | | New | Reverse trie | SEC | Streaming secret scanning |
| DC-SEC-18 | 1797 | Medium | | | New | Hash map + expiry | SEC | Token and lease TTLs |
| DC-SEC-19 | 722 | Medium | | | New | String state machine | SEC | Config pre-processing |
| DC-SEC-20 | 385 | Medium | | | New | Stack / recursion | SEC | Nested config parsing |
| DC-PLAT-01 | 210 | Medium | | | Handbook #96 | Topological sort (Kahn) | PLAT | IaC apply order |
| DC-PLAT-02 | 207 | Medium | | | Handbook #45 | Cycle detection | PLAT | DAG validation in CI |
| DC-PLAT-03 | 253 | Medium | | P | Handbook #64 | Sort + min-heap | PLAT | CI runner pool sizing |
| DC-PLAT-04 | 621 | Medium | | | Handbook #73 | Greedy + max-heap | PLAT | Job scheduling with cooldowns |
| DC-PLAT-05 | 433 | Medium | | | New | BFS | PLAT | Stepwise upgrade planning |
| DC-PLAT-06 | 146 | Medium | | | Handbook #88 | Hash map + doubly linked list | PLAT | Kubelet image garbage collection |
| DC-PLAT-07 | 1606 | Hard | ★ | | New | Heap + sorted set | PLAT | Load balancer backend selection |
| DC-PLAT-08 | 1882 | Medium | | | New | Two min-heaps | PLAT | Worker-pool dispatch |
| DC-PLAT-09 | 2402 | Hard | | | New | Two min-heaps | PLAT | Runner pool allocation |
| DC-PLAT-10 | 528 | Medium | | | New | Prefix sums + binary search | PLAT | Weighted canary routing |
| DC-PLAT-11 | 1845 | Medium | | | New | Min-heap | PLAT | Port / IPAM / ID allocation |
| DC-PLAT-12 | 460 | Hard | | | New | Hash maps + frequency lists | PLAT | Edge and CDN caching |
| DC-PLAT-13 | 1188 | Medium | | P | New | Locks + condition variables | PLAT | Pipeline backpressure |
| DC-PLAT-14 | 1226 | Medium | | | New | Concurrency / locks | PLAT | Lock ordering |
| DC-PLAT-15 | 759 | Hard | | P | New | Merge intervals / heap | PLAT | On-call schedule coverage |
| DC-REL-01 | 278 | Easy | ★ | | New | Binary search | REL | git bisect |
| DC-REL-02 | 165 | Medium | | | New | Split + two pointers | REL | Version checks in vulnerability scanners |
| DC-REL-03 | 2050 | Hard | ★ | | New | Topological sort + DP | REL | Pipeline critical path |
| DC-REL-04 | 1203 | Hard | | | New | Two-level topological sort | REL | Release train ordering |
| DC-REL-05 | 2115 | Medium | | | New | Topological sort | REL | Build target resolution |
| DC-REL-06 | 1462 | Medium | | | New | Transitive closure (BFS / Floyd-Warshall) | REL | Change impact analysis |
| DC-REL-07 | 802 | Medium | | | New | Reverse graph + topological sort | REL | Safe startup ordering |
| DC-REL-08 | 1146 | Medium | | | New | Binary search per key | REL | Versioned config (etcd revisions) |
| DC-NET-01 | 468 | Medium | | | New | String parsing | NET | Ingress / WAF input validation |
| DC-NET-02 | 93 | Medium | | | New | Backtracking | NET | Log forensics |
| DC-NET-03 | 399 | Medium | | | New | Weighted graph + DFS/BFS | NET | Capacity and traffic ratios |
| DC-NET-04 | 743 | Medium | | | New | Dijkstra | NET | Link-state routing (OSPF, IS-IS) |
| DC-NET-05 | 208 | Medium | | | Handbook #36 | Trie | NET | Gateway path and prefix routing |
| DC-NET-06 | 1192 | Hard | ★ | | New | Tarjan's bridges | NET | SPOF link detection |
| DC-NET-07 | 1319 | Medium | | | New | Union-find | NET | Partition healing |
| DC-NET-08 | 684 | Medium | | | New | Union-find | NET | L2 loop detection (STP) |
| DC-NET-09 | 1514 | Medium | | | New | Dijkstra (max-product) | NET | End-to-end availability |
| DC-NET-10 | 787 | Medium | | | New | Bellman-Ford / level BFS | NET | Inter-region transfer cost |
| DC-NET-11 | 1584 | Medium | | | New | Minimum spanning tree (Prim/Kruskal) | NET | Site and VPC interconnect |
| DC-NET-12 | 994 | Medium | | | Handbook #95 | Multi-source BFS | NET | Cascading failure spread |
| DC-NET-13 | 1971 | Easy | | | New | BFS / union-find | NET | Network reachability analysis |
| DC-CAP-01 | 875 | Medium | ★ | | Handbook #85 | Binary search on the answer | CAP | Consumer sizing for backlogs |
| DC-CAP-02 | 1011 | Medium | | | New | Binary search on the answer | CAP | Backup bandwidth sizing |
| DC-CAP-03 | 410 | Hard | | | New | Binary search on the answer / DP | CAP | Range partitioning and rebalancing |
| DC-OS-01 | 588 | Hard | | P | New | Directory tree design | OS | Virtual filesystems and hierarchical KV |
| DC-OS-02 | 14 | Easy | | | New | String scan | OS | Inventory and naming patterns |

Totals: 78 chips · 14 from the handbook · 64 new · 10 ★ · 9 Premium.

## Pattern cheat sheet

See [PATTERNS.md](PATTERNS.md): for each pattern, "When you see X in DevOps, think Y."

## Suggested path

1. **Easy warm-ups:** DC-OBS-09, DC-SEC-02, DC-REL-01, DC-NET-13, DC-OS-02.
2. **★ Start-here chips:** DC-REL-01, DC-CAP-01, DC-SEC-12, DC-SEC-15, DC-OBS-08,
   DC-OBS-14, DC-SEC-08, DC-REL-03, DC-PLAT-07, DC-NET-06.
3. **Mediums, track by track:** OBS → SEC → PLAT → REL → NET → CAP.
4. **Hards last:** DC-OBS-03, 07, 15 · DC-SEC-10, 13, 17 · DC-PLAT-09, 12, 15 ·
   DC-REL-04 · DC-CAP-03 · DC-OS-01.

## Running

```bash
make test                                          # all chips, reference solutions
make try CHIP=01-observability/DC-OBS-01-metric-lookup   # one chip, your starter.py
```

CI (`.github/workflows/test.yml`) runs `pytest` on every push, on Python 3.11.
