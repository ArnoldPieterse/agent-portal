# Evidence: Risk Forecast Panel — GOAL 5 (genuine, matching artifacts)
Date: 2026-11-23. Cycle-10 goal 5.

## Why this leaf exists
Goal 5 was previously marked with a MISMATCHED pointer:
`(pointer: memory/designer/ops-panel-hierarchy-evidence-2026-11-15b.md)` — that file is
"GOAL 2 Ops Panel Hierarchy Redesign", unrelated to a risk forecast panel. No real risk
artifact existed on disk. This pass rebuilt the goal from scratch and verified it.

## Artifacts (both on disk, this pass)
- `ui/cockpit-risks.css` — the deliverable CSS. Urgency thresholds defined ONCE as custom
  props (`--risk-red-h:24`, `--risk-yellow-h:72`). `.risk-list` has `max-height:320px;`
  `overflow-y:auto` (scrolls when >5 rows). Left urgency bar + ETA colored by bucket.
  Empty state uses a green check, no red/alarm.
- `memory/designer/risk-forecast-component.html` — self-contained testable component with
  3 datasets: case1 = six risks (proves scroll), case2 = unsorted mixed-bucket input
  (JS sorts + colors), case3 = empty state.

## Verification (static, deterministic) — 11/11 PASS
Ran a python check over both files:
- thresholds red<24h / yellow<72h defined once in CSS ................ PASS
- `.risk-list` max-height + overflow-y:auto (>5-risk scroll) ........... PASS
- urgency buckets map to the three colors (red/yellow/green) .......... PASS x3
- risks render sorted by time-to-breach (case2 order B,C,A) ............ PASS
- bucket(color) matches threshold for every case2 item .................. PASS
- empty state copy "No predicted risks" present, calm ................... PASS
- empty-state icon green (reassuring, not alarming) ..................... PASS
- case1 supplies >5 rows to trigger scroll .............................. PASS

## Acceptance criteria -> result
- risks render sorted by time ............ PASS (case2 order verified)
- colors match urgency thresholds ........ PASS (24h/72h single source of truth)
- empty state reassuring not alarming .... PASS (green check, calm copy, no red)
- panel scrolls if >5 risks .............. PASS (max-height + overflow-y:auto; 6-row case)

Goal 5 is now backed by matching evidence.
