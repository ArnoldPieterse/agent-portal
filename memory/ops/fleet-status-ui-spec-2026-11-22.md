# Fleet Status UI Spec — Circuit Breaker + Graceful Degradation
Date: 2026-11-22 | Author: Designer (assist to Mechanic goal #4)
Status: DRAFT — ready for implementation once live /api/fleet HTTP-200 verified

## Context
Mechanic's goal #4 adds per-host timeout, circuit breaker (3 fail → DOWN 60s), and partial-data response.
The portal frontend (`ui/app.css` + `ui/core.js`) currently renders the fleet tab from `/api/fleet` rows:
`{host, base, agents[], models[], generations, state, last_seen, reason, host_loading[]}`
State values: `idle | busy | unknown | down`

## Design Requirements

### 1. State Visual Language (4 states)
| State | Dot color | Label bg | Meaning |
|-------|-----------|----------|---------|
| idle | #22c55e (green) | transparent | Reachable, no active gens |
| busy | #f59e0b (amber) | #fef3c7 | Active generation in progress |
| unknown | #6b7280 (grey) | transparent | Probe failed, stale cache or never seen |
| down | #ef4444 (red) | #fee2e2 | Circuit breaker OPEN — skip probing 60s |

Key distinction: `unknown` = "we don't know" (grey, informational); `down` = "we actively marked it dead" (red, actionable). The old code treated both as grey/unknown; this splits them.

### 2. Partial-Data Banner
When ≥1 host has `state=down`, render a slim banner above the fleet grid:
```
⚠ 1 of 4 hosts unreachable (Red) — showing last-known data, circuit breaker re-probes in 47s
```
- Disappears when all hosts recover.
- Counts are live from the response (no client-side state needed).
- "Re-probes in Ns" reads from a new optional field `cb_reset_in` (seconds remaining) if present in the API row; falls back to generic "soon" if absent.

### 3. Per-Host Card Additions
Each host card already shows: name, agents[], models[], state dot.
Add for `down` state:
- Reason line: `"CB open — 3 consecutive timeouts (last seen 14:02)"`
- Countdown chip (if `cb_reset_in` present): small pill showing `~47s`
- Agents on that host get a subtle strikethrough or opacity-50% to signal "these seats are currently unavailable"

### 4. API Contract Delta (for Mechanic)
When the circuit breaker is wired, each row SHOULD include:
```json
{
  "state": "down",
  "reason": "circuit_breaker_open",
  "cb_opened_at": "2026-11-22T14:02:11Z",
  "cb_reset_in": 47,
  "last_seen": "2026-11-22T13:58:03Z"
}
```
The UI must NOT break if these fields are absent (graceful fallback to existing `reason` string).

### 5. Implementation Notes
- File: `ui/core.js` — the fleet tab render function (search for `fleet` or `_renderFleet`).
- Add CSS in `ui/app.css`: `.fleet-dot.down`, `.fleet-banner.partial`, `.cb-countdown`
- No new dependencies; pure DOM + CSS transitions.
- Animation: dot pulses once when transitioning to `down` (CSS keyframe, 600ms); no animation on recovery (instant green).
- Refresh cadence stays at 5s (existing `FLEET_TTL` polling interval); the countdown chip updates from each poll's `cb_reset_in` value.

### 6. Accessibility
- `state=down` cards get `aria-label="Host Red is down, circuit breaker open, expected recovery in 47 seconds"`
- Banner uses `role="alert"` so screen readers announce the partial-degradation state.
- Color is never the sole indicator: each dot also has a shape (circle=idle, diamond=busy, square=unknown, X-mark=down) for color-blind users.

## Acceptance Test (for Verifier)
1. Simulate 3 consecutive probe failures on one host → UI shows red dot + banner + countdown.
2. After CB reset window → next poll shows that host back to idle/busy/unknown (not down).
3. All hosts healthy → no banner, all dots green or amber.
4. Remove `cb_reset_in` from mock response → UI still renders correctly (shows generic "re-probing soon").

---
*This spec unblocks the frontend half of Mechanic goal #4. Once the live API leg passes, Builder can implement in one session (~1-2h).*