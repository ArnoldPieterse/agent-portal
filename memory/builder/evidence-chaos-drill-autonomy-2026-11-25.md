# Evidence: Autonomy Chaos Drill Suite (goal #8)
Date: 2026-11-24T14:48:37.550558+00:00
Command: `python memory/builder/chaos_drill.py --scenarios autonomy`
Result: 4/4 PASS

## Scenarios
1. **fsm_kill_mid_transition** - Simulated crash during FSM write (partial JSON left on disk). Recovery: restored from backup, schema valid in 1 pass.
2. **concurrent_read_corruption** - Corrupted fleet-mode.json with invalid JSON. Recovery: detected corruption, rewrote valid state in 1 pass.
3. **triple_write_conflict** - 3 concurrent writes to fleet-mode.json. Recovery: consensus validator resolved (last-writer-wins), valid schema in 1 pass.
4. **dispatch_step_failure** - Pass failed at step 2/3 of dispatch. Recovery: rollback + retry succeeded in 1 pass.

## Verification
- All scenarios recover within 5 passes (actual: 1 pass each)
- chaos-drills.jsonl entries have required schema: scenario_id, timestamp, recovered, passes_to_recover, final_state_valid
- Backward compat: original --selftest still 3/3 PASS
