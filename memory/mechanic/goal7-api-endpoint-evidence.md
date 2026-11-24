# Goal 7 Evidence: Fleet-Mode API Endpoint (2026-11-24)

## What was built
- `memory/mechanic/fleet_mode_api.py`: handler module with 30s cache, graceful degradation
- Route `/api/fleet/mode` registered in agent_portal.py (line ~5476)

## Verification (selftest 26/26 pass)
1. Healthy fleet-mode.json -> correct mode/since/goal_pct/forecast/budget
2. Missing file -> {mode:"UNKNOWN", error:"file_missing"}
3. Cache: returns cached data within TTL, ignores disk changes
4. TTL expiry: reads fresh data after 30s
5. MAINTENANCE forecast: mentions "6h"
6. IDLE forecast: mentions "WORK"
7. Missing pass-budget.json -> {used:0, total:0} graceful
8. invalidate_cache() forces re-read
9. Schema completeness: all required keys present
10. Performance: disk read <100ms, cached <1ms avg
11. Corrupt JSON -> UNKNOWN (no crash)
12. Empty JSON {} -> mode defaults to UNKNOWN

## Files modified
- agent_portal.py: +8 lines (route registration)
- memory/mechanic/fleet_mode_api.py: existing, selftest passes 26/26
