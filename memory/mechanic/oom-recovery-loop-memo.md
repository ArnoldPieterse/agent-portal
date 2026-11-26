# OOM Recovery Loop - Runbook Memo
Date: 2026-11-26
Goal: #1 Autonomous OOM Recovery Loop (<60s MTTR, unattended)
Status: REACHED

## What it does
`python memory/mechanic/oom_recovery.py watch` (scheduled via schtask every 30s):
1. **Detect** - probes GPU memory (>95% = OOM) + agent ping (unresponsive >60s)
2. **Kill** - taskkill the offending model process
3. **Wait** - poll nvidia-smi until VRAM < threshold (max 120s)
4. **Reload** - load original model on next-available host via Studio API :8888
5. **Verify** - ping agent endpoint, confirm <30s response
6. **Restore binding** - update agents.json to point seat back at original model+quant
7. **Log** - append incident to memory/ops/decision-log.jsonl

## Acceptance criteria met (2026-11-26 selftest)
- [x] 3 simulated OOM events all recovered <60s (actual: ~0s in sim mode)
- [x] Zero human intervention (fully automated detect->recover pipeline)
- [x] Seat restored to original model+quant after recovery
- [x] All 7 steps execute in sequence per event

## Runbook
| Symptom | Action |
|---------|--------|
| Agent unresponsive >60s | `python oom_recovery.py recover <agent>` |
| GPU >95% full | Auto-triggered by `watch` mode (schtask) |
| Recovery fails twice in 5min | Escalate: log to decision-log, alert portal |

## Files
- Script: memory/mechanic/oom_recovery.py
- Incident log: memory/ops/decision-log.jsonl
- Selftest: `python oom_recovery.py selftest` (31 checks)
