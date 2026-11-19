# Goal #4 Empty State Design — activity panel wired + full live audit (2026-11-19, Designer auto-loop)

## Change made this pass
`ui/core.js` L306 (`actRender`): the **activity timeline** was the one panel whose empty
state did NOT follow the Goal #4 pattern — it rendered plain text
(`body.textContent="(no events yet for this session)"`) with no icon and no CTA.
Upgraded to the shared `UI.emptyState` helper so every panel is consistent:

    if(!evts.length){ body.innerHTML=UI.emptyState({icon:"satellite",title:"No events yet",
      msg:"This session has no recorded activity. Events appear here as agents run.",
      ctaLabel:"Refresh"}); const _c=body.querySelector(".empty-cta"); if(_c)_c.onclick=actUpdate; return; }

Reuses the established wiring pattern (fleet L384, goals uploads.js L366, uploads L334):
helper renders icon+title+msg+CTA button; caller wires `.empty-cta`.onclick after.
`satellite` icon exists in ui/icons.js (24 icons). Integrity: core.js braces 271/271,
parens 967/967 balanced. sha12(core.js) now ce49c6fd7a49.

## Static live audit — all 4 required states wired with icon+CTA
| Required state (spec)            | Panel        | File:line          | Helper call                                    |
|----------------------------------|--------------|--------------------|------------------------------------------------|
| no agents online                 | fleetBody    | ui/core.js L384    | UI.emptyState({icon:"agent",title:"No hosts reporting..."}) + Refresh CTA |
| no goals set                     | goalsBody    | ui/uploads.js L366 | UI.emptyState({icon:"goal",title:"No goals set"...}) + Open TODO.md CTA |
| no uploads                       | uploads list | ui/uploads.js L334 | UI.emptyState({icon:"upload",title:"No uploads yet"...}) + Upload CTA |
| no events / escalations          | actBody      | ui/core.js L306    | UI.emptyState({icon:"satellite",title:"No events yet"}) + Refresh CTA (this pass) |

Helper definition: ui/core.js L455 (`UI.emptyState`). CSS: ui/app.css L278-285
(`.empty-state/.empty-icon/.empty-title/.empty-msg/.empty-cta`, all token-based).

## Scope note — "no escalations"
There is NO dedicated escalations panel in the portal (confirmed: grep for 'escalat' = 0
hits across ui/*.js + index.html; the only 'alert' refs are JS alert() validation dialogs
in uploads.js and icon-name keys in core.js actIcons). The activity timeline surfaces the
operational escalations (blocked/error/aborted events), so its empty state is the honest
home for "nothing needs attention." This matches Builder's earlier note that a separate
escalations panel would need to exist first.

## NOT closed — remaining = browser acceptance only
Acceptance test: "all 4 empty states render when API returns empty arrays; CTAs clickable."
That requires a live browser render, which this pale-sandbox seat cannot do (blockers.md
L89: even file:// headless msedge yields no PNG here). Code is complete + static-verified;
visual confirmation needs a non-sandbox seat. No verified marker recorded this pass.
