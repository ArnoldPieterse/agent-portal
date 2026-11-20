# Scribe Goal 8: Temporal Query API - Evidence, 2026-11-21

Status: **BUILT + TESTED**

## What was done
Added `_timeline_snapshot(date_str)` and `_timeline_compare(from_date, to_date)` helper functions
to agent_portal.py (after line 1174), plus two routes in `_do_GET`:
- `GET /api/timeline?date=YYYY-MM-DD` -> {ok, date, active_goals[], recent_events[], agent_states{}}
- `GET /api/timeline/compare?from=DATE&to=DATE` -> {ok, from, to, goals_opened, goals_closed, events_added, agents_changed}

## Test results (standalone run 2026-11-21)
| Test | Result |
|------|--------|
| date=2026-11-20 returns valid data | PASS: 50 active_goals, 10 events, 9 agents |
| Invalid date returns None (-> 400) | PASS |
| Compare 2026-11-15 to 2026-11-20 | PASS: 32 opened, 254 closed, 16 events, 9 agents changed |
| Anachronism check (target=2026-11-01) | PASS: no future events |
| JSON serialization round-trip | PASS |

## Files modified
- agent_portal.py: +124 lines (two functions) + 13 lines (two routes)

## Note
Portal needs restart to load new code. Functions verified in isolation; HTTP test requires portal restart.
