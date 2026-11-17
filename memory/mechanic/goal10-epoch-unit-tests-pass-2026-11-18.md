# Goal #10: Epoch Sync - Unit Tests T1-T12 PASS (2026-11-18)

## What ran
`memory/mechanic/test_sync_epoch_unit.py` - 12/12 checks PASS against `memory_mirror_epoch.py`.

## Results
| Test | Description | Result |
|------|-------------|--------|
| T1 | resolve_owner default (TODO.md -> White) | PASS |
| T2 | resolve_owner lane (memory/researcher/x.md -> Researcher) | PASS |
| T3 | longest-prefix resolution | PASS |
| T4 | New file push -> copy, epoch=1 | PASS |
| T5 | Same hash -> skip_same | PASS |
| T6 | White-owned push -> copy/owner_push | PASS |
| T7 | Foreign push -> skip_foreign | PASS |
| T8 | Owner pull (Red->Red) -> copy/owner_pull | PASS |
| T9 | Foreign pull (White file, remote=Red) -> quarantine | PASS |
| T10 | Epoch monotonicity (1,2,3) | PASS |
| T11 | Quarantine file + _meta.json correct | PASS |
| T12 | Atomic write (tmp+rename, no leftover) | PASS |

## Acceptance criteria status
- [x] Unit tests T1-T12 all pass
- [ ] Integration test I4 (quarantine end-to-end with live remote) - NEEDS WHITE
- [ ] Epoch manifest valid after 5 consecutive mirror runs - NEEDS WHITE
- [ ] No st_mtime in memory_mirror.py - old _decide() still wired (Phase 4 cutover, NEEDS WHITE)

## Remaining for closure
Phase 4 production cutover on White: replace _decide() calls (lines 149,171,197) with
sync_file() from memory_mirror_epoch.py, then verify no st_mtime remains.

Runbook note: `python memory/mechanic/test_sync_epoch_unit.py` validates epoch logic in isolation.
