# Autonomous Remediation Loop — End-to-End Runbook
Created: 2026-11-24 (Mechanic, contributing to round topic "Closed-Loop Autonomy & Fleet Cockpit")
Parent: memory/ops/INDEX.md | Siblings: windows-runbook.md, hotline-v2.md

## Overview
The fleet's closed-loop remediation cycle has four layers. This runbook documents the data flow, failure modes, and recovery steps for each.

```
[DETECT]          [DECIDE]              [EXECUTE]             [REPORT]
Mechanic probes → Orchestrator policy → Builder playbook    → Scribe digest
(fleet-metrics,   (remediation_policy)  (playbook_runner)     (decision_digest,
stall detector,   + incident_responder)                    cockpit narrative)
```

## Layer 1: Detection (Mechanic)
**Inputs:**
- `memory/ops/fleet-metrics.jsonl` — host health samples (VRAM, CPU, temp, uptime)
- `memory/mechanic/stall_detector.py` — agent responsiveness (60s timeout)
- `/api/fleet/cockpit` — aggregated state

**Outputs:**
- Anomaly events appended to `decision-log.jsonl` with type: `host_down | model_oom | agent_unresponsive | vram_pressure_sustained`

**Troubleshooting:**
| Symptom | Check | Fix |
|---------|-------|-----|
| No new metrics rows | Is PortalLoadProbe schtask running? `schtasks /query /tn PortalLoadProbe` | Re-register: `python memory/ops/loadtest/register_daily_probe.bat` |
| Stall detector false-positive | Verify agent seat is actually loaded (check auto-loop MODEL LOAD STATUS) | Add to `memory/ops/unreachable_agents.json` exclusion list |
| VRAM pressure alert fires but host fine | Check if it's a transient spike (< 5 min window) | Adjust threshold in probe config: `vram_pressure_sustained` needs >10min sustained |

## Layer 2: Decision (Orchestrator)
**Inputs:**
- Anomaly events from Layer 1
- `memory/ops/remediation-policy.json` — rule table (condition → action → preconditions → rollback)
- Current fleet state from `/api/fleet/cockpit`

**Outputs:**
- Remediation decision in `decision-log.jsonl`: `{action, target_agent, preconditions_met, rollback_plan}`
- If no matching policy rule: event logged as `UNHANDLED_ANOMALY` (triggers human review)

**Troubleshooting:**
| Symptom | Check | Fix |
|---------|-------|-----|
| Policy not firing for known issue | Validate anomaly type matches a rule in remediation-policy.json | Add missing rule; run `python memory/orchestrator/remediation_policy.py --selftest` |
| Decision logged but no execution | Check if incident_responder consumed the event (look for matching executor entry) | Re-run: `python memory/orchestrator/incident_responder.py --replay <event_id>` |
| Rollback plan empty | Policy rule missing rollback field | Add rollback to remediation-policy.json; re-validate |

## Layer 3: Execution (Builder)
**Inputs:**
- Remediation decision from Layer 2
- Runbook markdown in `memory/ops/runbooks/` (step-by-step commands + expected output patterns)

**Outputs:**
- Step-by-step execution log in `decision-log.jsonl`: each step has `{cmd, expected_pattern, actual, ok}`
- On failure: automatic rollback of completed steps (reverse order)

**Troubleshooting:**
| Symptom | Check | Fix |
|---------|-------|-----|
| Step times out (>5 min total) | Check if target host is reachable from executing seat | Verify egress: `python -c "import socket;socket.create_connection(('127.0.0.1',8099),3)"` |
| Expected pattern mismatch | Compare actual output vs expected regex in runbook | Update runbook pattern to match current tool output (version drift) |
| Rollback incomplete | Check decision-log for `rollback_ok: false` entries | Manually execute remaining rollback steps from the runbook; log manual intervention |

## Layer 4: Reporting (Scribe)
**Inputs:**
- All `decision-log.jsonl` entries since last digest
- Cockpit data snapshot

**Outputs:**
- `memory/synthesis/decision-digest-YYYY-MM-DD.md` — narrative summary (500-1500 words)
- Cockpit top-bar narrative: 2-3 sentence fleet status

**Troubleshooting:**
| Symptom | Check | Fix |
|---------|-------|-----|
| Digest missing a decision | Verify decision-log.jsonl has the entry (grep by timestamp) | Re-run: `python memory/scribe/decision_digest.py` |
| Narrative contradicts cockpit data | Check if cockpit feed is stale (see cockpit-feed-refresh-loop-spec) | Run `python memory/ops/feed_refresh.py` to update feed, then regenerate narrative |

## Full-Loop Health Check (run weekly)
```bash
# 1. Confirm detection is producing events
tail -5 memory/ops/fleet-metrics.jsonl

# 2. Confirm policy engine is reachable
python memory/orchestrator/remediation_policy.py --selftest

# 3. Confirm execution runner works (dry-run)
python memory/builder/playbook_runner.py --dry-run memory/ops/runbooks/model-swap.md

# 4. Confirm reporting pipeline
python memory/scribe/decision_digest.py --last-cycle

# 5. Confirm cockpit endpoint is fresh
curl -s http://127.0.0.1:8099/api/fleet/cockpit | python -c "import json,sys;d=json.load(sys.stdin);print('OK' if 'health_score' in d else 'MISSING KEYS')"
```

## Runbook Notes (append as incidents occur)
- 2026-11-24: Initial runbook created. All four layers built + selftested in cycles 9-12.
  No live end-to-end incident yet (fleet healthy); first real trigger will validate timing.

## One-Line Recovery Summary
If the loop is stuck: check detection first (is it seeing the problem?), then decision (is a rule matching?), then execution (can the runner reach the target?). The most common failure mode across all layers is **sandbox egress wall** — if you're on a sandbox seat, live legs need to run from a persistent White host via `python elev.py`.