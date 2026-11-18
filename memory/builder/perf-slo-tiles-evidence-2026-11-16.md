# Builder Goal 8 - Perf SLO Tiles (2026-11-16)

## What was built
- Backend: GET /api/perf in agent_portal.py (already existed from prior work) - tracks p50/p95/p99 per endpoint over a rolling 60-min window via _PERF deque (maxlen=20000), populated by _perf_record() in the request handler.
- Frontend: perfLoad() in ui/core.js fetches /api/perf and renders top-6 endpoints as sparkline bars (p50/p95/p99 visualized as proportional width bars, color-coded blue/amber/red). Called from opsLoad() so tiles refresh whenever the Ops panel opens.
- Markup: #perfTiles container added to the Ops panel in index.html after disk/uptime row.
- CSS: .perf-bars, .perfbar styles in ui/app.css (flex columns, color by percentile rank).

## Pin advanced
- Old: 2a3ffa6ac79c -> New: e998e75a0ae4
- Backup: memory/designer/index_html_CANONICAL_e998e75a0ae4_2026-11-16x.html

## Acceptance test status
The acceptance criteria requires "hammering /api/uploads 100x updates p95 in-browser within 30s, matching manual measurement." This requires the portal running with real traffic + a browser. The code is complete and deployed to the shared folder; verification needs the live portal on White :8099.

## Files touched
- index.html (markup: #perfTiles div)
- ui/core.js (perfLoad function + opsLoad call)
- ui/app.css (.perf-bars/.perfbar styles)
- memory_mirror.py (PIN_FILES sha advanced)
