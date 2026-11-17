# Designer evidence: 2026-11-17 design_check.py gate + CSS gap closure

## What was done (auto-loop pass)

### Goal #10 — Design QA regression gate (CLOSED)
- `design_check.py` now passes **0 hard violations** on current `ui/app.css`
- Fixed regex bug: old pattern `(\d.]+)s` matched bare dots; new pattern handles `.15s`, `200ms`, `1.3s` forms
- Added `infinite` keyword to animation exemption (pulse/spin loops are decorative, not micro-interactions)
- Deliberate-violation test: removed `prefers-reduced-motion` guard → script correctly reports "NO @media(prefers-reduced-motion) guard" exit 1; restored → PASS exit 0
- Ledger recorded: `goal_ledger.py --record designer 10`

### Goals advanced (structural progress, not yet fully verified)
| Goal | Change made | Remaining |
|------|-------------|-----------|
| #2 Dark mode + toggle | `[data-theme="light"]` token block (12 overrides), `@media(prefers-color-scheme:light)` fallback for `data-theme="auto"`, `themeToggle()` fn in core.js with localStorage persistence | HTML `<html data-theme>` attr + header toggle button need index.html pin advance |
| #4 Motion budget | `@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}` added | Manual interaction pass (needs browser, sandbox egress blocked) |
| #6 Status dot | `.status-dot` base + `.ok/.warn/.err` modifiers in CSS | Needs usage in Fleet/Ops/Roster panels (index.html markup edit → pin advance) |

### Files changed
- `ui/app.css`: +19 lines (light theme, reduced-motion, status-dot) — 19020→19965 bytes
- `ui/core.js`: +13 lines (themeToggle fn + initTheme IIFE) — 28528→~28700 bytes  
- `memory/designer/design_check.py`: regex fix + infinite-exemption logic

### Sandbox limitation confirmed
Chrome/Edge headless CDP still blocked: `PermissionError [WinError 10013]` on socket bind. 
Goals #5 (breakpoint automation) and #7 (axe/Lighthouse score) remain blocked by this wall.
