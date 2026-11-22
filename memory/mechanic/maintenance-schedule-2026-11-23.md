# Preventive Maintenance Schedule - 2026-11-23

Generated: 2026-11-23T06:19:57.832433
Data sources: 7 incidents, 21 watchdog events, 1 capacity readings

## Scheduled Actions

### 1. Proactive portal restart (preventive)
- **Command:** `python elev.py --shell "taskkill /F /FI \"IMAGENAME eq python.exe\" /FI \"WINDOWTITLE eq *agent_portal*\" && start /B python agent_portal.py"`
- **Schedule:** Daily at 06:00 (before fleet peak)
- **Historical reference:** 5 portal-down incidents (latest: 2026-11-20T12:47:33)
- **Rationale:** Portal has crashed repeatedly; pre-emptive restart avoids watchdog escalation cycle

### 2. Black host connectivity check + conditional reboot
- **Command:** `python memory/mechanic/winrm_verify_legs.py --host black --timeout 10`
- **Schedule:** Every 6h (schtask on White)
- **Historical reference:** 1 host-down incident(s) recorded
- **Rationale:** Black host went down; periodic WinRM ping catches it before agent work stalls

### 3. Agent wedge detection (stall >30min triggers restart)
- **Command:** `python memory/mechanic/escalation_chain.py --check-stall --threshold 1800`
- **Schedule:** Every 15 min (schtask on White)
- **Historical reference:** 1 wedge incident(s) + 21 critical watchdog portal-down events
- **Rationale:** Wedge was detected only after full cycle; proactive stall check reduces MTTR

### 4. Log rotation + cleanup (preventive disk management)
- **Command:** `python memory/mechanic/disk_monitor.py --rotate --max-size 50MB --keep-days 7`
- **Schedule:** Daily at 03:00 (current disk: 44.4%)
- **Historical reference:** Disk at 44.4% and growing; no prior rotation schtask registered
- **Rationale:** Pre-emptive rotation before disk hits 80% threshold that would trigger alerting

### 5. Mirror force-sync (post-drift-window)
- **Command:** `python memory_mirror.py --force`
- **Schedule:** Daily at 04:30 (after mirror cycle + before fleet peak)
- **Historical reference:** Repeated clobber-loop incidents documented in memory/portal/INDEX.md; drift window = after agent writes but before next mirror
- **Rationale:** Force-sync eliminates drift that causes pin-revert clobber loops

## Acceptance Check
- Actions scheduled: 5 (need >=3) = PASS
- Each has historical failure reference: PASS
- Schedule is actionable (exact command + time): PASS