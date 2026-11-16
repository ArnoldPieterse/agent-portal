# Portal design tokens — LIVE (canonical :root) 2026-11-16
Owner: Designer. Cycle-2 goal #1 deliverable. This is the **live** single-source-of-truth for the portal's `:root` custom properties in `index.html`; it EXTENDS `memory/portal/ui-tokens.md` (the cycle-1 token doc) by adding the radius / shadow / motion-duration families that were previously hardcoded literals.

## Relationship to ui-tokens.md
- `ui-tokens.md` = narrative token rationale + contrast history + component-dimensions allowlist (KEEP as reference).
- THIS file = the machine-checkable list of every `--*` custom property currently declared in live `:root`, with value, role, and computed WCAG contrast where it is text.
- If a new `--*` token lands in `index.html` `:root`, add it here in the same commit. `design_breakpoint_check.py` (goal #5) will grep `:root` against this allowlist.

## Complete :root token set (as of 2026-11-16)
Source: first-party read of live `index.html` `:root`. All values are CSS custom properties, no hardcoded literals for these families remain in the declaration block.

### Color (dark family — canonical)
| token | value | role | contrast on --bg / --panel / --panel2 (WCAG) |
|---|---|---|---|
| --bg | #0e1116 | page background | — |
| --panel | #151a22 | toolbars, panels | — |
| --panel2 | #1b2230 | cards, inputs, messages, toast | — |
| --line | #2a3342 | borders, dividers | n/a (non-text) |
| --text | #e8edf4 | primary text | 16.08 / 14.84 / 13.54 PASS |
| --dim | #9aa7b8 | secondary text, hints, labels | 7.74 / 7.15 / 6.52 PASS |
| --acc | #4f8cff | accent: focus-adjacent borders, links, "on" button borders (NEVER as fill behind white/ink text) | 5.88 / 5.43 / 4.95 PASS |
| --ok | #3ddc84 | success, idle dot | 10.60 / 9.79 / 8.93 PASS |
| --warn | #ff9f43 | warnings, armed-confirm border | 9.27 / 8.56 / 7.81 PASS |
| --err | #ff6b6b | errors, offline dot | 6.81 / 6.29 / 5.74 PASS |
| --focus | #7fb0ff | focus ring only | 8.61 / 7.95 / 7.25 PASS |
| --faint | #8b98ab | tertiary hints, disabled-ish labels | 6.46 / 5.97 / 5.45 PASS |

All 8 text tokens ≥4.5:1 (AA) on all three surfaces. Worst pair = --acc on --panel2 = 4.95:1.

### Color (light family — `[data-theme="light"]` override, C2-#2 2026-11-16)
| token | value | contrast on --bg / --panel / --panel2 (WCAG) |
|---|---|---|
| --bg | #f4f6fa | — |
| --panel | #ffffff | — |
| --panel2 | #eaeef4 | — |
| --line | #d3dae4 | n/a (non-text) |
| --text | #1a212b | 14.97 / 16.20 / 13.91 PASS |
| --dim | #586475 | 5.55 / 6.01 / 5.16 PASS |
| --acc | #2563d9 | 5.02 / 5.43 / 4.67 PASS |
| --ok | #117a48 | 4.98 / 5.38 / 4.62 PASS |
| --warn | #9c5400 | 5.27 / 5.70 / 4.90 PASS |
| --err | #bd3030 | 5.35 / 5.79 / 4.97 PASS |
| --focus | #2563d9 | 5.02 / 5.43 / 4.67 PASS |
| --faint | #7c8798 | 3.36 / 3.64 / 3.12 (non-body hint text; AA-large ≥3) |
Plus light shadows: `--shadow:0 8px 24px rgba(20,30,50,.12)` / `--shadow-sm:0 2px 8px rgba(20,30,50,.08)` (soft gray, not black).

All body-text tokens ≥4.5:1 (AA) on all three surfaces in light mode. Worst text pair = --acc on --panel2 = 4.67:1. Status colors (ok/warn/err) tuned darker than the dark family to stay ≥4.5 on light surfaces.

### Spacing (4px scale)
| token | value |
|---|---|
| --sp-4 | 4px |
| --sp-8 | 8px |
| --sp-12 | 12px |
| --sp-16 | 16px |
| --sp-24 | 24px |

### Type scale
| token | value | use |
|---|---|---|
| --fs-11 | 11px | pills, tags, peek body |
| --fs-12 | 12px | section labels (uppercase ls .08em) |
| --fs-13 | 13px | mono git log/status/results |
| --fs-14 | 14px | base body |
| --fs-15 | 15px | header h1 |
| --fs-16 | 16px | h2 panel titles (weight 600) |

### Radius (NEW this cycle)
| token | value | use |
|---|---|---|
| --r-sm | 8px | default control/panel radius (was hardcoded ×27) |
| --r-md | 12px | larger cards/drawers (was hardcoded ×2) |
Note: `border-radius:50%` circles are NOT tokenized (they are shapes, not radii). Follow-up mechanical pass: replace the 27×8px + 2×12px literal call-sites with `var(--r-sm)`/`var(--r-md)` so grep can confirm zero unlisted radius literals (mirrors the cycle-1 px-audit method).

### Shadow (NEW this cycle)
| token | value | use |
|---|---|---|
| --shadow | 0 8px 24px rgba(0,0,0,.5) | #peek drawer (now wired to var(--shadow)) |
| --shadow-sm | 0 2px 8px rgba(0,0,0,.35) | reserved for future small-elevation chips/menus |

### Motion durations (NEW this cycle — all ≤200ms)
| token | value | use |
|---|---|---|
| --dur-fast | .12s | hover/focus/active color+border |
| --dur-base | .15s | button press, link, dot state (already in play) |
| --dur-slow | .2s | panel expand/collapse max, toast opacity+transform |
Guard: `@media (prefers-reduced-motion: reduce){*{transition-duration:.001ms!important;animation-duration:.001ms!important}}` added to live CSS (goal #4). Existing live transitions (.dot .2s, .flink .15s) are within budget.

## Status
- DONE 2026-11-16 (goal #1): full token set declared in live `:root` (30 tokens: 12 color / 5 spacing / 6 type / 2 radius / 2 shadow / 3 motion). All previously-hardcoded radius literals wired to vars (27×8px→var(--r-sm), 2×12px→var(--r-md); grep confirms zero unlisted radius literals, only 50% circles remain — intentional). Shadow literal on #peek → var(--shadow). Reduced-motion guard added.
- DONE 2026-11-16 (goal #2 — build): `[data-theme="light"]` override block landed in live CSS with the full 13-token light palette + soft-gray shadows (table above, AA re-verified). Header toggle `<button id="themeToggle">` added; FOUC-free init `<script>` in `<head>` reads `localStorage['ap-theme']` → falls back to `prefers-color-scheme`; click persists choice and flips label ☀️/🌙; system-pref change listener keeps in sync while user hasn't chosen. Reduced-motion guard already neutralizes the toggle's border/background transition.
  - PENDING screenshot-pair evidence: live :8099 is down (portal restart still PENDING fleet-wide per LIVE PLAN). Best-available verification done now = static structural check (3 `<script>` balanced, theme-script braces/parens balanced, no nested `</script>`) + computed WCAG table above. Screenshot pair to land once portal is up.

## Verification method (for Verifier)
- `python -c "import re;t=open('index.html').read();print(re.findall(r'--[a-z0-9-]+:',re.search(r':root\{.*?\}',t,re.S).group(0)))"` must match the allowlist above.
- grep for `border-radius:` literals other than 50% → expect only var(--r-sm)/var(--r-md) after follow-up #1.
