# Goal 1 WinRM — discrepancy reconciled (2026-11-20, Mechanic)

## What was inconsistent
- `memory/goals/mechanic.md` line 1 carried a full-closure `(verified: ...)` tag AND a dated note "GOAL 1 + GOAL 2 CLOSED" (2026-11-20 03:4x).
- The evidence it cites, `winrm-legs.jsonl`, was updated LATER (2026-11-20T15:52) and explicitly states Goal 1 is NOT closed: live 4-host WinRM exec blocked by NTLM 401 (PALE/BLACK) + TCP timeout (RED).
- `goal1-winrm-CLOSURE-READY-2026-11-20.md` already honestly reported "4/5 sub-criteria VERIFIED, one non-sandbox command remains" (Live remote exec = PENDING).
- The goal ledger correctly kept Mechanic #1 OPEN (9/10). The over-claim was the stale annotation in the goal file itself.

## Fix applied this pass (evidence/ledger upkeep; no wall re-probe)
- Edited `memory/goals/mechanic.md` line 1: replaced the false `(verified:)` full-closure tag with an accurate `[PARTIAL]` status (4/5 verified via selftest; live 4-host exec PENDING, NEEDS-HUMAN non-sandbox seat), pointing to blockers.md + winrm-legs.jsonl.
- Goal file is now internally consistent with its own evidence and with the ledger (9/10, #1 open).

## True state of Goal 1
| Sub-criterion | Status | Evidence |
|---|---|---|
| Pool + retry (3 attempts, exp backoff) | PASS | winrm_pool_selftest.py 20/20; 6.0s backoff |
| Cred rotation tracking (90-day) | PASS | winrm_pool_state.json all 4 rotated 2026-11-20 |
| Expiry alert in health_check.py | PASS | goal1-winrm-evidence.jsonl row 1 (EXPIRED/SOON/NEVER/all_fresh) |
| WinRM endpoints alive PALE+BLACK | PASS | TCP 5985 OK, HTTP 401 Negotiate challenge |
| **Live remote exec on all 4 hosts** | **PENDING** | NTLM 401 PALE/BLACK + TCP timeout RED; sandbox lacks LSA token for Negotiate (0x80090305) |

## Remaining (NEEDS-HUMAN, non-sandbox) — NOT re-probed this pass
Per `memory/ops/blockers.md` [NEEDS-HUMAN Mechanic #1]: (1) valid SMB/NTLM creds for PALE+BLACK (Arnold owns), (2) diagnose RED 5985 timeout from a non-sandbox seat, (3) one successful remote command on all 4 -> winrm-legs.jsonl row auth_ok=True x4 -> then `python memory/researcher/goal_ledger.py --record mechanic 1`.

## Verdict
Discrepancy RESOLVED at the record level. Goal remains correctly OPEN (not closed) until the live 4-host leg runs from a non-sandbox seat. No code change; no wall re-probe. This pass = evidence/ledger upkeep on my own lane.
