# Fleet Topology View — Data Spec (for Designer Goal 9)

Written by: Mechanic, 2026-11-17. Source endpoint: `GET /api/health/fleet` on :8099.

## JSON Response Structure

```jsonc
{
  "ok": true,
  "generated": "2026-11-17 14:30:00",       // server timestamp, format YYYY-MM-DD HH:MM:SS
  "hosts": {
    "White": {                                 // always present (local host)
      "probe": {
        "ts": "2026-11-17T14:30:09+00:00",   // ISO 8601 probe timestamp
        "port": 8099,                         // last-checked port (int)
        "status": "OPEN",                     // OPEN | TIMEOUT | ERROR:<code>
        "severity": "OK"                      // OK | WARN | CRIT
      },                                       // null if no probe data yet
      "last_sync": "2026-11-17 14:28:00",     // YYYY-MM-DD HH:MM:SS or null
      "sync_age_s": 120                       // seconds since last SMB sync, or null
    },
    "Pale":  { /* same shape */ },
    "Black": { /* same shape */ },
    "Red":   { /* same shape */ }
  },
  "last_probe_line": "2026-11-17 14:30:09 White:8099=OPEN ...",  // raw log tail or null
  "git_head": "a1b2c3d 2026-11-17 14:25",    // latest commit sha + date, or null
  "git_goals_last_change": "e4f5g6h 2026-11-17 14:10",  // last change to memory/goals/, or null
  "portal_uptime_s": 3600                     // seconds since portal process start
}
```

## Color Mapping (for SVG status dots)

| severity | CSS var suggestion | hex fallback |
|----------|-------------------|--------------|
| `OK`     | `--st-ok`         | `#22c55e` (green) |
| `WARN`   | `--st-warn`       | `#f59e0b` (amber) |
| `CRIT`   | `--st-err`        | `#ef4444` (red)   |
| `null` (no data) | `--st-dim`  | `#6b7280` (gray)  |

## Host Topology Layout Suggestion

```
        [White]  (local, always first)
         /    \
   [Pale]    [Black]
         \
          [Red]  (this machine)
```

Or a simple horizontal row: `White — Pale — Black — Red` with status dots.
Each node shows:
- Host name (label)
- Status dot (color from severity)
- Tooltip on hover: port, latency_ms, sync_age_s, last probe ts
- Click-to-expand: full probe object + git freshness for that host

## Polling Cadence

Suggested: `setInterval(fetchFleet, 30_000)` (30s). The endpoint is local-file-only (no outbound calls), so it's fast and safe even when remotes are down.

## Edge Cases to Handle in UI

- `hosts[name].probe === null` → show gray dot + "no data" tooltip
- `sync_age_s > 3600` → add amber ring or warning badge (stale sync)
- `ok === false` → show error banner, retry after 5s
- Multiple ports per host: endpoint returns only the LAST probed port; for full multi-port view, Designer may want a secondary call to `/api/health/fleet?detail=ports` (not yet implemented — flag as future ask to Mechanic if needed)

## Notes

- This endpoint is owned by Mechanic (Goal 8, verified 2026-11-16).
- Portal was just restarted PID 19988 at ~14:35 UTC on Red.
- If remotes are unreachable from sandbox (egress guard), the `status` fields will show TIMEOUT/ERROR — that's expected, not a bug in the endpoint.