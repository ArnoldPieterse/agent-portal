# Verifier assist — Orchestrator #2 Fleet Capacity Governor (static/simulate leg)
Date: 2026-11-23
Seat: Black (sandbox)

## What was tested
Ran `python memory/orchestrator/capacity_governor.py --simulate` and `--simulate --threshold 99` from this seat.

## Results
| Criterion | Status | Evidence |
|-----------|--------|----------|
| simulated high-VRAM triggers unload of correct model | PASS | exit 0, "UNLOAD_SUCCESS: host=White model=quinn-q4 vram=92.0%" (LRU = Researcher's quinn-q4, correct) |
| log entry present | PASS | capacity-governor.jsonl appended two entries at 19:28Z today (UNLOAD_SUCCESS + OK for default; OK+OK for threshold-99) |
| no action below threshold | PASS | `--threshold 99` -> "SIMULATE: 0 action(s) taken"; both hosts logged OK |
| restoration on cooldown works | **GAP** | No cooldown mechanism exists in capacity_governor.py (227 lines). Code unloads and stops; no re-load path, no cooldown timer, no state file tracking unload time. Acceptance criterion cannot be met without new code. |

## Gap detail
The acceptance line says "restoration on cooldown works" but the implementation has:
- No cooldown constant or parameter
- No state file recording when a model was unloaded
- No re-load trigger after cooldown expires
- No `--restore` or similar flag

Orchestrator needs to implement: (1) write unload timestamp to a state file (e.g. capacity-cooldown.json), (2) on next run, check if any previously-unloaded model's cooldown has expired and issue /api/inference/load, (3) log RESTORE_SUCCESS/RESTORE_FAIL entries.

## Verdict
3/4 criteria PASS via simulate; 1 criterion (cooldown restoration) requires new implementation code before the goal can be closed.
