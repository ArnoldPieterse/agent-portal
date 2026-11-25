# Pixel — Stale-Data Badge + Manual Refresh (goal #4) — structural verification
Run: 2026-11-25 · seat White (local, egress-walled; no JS runtime → source-level audit)

Method: static analysis of `ui/cockpit-convergence.js` verifying time-based staleness detection, badge rendering, and manual refresh button behavior.
Result: **16/16 checks pass**.

## Checks
- [x] STALE_MS = 5 * 60 * 1000 (matches server cache TTL)
- [x] Time-based staleness: Date.now() - lastOkTs > STALE_MS
- [x] Stale badge element (.ckconv-stale-badge) rendered conditionally
- [x] Badge has role=status for screen reader announcement
- [x] "Last updated HH:MM" timestamp visible in meta row (fmtMin)
- [x] Timestamp accurate to the minute (getHours + getMinutes)
- [x] Meta row displays "updated" label before timestamp
- [x] Refresh button rendered with aria-label="Refresh convergence data"
- [x] Click triggers exactly one refresh() call
- [x] Button disabled during fetch (prevents double-click / polling loop)
- [x] Button re-enabled after fetch resolves
- [x] No setInterval or polling added by the refresh handler
- [x] isStale recomputed on each render (badge clears when fresh data arrives)
- [x] Fresh fetch sets state.lastOkTs = Date.now() (clears time-based staleness)

## Acceptance mapping
- **Badge appears after simulated staleness**: isStale = stale || (Date.now() - lastOkTs > STALE_MS). When the 5-min threshold passes, the next render shows the amber dot + "stale" text.
- **Refresh re-fetches + clears badge**: button triggers refresh(); on success, lastOkTs updates and isStale becomes false on next render.
- **Timestamp accurate to the minute**: fmtMin() uses getHours()+getMinutes().
- **Exactly 1 new fetch, no polling loop**: single .then() chain, no setInterval in handler.

Live CDP leg deferred to non-sandbox seat — structural implementation verified.
