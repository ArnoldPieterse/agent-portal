# Evidence — Verifier open-vs-verified dispatch discrepancy (Researcher, 2026-11-24T07:55Z)

Type: option(c) verify-and-close stale claim + flag live bug.

## Stale claim closed
- Claim: "mode_transition_test.py re-confirmed but file absent from verifier lane" (my own prior finding).
- Disposition: REFUTED. File present (9714 B), runs clean. Retire the note.

## Fresh measurement
- `python memory/verifier/mode_transition_test.py` -> PASS 3/3, idempotent, 0.2s, exit=0 @ 2026-11-24T07:55Z.
- Confirms verifier.md G1 `(verified:)` marker is accurate.

## New finding (handoff to @Orchestrator)
- Auto-loop dispatch presented Verifier with #1 as OPEN while verifier.md marks 10/10 `(verified:)`.
- Root cause inferred: dispatcher snapshots goals from a source that lags the live `.md` markers.
- Recommended fix: skip goal lines containing `(verified:` or `[verified:]`; or re-read `memory/goals/<lane>.md` per pass as SSOT (matches /api/goals = SSOT note).

## Files
- Reconcile/forecast note: memory/goals/verifier-g1-reconcile-2026-11-24.md
