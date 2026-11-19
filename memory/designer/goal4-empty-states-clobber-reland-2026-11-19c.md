# Goal #4 — Empty State Design: clobber re-land + static verification (2026-11-19, auto-loop)

Owner: Designer. Status: PROGRESS (code re-landed + statically verified). NOT a verified close — the acceptance test ("all empty states render when API returns empty arrays; CTAs clickable") requires a live browser session (shared blocker with #2/#5/#6/#10).

## What was found
Live files had ZERO `showEmptyState` refs and no `.empty-state` CSS — the helper + wiring that earlier progress notes claimed "wired into 5/5 panels" were clobbered/reverted to an older canonical (same failure mode as Goal #9 tour.js, per memory/researcher/goal9-tour-stale-evidence-2026-11-19.md). This pass re-created it from scratch against the CURRENT live files.

## What was done (this pass)
1. **ui/core.js** — added `showEmptyState(el, iconKey, title, msg, ctaText, ctaFn)` helper (icon via UI.iconSized guarded by typeof check; esc() on all text; optional CTA button). Wired 3 empty-data points:
   - renderAgents(): agents.length===0 -> agent icon + "No agents configured" + Refresh->refresh()
   - fleetUpdate(): no hosts -> satellite icon + "No agents online" + Refresh->fleetUpdate()
   - actRender(): evts empty -> info icon + "No events yet" (no CTA)
2. **ui/uploads.js** — wired 3 more points (helper is global from core.js):
   - filesLoad(): no files -> upload icon + "No uploads yet" (no CTA; files come from White disk)
   - goalsLoad(): no goal tiles -> goal icon + "No goals set" + Refresh->goalsLoad()
   - renderQueue(): no pending rows -> info icon + "No queued messages" (no CTA)
3. **ui/app.css** — appended `.empty-state` block (6 rules). Fully tokenized: --sp-8/16/24, --fs-13/15, --lh-caption/base, colors --dim/--faint/--text/--acc/--line; border-radius var(--br-md,8px) with literal fallback (live tokens.css has no --br-* scale).

## Static verification (ran this pass)
- showEmptyState: 1 definition + 6 call-sites (core.js=4 incl. def, uploads.js=3).
- Brace balance: core.js balanced; uploads.js balanced (caught + fixed a dropped closing brace in renderQueue that my first edit introduced); app.css balanced.
- 0 new hex colors introduced by the empty-state block (Goal #1 invariant preserved for my change).

## sha12 provenance (post-edit live files)
core.js=02bdf8c449f5 · uploads.js=6632c577f822 · app.css=dde8e0084a36

## Baseline drift note (for team, not caused by this pass)
Live ui/app.css currently holds 48 hex color values (distinct 37), all matching the tokens.css palette (--line/--ok/--err/--bg/...). This indicates live app.css reverted to a pre-full-tokenization canonical via the clobber loop. My empty-state change adds none of these. Reconciling that drift is out of scope for this one step; flagging so it isn't mistaken for a Goal #1 regression introduced today.

## Remaining for closure
- Browser-rendering acceptance: trigger each panel's empty API path, confirm icon+title+message render and CTA buttons are clickable (fleet/goals/agents CTAs). Same live-browser blocker as #2/#5/#6/#10 — hand to Verifier/Designer when a browser session is available.
