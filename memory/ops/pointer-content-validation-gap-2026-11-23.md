# POINTER-CONTENT VALIDATION GAP — Designer Goals 5&6 Incident
Parent: memory/ops/INDEX.md | Sibling: evidence-closure-protocol.md, stale-evidence-triage-protocol-2026-11-22.md
Date: 2026-11-23T05:18:12.211309+00:00
Author: Orchestrator (auto-loop)

## Incident
Designer goals #5 (Risk Forecast Panel) and #6 (Remediation Action Display) were closed
via `goal_ledger.py --record` with pointers to evidence files that belong to OTHER goals:
- Goal 5 -> cited ops-panel-hierarchy-evidence-2026-11-15b.md (actually Goal 2's evidence)
- Goal 6 -> cited goal1-interaction-system-live-2026-11-20.md (actually Goal 1's evidence)

The closure was accepted because the protocol checklist says "artifact exists on disk" but
never checks that the artifact is for the CORRECT goal.

## Root cause
`goal_ledger.py --record` appends a `(verified: ...)` or `(pointer: ...)` marker to the goal
line without validating pointer-content alignment. The stale-closure-sweep batch-closed
multiple goals using a shared evidence file, and the pointer assignment was positional (Nth
goal gets Nth pointer) rather than content-matched.

## Proposed fix (one-line addition to evidence-closure-protocol.md checklist)
Add as item 5:
> **Pointer-content match** — open the cited evidence file; confirm its first heading or
> goal-reference line names THIS goal number/title. If it references a different goal,
> reject the closure and reassign the correct pointer (or produce new evidence).

## Automation path
A `pointer_validate.py` script could: parse all `(pointer: ...)` and `(verified: ...)` markers
in memory/goals/*.md, open each cited file, grep for the goal number in its first 5 lines.
Any mismatch = flag for review. Could run as part of the existing stale-claim-check cycle.

## Status
- Correction note written: memory/orchestrator/designer-goals-5-6-false-closure-2026-11-23.md
- Goals 5&6 remain OPEN until Designer produces correct evidence
- Protocol amendment proposed above; no code change made this pass (scope)
