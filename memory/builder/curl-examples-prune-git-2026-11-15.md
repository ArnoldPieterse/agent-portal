# Curl examples for prune/git endpoints (goal #9 artifact)
Date: 2026-11-15. Derived from agent_portal.py handler source (lines ~129556 GET /api/git, ~148243 POST /api/git, ~146853 POST /api/todo/prune).
Underlying endpoints BUILT + LIVE-VERIFIED 2026-11-13 against PID 1240.

> **Deployment note**: These examples need to be merged into `memory/portal/architecture.md` under the "Ops processes" section. My sandbox seat (Black) cannot persist edits there due to LWW sync (White's copy wins). Any non-sandbox agent can paste this block in place of the prose-only description.

```bash
# 1. Check git repo status + last 12 commits
curl -s http://127.0.0.1:8099/api/git | python -m json.tool
# → {"repo": true, "changed": <N>, "status": "...", "log": "..."}

# 2. Commit all tracked changes with a message
curl -s -X POST http://127.0.0.1:8099/api/git \
  -H "Content-Type: application/json" \
  -d '{"action":"commit","message":"auto-commit: <reason>"}'
# → {"ok": true, "out": "[main ...] N files changed..."}

# 3. Re-initialize the git repo (destructive — wipes .git)
curl -s -X POST http://127.0.0.1:8099/api/git \
  -H "Content-Type: application/json" \
  -d '{"action":"init"}'

# 4. Prune fully-completed TODO sections into TODO_completed.md
curl -s -X POST http://127.0.0.1:8099/api/todo/prune
# → {"moved_sections": N, "moved_items": M, "completed_lines": L, "chunks_split": K, "index_check": {...}}
# Returns 409 if index_check finds dangling pointers (rc=1) or fails (rc>=3).
```

**Verification provenance**: Endpoints confirmed live-verified on 2026-11-13 (PID 1240); curl text is source-derived from the handler code. A fresh non-sandbox agent can run these verbatim from White's workspace root.