# index.html audit — written critique (Designer goal, 2026-11-15)
Scope: chat + Ops + Fleet panels of the live `index.html` (987 lines, audited line-by-line;
contrast ratios computed from the actual hex values in :root; layout claims verified against
the CSS cascade + the JS that builds each panel). Ranked by severity. 10 issues.

## HIGH

### H1 — `.frow` class collision breaks Fleet-panel row layout (layout bug, not polish)
- Where: L92 `.frow{display:flex;gap:10px}.frow>div{flex:1}` (dialog **form** rows) vs L120
  `.frow{padding:7px 0;border-bottom:1px dashed…;font-size:12.5px}` (fleet host rows); the fleet
  JS builds `<div class="frow"><span.fdot><b>host</b><span.hint>…<div.fmodels>…<div.hint>agents:…`.
- What happens: both rules apply to every `.frow`. The five children of a fleet row (dot, name,
  hint, models div, agents div) all become flex items in ONE non-wrapping row, and the two inner
  `<div>`s get `flex:1` — so the model list and "agents:" line render **beside** the host name,
  stretched to share leftover width, instead of stacking under it (the `margin-left:16px`
  indentation on both proves block-stacking was intended). Long model lists then overflow with no
  wrap/ellipsis.
- Fix: rename the dialog form-row class (e.g. `.dform`), or scope L92 as `dialog .frow{…}` /
  `dialog .frow>div{flex:1}`. One-line change, restores intended fleet layout.

### H2 — four small-text contrast failures below WCAG AA 4.5:1 (computed)
| element | line | color stack | ratio on its bg | verdict |
|---|---|---|---|---|
| `.msg.silentmsg .body` | L56 | var(--dim) @ opacity .7, 10.5px | **3.92:1** on --panel2 | FAIL |
| `.think summary` | L46 | var(--dim) @ opacity .75, 10.5px italic | **4.26:1** on --panel2 | FAIL |
| `.aev .at` (activity timestamps) | L140 | #6b7688, 11.5px | **3.80:1** on --panel | FAIL |
| `.chipfile .sz` (upload sizes) | L82 | var(--dim) @ opacity .6, 12px | **3.23:1** on --panel2 | FAIL |
- Pattern: an already-dim color (#9aa7b8 = 7.74:1 at full strength) is *further* dimmed by
  element opacity — the double penalty is what pushes each below 4.5. These are exactly the
  "secondary" texts (silent messages, thinking traces, timestamps, file sizes) a user squints at.
- Fix: drop the extra opacity and use one explicit muted token (e.g. `--faint:#7d8b9e`, ≈5.2:1 on
  --panel2) for all four; keep opacity only as a hover/transition device, never as the base state.

## MEDIUM

### M3 — no type scale; four sibling panels carry four different header treatments (hierarchy)
- Sizes in play across the file: 10.5 / 11 / 11.5 / 12 / 12.5 / 13 / 14 / 15 / 18 / 22 px — ten
  steps with no ratio. Panel titles specifically: `h1` 15px/600 (L14), aside `.ah` 12px uppercase
  letterspaced (L20), `#fleetHead`/`#opsHead` 13px normal-case (L118/L131), `#actHead` 12px dim
  (L136). The four collapsible panels (Activity/Fleet/Files/Ops) are peers, yet their headers use
  three different sizes and two different color weights — the eye can't rank them, and Activity
  reads as "less important" purely by accident of its header style.
- Fix: one panel-header treatment for all four (13px/600, --text), reserve uppercase-letterspaced
  12px for the aside only; collapse font sizes to a 4-step scale (11 / 12.5 / 14 / 16).

### M4 — mode bar: six equal-weight buttons, destructive action off-palette (hierarchy)
- L181–186: Activity, Fleet, Files, Ops, Reset, Stop sit in one row at identical 12px/border style.
  Only separators are whitespace. `#stopBtn` is distinguished by inline `color:#ff8f8f` (L186) —
  off-palette (the token is `--err:#ff6b6b`, L10); both pass contrast (7.96 vs 6.29) but the inline
  value drifts from the system and will desync if --err changes.
- Fix: group the four toggles; push Reset/Stop right with a `1px var(--line)` divider or margin;
  style Stop as `border-color/color: var(--err)` (no inline hex); consider `.btn.danger` class.

### M5 — inconsistent padding across the four collapsible panels (spacing)
- `#actBody` 4px/14px/10px (L138) · `#fleetBody` 6px/14px (L119) · `#filesList li` 5px/10px (L156)
  · `#opsBody` 6px/14px/10px (L132); heads: actHead 6px/14px (L136) vs fleetHead/opsHead 8px/14px
  (L118/L131). With two or three panels open at once the density visibly steps from panel to panel.
- Fix: single shared rule for `#actPanel,#fleetPanel,#filesPanel,#opsPanel` body/head padding
  (e.g. head 8px/14px, body 6px/14px/10px).

### M6 — nested scroll regions in the Ops panel (spacing/UX)
- `.opsbox` has `max-height:84px;overflow-y:auto` (L133) **inside** `#opsBody{overflow-y:auto}`
  (L132) inside `#opsPanel{max-height:360px}` (L129): gitStatus and gitLog each grow their own
  scrollbar within a panel that already scrolls — scrollbar-in-scrollbar, and the inner limit hides
  content behind a scroll affordance most users won't notice.
- Fix: remove `max-height`/`overflow` from `.opsbox` (outer scroll owns it), or give opsbox a fixed
  line budget with no inner scroll. The two new host tiles already opt out with `max-height:none` —
  make that the default.

## LOW

### L7 — Fleet head hardcodes "4-host fleet" (hierarchy/labeling)
- L194 `<span>4-host fleet · live while open (5s refresh)</span>` is static text; `#fleetStat`
  already computes `up/total` from the response. Add a host to agents.json and the title lies.
- Fix: render the count from `o.hosts.length` in `fleetUpdate()`.

### L8 — Ops head label no longer covers its content (hierarchy/labeling)
- L198 "Repo ops · local git in C:\Projects\Workspace" predates the disk-usage + portal-uptime
  host tiles added 2026-11-15; the panel is now repo **and** host telemetry.
- Fix: rename to e.g. "Ops · repo + host (C:)" and keep the path in a title tooltip.

### L9 — keyboard focus ring covers only ~2 of 8 interactive zones (a11y, adjacent to hierarchy)
- A3's `:focus-visible` rule (L144–146) targets `#opsPanel button/input`, `#modeBar button`,
  `.seg button` only. Agent cards, attach menu buttons, dialog buttons/inputs, and the
  act/fleet/files toggle buttons have no visible focus style — keyboard users lose their position
  marker in most of the UI.
- Fix: extend the selector list to `#agentList .acard, .amenu button, dialog button, dialog input,
  #actBtn,#fleetBtn,#filesBtn` (same 2px var(--focus) ring).

### L10 — round-end chips break the message vertical rhythm (spacing)
- `#msgs{gap:12px}` (L41) sets the inter-message rhythm, but `.roundend{margin-top:6px}` (L51)
  makes round-end chips sit at half that distance from the message above while everything else
  sits at 12px — a subtle but visible unevenness in long group rounds.
- Fix: make `.roundend` a flex child of the gap rhythm (remove its own margin-top; wrap with the
  message or add `margin-top:-6px` + keep 12px effective).

## Summary
| # | severity | kind | one-liner |
|---|---|---|---|
| H1 | HIGH | layout | `.frow` collision renders fleet models/agents inline, stretched |
| H2 | HIGH | contrast | 4 small-text elements below AA (3.23–4.26:1), opacity-on-dim pattern |
| M3 | MED | hierarchy | no type scale; 4 peer panels, 4 header styles |
| M4 | MED | hierarchy | mode bar equal-weight buttons; Stop off-palette inline color |
| M5 | MED | spacing | 4 different body paddings across the collapsible panels |
| M6 | MED | spacing | nested scrollbars in Ops panel (.opsbox inside scrolling #opsBody) |
| L7 | LOW | hierarchy | "4-host fleet" hardcoded in fleet head |
| L8 | LOW | hierarchy | ops head title stale after host-tile extension |
| L9 | LOW | a11y | focus ring missing on 6 of 8 interactive zones |
| L10 | LOW | spacing | round-end chips at half the message gap rhythm |
