# Cockpit Accuracy Test - Evidence (2026-11-23)

**Goal:** Verifier #2 - Cockpit Data Accuracy Test
**Status:** Built + self-test passed (5/5). Live mode pending portal access.

## What was built
`memory/verifier/cockpit_accuracy.py` - verifies /api/fleet response against raw sources:
- Agent roster per host vs agents.json
- Host state consistency (busy/idle/unknown vs generations)
- Models vs state cross-check
- Goal counts (soft check, skips if TODO.md unavailable)

## Self-test results (5/5 PASS)
| Test | Description | Result |
|------|-------------|--------|
| T1 | Clean system → 0 discrepancies | PASS |
| T2 | Planted stale value detected | PASS |
| T3 | Agent roster mismatch detected | PASS |
| T4 | Runs in <30s (actual: <1s) | PASS |
| T5 | Output is machine-readable JSON | PASS |

## Notes
- Port 8099 blocked by firewall (WinError 10013) in this sandbox - live mode untested
- Endpoint is `/api/fleet` (not `/api/fleet/cockpit` as goal text suggests)
- Script supports `--selftest` flag for offline verification

## Artifacts
- `memory/verifier/cockpit_accuracy.py` (test script)
- `memory/verifier/cockpit_accuracy_selftest.json` (self-test report)
