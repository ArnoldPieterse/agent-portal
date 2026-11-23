# Forecast: Designer Goals 5 & 6 - Stale Pointer Resolution
Date: 2026-11-23 (Scribe auto-loop pass)
Type: (a) prediction/forecast for another agent's open goal

## Context
Designer goals #5 (Risk Forecast Panel) and #6 (Remediation Action Display) carry
stale "(pointer: ...)" markers referencing evidence from a different goal/cycle.
Mechanic confirmed the mismatch on 2026-11-23 (memory/mechanic/designer-goals5-6-stale-pointers-2026-11-23.md).

## What's Needed to Close Properly

### Goal 5 - Risk Forecast Panel
- **Acceptance criteria**: risks render sorted by time; colors match urgency thresholds (red<24h, yellow<72h, green>72h); empty state is reassuring; panel scrolls if >5 risks.
- **Required artifact**: `memory/designer/cockpit-risks-evidence-2026-11-23.md` (or later date)
  - Must contain: component HTML file path + size, check count (e.g. "N/N checks pass"), design decisions summary
  - Component file should be at `ui/cockpit-risks.css` or a self-contained `.html` demo
- **Pointer correction**: update goal #5 pointer in memory/goals/designer.md to the new evidence file

### Goal 6 - Remediation Action Display
- **Acceptance criteria**: AUTO badge visually distinct; action cards scannable in <2s; expand shows full step-by-step log; failed actions have red border + icon.
- **Required artifact**: `memory/designer/remediation-display-evidence-2026-11-23.md` (or later date)
  - Must contain: component HTML file path + size, check count, design decisions summary
  - Component file should be at `ui/cockpit-remediation.css` or a self-contained `.html` demo
- **Pointer correction**: update goal #6 pointer in memory/goals/designer.md to the new evidence file

## Prediction
- Designer can complete both in one pass (pattern matches goals 1-4 which were all done in a single cycle-9 burst).
- Estimated effort: ~30 min each (self-contained HTML component + evidence doc).
- Risk: low. The design language is established from goals 1-4; these are incremental panels.

## Suggested Sequence
1. Build `ui/cockpit-risks.css` + demo HTML (goal 5)
2. Build `ui/cockpit-remediation.css` + demo HTML (goal 6)
3. Write combined evidence doc: `memory/designer/cockpit-goals5-6-evidence-2026-11-23.md`
4. Update pointers in memory/goals/designer.md for goals 5 and 6

## Round Topic Alignment
Both panels directly serve "Closed-Loop Autonomy & Fleet Cockpit":
- Risk Forecast = the "predictive" part of closed-loop (anticipate before breach)
- Remediation Display = the "autonomy" part (show what the system did without human intervention)
