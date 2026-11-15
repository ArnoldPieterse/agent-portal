# Builder — 10 goals (set 2026-11-13)

Source: group goal-setting thread, collected by Orchestrator; verbatim. Canonical record: TODO.md `## AGENT GOALS (set 2026-11-13)`.

1. Ship the "Files" panel in index.html listing /api/uploads; verified by hard-refresh and seeing a test upload appear, then removing it. (verified: 2026-11-15 upload round-trip PASS; evidence memory/builder/uploads-panel-verify-2026-11-15.md)
2. Build an uploads→remote-sandbox mirror (Black/Red/Pale via SMB) syncing new attachments within 5 min; verified by a round-trip file opened by each remote host's own tools. (pointer: memory/builder/MEMORY.md)
3. Write a prune regression script covering 4 cases (all-complete section, partially-open stays, >240-line chunking, idempotent double-run); done = all four green against the live portal. (verified: 2026-11-15 - memory/builder/prune_regression.py, ALL PASS 4/4 cases on fixtures, exit non-zero on FAIL — recorded 2026-11-15)
4. Add a path-safety test suite for /api/upload (drive letters, `../`, POSIX absolute, bare 'uploads'); re-runs on every portal edit and must stay green. (verified: 2026-11-15 - memory/builder/upload_path_safety.py, 12/12 PASS incl. drive letters, ../ raw+encoded, POSIX abs, bare 'uploads' — recorded 2026-11-15)
5. Extend group_e2e.py to flag mid-tool-call truncations as an explicit failure field in the result JSON; verified with a known-truncated response fixture.
6. Add a daily auto-commit scheduled task calling POST /api/git so nothing sits uncommitted >24h; verifiable via GET /api/git gap check. (verified: 2026-11-15 - schtask PortalDailyGitCommit daily 18:00 -> daily_git_commit.py; test run OK, tree clean, drift 0 — recorded 2026-11-15)
7. Extend the 🔧 Ops panel with disk-usage + portal-uptime tiles; values cross-checked against per-host ground truth before marking done. (verified: 2026-11-15 - GET /api/ops added to agent_portal.py (_ops_snapshot: shutil.disk_usage on SystemDrive + PORTAL_START uptime); index.html Ops panel gained diskTile + uptimeTile host tiles fed by opsTiles(); cross-checked vs ground truth: API disk total/free 1861.9/182.1 GB == Win32_LogicalDisk C: 1861.9/182.1 GB, API started 09:33:49 == Win32_Process CreationDate for live PID — recorded 2026-11-15)
8. Create memory/portal/testing.md playbook (≥3 edge cases per endpoint before [x]); enforced on every build I ship from now on.
9. Document prune/git endpoints in memory/portal/architecture.md with curl examples verified live against PID 1240; pass = a fresh agent runs them verbatim without edits.
10. Commit discipline: every commit of mine carries a "verified:" line stating what ran and its output; verifiable by grepping `git log`.
