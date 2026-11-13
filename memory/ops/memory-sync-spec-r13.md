# MEMORY-SYNC SPEC (r13, 2026-11-12) — owner: Mechanic; runs ONCE after human re-drop

Why: per-host memory trees are divergent subsets (Mechanic r12 probe FAIL; Archivist confirmed from its seat).
Goal: one reconciliation pass into the shared post-re-drop tree. No new machinery — copy + hash-verify only.

## Procedure (post re-drop, on the host with the shared tree)
1. Collect `memory/` trees from every reachable host (Red local; Pale/Black via bundle drop or re-probe).
2. Union into shared `memory/`. Conflict rule: newest mtime wins per relative path; tie -> larger file.
   Never delete a host-only file in this pass — list it for review instead.
3. Verify: sha256 of every shared file matches the union manifest; spot-checks below must pass.

## Spot-checks (must be true after sync)
- `memory/portal/merge-pack.md` agent_portal.py line contains: `THIS file's first 1600 chars`
- `memory/portal/v1-inventory.md`: no stale `26 ... UNLISTED` lines (line-3 verbatim quote "...and 26 more" stays)
- `memory/INDEX.md` present with all three sub-indexes (portal, llm, ops) resolvable

## Baseline — Red tree as of 2026-11-12 23:5x (10 files, sha256[:12])
```
memory/portal/upgrades-2026-11-12.md        1211 B  01fb5641c742
memory/portal/v1-upgrade-state-2026-11-12.md 2459 B  14713d3c9e77
memory/portal/v1-upgrades-decisions.md       3465 B  06b7cba139dd
memory/portal/v1-upgrades-round-2.md         2236 B  f2b50f0cd768
memory/portal/v1-upgrades-round-3.md         3249 B  492bff09f1bf
memory/portal/v1-upgrades-round-4.md         3334 B  8e9e66fa03a5
memory/portal/v1-upgrades-round-5.md         5843 B  e6415738bd52
memory/portal/v1-upgrades.md                 1159 B  2ab5196d4f52
memory/synthesis/2026-11-12-consolidated-state.md 4077 B e76bf7d35048
memory/synthesis/2026-11-12-upgrade-round.md   1853 B ddf53e10a341
```

## Known deltas (r12 + Archivist r17)
- `v1-upgrades-round-3.md`: on Red, absent on Pale (Archivist).
- Absent on Red entirely: `memory/INDEX.md`, `memory/llm/*`, `memory/ops/*` (pre-this-file),
  `memory/portal/merge-pack.md`, `memory/portal/v1-inventory.md`. The Archivist-fixed versions of
  those two (post-r17, diff-verified on its seat) are canonical.
- Orchestrator r13 artifacts (TODO.md ROUND-13, BUNDLE-SHA256.txt regen, agents.json rebind)
  and Researcher's probes-external/ + smoke4 exist only in their seats — not on Red; union step picks them up.

## Runbook note (one-liner)
Broke: per-host memory trees diverged (subsets). Fix: post-re-drop union with newest-mtime-wins + sha256 verify per this spec.
