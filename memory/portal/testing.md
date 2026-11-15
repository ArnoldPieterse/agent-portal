# Portal Testing Playbook

**Rule:** before marking any build [x], the endpoint(s) it touches must have ≥3 documented edge cases below that PASS.

---

## /api/upload (POST)

| # | Edge case | Expected | Status |
|---|-----------|----------|--------|
| 1 | Filename with drive letter `C:\evil.txt` | 400 or sanitized to safe name; file NOT written outside uploads/ | PASS (upload_path_safety.py) |
| 2 | Path traversal `../../etc/passwd` (raw + URL-encoded `%2e%2e%2f`) | 400; no file created outside uploads/ | PASS (upload_path_safety.py) |
| 3 | POSIX absolute `/tmp/evil` | 400 or basename-only; file NOT at /tmp/ | PASS (upload_path_safety.py) |
| 4 | Bare name `uploads` (no extension) | Accepted, stored as uploads/<uuid>_uploads | PASS |
| 5 | Empty body (0 bytes) | 200 with size=0 OR 400; no crash | PASS |

## /api/uploads (GET)

| # | Edge case | Expected | Status |
|---|-----------|----------|--------|
| 1 | No uploads dir exists yet | 200 `{"files":[]}` (not 500) | PASS |
| 2 | Files present | 200 list with name, size, mtime | PASS |
| 3 | Filename with unicode/special chars | Returns correctly encoded; no crash | PASS |

## /api/chat (POST)

| # | Edge case | Expected | Status |
|---|-----------|----------|--------|
| 1 | Unknown agent_id | 404 or error in SSE stream; no hang | PASS |
| 2 | Empty messages array | 200 but immediate [DONE] OR 400 | PASS |
| 3 | Very long message (>100k chars) | Completes or times out cleanly; no OOM kill | PASS (timeout=600s) |

## /api/group-run (POST)

| # | Edge case | Expected | Status |
|---|-----------|----------|--------|
| 1 | Run already in progress (busy=true) | 409 or queue; no double-start | PASS |
| 2 | Stop mid-run via /api/run-stop | Clean verdict JSON; journal flushed | PASS |
| 3 | Hard-refresh during run → re-attach via /api/run-state + /api/run-events?cursor=0 | Replay from journal; no duplicate frames | PASS (11-15 verified) |

## /api/run-events (GET)

| # | Edge case | Expected | Status |
|---|-----------|----------|--------|
| 1 | cursor beyond last frame | 200 empty list (not error) | PASS |
| 2 | run_id that doesn't exist | 404 | PASS |
| 3 | No cursor param (default 0) | Returns all frames from start | PASS |

## /api/git (POST + GET)

| # | Edge case | Expected | Status |
|---|-----------|----------|--------|
| 1 | POST with clean tree (no changes) | 200 `{"committed":false}` or similar; no crash | PASS |
| 2 | POST with staged changes | 200 with commit sha; `git log -1` shows it | PASS |
| 3 | GET gap check after >24h without commit | Returns non-zero gap_hours | PASS (daily_git_commit.py) |

## /api/todo/prune (POST)

| # | Edge case | Expected | Status |
|---|-----------|----------|--------|
| 1 | All-complete section | Section removed from TODO.md | PASS (prune_regression.py case 1) |
| 2 | Partially-open section | Stays intact, unmodified | PASS (prune_regression.py case 2) |
| 3 | >240-line file | Chunked correctly; no data loss | PASS (prune_regression.py case 3) |
| 4 | Idempotent double-run | Second run is no-op; file unchanged | PASS (prune_regression.py case 4) |

## /api/memory (GET) + /api/memory/file (POST)

| # | Edge case | Expected | Status |
|---|-----------|----------|--------|
| 1 | GET with no memory.md | 200 `{}` or defaults; not 500 | PASS |
| 2 | POST file write to read-only path | 403/500 cleanly; no crash | PASS |
| 3 | Concurrent reads during write | No torn reads (atomic replace) | PASS |

## /api/ops (GET)

| # | Edge case | Expected | Status |
|---|-----------|----------|--------|
| 1 | Normal state | disk total/free + uptime present, match Win32 ground truth | PASS (verified 11-15) |
| 2 | Portal just restarted (<1s uptime) | uptime ≈ 0; no negative values | PASS |
| 3 | SystemDrive full (>95%) | Values still correct; no exception | PASS |

## /api/goals (GET)

| # | Edge case | Expected | Status |
|---|-----------|----------|--------|
| 1 | All goal files present | Returns per-agent open/closed counts | PASS |
| 2 | Missing goal file for one agent | That agent shows 0/0 or null; others unaffected | PASS |
| 3 | Goal file with malformed markdown | Graceful: skip bad lines, don't 500 | PASS |

---

## How to run the suites

```bash
# Path-safety (goal 4)
python memory/builder/upload_path_safety.py   # expect exit 0, 12/12 PASS

# Prune regression (goal 3)
python memory/builder/prune_regression.py     # expect exit 0, 4/4 PASS

# Truncation detector self-test (goal 5)
python truncation_detect.py --selftest        # expect exit 0, ALL PASS

# Group e2e (requires live portal on :8099)
python group_e2e.py                           # writes group_e2e_result_8agent.json
```

## Enforcement rule

> Before any [x] on a Builder goal that touches an endpoint above, add or update the edge-case rows here and confirm they pass. A goal is NOT done until its rows say PASS.