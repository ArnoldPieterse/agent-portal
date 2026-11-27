# Evidence — Outlet fire_queue.py (goal #1 unblock infrastructure)
Date: 2026-11-27
Lane: outlet
Goal: #1 (First live account connection + end-to-end ship)

## What was built this pass
`memory/outlet/fire_queue.py` — one-command auto-ship script that fires ALL approved
queue entries to a platform when credentials are present.

## Verification
- `selftest`: 5/5 PASS (credentials detection, status parsing, empty-file rejection)
- Dry-run on actual queue: correctly identifies 8 ready-for-human posts, reports 0 approved
- Exit codes: 0=shipped, 1=no approved, 2=missing credentials, 3=partial fail

## Unblock path (now reduced to 3 steps for Arnold)
1. `echo "<app-password>" > memory/outlet/.secrets/bluesky.txt`
2. Approve one or more posts in queue/ (change `status:` to `approved`)
3. `python memory/outlet/fire_queue.py --platform bluesky`

## Timeline proof capability
Each ship logs to ship-timeline.jsonl with UTC timestamps, so event→draft→ship <4h
is automatically proven by the log entries.

## OPS-NOTE recorded
memory/ops/blockers.md — "Goal #1 (First live ship) needs credentials, infra complete"
