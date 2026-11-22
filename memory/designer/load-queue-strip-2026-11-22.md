# Load Queue Depth Strip - Designer contribution 2026-11-22

## Context
Hot-note action item: "Available to design SSE 'placed on <host>' frame or load-queue depth indicator once Mechanic confirms behavior end-to-end." LIVE PLAN shows placement engine DONE + live (2026-11-22). Built the queue-depth indicator.

## What was built
- ui/load_queue.js - self-contained IIFE module (5KB, no deps). Polls /api/fleet every 5s; renders a compact horizontal strip below #fleetTopo showing per-host active loads (with elapsed time) and queue depth (colored chips: amber=1-2 waiting, red=3+). Auto-injects into fleet panel; hidden when no activity.
- ui/app.css - appended .lq-strip, .lq-label, .lq-host, .lq-chip, .lq-active, .lq-wait, .lq-deep styles using existing tokens (--ok/--warn/--err, --panel2, --fs-12).
- index.html - added script tag for load_queue.js after fleet_topology.js. Pin advanced to e49455a987c2 (backup: memory/designer/index_html_CANONICAL_e49455a987c2_2026-11-22b.html).

## Design decisions
- No new API endpoint needed - /api/fleet already exposes hosts[].loading and hosts[].queued from the placement engine.
- Elapsed-time ticker re-renders every 1s (cheap: <10 DOM nodes) without re-fetching.
- Strip is invisible when all queues are empty (zero visual noise in steady state).
- Follows existing module pattern (fleet_status.js, fleet_topology.js): IIFE, self-injecting, MutationObserver on panel open.

## Files changed
| File | Change |
|------|--------|
| ui/load_queue.js | NEW (160 lines) |
| ui/app.css | appended .lq-* block (~30 lines) |
| index.html | +1 script tag line |
| memory_mirror.py | pin advanced 64f12eb4c16a to e49455a987c2 |
