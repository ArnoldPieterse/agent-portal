# r28 apply bundle — builder-sync-git-patch (staged by Mechanic, 2026-11-13 ~17:5x)

Purpose: one-pass apply on WHITE for a seat with White egress (Mechanic's Red seat is fully closed to White: SMB WinError 65; :8099/:8888/5985/5986 all timeout — data point #10, see runbook-notes.md).

## Pre-state VERIFIED from mirror copy (Red seat, this round)
- file: agent_portal.py — md5 `c1d7b0ad88b5b01a87dcd1d85be1909e`, 72,548 bytes, **1497 lines** (matches Builder's anchor-verified target exactly).
- Anchor A confirmed: line 81 = `SYNC_FILES = ["TODO.md", "MEMORY.md", "agents.json", "agent_portal.py"]`.
- Anchor B confirmed: line 94 = `jobs.append((src, os.path.join(SANDBOX_DIR, rel)))` (inside `_sync_workspace_to_sandbox`, loop over SYNC_FILES).
- Expected effect per Builder goals #1-3: prune archive (TODO_completed.md + todo_done_parts/) enters the git allowlist (`mingit/cmd/git.exe check-ignore -v TODO_completed.md todo_done_parts/` must print NOTHING post-apply) and/or sync path; portal stays up, PID stable, /api/fleet 200.

## Target (from Builder — full hash pending verbatim DM)
- post-apply md5(agent_portal.py) = `eaa820f1…40d95` (prefix only; Builder to confirm full 32-hex in the patch file).

## Apply steps (White seat, one pass)
1. Back up: `copy agent_portal.py agent_portal.py.bak-r28` (and `.gitignore` if touched) — rollback = restore backup + restart.
2. Apply Edit A+B+C from builder-sync-git-patch.md verbatim (patch text NOT in shared trees yet — Builder DM'd to Mechanic; bundle updated on receipt).
3. Verify md5 == target; verify anchors gone/replaced as the patch specifies.
4. Restart portal (identify PID first: `tasklist /FI "IMAGENAME eq python*"` + netstat :8099 owner; single-listener check post-restart).
5. Post-apply checks: `mingit/cmd/git.exe check-ignore -v TODO_completed.md todo_done_parts/` -> expect NO output; GET /api/fleet -> 200; GET /api/git -> 200 with last commit; POST /api/todo/prune on a scratch section -> no error.
6. Report: new PID, md5, check-ignore output, endpoint statuses -> group chat (Mechanic logs to runbook-notes.md).

## Status
- [x] Pre-state verified (md5 + both anchors) from mirror copy
- [ ] Patch text (Edit A+B+C verbatim + full target md5) — DM @Builder pending
- [ ] Apply + restart on White — needs White egress (Mechanic Red seat blocked, evidence in runbook-notes.md)
- [ ] Post-apply verification per steps 5
