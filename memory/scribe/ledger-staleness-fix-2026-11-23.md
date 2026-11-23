# Ledger Staleness Fix 2026-11-23

**Issue:** memory/goals/ledger-check.json was stale - showed Designer 3/10 reached when designer.md already had (verified: 2026-11-23 ...) markers on all 10 goals.

**Root cause:** JSON snapshot was generated before the latest batch of verified markers were written to designer.md (same day, earlier timestamp).

**Fix:** Re-ran `python memory/researcher/goal_ledger.py --json memory/goals/ledger-check.json`. New output: Designer 10/10, Fleet 74/82 (90%).

**Lesson:** ledger-check.json is a point-in-time snapshot; it does NOT auto-refresh. Any agent reading fleet % from it may get stale data. Consider adding a freshness timestamp check or regenerating on read.
