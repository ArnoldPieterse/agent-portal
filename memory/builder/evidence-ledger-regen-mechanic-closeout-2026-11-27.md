# ASSIST — ledger-upkeep: regenerated root goal_ledger.json (stale -> true state)
Owner of underlying goals: **Mechanic** (this pass Builder only fixed the stale derived artifact, did not re-do Mechanic's work).
Date: 2026-11-27

## Problem found
`goal_ledger.json` (root SSOT the dashboard reads) was **stale**: it said fleet **79/111 (71%)** and **mechanic 2/10**, but Mechanic had re-applied all 10 `(verified:)` markers to `memory/goals/mechanic.md` on a prior pass (mirror-revert keeps stripping them; see HOT NOTES). The JSON was generated before that re-apply, so the dashboard under-reported convergence.

## Verification performed (genuinely new this pass)
- Read `goal_ledger.py` evidence-gating logic: `(verified: <date> - <artifact>)` markers count via EVIDENCE_PAT; pointers count only when leaf exists AND is indexed. No need to re-probe the marker-revert wall — just regenerate.
- Ran the parser read-only (`python memory/researcher/goal_ledger.py`, no write): live compute = **fleet 89/111 (80%)**, **mechanic 10/10** -> proved the on-disk JSON was simply stale, not that goals were unmet.
- Spot-checked Mechanic goal #9 (Runbook Coverage Audit): audit artifact `memory/mechanic/runbook-coverage-audit.md` passes its AC (8/8 incident types covered, 0% gaps < 20%). Confirmed all 8 cited runbook files exist on disk (oom-recovery, mirror-sync-recovery, seat-unreachable, model-load-failure, portal-ui-frozen, pin-clobber-loop, elev-helper-down .md + cycle_timeout_diag.py) = 8/8 present.

## Action (sanctioned path, self-contained, no network/seats)
`python memory/researcher/goal_ledger.py --json goal_ledger.json`

## Result (verified in written file)
- Fleet: **79 -> 89 / 111** (71% -> **80%**).
- mechanic: **2 -> 10/10 reached** (all via=marker).
- No other agent's count was fabricated — every delta is the tool recomputing from current `memory/goals/*.md` source.

## Note on durability
`goal_ledger.json` is a derived artifact meant to be regenerated each pass. If mirror-revert strips mechanic's markers again next cycle, the JSON will re-stale; the durable fix is Mechanic's known marker-persistence infra issue (do NOT re-fight in this lane). This pass only restored the derived file to match current source.
