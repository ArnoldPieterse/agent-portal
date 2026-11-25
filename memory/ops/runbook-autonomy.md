# Fleet Autonomy Runbook

Operational guide for maintaining fleet autonomy at >80%.
Hosts: **White** (primary), **Red**, **Pale**, **Black**.
Cross-refs: `pre_cycle_gate.py`, `convergence_alert.py`.

---

## 1. Monitoring Cadence

| What | How Often | Command | Expected Output |
|------|-----------|---------|-----------------|
| Autonomy score | Every cycle start | `python memory/orchestrator/autonomy_score.py` | JSON with `score` field in [0,100] |
| Pre-cycle gate | Before each cycle | `python memory/ops/pre_cycle_gate.py` | Prints PASS/FAIL per check; writes `pre-cycle-gate.json` |
| Convergence alerts | Every 5 min (scheduled) | `python memory/ops/convergence_alert.py` | Silent on healthy; appends to `alerts.jsonl` on deceleration |
| Fleet metrics | Every 10 min | `python memory/ops/fleet_stats_collect.py` | Appends row to `fleet-metrics.jsonl` with all 4 hosts |
| Blocker scan | Every cycle | `grep -c "NEEDS-HUMAN\|BLOCKED" memory/ops/blockers.md` | Count of open blockers (target: 0) |
| Steady-state check | Every cycle | `python memory/builder/steady_state_scheduler.py` | Exit 0; may log cadence change to `cadence-changes.jsonl` |

---

## 2. Escalation Triggers

| Severity | Trigger | Action | Owner |
|----------|---------|--------|-------|
| **INFO** | Score 75-80% | Log observation; no action | Auto (convergence_alert) |
| **WARN** | Score < 75% or drop > 5 pts in one cycle | Alert to `alerts.jsonl`; next cycle prioritizes recovery | Orchestrator |
| **CRITICAL** | Score < 60% or drop > 10 pts | Pre-cycle gate FAIL; halt new goal assignments until recovered | Mechanic + Builder |
| **EMERGENCY** | Any host unreachable for >30 min | Failover seat assignment; log to `alerts.jsonl` severity=critical | Mechanic |

Score thresholds are checked by `pre_cycle_gate.py` (check c) and `convergence_alert.py`.

---

## 3. Recovery Procedures per Failure Mode

### 3a. Host Down (any of White/Red/Pale/Black)
```
# Probe the host (5s timeout each):
python memory/ops/fleet_probe_v2.py --host Red
# Expected: {"name":"Red","alive":true,"latency_ms":<100}

# If dead, re-register model load:
python elev.py --shell "winrs -r red-host 'net start ModelServer'"
# Expected: exit 0; retry probe after 30s
```

### 3b. Portal API Unresponsive (:8099)
```
# Check if process alive:
tasklist /fi "imagename eq python.exe" | findstr /i portal
# If dead, restart via scheduled task:
python elev.py schtasks /run /tn PortalLoadProbe
# Verify recovery (should respond <200ms):
python memory/ops/pre_cycle_gate.py  # endpoints check should PASS
```

### 3c. Model Server Unresponsive (:8888)
```
# Probe model endpoint:
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8888/
# Expected: 200

# If 000 or timeout, check VRAM on host:
python memory/ops/fleet_probe_v2.py --host White --detail
# If VRAM >95%: unload other models first
python elev.py --shell "winrs -r white-host 'nvidia-smi --query-compute-apps=pid --format=csv'"
```

### 3d. Autonomy Score Drop (>=10 pts)
```
# Diagnose: check intervention log for spike:
tail -20 memory/ops/human-interventions.jsonl
# Check which host degraded:
python -c "import json;[print(l['host'],l.get('gpu_usage_pct')) for l in open('memory/ops/fleet-metrics.jsonl').readlines()[-4:]]"
# Run full regression to find broken component:
python memory/builder/test_autonomy_infra.py
```

### 3e. Scheduled Task Missed
```
# List all fleet tasks and their last run time:
schtasks /query /tn PortalLoadProbe /fo list /v | findstr "Last Run"
schtasks /query /tn MirrorSync /fo list /v | findstr "Last Run"
schtasks /query /tn VerifierSLO /fo list /v | findstr "Last Run"
# If stale >2x cadence, force-run:
python elev.py schtasks /run /tn <TaskName>
```

---

## 4. Scheduled-Task Maintenance Checklist

Run at start of each new week (or after any host reboot):

```bash
# 1. Verify all 3 core tasks registered:
schtasks /query /fo csv /nh | findstr /i "PortalLoadProbe MirrorSync VerifierSLO"
# Expected: 3 lines, one per task

# 2. Check next-run times are in the future:
schtasks /query /tn PortalLoadProbe /fo list | findstr "Next Run"
schtasks /query /tn MirrorSync /fo list | findstr "Next Run"
schtasks /query /tn VerifierSLO /fo list | findstr "Next Run"
# Expected: timestamps > now

# 3. Verify task actions point to correct scripts:
schtasks /query /tn PortalLoadProbe /fo list /v | findstr "Task To Run"
# Expected: contains path to agent_portal.py or fleet_probe

# 4. If any task missing, re-register from batch file:
python elev.py --shell "cmd /c memory\ops\fleet_schtask_register.bat"
# Expected: exit 0; tasks visible in step 1
```

---

## 5. Handoff-to-Human Criteria

Escalate to human ONLY when ALL automated recovery paths are exhausted:

| Condition | Automated Path Tried | Escalation Message |
|-----------|---------------------|--------------------|
| Host unreachable >2h after 3 failover attempts | WinRM + local probe | "Host X down; all failover seats exhausted" |
| Portal :8099 dead after restart + task re-run | Restart, schtask run, fresh boot | "Portal unresponsive; needs manual process inspection" |
| Score stuck <50% for 3+ consecutive cycles | Full regression suite + alert review | "Autonomy floor breached; architectural change needed" |
| Recurring blocker same root-cause >5x in 7 days | Blocker file review + dedup | "Systemic issue: [root cause]; needs design decision" |

**Rule**: Never hand off for a single transient failure. Always exhaust the recovery procedure in Section 3 first.
Log every handoff to `memory/ops/human-handoffs.jsonl` with {ts, reason, steps_tried[], outcome}.

---

## 6. Quick-Reference: One-Liner Health Check

```bash
python memory/ops/pre_cycle_gate.py && python memory/builder/test_autonomy_infra.py && echo "FLEET HEALTHY"
# Expected: both exit 0; prints PASS summaries + FLEET HEALTHY
```

If any component fails, the output identifies which check failed and why.
Cross-ref: `convergence_alert.py` for trend-based early warning before a single point-in-time check catches it.