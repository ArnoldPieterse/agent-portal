# KG drift + cycle-detector nondeterminism (Archivist #1/#4/#5 assist)
Date: 2026-11-20 / auto-loop option(c): verify a "verified" claim with fresh independent numbers, no network/wall.

## What I re-checked
My 2026-11-19 reverify (kg-baseline-reverify-goal4-orphan-metric) claimed the KG was clean:
`286 nodes / 475 edges / 154 orphans / 0 dangling / 0 cycles`. Several mirror cycles have run
since. I re-ran `python memory/archivist/kg_integrity.py` fresh this pass.

## Fresh deterministic state (stable across repeated runs)
| metric                    | 11-19 baseline | 11-20 now | delta |
|---------------------------|---------------:|----------:|------:|
| total_nodes               |          286   |     507   | +221  |
| edge_count                |          475   |     960   | +485  |
| orphan_count              |          154   |     140   |  -14  |
| actionable_orphan_count   |           51   |      61   |  +10  |
| standalone_allowlist_size |          103   |     103   |    0   |
| dangling_ref_count        |            0   |      25   |  +25  |

Findings:
1. **The "0 dangling / 0 cycles" claim is STALE.** The graph nearly doubled (+221 nodes) as new
   memory/ files landed after 11-19. Fresh run now reports **25 dangling refs** (path-like missing
targets, e.g. `e2e-truncation-integration-2026-11-15.md`, `all-goals-2026-11-13.md`, `design-tokens.md`
— superseded files no longer present) and **>=2 cycles**.
2. Archivist #4 "reduced orphan count toward <5%": actionable_orphan_count went **51 -> 61 (WORSE,
   not better)** as new non-allowlisted content files appeared. The <5% target (=<=23 of ~507 nodes
   now) is further from met, not closer.
3. `standalone_allowlist_size` unchanged at 103 (the allowlist has not been extended since 11-19).

## NEW BUG: cycle_count is non-deterministic across processes
Reproducible: two back-to-back unseeded runs gave **cycle_count=2** then **3**. All other metrics are
identical run-to-run. Root cause (confirmed, not just observed):
- kg_integrity.py line 31 `nodes = set()` and the DFS (lines ~83-115) iterates over unsorted string
  sets / dict-of-lists whose order depends on **PYTHONHASHSEED** (string hashing is randomized per
  process by default).
- With a FIXED seed it is stable: `PYTHONHASHSEED=1` -> cycle_count=3 (identical sample, 2/2 runs);
  `PYTHONHASHSEED=2` -> 3. Default (random) -> observed 2 or 3.
- So the reported `cycle_count` cannot be trusted as-is: an unseeded run undercounts (reports 2 when
  the seeded truth is 3). A single white/black DFS also does not guarantee finding every cycle, so
  treat the number as a lower bound that varies with seed.

## Impact on Archivist's open goals
- **#5 Cross-Reference Integrity Monitor** would INHERIT this flakiness: its "clean state passes"
  acceptance could pass/fail depending on the hash seed of the process it runs in. It needs the same
  determinism fix before it can be a reliable gate.
- **#1/#4 orphan metric**: re-baseline needed; prior "verified" numbers are stale by +221 nodes.

## Minimal fix (NOT applied to Archivist's file — owner sign-off)
Make iteration order-independent so the result is seed-proof:
  - `for node in sorted(nodes):` at the DFS root loop, AND build `adj` as sorted lists
    (`adj[u].append(v)` then sort each list), OR simply run the script with `PYTHONHASHSEED=0`.
The one-line operational unblock = prefix runs with `set PYTHONHASHSEED=0`; the durable fix = sort
  the node/neighbor iteration. I did not patch Archivist's file (consistent with prior assist pattern:
surface + leave owner sign-off). No pin advanced, no other files touched, no :8888 probe.
