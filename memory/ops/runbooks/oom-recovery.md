# OOM Recovery Runbook

## Trigger
Model killed by OOM (VRAM exhaustion). Detected via model-load.jsonl or seat probe.

## Steps
1. Identify victim seat from fleet-heartbeat.json (status=down, reason=oom)
2. Unload model: `python elev.py --shell "taskkill /F /IM python.exe /FI "WINDOWTITLE eq *model*""` (or API call)
3. Wait for VRAM free: poll nvidia-smi until < 500MB used on target GPU
4. Reload model (possibly downgraded quant): `python memory/mechanic/oom_recovery.py --reload <seat>`
5. Verify seat back online: probe returns 200 within 30s
6. Log incident: memory/ops/incidents/oom-recovery-<ts>-<seat>.md

## SLA
Full recovery < 60s (MTTR target)
