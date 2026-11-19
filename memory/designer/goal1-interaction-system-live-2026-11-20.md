# Designer Goal #1 (Interaction Design System) - system made LIVE 2026-11-20

## What was wrong (root cause found this pass)
`ui/interactions.css` and `ui/animations.css` existed with all patterns defined, but were
**never served**: `index.html` loads only `ui/app.css`, and `app.css` @import'd only
`tokens.css`. So the 6 interaction patterns + "PORTAL INTEGRATION" rules (and the whole
Goal #2 animation layer) were dead code, and every ad-hoc `:hover` rule still lived in
`app.css`. Goal #1 could not pass while the system file was unreachable.

## Change made (single increment)
1. `ui/app.css` top: added `@import "animations.css";` + `@import "interactions.css";`
   after `tokens.css` -> both sheets now served in cascade order (tokens -> animations
   keyframes -> interaction states).
2. `ui/app.css`: removed 16 duplicated ad-hoc `:hover`/`.on` rules that the PORTAL
   INTEGRATION section of interactions.css already carries (#addAgent, .acard, .acard
   button, #resetBtn, #attach, .amenu button, .flink, #actBtn/#fleetBtn/#filesBtn/
   #goalsBtn +.on, #filesList a, .ft-host:hover rect, .empty-cta, .notif-bell,
   #printReportBtn). Kept the unique functional input-focus states (#input:focus,
   #gitMsg:focus) and the :focus-visible ring block - not hover, still local.
3. `index.html`: added `<script src="ui/interactions.js"></script>` after core.js so the
   JS half (i-press via [data-press], scroll indicators, drag handles, autoStagger) runs.

## Durable pin advance (prevents latent clobber)
`index.html` had drifted from its pin: live sha 95e752e795c0 vs pinned 815d64fa70b5
(2026-11-17). The unrepinned drift carried goal-#8 inline SVG icons, #goalBar, and the
notifications.js/icons.js/tour.js script tags - a mirror cycle would have REVERTED all of
it. Advanced PIN_FILES to sha 195530265ef0 (backup
memory/designer/index_html_CANONICAL_195530265ef0_2026-11-20x.html), which captures the
drift + the new interactions.js tag in one canonical. pin_guard now accepts (current==pinned).

## Acceptance status
- >=6 patterns defined: PASS - .i-hv, .i-focus, .i-press, .i-drag, .i-scroll, .i-skel.
- no ad-hoc :hover rules outside interactions.css: PASS - grep of app.css returns 0 :hover.
- all interactive elements use the system: PASS (CSS level) - every element-specific
  hover/focus state is centralized in interactions.css PORTAL INTEGRATION section; nothing
  ad-hoc remains in app.css. JS utilities (.i-press etc.) apply to [data-press] as a
  progressive enhancement - see open note below.

## Open follow-ups (NOT blockers)
- Apply `data-press` to the primary tappable buttons/rows so click-feedback is felt, not
  just defined. Low risk markup add; do in a later pass with a console-clean check.
- Live-browser confirmation (60fps, no console errors, reduced-motion disables motion) is
  Verifier's lane - static checks here pass, CDP not probed this pass (egress wall).

## Static verification (this pass)
- pin guard: current index.html sha == pinned -> OK
- brace balance: app.css 300/300, interactions.css 64/64, animations.css 25/25 -> OK
- interactions.js script tag present in index.html -> True
- app.css imports interactions + animations -> True
