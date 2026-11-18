# Goal 11 - Hot LLM Load Functional Test Suite - Progress Evidence (2026-11-18)

## What was done
1. Goal #11 drafted in memory/goals/verifier.md (user-directed, cycle-6 addition)
2. `memory/verifier/hotload_test.py` built (12,730 bytes, 5 checks):
   - load_poll: Q8_0 load -> poll until resident (async ack pattern)
   - unload_poll: Q8_0 unload -> poll until gone
   - eviction: observation-mode check of documented asymmetry (Q4 evicts Q8, not vice versa)
   - alias_preservation: verifies atlas-q8 and quinn-q4 path bindings intact
   - conflict_409: tests 409 response during active generation (safe skip if idle)
3. Syntax verified: `python -c "import ast; ast.parse(...)"` -> SYNTAX OK

## Live execution status
- Sandbox blocks localhost:8888 (WinError 10013) - same limitation as Goal 6
- Script is ready for direct execution on White: `python memory/verifier/hotload_test.py --suite all`
- Dry-run mode available for connectivity-only check without mutations

## Remaining to full verification
- Run suite live on White (outside sandbox) to get PASS/FAIL per check
- Confirm eviction observation matches 2026-11-15 drill finding
- Verify alias preservation holds after a real swap cycle

## Files
- memory/verifier/hotload_test.py (the test harness)
- memory/goals/verifier.md (goal #11 defined)
