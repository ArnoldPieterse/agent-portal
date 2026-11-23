# Scheduler consolidation + popup elimination (2026-11-23)

## What changed
- **One auto-start entry, everything else in-process.** The PortalRun schtask (old
  wscript -> cmd -> portal_guardian.py chain) is DELETED. Boot path is now a per-user
  Startup-folder VBS: %APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\portal_host.vbs
  (copy of memory/ops/launch_host.vbs) -> windowless python portal_host.py.
  No elevation needed (schtasks /create in \\ root folder is admin-only; the :8098
  elev helper runs unelevated white\\white - verified).
- **portal_host.py** supervises: portal process (respawn if :8099 down), the in-process
  scheduler thread (all 6 cycle jobs via run_steps.py), and OOM watch.
- **oom_loop fix:** oom_recovery.py 'watch' is ONE-SHOT (exits by design) - the host now
  runs it every 5 min as a subprocess instead of treating it as a daemon (the old code
  respawned it every 60 s, logging a dead pid each time).
- **Popup root cause fixed:** memory/ops/run_steps.py spawned steps with bare
  subprocess.run -> a console window + focus steal per step per cycle. Now
  creationflags=CREATE_NO_WINDOW. (Scheduler's own spawn already had NO_WINDOW.)
- **UI->host action queue:** POST /api/scheduler {job, action} now queues to
  memory/ops/scheduler-cmd.json; host drains within ~5 s and calls portal_scheduler.action
  (run/pause/resume). Verified end-to-end: run-now on cycle_5m fired at the next tick.
- **Launch-path updates** (PortalRun references): reboot_recover.py, recover_all.py,
  restart_portal.py, failover_drill.py -> wscript launch_host.vbs.
- **Archived:** portal_guardian.py + portal_watchdog.py -> archive/orphaned_20261123/
  (dead chain). Stale fleet backups (Nov19-20, 283 MB) + stale dedup/freshness reports
  (Nov20, ~49 MB) -> archive/bloat_20261123/. memory tree 517 MB -> 194 MB (size_guard OK).

## Verified
- Single-instance guard: second VBS launch logs exit-duplicate, exactly one host.
- cycle_30m rc=0 with patched reboot_recover; size_guard now passes.
- All patched files py_compile clean.

## Follow-ups
1. No fleet backup newer than 2026-11-20 existed when the old ones were archived -
   confirm what is supposed to create daily fleet backups (none of the 6 cycle jobs does).
2. memory/ops/merge-queue holds 127 near-duplicate agent_portal.py snapshots (~20 MB,
   all dated today) - something re-queues the file every edit; find and stop the source.
3. Dashboard header still says "1 schtask: PortalRun -> guardian" - locate that string
   (not in index.html/agent_portal.py as of this note) and update the label.
