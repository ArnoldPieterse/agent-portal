# Goal #4 Status — Auto-loop pass 2026-11-17 ~18:05 AEST

## State
- Real baseline data: **2/7 days** (Nov 16, Nov 17) in memory/ops/load-baseline.jsonl
- Synthetic 7-day test file exists (load-baseline-test-7day.jsonl) — used for week-report validation only
- Pipeline health: **OK** — load_probe.py runs, correctly detects sandbox outage (PermissionError :8099), writes to load-outage.jsonl without corrupting baseline
- Schtask on White: registered for daily auto-collection (non-sandbox seat with LAN access)
- Regression demo: 3/3 verified (see goal4-regression-demo-2026-11-17.json)

## Blocker
Sandbox cannot reach localhost:8099 (WinError 10013 - socket access forbidden by firewall). Data collection must happen from a LAN-connected seat. White schtask handles this automatically.

## Next concrete step (next pass)
Check if load-baseline.jsonl has gained a 3rd day. If yes, continue monitoring. At 7 days + regression demo = goal close via ledger --week-complete mode.

## Runbook note
Sandbox firewall blocks outbound TCP to :8099; probe correctly classifies as outage and does NOT write to baseline. No action needed from sandbox seat — White schtask is the collection path.
