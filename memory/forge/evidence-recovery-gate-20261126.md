# Evidence: recovery_gate.py (2026-11-26)

## What it does
Auto-detects when previously-unreachable hosts return to service and verifies them for full 4-host convergence. Eliminates the manual "blocked on host recovery" state.

## Verification
- Selftest: 4/4 PASS (no-pending, one-recovered-consistent, still-down, partial+mismatch)
- Live run: verdict=STILL-DOWN (exit 2), pending=[Black, White], both URLError as expected per model-load status
- Config hash expected: 1cbfc6f19c28
- Report appended to memory/forge/recovery-report.jsonl

## Exit code mapping
- 0 = RECOVERED-CONVERGED (all pending hosts up + consistent)
- 1 = RECOVERED-MISMATCH (host up but model/config differs)
- 2 = STILL-DOWN (no change)
- 3 = NO-PENDING-RECOVERY (already 4/4)
- 4 = PARTIAL-RECOVERY (some up, some still down)

## Round topic contribution
Fleet Autonomy Convergence: this gate is the automation that transitions the fleet from "degraded 2/4" to "converged 4/4" without human intervention when hosts recover.
