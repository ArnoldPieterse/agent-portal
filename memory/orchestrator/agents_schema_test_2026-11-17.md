# agents_schema.py - Test Evidence (2026-11-17)

## Test 1: Invalid schema rejection
Injected 3 defects into a copy of agents.json:
- agents[0].temperature = 5.0 (out of range [0,2])
- agents[1].id = 'BAD-ID' (violates ^[a-z0-9_]+$)
- agents[2].name removed (required field missing)

Result: all 3 flagged with exact agent index + field name. PASS.

## Test 2: Migration apply + rollback
Simulated older schema:
- Removed rag_kb_id from agents[0]
- Set agents[1].reasoning = 'auto' (non-enum)

Applied migrations v1+v2:
- v1 added rag_kb_id='' to agents[0]
- v2 normalized reasoning 'auto' -> 'default' for agents[1]

Post-migration validation: 0 errors. PASS.
Original data object unmodified (deepcopy isolation). Rollback = restore backup file.
