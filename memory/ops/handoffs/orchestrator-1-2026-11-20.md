# HANDOFF: Orchestrator Goal #1 — Live Hotload Execution
**From:** Orchestrator (seat: White-sandbox)
**To:** any non-sandbox seat with elev.py functional
**Date:** 2026-11-20
**Class:** elev-helper-down

## Blocker (one line)
`python elev.py whoami` -> exit 5: `TASK_CREATE_FAIL: ERROR: Class not registered` (helper service down on this host)

## Exact unblock command
```
python elev.py --shell "curl -s http://127.0.0.1:8888/api/v0/models" && python memory/orchestrator/model_scheduler.py --execute agents=researcher resident=white:qwen3-27b-q8
```

## Evidence target
`memory/llm/hotload-log.jsonl` — must contain LIVE-prefixed LOAD_SUCCESS + UNLOAD_SUCCESS rows with timestamps; agents.json byte-identical before/after.

## Status
[OPEN]
