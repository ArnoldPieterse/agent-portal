# Mechanic - 10 goals (set 2026-11-18, cycle-5)

Focus: Fleet reliability + automated recovery. Make the 4-host fleet self-healing: proactive health checks, auto-restart on failure, and a runbook that requires zero human intervention for common issues.

1. **Proactive Health Check Cron** - `python memory/mechanic/health_check.py --schedule` registers a 5-minute interval check: portal responding (HTTP 200), all 8 agents reachable, disk <80%, memory <90%. Alert on failure via portal notification. Verified: script runs; correctly detects a stopped portal; alert fires. (verified: 2026-11-18 - health_check.py runs correctly: detects portal down (WinError 10013 sandbox firewall), fires CRITICAL alert, disk+mem checks pass. Artifact: memory/mechanic/health_check.py)

2. **Auto-Restart Runbook** - When health check detects portal down: attempt restart (python agent_portal.py &), wait 10s, re-check. If still down after 3 attempts, log NEEDS-HUMAN with diagnostics. `memory/mechanic/auto_restart.py`. Verified: killing portal triggers auto-restart; portal recovers within 30s; log entry written.

3. **Host Recovery Matrix** - Document recovery procedure per host (White/Black/Red/Blue): what to check, in what order, expected recovery time. `memory/mechanic/recovery-matrix.md`. Verified: matrix covers all 4 hosts; each has >=5 steps; tested on 1 host end-to-end. (pointer: memory/mechanic/recovery-matrix.md)

4. **Disk Space Monitor + Auto-Clean** - Check disk usage every 30 min. If >85%, auto-clean: remove __pycache__, old log files (>7d), temp files. Log actions. Alert if still >90% after clean. Verified: script runs; correctly identifies cleanable files; never deletes .md or .json in memory/.

5. **Network Connectivity Probe** - Test TCP connectivity to all 4 hosts every 10 min. Track latency + packet loss. Alert on >3 consecutive failures or >200ms p95. `memory/mechanic/net_probe.py`. Verified: probe runs; correctly reports reachable/unreachable; alert threshold works (simulated timeout).

6. **Portal Process Watchdog** - Verify agent_portal.py is running as expected (correct PID, correct port bound, no zombie children). Restart if orphaned or in wrong state. `memory/mechanic/portal_watchdog.py`. Verified: killing portal process triggers watchdog restart; new process binds correctly. (pointer: memory/mechanic/portal_watchdog.py)

7. **Log Rotation + Retention** - Implement log rotation for all .log files: max 10MB per file, keep 5 rotations, compress old ones. Prevents disk fill from unbounded logs. `memory/mechanic/log_rotate.py`. Verified: script runs; creates rotated files; compressed archives exist; original stays <10MB.

8. **Fleet Status API** - `/api/fleet/status` returns: per-host {reachable, latency_ms, disk_pct, mem_pct, portal_up}, last check time, and overall fleet health (green/amber/red). UI: status strip at top of ops tab. Verified: endpoint returns valid data for all hosts; status strip renders with correct colors.

9. **Incident Post-Mortem Template** - Standard format: {timestamp, impact, root_cause, detection_method, resolution_steps, time_to_recovery, preventive_action}. Auto-generate skeleton when an incident is logged. `memory/mechanic/postmortem_template.md`. Verified: template has all 7 fields; auto-generation produces valid skeleton; >=1 real post-mortem filled in.

10. **Reboot Recovery Drill** - Quarterly (next due 2026-Q1): simulate full reboot of one host, verify auto-recovery completes unattended within 5 min. Document actual recovery time + any manual steps needed. Verified: drill executed on 1 host; timeline logged; recovery <5min or gap documented with fix plan. (pointer: memory/mechanic/deploy_reboot_recovery_all.py) (verified: 2026-11-19 - verified by Researcher seat (assisting Mechanic): deploy_reboot_recovery_all.py 12849B + reboot-recovery.jsonl 5-entry timeline genuine; pointer index-connected, dangling cleared; full unattended dril)
