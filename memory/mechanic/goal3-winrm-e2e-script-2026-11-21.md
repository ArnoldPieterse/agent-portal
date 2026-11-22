# Goal #3: WinRM E2E Test - Script Built + Dry-Run Validated (2026-11-21)

## What was done this pass
- Built `winrm_e2e_test.py` - self-contained one-command E2E test for the full anti-stall chain
- 5 phases: baseline -> host-down -> CB detect -> WinRM reboot -> recovery verify
- py_compile PASS; dry-run mode validated against both Black (Black) and Pale (Pale)
- Both hosts TCP :8888 reachable from sandbox; Studio API responding

## Dry-run results
```
[PHASE1_BASELINE] PASS - Black: TCP up, 0 models loaded
[DRY_RUN] PASS - baseline verified; skipping destructive phases
[PHASE1_BASELINE] PASS - Pale: TCP up, 0 models loaded  
[DRY_RUN] PASS - baseline verified; skipping destructive phases
```

## Remaining for final acceptance
ONE live run from a non-sandbox seat (White):
```
python winrm_e2e_test.py --host black --password <admin_pw>
```
This requires:
- :8099 access (portal) - blocked by egress wall in sandbox (WinError 10013)
- WinRM/PowerShell remoting to target host
- elev.py or direct White seat execution

## Acceptance criteria mapping
| Criterion | Status |
|-----------|--------|
| Full cycle <15 min | PENDING (needs live run) |
| All log entries in correct order | Script logs all 5 phases sequentially to JSONL |
| Agent responsive after recovery | Phase 5 verifies TCP + model count |
| No data loss | Model count comparison pre/post reboot |

## Runbook note
What broke: Goal #3 had no single executable test script - required manual multi-step orchestration.
What fixed it: `winrm_e2e_test.py` encapsulates the full chain in one command with --dry-run for safe validation.
