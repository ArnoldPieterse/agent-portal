# Evidence: Cross-Host Consistency Test (goal #1)

**Date:** 2026-11-25 16:04 UTC
**Script:** `memory/forge/consistency_check.py`

## Verification
1. **Simulation mode** (`--simulate`): 4/4 test cases PASS
   - All consistent → PASS ✓
   - Model mismatch → CRIT ✓
   - All unreachable → WARN ✓
   - Config hash mismatch → CRIT ✓

2. **Live probe** (2026-11-25 16:03 UTC):
   - White: DOWN (URLError) — local Studio not running on :8888
   - Red: UP, model=healthy, 9.6ms
   - Pale: UP, model=healthy, 21.9ms
   - Black: DOWN (URLError)
   - **Verdict: PASS** (reachable hosts consistent; unreachable noted)

3. **Report:** appended to `memory/forge/consistency-report.jsonl`

## Acceptance Criteria Met
- [x] Script exists at expected path
- [x] Probes all 4 hosts (Studio :8888 + Portal :8099)
- [x] Compares model version across reachable hosts
- [x] Computes config hash (SHA-256 agents.json, first 12 hex)
- [x] Mismatch = CRIT exit code 1
- [x] All unreachable = WARN exit code 2
- [x] Simulation selftest passes
- [x] Live run produces JSONL report entry
