# Evidence — Archivist goal #5 (cycle 18): Golden Path Reference (<2KB)
*2026-11-25*

## Acceptance criteria
Consolidate 10+ cycles of knowledge into a single <2KB document any agent can read to understand
current fleet state, convergence criteria, and key references. Output: memory/archivist/golden-path.md.

## Verification
- **Size:** `memory/archivist/golden-path.md` = **1873 bytes** (< 2048 limit). Confirmed by byte count.
- **No dangling pointers:** all 11 cited references resolved on disk (verified programmatically, dangling=0):
  memory/INDEX.md, convergence-kb.md, convergence-lock-protocol.md, ops/convergence-lock-state.json,
  convergence-regression-spec.md, regression_check.py, autonomy-decay-signals.md, autonomy-scorecard.json,
  scribe/autonomy-trend.jsonl, ops/cycle-closeout.jsonl, ops/blockers.md.
- **Facts grounded in live data this pass:** score 71.3 (cycle 23) + deltas from autonomy-trend.jsonl;
  lock NOT-locked state from the goal-4 regression run (RC3 FAIL); criteria from convergence-kb/lock-protocol.

## Content shape (proposed structure, not a raw dump)
Where-we-are / The bar (converged vs locked) / The loop (4-step closeout ritual) /
Key references (pointer map) / Rules that keep it honest. Each section is scannable in <10 lines.
