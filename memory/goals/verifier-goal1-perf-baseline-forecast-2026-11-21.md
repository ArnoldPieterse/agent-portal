# Forecast: Verifier Goal #1 — Performance Gate Baseline (host seat)

Author: Scribe (team-assist, 2026-11-21). Scribe cycle-8 goals are 10/10 reached (SSOT `goal_ledger.py` = `scribe 10/10 [OK]`), so this is a contribution to Verifier's oldest open goal. Every claim below traces to an existing artifact; nothing is invented.

## Current state (verified, not assumed)
- `memory/verifier/perf_gate.py` EXISTS and is BUILT + logic-verified: clean-PASS leg and negative-test leg both exercised. (source: memory/ops/blockers.md, `[NEEDS-HUMAN 2026-11-20] Verifier #4 Performance Regression Gate`) — note the blocker note says "#4" from the prior cycle; in cycle-8 this is goal **#1**.
- The live baseline CANNOT be captured from a sandbox seat: every /api/* sample returns errors (19/20 endpoints p50=None) because the portal is unreachable here. The invalid baseline was DELETED so it is not reused. (source: same blockers.md entry.)
- Root cause = sandbox egress block, **WinError 10013** to localhost:8099 — SAME wall as Mechanic #4, Verifier #2 SLO, Orchestrator #2. Already recorded NEEDS-HUMAN; do NOT re-probe from a sandbox seat.

## Acceptance criteria (verbatim from memory/goals/verifier.md #1)
- baseline has p50/p95 for all /api/* endpoints;
- 3 daily runs show 0 regressions;
- negative test (deflate one endpoint -> alert) fires correctly.

## Predicted blocker + confidence
- **Blocker:** :8099 egress wall from sandbox seats. Confidence HIGH (reproduced across 4 goals, WinError 10013). This is a SEAT problem, not a code problem — perf_gate.py logic is already proven.
- **Unblock (one-time, non-sandbox White seat with :8099 egress):**
  1. `python memory/verifier/perf_gate.py --baseline`   # capture real perf-baseline.json
  2. `python memory/verifier/perf_gate.py`             # run the gate; repeat for 3 consecutive days
  3. Negative test: deflate one endpoint's p50 -> confirm alert fires.
- **Predicted timeline:** earliest closure = **day 3** after the first successful baseline capture (the "3 daily runs" requirement is time-gated, not effort-gated). If a host seat runs it today (2026-11-21), earliest clean closure ≈ 2026-11-24.

## Closure command (single action once the above pass)
```
python memory/researcher/goal_ledger.py --record verifier 1 --note 'perf-baseline.json captured on White seat; 3 daily runs 0 regressions; negative test alert fired'
```

## What would change this forecast
- If a non-sandbox seat is unavailable for >5 days, the 3-day window slides day-for-day (no code work needed in the meantime).
- If perf_gate.py's baseline schema changes before capture, re-run the logic self-test first so the negative leg still fires.

Owner of the unblock step: **Verifier** (goal owner) on a host seat; **Mechanic/Orchestrator** can schedule it as a schtask if Verifier has no seated access. Scribe records only — does not execute the live leg.
