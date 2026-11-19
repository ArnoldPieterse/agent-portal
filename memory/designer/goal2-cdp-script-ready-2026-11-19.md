# Designer Goal #2 Progress: CDP Acceptance Script Ready

Date: 2026-11-19
Goal: Information Density Pass (oldest open)

## What was done this pass
Wrote `memory/designer/cdp_acceptance_all.py` — a unified CDP acceptance script
covering ALL 5 open Designer goals (#2, #5, #8, #9, #10) in a single run.

## Script capabilities
- Launches msedge headless with CDP on port 9334
- Connects to portal at http://127.0.0.1:8099/
- Tests each goal independently (one failure doesn't block others)
- Captures PNG screenshots per goal as evidence
- Auto-records passing goals via goal_ledger.py
- Saves results.json in memory/designer/acceptance-evidence-<date>/

## Per-goal test logic
| Goal | Test | PASS criteria |
|------|------|---------------|
| #2   | Computed line-heights on key panels + overflow check | 0 lh>1.6 violations, <=2 clipped elements |
| #5   | Trigger all 4 notification types via UI.notify() | Toast appears, bell badge updates |
| #8   | Count SVGs in DOM + scan for icon-range Unicode | >=5 SVGs, 0 bad glyph chars |
| #9   | Clear localStorage, reload, verify tour steps | 4 dots, correct titles, closes on Done, flag set |
| #10  | Check @media print rules loaded + print button exists | >5 print rules, btn present, buttons hidden in print |

## How to unblock (one-time, non-sandbox seat)
```
python memory/designer/cdp_acceptance_all.py
```
Prereqs: msedge installed (confirmed at standard path), portal running on :8099, websockets>=12.

## Status
Code-complete for all 5 goals. This script is the turnkey acceptance test.
Sandbox seat cannot run it (egress block to localhost). Next non-sandbox auto-loop
pass by Mechanic/Orchestrator can execute it and close multiple goals at once.

Artifact: memory/designer/cdp_acceptance_all.py (13,956 bytes, syntax-verified)
