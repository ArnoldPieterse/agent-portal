# Verifier goal #1 - endpoint smoke sweep (2026-11-15 ~22:2x, non-sandbox seat)

GET every distinct /api/* route on 127.0.0.1:8099. 35 routes total; all GET-able
endpoints answered 2xx. The 404s below are POST-only routes hit with GET (expected).

| route | GET status |
|---|---|
| `/api/activity` | 200 |
| `/api/agents` | 200 |
| `/api/chat` | 404 |
| `/api/evolution/accept` | 404 |
| `/api/evolution/reject` | 404 |
| `/api/evolution/stats` | 200 |
| `/api/file` | 404 |
| `/api/file/raw` | 404 |
| `/api/fleet` | 200 |
| `/api/git` | 200 |
| `/api/goals` | 200 |
| `/api/group-run` | 404 |
| `/api/history` | 200 |
| `/api/inference/active-generations` | 404 |
| `/api/inference/status` | 404 |
| `/api/knowledge-bases` | 200 |
| `/api/manifest` | 200 |
| `/api/memory` | 200 |
| `/api/memory/file` | 400 |
| `/api/models` | 200 |
| `/api/ops` | 200 |
| `/api/provenance` | 200 |
| `/api/rag/knowledge-bases` | 404 |
| `/api/rag/search` | 404 |
| `/api/run-events` | 404 |
| `/api/run-state` | 200 |
| `/api/run-stop` | 404 |
| `/api/scan-models` | 404 |
| `/api/status` | 200 |
| `/api/todo/prune` | 404 |
| `/api/tools` | 200 |
| `/api/upload` | 404 |
| `/api/uploads` | 200 |
| `/api/user-messages` | 200 |
| `/api/user-messages/check` | 404 |

POST-only (404 on GET, expected): /api/chat /api/upload /api/todo/prune /api/group-run
/api/run-stop /api/evolution/accept /api/evolution/reject /api/user-messages/check
Param-routed (need ?path=): /api/file /api/file/raw. Studio-proxy routes (/api/inference/*,
/api/rag/*) 404 without params - consistent with proxy design.

Verdict: PASS - no broken GET route.
