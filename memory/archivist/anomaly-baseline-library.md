# Anomaly Baseline Library
Generated: 2026-11-26 | Source: compiled from ops evidence + runbooks
Purpose: reference for detection signatures and thresholds across all observed anomaly types.

## 1. OOM (VRAM Exhaustion)
**Signature:** model process killed; seat status=down reason=oom in fleet-heartbeat.json
**Detection Threshold:** VRAM usage >95% on target GPU; nvidia-smi shows OOM kill in dmesg
**Baseline Frequency:** 8 recorded events (2026-11-26 simulation batch); historical: ~1/3 cycles
**Recovery SLA:** <60s MTTR (target); measured: <45s in v2 verified run
**Detection Source:** memory/mechanic/oom-recovery-evidence.jsonl, seat probes
**Key Fields:** ts, host, model, gpu[], backup, simulation
**Runbook:** memory/ops/runbooks/oom-recovery.md
**Auto-Recovery:** oom_recovery.py --reload <seat>; downgrade quant on retry

## 2. Cycle Timeout
**Signature:** cycle duration exceeds SLA (30min baseline); auto-diagnostic fires
**Detection Threshold:** elapsed > 1800s from cycle start; diagnostic captures stack+model+passes
**Baseline Frequency:** 4 diagnostic captures (2026-11-26); 3 incident files in ops/incidents/
**Recovery SLA:** diagnostic written <5min after breach; root cause identified same cycle
**Detection Source:** memory/mechanic/cycle-timeout-diag-evidence.jsonl, ops/incidents/cycle-timeout-*
**Key Fields:** ts, mode, results[sim, ok, fields(stack,model,passes)]
**Runbook:** memory/ops/runbooks/ (cycle-timeout section)
**Auto-Recovery:** cycle_timeout_diag.py auto-captures; Mechanic triages next pass

## 3. Mirror Revert
**Signature:** file content reverts to pre-edit state after mirror sync; pin-file clobber
**Detection Threshold:** md5 mismatch between local edit and post-sync state; >1 revert in 10min window
**Baseline Frequency:** ~12 documented incidents (Nov 17-20 cluster); guard executed 1x (2026-11-20)
**Recovery SLA:** pin re-applied <5min; root cause identified same cycle
**Detection Source:** memory/mechanic/mirror-revert-guard-executed.jsonl, ops/mirror-revert-* files
**Key Fields:** ts, agent, action, ref
**Runbook:** memory/ops/mirror-revert-prevention-2026-11-18.md
**Auto-Recovery:** pin-guard (Option B) auto-executes; sentinel design in ops/mirror-revert-sentinel-design

## 4. Model Load Failure
**Signature:** model fails to load on seat (timeout, missing file, VRAM insufficient)
**Detection Threshold:** load attempt >30s without ready signal; reason field in model-load.jsonl
**Baseline Frequency:** ~2-3/cycle across 4 hosts (est. from seat probe failures); 5 seats unreachable at last run start
**Recovery SLA:** <30s per retry attempt; max 3 attempts before escalation to backup seat
**Detection Source:** model-load.jsonl, seat probes, fleet-heartbeat.json
**Key Fields:** ts, seat, model_id, reason, attempt
**Runbook:** memory/ops/runbooks/model-load-failure.md
**Auto-Recovery:** retry with adjusted params (downgrade quant); after 3 fails: mark degraded + route to backup

## Detection Threshold Summary
| Anomaly | Trigger Condition | SLA | Auto-Recovery? |
|---------|-------------------|-----|----------------|
| OOM | VRAM >95% + process kill | <60s MTTR | Yes (oom_recovery.py) |
| Timeout | elapsed >1800s | diag <5min | Partial (auto-capture only) |
| Mirror Revert | md5 mismatch post-sync | pin <5min | Yes (pin-guard Option B) |
| Model Load Fail | load >30s no ready | 3x30s then escalate | Yes (quant downgrade) |

## Data Sources Index
- memory/mechanic/oom-recovery-evidence.jsonl (8 entries)
- memory/mechanic/cycle-timeout-diag-evidence.jsonl (2 entries)
- memory/mechanic/mirror-revert-guard-executed.jsonl (1 entry)
- memory/ops/anomalies.jsonl (1 entry)
- memory/ops/incidents/ (7 files: 3 timeout + 1 OOM + others)
- memory/ops/runbooks/oom-recovery.md
- memory/ops/runbooks/model-load-failure.md
- memory/researcher/mirror-revert-* (20+ analysis files)

## Gaps & Notes
- Model-load-fail has no dedicated JSONL evidence file yet (relies on model-load.jsonl + seat probes)
- Mirror-revert guard only executed once; sentinel design not yet deployed
- Timeout auto-recovery is capture-only; triage still manual (Mechanic next pass)
- No compound anomaly patterns documented yet (e.g., OOM triggering model-load-fail cascade)
