# All-Clear State — Cockpit Visual Spec
_When fleet reaches 100% goals + steady-state, the portal shifts to a calm/complete visual register. This spec tells Pixel exactly what to build._

## Trigger conditions (data-driven, not hardcoded)
- `fleet_pct_reached === 100` in goal_ledger.json
- `steady_state === true` in fleet-mode.json
- Both must be true simultaneously; either alone = partial state (see "Partial" below)

## Layout changes (cockpit panel only, not full portal)

### Header bar
- Replace mode badge (WORK/MAINTENANCE/IDLE) with a single pill: `STEADY` in var(--ok) tint, no pulse animation
- Subtitle line: "All lanes converged · last delta {N}h ago" using relative time
- Remove the goal-progress bar entirely — 100% is the resting state, showing it is noise

### Agent list (#agentList)
- All agent rows collapse to a single-line compact mode: name + status dot (green) + idle duration
- No expand-on-hover cards; the detail view is one click away but not surfaced
- Sort by last-activity descending (most recently active first) — replaces alphabetical

### Decision queue
- Empty state: centered icon (checkmark-in-circle, 32px, var(--dim)) + text "No pending decisions" in var(--text)
- No placeholder cards, no skeleton loaders — the absence IS the message

### Runbook panel
- All buttons disabled (opacity 0.4, cursor: not-allowed)
- Panel header changes from "Runbooks" to "On Standby"
- A single line below: "Fleet is in steady state. Runbooks available on demand."

## CSS tokens (add to ui/app.css under a new section)
```css
/* Steady-state overrides — applied when body has [data-fleet-state="steady"] */
body[data-fleet-state="steady"] .mode-badge {
  background: color-mix(in srgb, var(--ok) 15%, transparent);
  color: var(--ok);
  border-color: var(--ok);
}
body[data-fleet-state="steady"] .goal-bar { display: none; }
body[data-fleet-state="steady"] .agent-row { max-height: 2rem; overflow: hidden; }
body[data-fleet-state="steady"] .decision-queue:empty::after {
  content: "No pending decisions";
  display: block; text-align: center; padding: 2rem; color: var(--dim);
}
body[data-fleet-state="steady"] .rb-btn { opacity: 0.4; pointer-events: none; }
```

## Data binding (core.js)
```js
// In renderCockpit(), after loading ledger + fleet-mode:
const steady = ledger.fleet_pct_reached === 100 && fleetMode.steady_state;
document.body.dataset.fleetState = steady ? 'steady' : 'active';
```

## Partial state (one of two conditions met)
- Show a thin top bar: "Converging… {pct}% goals · steady-state pending" in var(--warn) tint
- Everything else stays in normal active mode

## Verification checklist (for Forge gate)
- [ ] `data-fleet-state="steady"` appears on body when both conditions true
- [ ] Goal progress bar has `display: none` via CSS (not removed from DOM)
- [ ] All 14 agent rows render in compact single-line mode
- [ ] Decision queue shows empty state text when no items
- [ ] Runbook buttons have pointer-events: none
- [ ] No console errors in Playwright pageerrors[]
- [ ] Partial state bar appears when only one condition is met

## Anti-patterns (do NOT)
- Do not add a confetti/celebration animation — it's a resting state, not an event
- Do not hide the agent list entirely — operators still need visibility
- Do not require a page reload to enter steady-state — it should transition on next data poll
