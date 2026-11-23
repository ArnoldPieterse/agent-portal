# Fleet Cockpit — UX Improvement Spec (Designer, 2026-11-23)

Context: Builder shipped the cockpit as a single-column slide-out panel (`ui/cockpit.js`,
injected via IIFE). It works but has hierarchy and affordance gaps that weaken its role
as the "single pane of glass" for closed-loop autonomy. This spec is ordered by user-
impact; each item is independently shippable.

---

## 1. Alert Strip (highest impact — makes red states impossible to miss)

**Problem:** A host going down or an agent becoming unresponsive only appears mid-scroll
in the agent grid. No top-level signal tells the operator "something needs attention NOW."

**Fix:** Add a sticky `.ckp-alert` strip directly under the `<h2>`:
- Height 32px, full-width, `position:sticky; top:0; z-index:10`
- When any host is unreachable OR any agent is unresponsive: background `var(--err)` at
  15% opacity + left border 3px solid `var(--err)`; text lists the affected entities
- When all clear: no strip (zero visual cost)
- Data source: already in `/api/fleet/cockpit` response (`hosts[].reachable`,
  `agents[].status`)

**Acceptance:** with a simulated host-down, the strip is visible without scrolling;
with all-clear it renders nothing.

---

## 2. Panel Priority Hierarchy (reorder + visual weight)

**Problem:** All six sections are equal-weight rows in one scroll column. The operator's
question on open is "is anything wrong?" — that maps to Health + Risks, not Agent Grid.

**Fix:** Reorder to:
1. **Health Score + 7d sparkline** (existing gauge) — move to position 1, add delta chip
   (`↑+3 vs last cycle` / `↓-5`) using `health_trend` field already in API
2. **Predicted Risks** — position 2; color-code each risk row by severity (existing
   `predicted_risks[].severity`) with left-border accent
3. **Agents** — position 3 (reference, not alert)
4. **Hosts** — position 4
5. **Goal Progress** — position 5
6. **Decision Log** — position 6 (most verbose, least time-critical on open)

Add a subtle visual break: sections 1-2 get `margin-bottom:20px` + slightly larger
section headers (12px vs 11px); sections 3-6 use the existing 11px.

**Acceptance:** health gauge is visible in viewport on panel open at 1440px width without
any scroll; decision log requires scrolling past all other panels.

---

## 3. Decision Log — Action Affordances (closed-loop signal)

**Problem:** The decision log shows what happened but offers no inline action. For a
closed-loop system, the operator needs to see "this decision is reversible" and be able
to trigger rollback without leaving the cockpit.

**Fix:** In each `.ckdec .hd` row, when the decision has `action_type` in
(`model_swap`, `host_failover`, `task_reroute`) AND status is `completed`:
- Append a small button: `↩ Rollback` (or `✓ Acknowledge` if no rollback applies)
- Button style: 11px, ghost border, `color:var(--acc)`; on hover fills with accent
- On click: POST to `/api/fleet/cockpit/rollback` with the decision ID (Builder adds
  endpoint); show inline toast "Rollback initiated" on success

**Acceptance:** a completed model_swap decision shows a Rollback button; clicking it calls
the endpoint and updates the row status to `rolling_back`.

---

## 4. Gauge Delta + Trend Arrow (context without extra panels)

**Problem:** The health gauge shows a number but no direction. "72" means nothing
without knowing if it's going up or down.

**Fix:** Next to the gauge number, render a small inline span:
- `health_trend > 0`: green `↑` + value (e.g. `↑3`)
- `health_trend < 0`: red `↓` + value
- `health_trend == 0`: grey `→`
- Font: 12px, weight 500, margin-left 6px

**Acceptance:** when API returns `health_trend: -5`, the gauge shows "67 ↓5" in red.

---

## 5. Responsive Grid Fix (768px)

**Problem:** `.ckgrid` uses `repeat(auto-fill, minmax(150px, 1fr))`. At 375px viewport
(full-width mobile), this produces ~2 columns of 150px cards with excessive gap — the
card text truncates aggressively.

**Fix:** Add a media query:
```css
@media(max-width:480px){.ckgrid{grid-template-columns:1fr}}
```
Single-column stack on very narrow screens; cards get full width, no truncation.

**Acceptance:** at 375px viewport, agent cards are single-column, name + status fully
visible without ellipsis.

---

## 6. Keyboard / A11y (low effort, high polish)

- Panel open/close button: add `aria-expanded` + `role="switch"`
- Each `.ckdec .hd`: make it a `<button>` (currently a div with cursor:pointer) for
  native Enter/Space toggle
- Alert strip: `role="alert"` so screen readers announce it when it appears
- Gauge: `role="meter"` + `aria-valuenow` / `aria-valuemin` / `aria-valuemax`

**Acceptance:** Tab key reaches panel button → Enter toggles; Tab reaches decision rows →
Enter expands; alert strip announced by NVDA/VoiceOver when it appears.

---

## Implementation Notes for Builder
- Items 1, 2, 4, 5 are CSS + JS reorder only — no new API fields needed (all data
  already in `/api/fleet/cockpit` response)
- Item 3 requires a new endpoint (`POST /api/fleet/cockpit/rollback`) — coordinate with
  Builder; the UI can ship first with a disabled button + tooltip "Rollback pending"
- All changes go in `ui/cockpit.js` (inline CSS via the existing `css()` function) and
  optionally `ui/app.css` for the alert strip if it needs to exist before panel opens
- Estimated effort: items 1+2+4+5 together ≈ 1 hour; item 3 ≈ 2h (incl. endpoint);
  item 6 ≈ 30 min

## Files Touched
- `ui/cockpit.js` — primary (all 6 items)
- `ui/app.css` — alert strip styles only if needed pre-open (item 1)
- `agent_portal.py` — new `/api/fleet/cockpit/rollback` endpoint (item 3, separate PR)

---
*Designer, 2026-11-23. Serves round topic: Closed-Loop Autonomy & Fleet Cockpit.*
*Handoff target: Builder (primary) + Verifier (acceptance tests per item).*