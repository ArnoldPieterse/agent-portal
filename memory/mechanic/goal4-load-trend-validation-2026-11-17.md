# Goal 4 progress: load_trend.py synthetic validation (2026-11-17)

Parent: memory/goals/mechanic.md. Sibling: memory/ops/load_trend.py, load-baseline.jsonl.

## What ran
Synthetic 5-day dataset fed through `load_trend.py` analysis function to validate the
regression detection pipeline end-to-end without the live portal.

## Results (all PASS)
| Test | Expected | Got |
|------|----------|-----|
| c50 regression (+40% p95) | DETECTED | DETECTED (p95 1050ms vs median 747.5ms) |
| c10 normal variance | NOT flagged | OK (ratio 1.01) |
| c200 normal variance | NOT flagged | OK (ratio 1.009) |
| Portal-down day (100% errors) | Skipped from analysis | Correctly excluded |

## What this proves
The SLO pipeline is **built and logic-validated**. When the portal recovers, daily probe
runs will accumulate real data and `load_trend.py` will auto-flag regressions >30% above
median. No further code changes needed for detection.

## Remaining for full closure
- 6 more real daily probe runs (need portal up at :8099)
- One real regression demo caught in production data

## Unblock dependency
Portal restart required: `pythonw agent_portal.py` from non-sandboxed context, OR next
user logon fires PortalRun schtask. Code fix already applied (see portal-permissionerror-fix).
