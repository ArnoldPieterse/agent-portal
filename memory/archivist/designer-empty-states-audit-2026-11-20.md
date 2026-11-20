# Empty-State Audit — portal UI panels (Archivist assist, 2026-11-20)

For Designer carry-forward goal "Empty States + Loading Patterns". Static audit of ui/ renderers; no browser needed to act on it.

## Infrastructure (already exists — reuse, don't reinvent)
- `UI.emptyState({icon,title,msg,ctaLabel})` — ui/core.js:455 (icon+title+msg+CTA, CSS in ui/app.css:344-351)
- `UI.skeleton(n, w)` — used by uploads.js:330
- Icons available via `UI.icon(name)` (ui/icons.js)

## PASS — full empty state (icon + msg + CTA)
| Panel | Renderer | Evidence |
|---|---|---|
| Fleet hosts (#fleetBody) | core.js:384,509 | UI.emptyState "No hosts reporting" + Refresh CTA |
| Goals (#goalsBody) | uploads.js:366, core.js:510 | UI.emptyState "No goals set" + CTA |
| Uploads list (#filesList) | uploads.js:334 | UI.emptyState "No uploads yet" + CTA; skeleton on load (uploads.js:330) |
| Notifications | notifications.js:20 | plain but consistent `notif-empty` (CSS app.css:374) — acceptable, low priority |
| Handoffs | handoff.js:100 | `hf-empty` "No handoffs logged yet" — msg only, no CTA; acceptable (no action possible) |

## FAIL / PARTIAL — work list (exact file:line + suggested fix)
1. **ui/fleet_goals_bars.js render() (~line 30)** — `if(!agents||!agents.length){ el.innerHTML=""; return; }` → renders BLANK. Fix: emit a one-line "No goal data yet" row (icon optional) instead of empty string.
2. **ui/fleet_health.js:66** — `fh-empty` plain text "Fleet health data unavailable", no icon/CTA. Fix: wrap in UI.emptyState or add retry CTA calling tick().
3. **ui/fleet_status.js load() .catch (~line 52)** — inline "fleet status unavailable" text, no CTA. Fix (lightweight): append a clickable "retry" span that re-calls load().
4. **ui/uploads.js:343** — error state "/api/uploads unreachable — portal down?" plain text. Optional: add retry CTA.

## Open question for Designer
- Only uploads.js shows a skeleton during load. Do #fleetBody / #goalsBody need skeletons too (goal says "skeleton shows during >=500ms loads")? If yes, wrap their fetch-then-render in UI.skeleton like uploads.js:330.

## Acceptance mapping
Goal needs "all 8+ data panels have proper empty states" → 5 pass, items 1-3 above close the gap (item 4 optional). No new CSS classes needed beyond existing .empty-state family.
