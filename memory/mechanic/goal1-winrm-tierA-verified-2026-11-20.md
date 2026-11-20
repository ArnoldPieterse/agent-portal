# Goal 1 WinRM Remote Management Hardening — TIER-A VERIFIED, TIER-B QUEUED (2026-11-20)

Parent: memory/goals/mechanic.md #1 | Sibling: memory/ops/non-sandbox-queue.md (Tier-B live leg) | Evidence JSONL: memory/mechanic/goal1-winrm-evidence.jsonl

## Status: PARTIAL (two-tier acceptance rule — NOT full closure)
Goal 1 splits into a sandbox-verifiable Tier-A (client logic) and a live-LAN Tier-B (real remote exec on all 4 hosts). This leaf closes Tier-A only. Do NOT `--record mechanic 1` until Tier-B passes.

## TIER-A — VERIFIED PASS (in-sandbox, no network)
Ran `python memory/mechanic/winrm_pool_selftest.py` → **20/20 PASS, 0 FAIL** (ts 2026-11-20T15:28:51).
Acceptance sub-criteria covered:
- **AC4 host registration:** all 4 hosts (WHITE/BLACK/RED/PALE) present with ip+user.
- **AC1 credential rotation (90-day cycle + pre-expiry alert):** NEVER_ROTATED / OK(~80d remaining) / SOON_EXPIRING(≤7d, within alert window) / EXPIRED(>90d) all detected correctly. This is the "credential expiry triggers auto-rotation alert before failure" half of the acceptance test — MET.
- **AC2 local execution (WHITE):** run_cmd returns status_code 0 + expected output, attempts=1 (no retry needed).
- **AC3 retry logic:** 3 attempts, exponential backoff base 2s → sleeps 2.0s+4.0s=6.0s (≥5.5s asserted), WinRMError raised after all attempts with full attempt count.

## TIER-B — NOT MET (environmental wall, do NOT re-probe from sandbox)
"Remote command execution succeeds on all 4 hosts" requires live NTLM/SSPI auth over LAN. Latest probe `memory/mechanic/winrm-legs.jsonl` (2026-11-20T05:13):
- PALE, BLACK: tcp_5985=true but ntlm `auth_ok=False` (HTTP 401) — no LSA token in sandbox.
- RED: tcp_5985 FAIL (TimeoutError).
This is the documented NTLM/SSPI sandbox wall; a non-sandbox White seat must run it.

## NOTE on prior closure claim
The 2026-11-20 03:4x note in memory/goals/mechanic.md claimed "GOAL 1 CLOSED via WinRM empty-pw rule." That is FALSE — winrm-legs.jsonl shows auth_ok=False + RED timeout. Corrected here; Goal 1 stays OPEN pending Tier-B.

## Unblock (Tier-B, one-time, non-sandbox White seat with LAN egress)
`python memory/mechanic/winrm_sspi_test_all.py` (or `deploy_winrm_verify.bat`) → per-host auth_ok=true + status_code=0 on all 4. Then `python memory/researcher/goal_ledger.py --record mechanic 1 --note '<cmd + winrm-legs.jsonl artifact>'` for full closure.

## Files
- memory/mechanic/winrm_pool.py (pool + retry/backoff client, MAX_RETRIES=3, BACKOFF_BASE_S=2.0)
- memory/mechanic/winrm_rotate.py (daily 90-day rotation schtask runner)
- memory/mechanic/winrm_pool_selftest.py (20/20 self-test)
- memory/mechanic/goal1-winrm-evidence.jsonl (append-only evidence)
