# Preflight Check Built + unblock_all.py Bug Fixed (2026-11-23)

## What was done
1. **Built `preflight_check.py`** — validates 7 prerequisites before running `unblock_all.py`:
   - P1: Portal :8099 listening
   - P2: WinRM :5985 reachable to target host
   - P3-P6: All referenced scripts exist + py_compile clean
   - P7: load_trend.jsonl has data
   - Exit 0 = GO, exit 1 = HOLD with specific failures listed

2. **Fixed bug in `unblock_all.py`** (phase_winrm):
   - Was referencing `winrm_e2e_test.py` (non-existent file)
   - Actual script is `e2e_anti_stall_test.py`
   - Also fixed arg format: was `--host black` (space), correct is `--host=BLACK` (equals, uppercase)
   - Removed dead `WINRM_PASSWORD` env var code (script doesn't use it)

## Baseline from sandbox seat (2026-11-23T01:18)
```
P1_portal_8099:      FAIL (WinError 10013 - egress wall, expected in sandbox)
P2_winrm_black:      FAIL (timeout - no LAN access from sandbox, expected)
P3_deploy_schtasks:  PASS
P4_winrm_e2e_test:   PASS (after fix)
P5_unblock_all:      PASS
P6_mirror_heal:      PASS
P7_load_trend_data:  PASS (1 row exists)
VERDICT: HOLD (2 failing) - both are sandbox-only, will pass on non-sandbox White
```

## Impact
- `unblock_all.py` would have FAILED at phase 2 with "script missing" before this fix
- Now the one-shot script is correct and ready for a non-sandbox seat
- Preflight gives a 10-second sanity check before committing to the full run

## Files changed
- NEW: `memory/mechanic/preflight_check.py` (5.2 KB, py_compile PASS)
- EDITED: `memory/mechanic/unblock_all.py` (script name + arg format fix)
- EVIDENCE: `memory/mechanic/preflight-2026-11-23.jsonl`