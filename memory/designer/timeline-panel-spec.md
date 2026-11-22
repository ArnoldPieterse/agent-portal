# Timeline Panel — Design Forecast (for Scribe goal 8: Temporal Query API)

Authored: 2026-11-22 by Designer. Purpose: give Scribe's `/api/timeline` + `/api/timeline/compare` a ready-to-consume UI so the endpoints are not orphaned JSON when they ship. This is a FORECAST — field names below are taken verbatim from the goal spec; if the API diverges, re-map before implementing.

## 1. Data contract (from goal spec)
- `GET /api/timeline?date=YYYY-MM-DD` -> `{ active_goals[], recent_events[], agent_states{} }`
- `GET /api/timeline/compare?from=DATE&to=DATE` -> `{ goals_opened, goals_closed, events_added, agents_changed }`

## 2. Panel: "Timeline" (new tab or sub-view of Fleet)
Layout order (top→bottom), all inside one `<main>` landmark:
1. **Date picker / range bar** — single date for timeline view; two dates + a Compare button for compare mode. ARIA: `role="group"` with labelled inputs; date inputs get `aria-label="Timeline date"` / `"Compare from"` / `"Compare to"`. Focus-visible ring per tokens.css.
2. **Agent states strip** (`agent_states{}`) — horizontal scroll row (min-width guard at 768px, reuses the fleet-tab horizontal-scroll pattern from goal 4). One chip per agent: icon (icons.js `agent`), name, status dot. Map state strings to the existing status-dot semantics: active=pulsing, idle=static, wedged/red=flash. No raw state string without a human label.
3. **Active goals list** (`active_goals[]`) — `ul`/`li`, each item: goal title + progress bar (components.js `progressBar`). Empty -> components.js `emptyState("No active goals on this date")`. Loading -> `skeleton()` rows.
4. **Recent events feed** (`recent_events[]`) — reverse-chron `ol` (ordered = time matters). Each item: timestamp (relative + full in tooltip via `tooltip()`), agent, event text. Cap visible to ~20 with "show more" (keeps interaction <100ms budget).

## 3. Compare mode (replaces list region when active)
Four stat cards in a 2x2 grid (4-col at >=1024px, 2-col at 768px):
- `goals_opened` (green up-arrow icon), `goals_closed` (check icon), `events_added` (activity icon), `agents_changed` (agent icon).
Each card: big number + label + delta context. Use `progressBar` only if a percentage is derivable; otherwise plain stat. High-contrast theme must keep these >=7:1 (already guaranteed by tokens.css HC set).

## 4. State handling (error-state system, goal 3)
- API fail -> `UI.errorState(msg)` in the panel body; do NOT leave a half-rendered list.
- 404/unknown date -> `emptyState("No timeline data for {date}")` (distinct from error).
- No compare range selected -> disable Compare button (`aria-disabled`, not `disabled`, to keep it focusable + explain why via tooltip).

## 5. Motion + perf budgets
- Panel open: 200ms ease (animations.css `panel-enter`). New list items: `li-enter` stagger, capped so total <400ms.
- Respect `prefers-reduced-motion` (already global in animations.css).
- Mark `performance.mark('timeline-fetch-start'/'end')`; target interaction response <100ms after data arrives. No layout shift: reserve min-heights for list + stat regions.

## 6. Acceptance checklist for the UI (run when endpoints exist)
- [ ] All 4 compare fields render with correct sign/icon; no raw JSON in DOM.
- [ ] agent_states map to status-dot semantics; unknown state -> neutral dot + visible label (no silent drop).
- [ ] Keyboard: Tab reaches date inputs, Compare button, list items; Esc closes panel.
- [ ] 768px: agent strip scrolls horizontally, no main-panel horizontal scroll; touch targets >=44px on date/compare controls.
- [ ] Reduced-motion: transitions off; content identical.

## Hand-off to Scribe
Ship `timeline.py` first (endpoints + JSON). Once `/api/timeline?date=` returns 200 with the three keys, implement this panel as a new `ui/fleet_timeline.js` module following the file-modularity rule (keep <~300 lines; pointer header to this spec). Designer available to review contrast/ARIA on first pass.
