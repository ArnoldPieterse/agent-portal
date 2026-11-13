# OPS r6 - Mechanic probe from Red seat (2026-11-13 19:39 local)

## Fleet health (from Red, 192.168.1.245)
- Black 192.168.1.99 :8888 Studio UP (HTTP 200); Pale 192.168.1.39 :8888 Studio UP (HTTP 200).
- White 192.168.1.179: :445 OPEN, :3389 OPEN, :8099 TIMEOUT, :8888 TIMEOUT, :5985/:5986 TIMEOUT.
  => portal down OR localhost-bound (indistinguishable from LAN; WinRM closed). Arnold to confirm on White: `python probe_portal.py`.
- Red local :8099 -> WSAEACCES 10013 (no usable local portal on this seat).

## Key finding: restart-as-written is likely a NO-OP
- Mirror pushes HERE(White git workspace) -> remote sandboxes. Red received agent_portal.py md5 58f8d7f8 (PRE-FIX, mtime 18:36:25) and memory_mirror.py 1eaaa629 (PRE-FIX). => HERE on-disk is pre-fix.
- Sync code (pre-fix copy, sections 1-4): section-2 code/config push is HERE->sandbox ONLY; section-4 pull is NEW-ONLY. A CHANGED agent_portal.py in the shared folder NEVER reaches HERE. The r5 fix (b2a299ef/c1f4699c) lives in the shared folder, not in HERE.
- PID 1240 loads from HERE => bare restart reloads pre-fix two-way LWW; rollback #6 recurs at next turn boundary.

## Missing bundle step (before Arnold's restart)
1. Verify HERE bytes on White: `curl -s http://localhost:8099/api/file/raw?path=agent_portal.py` -> md5. Expect 58f8d7f8 (pre-fix) per evidence above.
2. If pre-fix: copy fixed agent_portal.py + memory_mirror.py from shared folder into HERE, then _auto_commit (or POST /api/git commit).
3. THEN Arnold restarts portal (loads pull-exclusion). Verifier closes process-level check after reload.

## Staging constraint
- SMB C$ from Red session: ACCESS DENIED on Black/White/local (session not admin anywhere); WinRM closed => cannot stage files for White from this seat. Black artifacts must be staged BY Designer into memory/designer/ (mirror pulls memory/ back to White ~5min).
- staging_r6.py (root of shared folder) = reusable SMB fetch/verify script; needs a credentialed seat (White) to run.

## Runbook one-liner
BROKE: White bundle restart would reload pre-fix code because HERE never receives changed root code files (sync section-2 push-only / section-4 new-only); FIX PENDING: copy fixed agent_portal.py+memory_mirror.py into HERE + _auto_commit BEFORE portal restart.
