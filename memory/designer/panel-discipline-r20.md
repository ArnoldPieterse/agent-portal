# Designer A4 panel-discipline spec + hunks (r21 rewrite of lost r20 leaf) - 2026-11-14 ~05:3x

Provenance: the original `panel-discipline-r20.md` never propagated (Researcher r26 check: absent on a fourth consecutive seat; DM relay path structurally broken). This file is a NEW-file write under memory/designer/ per the established rule (new-file writes propagate; existing-file edits are LWW-skipped). Content reconstructed this round from first-party evidence: r19 sheet FAIL #3/#4 + live re-grep of canonical index.html on this seat.

## Scope
- A4 = fix for r19-sheet FAIL #3 (panel discipline: no one-open-at-a-time, no outside-click-to-close) - Hunk A, JS only.
- A4b = fix for r19-sheet FAIL #4 (layout shift on toggle: panels in normal flow push #msgs down 240-360px) - Hunk B, markup move + CSS lines.
Both apply via Builder's hash-gated one-shot against the current canonical; my r19 sheet remains the defect record of origin.

## Pre-apply baseline (this seat, this round, first-party)
| check | value |
|---|---|
| index.html | 67,681 B / md5 9c6b08e3d98355e632a72cb871d5b60d (binary; text-mode read = 66,716 chars = raw minus 965 CR - pin by binary md5) |
| Hunk-A anchor `$("filesRefresh").onclick=filesLoad;` | exactly ONE occurrence, L962, immediately before `</script>` (L963) |
| `panelToggles` / `panelClose` | 0 / 0 occurrences (pre-apply baseline; expect >=1 each post-apply) |
| panel id lines | actPanel x6 (L114,115,188,614,620,629); fleetPanel x5 (L116,117,193,656,659); opsPanel x6 (L129,130,144x2,197,672); filesPanel x4 (L152,153,212,961) |
| `#modeBar` CSS (L34) | display:flex row - NO overflow:hidden, so an absolute child is not clipped |
| outside-click idiom precedent | L715 attach menu: `document.addEventListener("click",e=>{ if(!e.target.closest("#attachWrap"))amenu.hidden=true; });` |

## Hunk A - JS, insert AFTER the anchor line (L962), before `</script>`
```js
// ---- A4 panel discipline (designer r20/r21): one-open-at-a-time + outside-click-close ----
const panelToggles={
  act:{btn:$("actBtn"),panel:$("actPanel")},
  fleet:{btn:$("fleetBtn"),panel:$("fleetPanel")},
  ops:{btn:$("opsBtn"),panel:$("opsPanel")},
  files:{btn:$("filesBtn"),panel:$("filesPanel")}
};
function panelClose(k){const t=panelToggles[k]; if(t&&t.panel.classList.contains("open"))t.btn.click();} // owning handler runs its own cleanup (actTimer/fleetTimer)
document.addEventListener("click",e=>{
  for(const k in panelToggles){
    const t=panelToggles[k];
    if(!t.panel.classList.contains("open"))continue;
    if(t.btn.contains(e.target)||t.panel.contains(e.target))continue;
    panelClose(k);
  }
});
```
Design notes:
- Closes by re-invoking the OWNING button handler (`btn.click()`), so each panel's own close branch runs - actTimer/fleetTimer are cleared exactly as when closed via their own button. The timer-gating contract in ac-a2-2-console-clean-criteria.md (timers fire ONLY while the panel has class `open`) is preserved verbatim.
- Mutual exclusion falls out of the same listener: clicking any toggle while another panel is open closes the other first (the synthetic event re-enters the listener; idempotent because every iteration re-checks `.open`). Each click strictly decreases the open count - no recursion loop.
- Clicks inside an open panel or on its own button are skipped (`contains` guards) - no double-toggle, refresh buttons keep working.
- No existing behavior modified: the four toggle handlers (L619/L655/L672/L961) are untouched; `actFollow`'s `.open` guard (L614) unaffected.

## Hunk B - zero layout shift (FAIL #4): markup move + CSS
1. Move the four panel divs (currently L188-215, siblings between #modeBar and #msgs) INSIDE #modeBar: wrap them in a new `<div id="panelDock">...` placed after the stopBtn line (L186) and before modeBar's closing `</div>` (L187).
2. CSS: extend L34 `#modeBar{...}` with `position:relative;`, and add ONE new rule:
   `#panelDock{position:absolute;top:100%;left:0;right:0;z-index:30;display:flex;flex-direction:column}`
Rationale: the dock is out of flow, so opening/closing any panel leaves #msgs offsetTop/clientHeight untouched (zero shift, zero scroll jump). Only one panel can be open at a time (Hunk A), so column stacking in the dock is safe. All JS references are by id (no DOM-order dependence); modeBar has no overflow:hidden (verified L34) so the overlay is not clipped; z-index 30 sits above .amenu (no explicit z-index). Panel max-heights (240/280/360/280), backgrounds and border-bottoms unchanged.

## Base note (WCAG-AA stamp)
Hunks verified against base 9c6b08e3 on this seat. The WCAG-AA canonical stamp 8ef4e2227a7afd506ed2b55dc9dd170d is the same byte count (67,681 B) and differs by a single line elsewhere in :root (the contrast swap = r19 FAIL #5); neither hunk touches that region. If Builder's hash gate expects 8ef4e222, re-run the two anchor findstrs above on that base before applying - anchors are identical in both bases.

## AC-A4 (functional acceptance - Verifier/Arnold, post-apply, White seat)
- A4-1 one-open: open any panel, then click a second panel's button -> exactly ONE `.open` across the four panels; the set of `.on` buttons equals the set of open panels.
- A4-2 outside-click close: with a panel open, click #msgs or empty chrome -> panel closed within 1 tick; devtools Network shows NO /api/activity or /api/fleet request for >=6 s after close (timers actually cleared).
- A4-3 zero shift: record `#msgs` offsetTop + clientHeight; open and close each of the four panels in turn -> values identical every time.
- A4-4 console clean per ac-a2-2-console-clean-criteria.md (hard-refresh pass, no panels opened during the observation window).

Owner: Designer. Status: spec + hunks final; apply = Builder (hash-gated one-shot), acceptance = Verifier/Arnold on White console. This file supersedes the lost r20 original - all cross-references to "panel-discipline-r20.md" resolve here.
