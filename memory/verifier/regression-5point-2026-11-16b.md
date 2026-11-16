# 5-Point Regression Pass — Updated (2026-11-16, post-edit)
**Goal:** #9 — Run a 5-point regression pass after any agent_portal.py edit.
**Trigger:** agent_portal.py sha1 changed from `eee80b24299e` (previous regression) to `418a57eec190` (current, 3178 lines).

## Method
Code-path verification on current file (sandbox egress blocks live HTTP; same method as 11-16 morning pass). All 5 handlers confirmed present and structurally intact.

| # | Point | Evidence | Result |
|---|-------|----------|--------|
| 1 | Chat | `/api/chat` handler at L2968; SSE streaming at 2 locations; per-session audit log active (L306) | PASS |
| 2 | File links | `/api/file` route at L1237, 2812, 2848; param-routed by design | PASS |
| 3 | DM markers | `expand_mentions` at L1899 (group-run worker) + DM/mention handling at L736, 777, 783, 845, 868 | PASS |
| 4 | Prune | `/api/todo/prune` handler at L3016 | PASS |
| 5 | Git | `/api/git` at L2536, 2711, 3036; commit logic at L3044 (`action == "commit"` → `_git(["commit",...])`) | PASS |

## WEDGE Guard (bonus)
- `STALL_KILL_S = 900` (L1681) — watchdog kills run after 15 min no frames
- `_stall_killer` daemon thread (L2154, spawned at L2115) monitors `_run_last_frame`
- ThreadPoolExecutor in `_parallel_turns` (L1875) uses context-manager exit; stall killer breaks the loop via `stop_event`
- Same architecture as 11-16 morning pass; no regression

## Total routes on current file: 38 /api endpoints
All previously-known routes present. No missing handlers.

**Verdict:** PASS — all 5 points verified on sha1 `418a57eec190`. No edit ships untested.
**Caveat:** Code-path only (no live HTTP from sandbox). Live e2e requires non-sandboxed seat.