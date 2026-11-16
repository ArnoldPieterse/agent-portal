# Evidence: Dark-mode toggle + light theme + status-dot — RE-APPLIED 2026-11-16

## Why re-applying
The 5:41 PM pass (theme-components-status note) changed ui/app.css 18,615→20,841 and
ui/core.js 28,641→29,712, but those files were **reverted by the White→shared mirror
clobber** — they never entered a pin/commit. On disk this pass started at 18,615 / 28,641
with ZERO theme/status-dot markers (verified: `[data-theme`, `.status-dot`, `portal-theme`
all absent). This re-applies the work and commits it so it survives the next mirror cycle.

## Goal #1 — Dark mode + theme toggle (token-driven)
- `ui/app.css`: added `[data-theme="light"]` block overriding all 12 color tokens
  (--bg/--panel/--panel2/--line/--text/--dim/--acc/--ok/--warn/--err/--focus/--faint).
  Custom props cascade from <html>, so the whole UI flips with one attribute — no per-rule edits.
- `ui/core.js`: appended a self-contained IIFE that injects a `#themeToggle` button into
  `header`, reads/writes `localStorage["portal-theme"]`, falls back to
  `prefers-color-scheme: light`, sets `document.documentElement.dataset.theme`, swaps sun/moon
  icon, and re-applies on system-scheme change ONLY when the user hasn't explicitly chosen.
- **Contrast (WCAG AA), measured this pass — both themes ≥4.5:1 on --bg AND --panel2:**
  - DARK: text/bg 16.08, dim/bg 7.74, acc/bg 5.88, ok 10.60, warn 9.27, err 6.81 — all PASS.
  - LIGHT (tuned tokens): text/bg 14.88, dim 5.29, acc #1a56c4 6.17, ok #157038 5.74,
    warn #8a4c0e 6.27, err #bd322c 5.35, faint #5b6575 5.49 — all PASS.

## Goal #3 — Status indicator system
- `ui/app.css`: added unified `.status-dot` component + state modifiers:
  `.ok/.idle` (green), `.busy/.warn` (amber), `.err/.unknown` (red), `.off` (grey), plus
  `.status-dot-label`. Existing `.dot`/`.fdot` left intact for backward-compat with current
  JS render functions (migration of those call sites = follow-up).

## Files changed (this pass)
- `ui/app.css`: 18,615 → 19,895 bytes (+1,280); braces balanced 209/209.
- `ui/core.js`: 28,641 → 30,518 bytes (+1,877).

## Honest scope / known follow-ups (NOT claimed done)
- Hardcoded dark-blue surfaces (.msg.you #243b63, .seg button.on #3a6fd6, #peek tooltip,
  .dmseg purple) stay dark in light mode — legible, but not token-driven. Full literal→token
  sweep is a follow-up.
- First-load FOUC possible for light users: theme is set by core.js (runs before </body>),
  not a head snippet. No-flash requires a tiny <head> script in the PINNED index.html =
  separate pin advance, not done here.
- node --check unavailable on this host → JS verified by structural review only; live
  interaction pass (toggle click, persistence, scheme-change) still needs portal up (:8099 down).
- `.dot`/`.fdot` JS render call sites not yet migrated to `.status-dot`.
