# Dangling Pointer Integrity Repair - 2026-11-20 (Verifier, contribution c/d)

## What ran
`memory/verifier/dangling_pointer_scan.py` (reusable scanner; reuses goal_ledger.POINTER_PAT + validate_pointer).

## Before / After
Scanned all `(pointer: <relpath>)` refs in `memory/goals/*.md` and validated each leaf exists AND is index-connected.
- BEFORE: 31 dangling total. 3 in ACTIVE (live, ledger-counted) goal files:
  - memory/goals/orchestrator.md:15 -> memory/orchestrator/goal6-dependency-resolver-progress-2026-11-20.md
  - memory/goals/researcher.md:15  -> memory/researcher/evidence-quality-2026-11-20.md
  - memory/goals/scheduled-background.md:14 -> memory/mechanic/test_chaos_drill_sim.py
- FIX (additive-only, one index line each): appended the 3 leaves to memory/orchestrator/INDEX.md, memory/researcher/INDEX.md, memory/mechanic/INDEX.md.
- AFTER: `python memory/verifier/dangling_pointer_scan.py --active` -> pointers scanned 33, dangling (real) = 0. The single remaining hit is the literal string `relpath` inside a prose example in designer-open-set-reconciliation-2026-11-19.md L23 (explaining ledger logic), NOT a real reference - correctly classified non-actionable.

## Verification of no miscount
Ran goal_ledger.parse_agent_file on the 3 active files: every pointer line ALSO carried an inline `(verified:`/`PROGRESS ... recorded` marker, so reached-status was NOT under- or over-counted before the fix. This repair is integrity hygiene (clean live pointers), not a score change.

## Cross-lane value
Directly feeds Archivist open goal #2 (Cross-Reference Integrity Monitor: no dangling edges). The scanner is the ready-made detector; run it after each mirror cycle to catch regressions. Owner credit: Orchestrator (goal 6 leaf), Researcher (evidence-quality leaf), Mechanic (chaos drill sim) - their live pointers now resolve.

## Repro
`python memory/verifier/dangling_pointer_scan.py --active`   # expect: dangling (real): 0
