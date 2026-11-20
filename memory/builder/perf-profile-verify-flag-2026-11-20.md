# Builder: perf_profile.py --verify flag implementation (2026-11-20)

## Problem
close_goal7.bat calls `python memory\mechanic\perf_profile.py --verify` but the flag was missing from the script. The .bat would always fail at step 2.

## Fix
Added `--verify` to perf_profile.py argparse + implemented `verify()` function:
- Reads perf-profile.json (OUT_PATH)
- Checks all endpoints have status="ok" with non-null p50/p95/p99
- Validates monotonicity: p50 <= p95 <= p99
- Exit 0 = PASS, exit 1 = FAIL (with per-endpoint error messages)

## Tests (all PASS)
| # | Scenario | Expected | Result |
|---|----------|----------|--------|
| 1 | Valid JSON (4 endpoints, monotonic) | exit 0 + "PASS" | ✓ |
| 2 | Null p95 on one endpoint | exit 1 + specific error | ✓ |
| 3 | Non-monotonic (p50>p95) | exit 1 + specific error | ✓ |
| 4 | Missing file | exit 1 + "does not exist" | ✓ |

## Impact
close_goal7.bat is now fully functional end-to-end. When run from a non-sandbox White terminal with portal access, it will:
1. Run 1h profile → writes real data
2. Verify percentiles (this fix) → PASS/FAIL gate
3. Register daily schtask
4. Record ledger evidence

Goal #7 remains (progress) until the live egress leg runs.
