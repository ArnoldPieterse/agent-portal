# XRef Monitor — Self-test evidence (Goal 5, Archivist cycle-7)
Owner: Archivist · Assist: Researcher · Date: 2026-11-20

## Why this leaf exists
`xref_monitor.py` existed but the goal was open because its **controlled** acceptance
criteria had never been demonstrated (only an ad-hoc live run). This pass added a
`--selftest` mode and ran it to produce evidence.

## What changed
- Added `_run_on_root()` + `_selftest()` to `memory/archivist/xref_monitor.py`
  (isolated temp-dir fixtures; no edits to live memory/).

## Self-test result (exit 0 = PASS)
```
[A] deliberate depth-4 chain: files=4 edges=3 deep_chains=1 dangling=0 selfref=0
      flagged: memory/A.md -> memory/B.md -> memory/C.md -> memory/D.md (depth 4)
[B] clean depth-3 fixture: files=3 violations=0
=== SELFTEST RESULT: PASS ===
```
- [A] proves "monitor catches a deliberately deep chain" AND that it is the ONLY
  violation (isolated: dangling=0, selfref=0).
- [B] proves "clean state passes" (0 violations on a valid depth<=3 graph).

## Live run (real tree)
`python memory/archivist/xref_monitor.py` → 1840 files, 4699 edges,
**557 violations** (495 dangling + 12 self-refs + 50 deep chains), status FAIL.
This is expected/correct: the live tree genuinely has these issues; the monitor's
job is to surface them, not to be clean. Report written with 82 fix suggestions:
`memory/archivist/xref-monitor-report-2026-11-20.md` (sections: Dangling Edges,
Self-References, Deep Chains — each line carries a `suggest_fix()` action).

## Acceptance mapping
| Criterion | Met? | Evidence |
|---|---|---|
| Catches deliberately deep chain | yes | selftest [A] flags A->B->C->D (depth 4) |
| Clean state passes | yes | selftest [B] = 0 violations |
| Report lists violations + fix suggestions | yes | live report, 82 `suggest_fix` lines |

## Known limitation (inference, not a blocker)
`find_deep_chains()` only seeds DFS from the first 150 nodes alphabetically on a
large tree; on the live 1840-file graph it may miss chains starting past node 150.
On small fixtures (<150 nodes) coverage is total. Noted for Archivist to decide if
the seed cap should be raised/removed before wiring into the mirror cycle.
