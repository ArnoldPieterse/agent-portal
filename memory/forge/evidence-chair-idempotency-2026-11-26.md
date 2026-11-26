# Forge Goal #1 Evidence: Chair Idempotency Test — 2026-11-26

## What ran
`python memory/forge/chair_idempotency.py` (exit code 0)

## Test design
Sandbox simulates a closed cycle (3 agents, all 10/10 verified). Runs `auto_cycle_transition.py --run` twice. Asserts:
1. No double-archive (archive count stable across runs)
2. No duplicate goals (goal file line counts stable)
3. Ledger unchanged (reached/total identical after both runs)

## Result: PASS

| Invariant | Run 1 | Run 2 | Status |
|-----------|-------|-------|--------|
| Archive count (orchestrator) | 1 | 1 | ✓ |
| Archive count (builder) | 1 | 1 | ✓ |
| Archive count (forge) | 1 | 1 | ✓ |
| Goal lines (orchestrator) | 10 | 10 | ✓ |
| Goal lines (builder) | 10 | 10 | ✓ |
| Goal lines (forge) | 10 | 10 | ✓ |
| Ledger (all agents) | 0/10 | 0/10 | ✓ |

## Bug found + fixed
Initial test run (before fix) revealed `auto_cycle_transition.py` was NOT idempotent under `--force`:
double-run created duplicate archive files (`agent-date_2.md`). Fixed by adding an idempotency
guard in `main()`: if a kickoff file for cycle+1 already exists, exit 0 immediately (no-op).

**Fix location:** `memory/orchestrator/auto_cycle_transition.py`, `main()` function, after cycle detection.
**Guard logic:** `kickoff_files = [f for f in os.listdir(gdir) if f.startswith(f"cycle{cycle+1}-kickoff-")]` → if found and not `--force`, print "IDEMPOTENT NO-OP" and return 0.

## Artifacts
- Test script: `memory/forge/chair_idempotency.py`
- Last run JSON: `memory/forge/chair_idempotency_last.json`
- Fix applied to: `memory/orchestrator/auto_cycle_transition.py`

## Verification command
```
python memory/forge/chair_idempotency.py
# Expected: PASS - all invariants hold. Chair is idempotent. (exit 0)
```
