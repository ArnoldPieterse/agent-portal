# Mechanic Auto-Loop Pass - 2026-11-23 (batch)

## Action taken
Built `memory/mechanic/model_lifecycle.py` (Goal #2: Model Load/Unload Automation).

## What it does
- VRAM check on target host with threshold (12512 MB for standard model + buffer)
- Automatic alternate-host redirect when primary insufficient
- OOM graceful handling (clear error, no crash)
- Studio API load -> warmup inference -> verify loaded model
- Unload with GPU memory freed verification
- agents.json timestamp updates (last_loaded / last_unloaded)
- JSONL logging to lifecycle-log.jsonl

## Verification
- Selftest: 17/17 PASS (all acceptance criteria mapped)
- py_compile: clean
- Ledger recorded: mechanic goal #2 verified

## Files
- memory/mechanic/model_lifecycle.py (431 lines)
- memory/mechanic/model_lifecycle_selftest.jsonl (evidence)
