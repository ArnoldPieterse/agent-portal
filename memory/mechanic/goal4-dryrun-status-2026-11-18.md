# Mechanic #4 - Dry-run verification + status (2026-11-18)

## Verified this pass
- `reboot_recover.py`: syntax OK (AST parse clean), 5 functions, correct logic flow
- `deploy_reboot_recovery_all.py`: syntax OK, 6 functions, idempotent (/f flag)
- **Live dry-run on Red sandbox seat**: `python memory/mechanic/reboot_recover.py --dry-run`
  - Result: "Clean boot detected. No recovery needed." (NO-OP, exit 0)
  - Detection logic (Event ID 6008 check) works correctly
  - Portal health check path validated (is_portal_running -> socket connect_ex)

## Status
| Component | State |
|-----------|-------|
| Script logic | VERIFIED (dry-run passes on Red) |
| Unit tests (Builder) | 6/6 PASS (command construction) |
| Local schtask registration | BLOCKED - COM wall in sandbox (documented in blockers.md) |
| Remote WinRM deploy | BLOCKED - sandbox egress to .39/.99/.245:5985 |
| elev.py helper | ABSENT at this seat |

## Exact remaining step (one command, non-sandbox White admin)
```
python memory/mechanic/deploy_reboot_recovery_all.py
```
This will:
1. Register FleetBootRecovery schtask locally (White) via schtasks /sc onstart /ru SYSTEM
2. Attempt WinRM deploy to Pale/Black/Red (requires pywinrm + port 5985 open)
3. Log results to memory/mechanic/reboot-recovery.jsonl

## Closure criteria after that step runs
- reboot-recovery.jsonl contains type=deploy_reboot_recovery_all with all_verified=true
- OR: local verified=true + remotes documented as manual-step (if WinRM unavailable on remotes)
- Then: `python memory/researcher/goal_ledger.py --record mechanic 4 --note 'deploy script run from non-sandbox; evidence reboot-recovery.jsonl'`

## Blocker ref
memory/ops/blockers.md -> "[NEEDS-HUMAN 2026-11-18] Mechanic #4 FleetBootRecovery schtask: COM wall on all sandbox seats"
