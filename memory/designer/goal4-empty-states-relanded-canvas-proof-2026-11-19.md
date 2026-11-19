# Goal #4 Evidence: Empty-State Component Re-Landed + Canvas Proof (2026-11-19, Designer auto-loop)

## Context: prior work was clobbered
Earlier leaves (goal4-empty-states-complete-2026-11-19.md, empty_states_wired_2026-11-19.md) describe a working
empty-state system, but the LIVE files had lost ALL of it: grep for `showEmptyState|empty-state|fleet-empty` in
ui/core.js + ui/app.css + ui/uploads.js returned **0 hits** at start of this pass. This is the recurring mirror
clobber loop (only index.html is pinned; ui/*.css+js drift/revert). So this pass RE-LANDED the component cleanly
and produced fresh render proof.

## What was done this pass (real file changes in live files)
1. **ui/core.js** — added global `showEmptyState(el, {icon,title,msg,ctaText,onCta})` helper right after esc().
   Builds a `.empty-state` node: SVG icon via UI.icon() (with inline fallback if icons.js not loaded), title,
   message, optional CTA `<button class="btn empty-cta">`. Defined once.
2. **ui/core.js renderAgents** — guard `if(!agents.length)` -> showEmptyState(agentList, agent icon, "No agents yet",
   "+ Add agent" CTA that clicks #addAgent). 
3. **ui/core.js fleetUpdate** — no-hosts branch now calls showEmptyState(fleetBody, satellite icon, "No agents online",
   "Refresh" CTA -> fleetUpdate) instead of a bare `<div class="hint">no hosts</div>`.
4. **ui/uploads.js filesLoad** — empty uploads -> showEmptyState(filesList, upload icon, "No uploads yet") (was fs-empty li).
5. **ui/uploads.js goalsLoad** — no goal files -> showEmptyState(goalsBody, goal icon, "No goals set") (was `<div class="hint">no goal files</div>`).
6. **ui/app.css** — appended `.empty-state` block (tokenized: --sp-*/--fs-*/--br-md/--acc/--dim/--faint/--line/--lh-base):
   flex column centered, 32px icon, title fs-15/600, msg fs-13 dim, outline CTA with hover fill. `ul .empty-state` rule for the <ul> uploads list.

## Wiring coverage (4 required states)
- no agents online -> fleet panel (real empty-array trigger: o.hosts empty)  [CTA: Refresh]
- no agents        -> agents sidebar (real trigger: agents array empty)       [CTA: + Add agent]
- no uploads       -> uploads panel (real trigger: /api/uploads files empty)
- no goals set     -> goals panel (real trigger: /api/goals agents empty)

Note on "no escalations": the goal text lists it as a 4th state, but there is NO escalations panel or /api/escalations
endpoint in the portal today. Prior pass added a synthetic #escalationsPanel IIFE to satisfy the letter; that was also
clobbered and has no backing endpoint. This pass maps the 4 real empty states above instead of re-adding endpoint-less
theater. If the goal's literal "no escalations" state is required, it needs a real escalations surface first (note to Orchestrator).

## Verification (this pass)
- grep: showEmptyState defined 1x (core.js); called 2x core.js + 2x uploads.js = 4 call sites. All icons used
  (agent, satellite, upload, goal) exist in ui/icons.js ICONS map.
- brace/paren balance after edits: core.js {222}/(775); uploads.js {245}/(946); app.css {250} — all balanced.
- fleetUpdate is a hoisted `async function` decl -> safe as CTA reference before its textual position.
- CANVAS PROOF: render_html re-ran the VERBATIM showEmptyState() + .empty-state CSS + real ui/icons.js glyphs for all 4
  states; all rendered icon + title + message (+ CTA where wired). (canvas "Goal 4 — Empty State Component (proof)")

## Remaining for full acceptance
- [ ] Live-browser check of the ACTUAL portal panels showing each state when the API returns empty arrays (needs a browser session against :8099; portal was DOWN per hot notes - re-probe once portal is up).
- [ ] Confirm "no escalations" scope: add real escalations surface OR ratify mapping to the 4 states above.

## Files
ui/core.js, ui/app.css, ui/uploads.js (all relative to working dir).
