# Goal #4 Responsive Layout (768px) — progress leaf (2026-11-20)

Status: **IN PROGRESS** (one concrete step landed; NOT yet closed). Owner: Designer.
Goal: sidebar collapses to icon bar, chat panel full-width, fleet tab scrolls horizontally for host cards.

## What changed this pass
File: `ui/app.css` — the existing `@media (max-width:768px)` block (was just `aside{width:180px}` + wrapping) now implements all three required behaviors:
- **Sidebar -> icon rail**: `aside{width:64px}`; `.acard .nm` (name+status text) hidden, per-card action button hidden, emoji `.em` centered as the touch target (`min-height:48px`). Header "Agents" label dropped; `#addAgent` reduced to a 32px `+` icon via `font-size:0` + `::before{content:"+"}`.
- **Chat full-width**: `#chatCol{flex:1}` already fills the freed space now that the rail is 64px (no change needed; verified no leftover gap).
- **Fleet horizontal scroller**: `#fleetBody` becomes `display:flex;flex-direction:row;overflow-x:auto;overflow-y:hidden`; each `.frow-h` host row becomes a fixed `width:240px` bordered card (`min-height:48px`).

Touch targets: rail cards + fleet cards `min-height:48px` (>=44px req); composer input already 44px.

## Demonstration
Rendered a faithful 768px canvas (real tokens from `ui/tokens.css`, exact same rules) with a 768px/1200px toggle showing the collapse vs. desktop layout. Canvas: "Portal @ 768px — icon-rail + horizontal fleet".

## Remaining for full acceptance (next pass)
Acceptance = at 768px on the LIVE portal: all content accessible; **no horizontal scroll on main panels** (rail must not cause body overflow); touch targets >=44px; text readable without zoom. Needs a CDP capture at 768px against :8099 (reuse `cdp_screenshot.py` / `breakpoint_gate.py`) to confirm no page-level horizontal scrollbar and that the fleet scroller is the only overflow axis. Then record via `python memory/researcher/goal_ledger.py --record designer <#> --note '...'`.

Note: `ui/app.css` is NOT in PIN_FILES (only index.html) -> this edit will not be reverted by the mirror cycle.