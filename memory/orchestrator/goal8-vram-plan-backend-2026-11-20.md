# Goal 8 VRAM Pressure Alerting — backend DONE (2026-11-20)

## What was built
1. `memory/orchestrator/vram_plan.py` — self-contained module:
   - Loads `memory/llm/hotload-catalog.json` as source of truth (host VRAM + model sizes)
   - `evaluate_plan(plan)` → per-host `{total_gb, predicted_gb, pct, alert, models}`
   - Alert threshold: >90% of host total VRAM
   - Writes timestamped alerts to `memory/ops/vram-alerts.jsonl` (JSONL, one record per over-threshold host)
2. `agent_portal.py` — two additions:
   - `_fleet_plan(plan)` function (loads vram_plan.py by path = single source of truth)
   - `POST /api/fleet/plan` route in `_do_POST`

## Verification (self-test, 2026-11-20)
- Simulated plan: qwen3-27b-q8 (30.1 GB) on white (32 GB total)
- Result: pct=94.1%, alert=True ✓
- vram-alerts.jsonl: 1 record written with correct host, models, predicted/total/pct fields ✓
- py_compile agent_portal.py: PASS ✓

## Remaining for full closure
- UI banner in fleet tab (ui/core.js): read /api/fleet/plan result or poll vram-alerts.jsonl; render red/amber banner when alerts_triggered > 0
- Live-HTTP 200 confirmation (needs safe portal restart window)

{"ts": 1795131566.469988, "goal": "orchestrator-8", "step": "UI VRAM alert banner built in ui/core.js (vramAlertInit + vramAlertUpdate); fetches /api/fleet/vram-alerts, shows last 5 alerts <24h as inline banner in fleet tab; bracket-balance verified", "artifact": "ui/core.js L573-610"}
