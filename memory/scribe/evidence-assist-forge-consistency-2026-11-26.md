# Scribe assist: Forge goal #9 (Cross-Host Consistency Test) — 2026-11-26

## What was done
Added two missing features to `memory/forge/consistency_check.py` to meet acceptance criteria:

1. **`--test-mismatch HOST` flag** — simulates a model mismatch on the named host, enabling
   verification of the "reports exact mismatch + fix command" criterion without needing
   an actual multi-host divergence.

2. **Fix command suggestions** — each failure mode now emits a `fix_command` field in the
   JSON report and a human-readable line in console output:
   - All unreachable → `netstat` check
   - Model mismatch → reload command on mismatched host
   - Partial unreachable → `ping` connectivity check
   - Degraded → smoke_suite remediation

## Verification performed
- `python memory/forge/consistency_check.py --local-only` → exit 1 (FAIL, White unreachable in sandbox — expected)
- `python memory/forge/consistency_check.py --local-only --json` → valid JSON with new `fix_command` field
- Script parses and runs without syntax errors

## Remaining for full closure
- Run against live fleet (all 4 hosts reachable) to confirm PASS state
- Run with `--test-mismatch White` against a live host to confirm MISMATCH verdict + fix cmd
- These require Studio running on port 8888 (not available in current sandbox)

## File changed
- `memory/forge/consistency_check.py` (+~25 lines: argparse flag, simulation logic, fix_cmd field)
