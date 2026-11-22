# Mechanic Goal #3 - RED Leg: Documented Failure (2026-11-15)

## Status: BLOCKED by sandbox network (documented per Arnold instruction to move on)

## Exact failure
- **Host**: Red ([redacted-LAN-IP])
- **Error**: WinError 10013 (not privileged) on outbound TCP from White sandbox
- **Reproduced**: 2026-11-15 ~23:xx - socket.connect_ex(('[redacted-LAN-IP]',445)) -> blocked/timeout
- **Root cause**: White sandbox has no outbound TCP egress to LAN subnets; Windows firewall blocks it
- **Impact**: Cannot execute reboot-recovery dry-run steps on Red from this seat

## What was completed (all other legs)
- WHITE leg: all 5 steps OK, logged memory/ops/verifier-healthcheck-white-2026-11-15.md
- PALE leg: fixed via JWT auth, all steps OK
- BLACK leg: green, all steps OK

## Unblock path (for non-sandbox seat)
Run the 5-step reboot-recovery dry-run manually on Red:
1. Verify portal process: `tasklist | findstr python`
2. Check port: `netstat -an | findstr :8099`
3. Tail log: last 20 lines of agent_portal.log
4. Verify SMB share accessible
5. Confirm scheduled tasks: `schtasks /query /tn PortalDailyGitCommit`

## Verdict
3/4 legs complete (White, Pale, Black). Red blocked by sandbox network restriction - NOT a runbook defect.
Runbook itself is validated on 3 hosts; the 4th requires non-sandbox execution.


---
CORRIGENDUM (hostdoc-consistency-v2 2026-11-18): script/log paths referenced here were seat-local ephemeral artifacts, never committed to the repo.
