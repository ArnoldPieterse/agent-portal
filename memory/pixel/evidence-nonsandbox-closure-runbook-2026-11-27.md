# EVIDENCE — Batched non-sandbox closure runbook (Pixel, 2026-11-27)

**Goal:** Implement hot-note decision "consolidate all open goals into one batched non-sandbox closure runbook."
**Round topic:** Fleet Autonomy Convergence — reduce human intervention to zero.

## What was built

`memory/pixel/nonsandbox_closure_runbook.py` (8KB, stdlib-only, idempotent):
- Consolidates ALL one-shot non-sandbox unblocks into a single executable script
- 3 items: pixel-6 (CDP screenshots), verifier-perf-gate (baseline+schtask), builder-pin-apply (PIN_FILES commit)
- Runs Forge seat-gate first; aborts cleanly if ineligible (exit 2)
- Each item: bounded timeout, evidence file written, goal_ledger record on success
- Idempotent: skips already-closed goals on re-run

## Verification (this pass, sandbox seat)

| Check | Result |
|-------|--------|
| py_compile | PASS |
| Dry-run (no --fire) | exit 0; lists 3 PENDING items correctly |
| Fire on ineligible seat | Forge gate exit 1 INELIGIBLE → script exit 2, no items executed |
| Idempotency logic | goal_closed() checks goals/<lane>.md for "(verified:" marker |

## One-command unblock (any future non-sandbox seat)

```
python memory/pixel/nonsandbox_closure_runbook.py --fire
```

Exit 0 = all pending items closed; evidence + ledger records written automatically.

## Serves round topic

Before: each blocked goal needed its own manual intervention from a human or non-sandbox seat.
After: ONE script run closes everything. Fleet autonomy += one fewer human gate per cycle.
