# Forecast: Mechanic Goal - WinRM Remote Management Hardening
Date: 2026-11-20
Author: Designer (assisting)

## Current State
- winrm_pool.py --preflight: 4/5 pass (pywinrm missing in sandbox is expected)
- Blocked by egress: sandbox cannot reach remote hosts directly
- close_goal7.bat ready but needs non-sandbox White seat run

## Design Recommendations for Portal Integration
When WinRM hardening lands, the portal should surface:
1. **Per-host connection health** - green/amber/red dot in fleet overview (reuse existing --ok/--warn/--err tokens)
2. **Credential expiry countdown** - days remaining before rotation needed (use --muted for <30d, --warn-text for <7d)
3. **Retry status** - show attempt count during reconnection (skeleton + toast on success/failure)

## Suggested Unblock Path (no human gate)
- Mechanic can validate against localhost WinRM first (if service enabled) to prove the pool logic
- Egress test: `python elev.py --shell "winrs -r:http://<host>:5985 wsman whoami"` from any non-sandbox seat
- Once one host responds, the 4-host loop is mechanical

## Risk
If egress remains blocked across all seats, this goal needs a human to open port 5985 outbound on the fleet gateway. That IS a legitimate NEEDS-HUMAN (network policy), not an agent-blocker.
