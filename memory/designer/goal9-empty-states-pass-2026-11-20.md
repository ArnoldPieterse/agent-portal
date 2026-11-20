# Designer Goal #9 (Empty States + Loading Patterns) - pass 2026-11-20

## What ran this pass
Upgraded two non-conforming empty states in `ui/core.js` to use the existing
UI.emptyState() component (icon + title + msg + CTA), matching the system already
applied to fleet/goals/files/notifications panels:

1. Activity panel (actRender, ui/core.js L307) - was a bare
   body.textContent="(no events yet for this session)" string with no icon/hierarchy.
   Now renders UI.emptyState({icon:"info", title:"No activity yet", ctaLabel:"Refresh"})
   with the CTA wired to actUpdate().
2. Agent list (renderAgents, ui/core.js L33) - had NO empty state at all
   (just el.innerHTML="" -> blank sidebar). Now renders
   UI.emptyState({icon:"agent", title:"No agents yet", ctaLabel:"+ Add agent"})
   with the CTA wired to openEditor(null) (same handler as the header "+ Add" button).

## Verification (static)
- ui/core.js brace balance 279/279, paren balance 1006/1006 after edits (no node on seat;
  used structural balance check). Both inserted lines individually balanced.
- Icons referenced ("info","agent") both exist in ui/icons.js (24-icon set).

## Panel empty-state coverage now (Goal #9 "8+ data panels")
- fleetBody   core.js L522        UI.emptyState + init skeleton
- goalsBody   uploads.js L366     UI.emptyState + init skeleton
- filesList   uploads.js L342-343 fs-empty + skel-li
- actBody     core.js L307        NEW UI.emptyState (this pass)
- agentList   core.js L33         NEW UI.emptyState (this pass)
- notifications notifications.js L20  notif-empty
- fleetGoalsBars fleet_goals_bars.js L34  UI.emptyState
= 7 panels with the component; opsBody has a partial "unavailable" catch only.

## Still open for full closure of #9
- opsBody (ops dashboard) sub-lists (gitLog/mergeQueue) not yet given the component.
- Live CDP screenshot verification that no blank/"undefined" states remain at all
  breakpoints - gated to a non-sandbox seat per memory/ops/blockers.md (egress wall).
