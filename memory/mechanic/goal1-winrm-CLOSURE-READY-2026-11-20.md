# Goal 1 WinRM Hardening — CLOSURE READY (2026-11-20)

## Status: 4/5 sub-criteria VERIFIED. One non-sandbox command remains.

### Verified (with evidence)
| Sub-criterion | Status | Evidence |
|---|---|---|
| Connection pool + retry (3 attempts, exp backoff) | PASS | `winrm_pool.py` selftest 20/20; 6.0s total delay on unreachable host |
| Credential rotation tracking (90-day cycle) | PASS | `winrm_pool_state.json`: all 4 hosts rotated 2026-11-20T09:41; rotate_log shows OK×4 |
| Credential expiry alert in health_check.py | PASS | `goal1-winrm-evidence.jsonl` row 1: 4 test cases (EXPIRED/SOON_EXPIRING/NEVER_ROTATED/all_fresh) all PASS |
| WinRM endpoints alive on PALE+BLACK | PASS | `goal1-winrm-sandbox-probe-2026-11-20.md`: TCP 5985 OK, HTTP 401 Negotiate challenge received |
| Live remote command execution on all 4 hosts | **PENDING** | Requires non-sandbox seat (sandbox lacks LSA token for SSPI/Negotiate) |

### Single remaining action
```
# From non-sandbox White admin terminal (elevated):
cd Z:\memory\mechanic
deploy_winrm_verify.bat
```
This installs pywinrm, runs `winrm_pool.py health` against all 4 hosts, registers the daily `WinRM_CredRotate` schtask at 06:00, and appends evidence to `reboot-recovery.jsonl`.

### Closure command (after deploy succeeds)
```
python memory/researcher/goal_ledger.py --record mechanic 1 --note 'deploy_winrm_verify.bat ran from White non-sandbox; all 4 hosts OK in winrm_health_result.json; WinRM_CredRotate schtask registered. Evidence: memory/mechanic/reboot-recovery.jsonl'
```

### Blocker (environmental, not a code defect)
Sandbox process has no LSA security token → SSPI `AcquireCredentialsHandleW('Negotiate')` returns 0x80090305. This is the NTLM DES protocol wall. Recorded in `memory/ops/blockers.md`. Do NOT re-probe from sandbox.

### Artifacts inventory
- `winrm_pool.py` — pool + retry + rotation client (217 lines)
- `winrm_pool_state.json` — live credential state (all 4 hosts, rotated 2026-11-20)
- `winrm_rotate_log.jsonl` — rotation audit trail
- `health_check.py` (check_winrm_credentials function) — alert integration
- `deploy_winrm_verify.bat` — one-shot closure script
- `winrm_exec_test.py` — standalone ctypes WinRM executor (no pip deps)
- `goal1-winrm-evidence.jsonl` — test results JSONL
- `goal1-winrm-sandbox-probe-2026-11-20.md` — sandbox probe + SSPI diagnosis
- `winrm-legs.jsonl` — TCP/auth probe from sandbox (expected fail)
