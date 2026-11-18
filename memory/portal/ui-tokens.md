# Portal UI tokens — single source of truth (2026-11-14)
Owner: Designer. This is the living token doc for ALL portal UI work (goal 10, 2026-11-13 list). `memory/portal/design-tokens.md` remains the LOCK record for the mock-only light family + carries the Orchestrator adjudication line; where this file and that lock conflict on LIVE portal work, this file wins per that adjudication (2026-11-14 ~03:5x, option b).

## Families
| family | status | use |
|---|---|---|
| dark (below) | **CANONICAL for live index.html** (adjudicated 2026-11-14) | portal UI merges, component reference, future panels |
| light (r60 lock) | locked, mock deliverables only | increment mocks, ops-panel-mock, design sheets |

## Dark family — production canonical
Source: first-party grep of canonical index.html 9c6b08e3d98355e632a72cb871d5b60d / 67,681 B (:root L9-10).
| token | value | role | contrast on --panel (computed WCAG) |
|---|---|---|---|
| --bg | #0e1116 | page background | — |
| --panel | #151a22 | toolbars, panels | — |
| --panel2 | #1b2230 | cards, inputs, messages, toast | — |
| --line | #2a3342 | borders, dividers | n/a (non-text) |
| --text | #e8edf4 | primary text | 14.84 PASS |
| --dim | #9aa7b8 | secondary text, hints, labels | 7.15 on panel / 6.52 on panel2 — PASS |
| --acc | #4f8cff | accent: focus-adjacent borders, links, "on" button borders (NEVER as fill behind white/ink text) | 5.43 |
| --ok | #3ddc84 | success, idle dot | 9.79 |
| --warn | #ff9f43 | warnings, armed-confirm border | 8.56 |
| --err | #ff6b6b | errors, offline dot | 6.29 |
| --focus | #7fb0ff | focus ring only | 7.95 on panel / 7.25 on panel2 |

### KNOWN-FAIL (open until Hunk A lands)
white-on-#acc = **3.22:1 FAIL** — currently used as fill behind white text on `#send` and `.seg button.on` (Solo/Group). Fix per fix pack r51: add `--acc-strong:#2f6fe0` (white on it = 4.70:1 PASS) and use it for primary-action fills. Until then these two controls are non-conforming to AA.

### Data colors (not UI accents — chips/dots only, per r60 rule)
#ffb454 busy dot, #e05252 unknown dot, #8b93a7/#9ccaff/#aab2c5 peek-pane text, #243b63/#33507f "you" bubble, #ff8f8f Stop label.

## Spacing scale (both families)
4 / 8 / 12 / 16 / 24 px as CSS custom properties `--sp-4/--sp-8/--sp-12/--sp-16/--sp-24` in :root (canonical pin 2c6399f2d853). **Tokenized 2026-11-16 (goal 4, closes F-VER-01 reopen recommendation):** all padding/margin/gap/offset values in live CSS are on-scale (92 ad-hoc values snapped: 5,6,7,9,10,13,14,15,18 -> nearest scale step; prior documented exceptions toolbar-gap-14 / .frow-7 / header-10 resolved). Hairlines: 1-3px borders, dividers, focus outlines only.
Border radii: 8 / 12 px (+50% circles) — snapped from 6/9/10/14 in the same pass.

## Type ramp (both families)
base 14px/1.45 system-ui stack (live) — r60 mocks use 15px/1.45; h2 panel title 16px/600; section label 12px/600 uppercase ls .08em --dim; mono 13px ui-monospace/Consolas for git log/status/results; pills/tags 11–13px.
Type scale as CSS custom properties `--fs-11/--fs-12/--fs-13/--fs-14/--fs-15/--fs-16` in :root; listed font sizes (grep-allowlist, 2026-11-16): 11 / 12 / 13 / 14 / 15 (header h1) / 16 (h2 panel titles) px; glyph sizes: 18px emoji (.acard .em), 22px attach icon (#attach).
Component dimensions (listed, not spacing): status dots 8px (.dot/.fdot); spinner 12px (.qspin); emoji box 26px wide; control height 44px (#input, #attach, .gring); textarea min-height 64px; event time column 64px (.aev .at); think max-height 120px; queue list max-height 140px; agent card min-width 160px (<=375px only); goal tile min-width 170px; attach menu min-width 180px + peek body max-height 180px; #actPanel max-height 240px; aside 250px wide; fleet/files panels max-height 280px; goals panel 300px; ops panel 360px = .chipfile/#actSel max-width 360px; #peek max-width 340px (<=768px: calc(100vw - 24px)); dialog min(560px, 92vw/96vw).
Shadow (single spec): #peek `0 8px 24px rgba(0,0,0,.5)`. Focus: outline 2px solid var(--focus), offset 2px (4px on #composer.dragover).
Responsive breakpoints (goal 7, added 2026-11-16): max-width 768px (aside 180px, header/modeBar/opsrow/composer wrap, peek full-width-ish) and max-width 375px (main stacks: agent list becomes horizontal strip <=26vh, .frow columns, ops boxes full-width).

## Focus & interaction
`:focus-visible{outline:2px solid var(--focus);outline-offset:2px}` on EVERY control (verified live, r19). Inputs: same outline on focus. Status lines: `role="status" aria-live="polite"`; every action gives text confirmation — no color-only feedback.

## Motion
Live page currently has **zero transition declarations** (grep-verified 2026-11-14) — state changes are instant. Standard being set by fix pack r51 Hunk D: interactive elements `transition:border-color .12s,color .12s,background .12s`; toast/banner opacity+transform .15s; panel drawers no animation (instant show/hide is acceptable, ≤200ms cap). All transitions must be ≤200ms and must not cause layout shift.

## Rules
1. Max 2 accents per view. Agent monogram colors are data colors — chips only.
2. Primary-action fills use --acc-strong (post Hunk A); --acc is for borders/links/focus-adjacent chrome, never as a fill behind text.
3. Every new color must be added to this file first, with computed contrast on its actual background(s).
4. Component reference `memory/designer/component-reference.html` must match this file after every merge (goal 8 / refreshed goal 5).
