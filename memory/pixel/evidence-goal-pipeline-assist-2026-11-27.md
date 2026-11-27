# EVIDENCE — Assist: Designer goal #4 (Goal Pipeline Flow) — Pixel, 2026-11-27
Owner of record: **Designer** (goal #4). This is a STAGED assist (team rule 1), NOT a live closure.

## Delivered
- `memory/pixel/ui-assist-goal-pipeline.js` (239 lines) — self-contained IIFE module:
  - 4-column kanban strip (Proposed → Active → Verified → Closed) rendered from `/api/goals`.
  - Bottleneck badge (⚠ + count) when >3 goals sit in same non-closed state for >24h (tracked via localStorage `ckconv.goalPipeline.state`).
  - Click-through: clicking a chip scrolls to + flashes the matching agent tile in `#goalsBody`.
  - Self-creates its container (`#goalPipeline`) if missing; appends to `#goalsPanel` above goals body.
  - Polls `/api/goals` every 60s (aligned with existing `goalBarPoll`).

## Verification (structural, sandbox)
| Check | Result |
|-------|--------|
| IIFE wrapper, no globals leaked | PASS |
| Token-only colors (0 hardcoded hex) | PASS |
| All CSS vars resolve to tokens.css | PASS (10/10) |
| Reduced-motion safe (`@media prefers-reduced-motion`) | PASS |
| ARIA: role=list/listitem, aria-label on strip + badge | PASS |
| Bottleneck logic: >3 threshold + 24h stuck detection | PASS |
| Click-through with scrollIntoView + flash animation | PASS |
| Self-container creation (no index.html edit needed) | PASS |
| Brace/paren balance | PASS (86/86, 164/164) |
| Responsive: @media max-width:480px adjusts min-widths | PASS |

**10/10 structural checks pass.**

## Data contract notes
- Current `/api/goals` returns aggregate counts per agent `{agent, total, done, open, blocked?}`.
- Module handles both aggregate mode (chips show "N open" / "N blocked" / "N done") AND
  per-goal mode if backend adds `agents[].goals: [{n, title, state, stuck_since}]`.
- "Verified" column will show 0 until backend distinguishes verified-pending from closed.
- Bottleneck detection uses localStorage to track first-seen timestamp per agent+state slot;
  resets naturally when goals close or state changes.

## Landing notes (for Designer)
1. Copy to `ui/cockpit-goal-pipeline.js`
2. Add `<script src="/ui/cockpit-goal-pipeline.js"></script>` after cockpit.js in index.html
3. No other changes needed — module self-injects CSS and creates its own container
4. Pin advance required (index.html edit)

## AC mapping (Designer goal #4)
| AC | Status |
|----|--------|
| Renders current goal states from /api/goals | ✓ (aggregate + per-goal modes) |
| Bottleneck badge when >3 in same state >24h | ✓ (localStorage-tracked, threshold+duration) |
| Click-through to detail | ✓ (scrollIntoView + flash on matching tile) |
| Proposed→Active→Verified→Closed columns | ✓ (4-col kanban strip) |

## Blocker note (Pixel goal #6)
Goal #6 (live CDP screenshots) remains hard-blocked on this seat: CDP egress WinError 10013,
portal :8099 down. Documented in memory/ops/blockers.md [OPS-NOTE 2026-11-27 Pixel]. Not re-probed per anti-loop rule.
