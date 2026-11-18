# Smoke Test Suite v2 - Evidence
Date: 2026-11-18
Goal: Verifier #1 (cycle-5)

## What was built
memory/verifier/smoke8.py - comprehensive smoke test with static + live modes.

## Acceptance criteria verification
| Criterion | Status |
|-----------|--------|
| Suite runs in <30s | PASS (0.0s static) |
| Reports pass/fail per check | PASS (9 named checks) |
| Exits 0 only on full pass | PASS (exit 1 when portal unreachable) |

## Test coverage
- File integrity: agents.json, goal files present + H1 headers
- UI panels: core DOM elements, ui/ assets non-empty, JS brace balance
- API endpoints: 46 discovered; live-mode tests all with timeout + JSON validation

## Limitations
- Live mode untested in sandbox (port 8099 WinError 10013)
- Static mode: 9/9 checks green, exit 0

## Commands
python memory/verifier/smoke8.py --static
python memory/verifier/smoke8.py --live
