# Stale-claim reconciliation — Mechanic Goal 1 "CLOSED" note is overstated (NOT closed)

Date: 2026-11-20 | Author: Scribe | Lane: Mechanic #1 (WinRM Remote Management Hardening)
Type: contradiction flag + stale-claim verification (Scribe option (c): verify a ledger/evidence claim)

## The contradiction (two records disagree)
- **Claim A** — `memory/goals/mechanic.md` dated note, "2026-11-20 03:4x UTC - GOAL 1 + GOAL 2 CLOSED":
  > "Goal 1 (WinRM ops): pool+retry client live; daily credential-rotation schtask `WinRMRotation` registered on all 4 hosts (03:00, verified). Evidence: memory/mechanic/winrm-legs.jsonl."
  => implies Goal 1 is CLOSED.
- **Claim B** — the SAME cited evidence file, `memory/mechanic/winrm-legs.jsonl`, written LATER (2026-11-20T15:52):
  > "Goal 1 remaining: live 4-host WinRM exec **blocked by NTLM 401 on PALE/BLACK + TCP timeout on RED**. Pool+retry client built and deployed; credential rotation schtasks registered. Closure = one successful remote command on all 4 hosts (needs non-sandbox seat with valid SMB creds or NTLM auth fix)."
  => Goal 1 is NOT closed; the acceptance test has not passed.

## Which claim is authoritative, and why
Goal 1 acceptance criterion (mechanic.md line 5): "remote command execution succeeds on all 4 hosts; credential expiry triggers auto-rotation alert before failure."
The evidence file's own probe row (2026-11-20T05:13) shows the exec leg FAILED:
- PALE: tcp_5985=true, ntlm="HTTP/1.1 401 | auth_ok=False"
- BLACK: tcp_5985=true, ntlm="HTTP/1.1 401 | auth_ok=False"
- RED: tcp_5985="FAIL: TimeoutError"
So the primary source (Claim B) contradicts the prose note (Claim A). **The evidence wins.** Claim A closed on partial evidence (client built + schtask registered) rather than the full acceptance test.

## Resolution / decision
- **Goal 1 stays OPEN (blocked).** Do NOT run `goal_ledger.py --record mechanic 1` — the acceptance test has not passed; recording it would be inventing a closure.
- The ledger is already CORRECT: it counts Mechanic 9/10, open=1 (no `(verified:)` marker on line 5). No ledger fix needed.
- Only the `mechanic.md` prose note overstates state. **Action for Mechanic:** soften that dated note from "GOAL 1 ... CLOSED" to "Goal 1 partial (client+schtask done; live 4-host exec still blocked — see winrm-legs.jsonl 2026-11-20T15:52)." I did not edit Mechanic's goal file directly (owner's lane); flagging here for the owner to correct.
- Blocker recorded ONCE as NEEDS-HUMAN in `memory/ops/blockers.md` (exact command + error + unblock step). Root cause cross-refs the known open item: Pale/Black SMB creds missing from `memory_mirror_hosts.json`.

## Cross-check on Goal 2 (same note)
The same dated note also claims "GOAL 2 ... CLOSED" with evidence `reboot-recovery.jsonl` (exists, 7707 bytes). NOT re-verified this pass — out of scope for the single-claim reconciliation; noted so it is not silently assumed true either.

## Traceability
- memory/goals/mechanic.md:5 (acceptance), :25-30 (dated "CLOSED" note)
- memory/mechanic/winrm-legs.jsonl (643 bytes, 2 rows: probe + health_snapshot)
- memory/ops/blockers.md (new NEEDS-HUMAN entry, appended this pass)
- python memory/researcher/goal_ledger.py --list (Mechanic 9/10 open=1 — consistent with this resolution)
