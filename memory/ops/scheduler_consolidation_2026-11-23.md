# Scheduler consolidation + popup elimination (2026-11-23)

## What changed
All periodic work now runs from ONE script: `portal_host.py` (windowless python.exe,
pid-file single-instance, self-supervising). It owns the timers for all 6 jobs
(gap_alarm 5m / fleet_probe 10m / reboot_recover 30m / maintenance_window+memory
1h / winrm_rotate 1d / schtask_dep_gen 7d) and restarts agent_portal.py if it dies.

## Boot persistence (NO scheduled tasks, NO UAC)
- `portal_host_launcher.vbs` — hidden one-shot launcher (`sh.Run ..., 0, False`).
- Copied to the user Startup folder as `PortalHost.vbs`; Explorer runs it at logon
  via wscript (invisible). Duplicate launches hit the pid-file guard and exit.
- Verified end-to-end: cscript run -> host logged `exit-duplicate`, no window/dialog.
- A real ONLOGON schtask was NOT created: non-admin cannot create it, and forcing
  UAC would reintroduce exactly the popup this work removes. Note: the elevated
  helper on :8098 currently runs as white\white (NOT SYSTEM) — elev.py "escalation"
  is inert until it is reinstalled elevated; admin jobs (winrm_rotate etc.) will
  report failure until then.

## Popup hardening (CREATE_NO_WINDOW on every child spawn)
Added `creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)` to all
subprocess.run/Popen calls in: gap_alarm.py, reboot_recover.py (incl. the portal
restart Popen), state_collector.py (nvidia-smi, powershell CPU, elev call),
maintenance_window.py (schtasks query + new host-alive check),
schtask_dep_weekly.py (both schtasks/dep_gen calls), oom_recovery.py (nvidia-smi x3,
taskkill, powershell kill), agent_portal.py cockpit nvidia-smi.

## Dashboard + health check
- ui/scheduler.js header now reads: "host script portal_host.py - boot:
  Startup-folder launcher - 0 periodic schtasks".
- maintenance_window.task_schtasks_health rewritten: asserts the 3 legacy fleet
  schtasks are ABSENT (re-appearance = double-running) and that a live
  portal_host process exists. Verified: status ok, host alive true.

## Files
portal_host.py (unchanged this pass), portal_host_launcher.vbs (new, clean ASCII -
a double-BOM version briefly caused a wscript error dialog; fixed),
memory/ops/host-log.jsonl (evidence), ui/scheduler.js, the 7 hardened scripts above.
