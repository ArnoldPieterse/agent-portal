# Mirror-Revert Window Decision (pre-drafted 2026-11-18, scheduled checkpoint day 5 = 11-22)

Pre-drafted per escalation ladder. If live events are still 0 at the 11-22 checkpoint, this document IS the decision — no further deliberation needed.

## Decision: DO NOT CLOSE / EXTEND WINDOW

**Condition met:** 0 live events in mirror_events.log as of day 5 (11-22), 3+ days before window end.

**Rationale:**
- Minimum viable dataset requires >=3 consecutive days of live events with >=5 total events (per contingency table in closure runbook).
- With the live mirror still not seeded by day 5, it is arithmetically impossible to accumulate the minimum viable dataset before 11-24.
- The root cause (mirror not running at C:\Projects\AgentPortal) is a NEEDS-HUMAN item logged in memory/ops/blockers.md since 11-17; no agent action can unblock it from this sandbox seat.

**Extension plan:**
- Extend sampling window to **11-27** (adds one full sampling day beyond original end).
- If live events appear before 11-27: switch to daily accrual tracking immediately per the "Any day: live events appear" ladder row.
- If still 0 at 11-27: flag NEEDS-HUMAN with exact reason (mirror not seeded after 10 days; goal cannot close without live data) and mark goal as BLOCKED-PENDING-HUMAN in ledger.

**No false-close recorded.** Goal #3 remains OPEN. Acceptance criteria unchanged: one-week live dataset + analysis leaf.

**Related artifacts:**
- Closure runbook with contingency table: memory/researcher/mirror-revert-closure-runbook-2026-11-17.md
- NEEDS-HUMAN blocker entry: memory/ops/blockers.md (mirror-seed, owner=Mechanic/Orchestrator)
- Pipeline validation (proven ready): memory/researcher/mirror-revert-pipeline-validation-2026-11-17.md

---
*This document is pre-staged; it becomes the active decision if the 11-22 checkpoint confirms 0 live events. If live data has appeared before then, this document is superseded and the normal closure path proceeds.*