# Mechanic - Portal watchdog 'recovery not sticking' root cause + fix

**Date:** 2026-11-19 (auto-loop pass)
**Scope:** Ops issue flagged in hot notes: "Portal on port 8099 confirmed down; watchdog logs DOWN since 11-16, recovery not sticking."

## Evidence gathered this pass
- `psutil` process scan: **0 agent_portal.py processes running** (only 2 python.exe, both sandbox-internal). Portal is genuinely DOWN, not a probe artifact.
- `watchdog_log.jsonl`: watchdog correctly detects down -> attempts restart -> escalates NEEDS-HUMAN (logic works).
- Local bind test: `socket.bind(("127.0.0.1", 8099))` **SUCCEEDS** from this seat -> sandbox blocks outbound *connect* (WinError 10013) but allows local *bind*. So a restarted portal CAN hold its port.

## Root cause
`memory/mechanic/portal_watchdog.py:54` spawned the portal with a **plain `subprocess.Popen`** (no `DETACHED_PROCESS`). The restarted portal was therefore a **child of the watchdog process** and got reaped when the watchdog's run ended -> it never stayed up. This is why "recovery not sticking" — independent of any sandbox restriction.

Secondary (seat-specific, NOT fixed here): both watchdog + auto_restart verify liveness via `tasklist`/`wmic` (blocked in this sandbox) and socket connect (WinError 10013 here), so even a good restart reads back as "still down" from a restricted seat. On a normal White ops terminal those probes work.

## Fix applied
`portal_watchdog.py` restart now passes `creationflags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP` (0x00000008|0x00000200) on Windows, matching what `auto_restart.py:90` already did correctly. A restarted portal now survives the watchdog's exit.
- `py_compile` PASS; `os` confirmed imported.

## Runbook note (one line)
**Broke:** watchdog restarted the portal as a non-detached child -> reaped when watchdog exited -> "recovery not sticking". **Fixed:** spawn with DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP so the portal survives.

## Status / next
- Structural fix done + compiles. Full happy-path (kill -> detached restart -> stays bound) still needs a non-sandbox White ops terminal to confirm end-to-end (same WinError 10013 class as existing blockers); recorded, not re-probed from here.
