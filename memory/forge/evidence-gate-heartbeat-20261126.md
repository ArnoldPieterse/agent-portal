# Evidence: Gate Heartbeat Monitor (NEW)

**Built:** 2026-11-25T19:50Z
**Artifact:** memory/forge/gate_heartbeat.py

## Purpose
Detects stale gate runs — the missing piece for true fleet autonomy. Gates that self-monitor
rather than waiting to be prompted. Part of Fleet Autonomy Convergence round topic.

## Verification
- First run: caught 2 STALE gates (runbook_audit 11.5h, fleet_autonomy_gate 4.3h) — exit 1
- Remediation: ran both stale gates (runbook_audit --json gaps=0 exit 0; fleet_autonomy_gate FLEET AUTONOMY READY 5.05s)
- Second run: ALL-FRESH, exit 0, all 5 gates green

## Design
- Scans 5 gate .jsonl reports + 1 JSON stamp (runbook-audit-last-run.json)
- Timestamp extraction: jsonl last-line 'ts' field → file mtime fallback → evidence-mtime fallback
- Threshold: 4h default (--threshold to override)
- Appends to memory/forge/gate-heartbeat.jsonl for trend tracking
- Exit codes: 0=ALL-FRESH, 1=STALE detected, 2=NO-DATA

## Round Topic Alignment
Fleet Autonomy Convergence requires gates that don't need human prompting. This heartbeat is the
self-monitoring layer: if a scheduled task or auto-loop stops calling a gate, the next heartbeat
run flags it. Combined with convergence_watch.py (state-transition alerts), the fleet now has
both reactive (verdict change) and proactive (stale detection) monitoring.

**VERDICT:** PASS — 5/5 gates FRESH, script operational, exit codes correct.
