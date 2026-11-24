# Evidence: fleet-mode.json source unification (2026-11-24)

**Problem:** Two divergent fleet-mode.json files existed:
- Root (`fleet-mode.json`, 154B): written by fleet_mode_writer.py, read by _get_fleet_mode() + dispatch_filter.py
- `memory/ops/fleet-mode.json` (285B): read by cockpit snapshot for mode banner

The ops file was stale (00:23, 25% goals) while root was fresh (100%), causing the
cockpit banner to display outdated mode data.

**Fix:** Changed `_cockpit_snapshot()` in agent_portal.py to read root `fleet-mode.json`
(line ~1698), unifying all readers to a single canonical source.

**Verification:**
- py_compile passes (syntax OK)
- Root file validates: mode=WORK, goal_pct=100.0, valid ISO-8601 timestamp
- All three consumers now read the same file: _get_fleet_mode(), dispatch_filter.py, cockpit snapshot

**File changed:** agent_portal.py (1 line path change + comment)
