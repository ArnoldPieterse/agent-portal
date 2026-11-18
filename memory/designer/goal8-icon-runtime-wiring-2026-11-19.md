# Goal #8 (Icon System) — concrete step: runtime icon API + activity-timeline wiring
Date: 2026-11-19 | Owner: Designer | Status: PROGRESS (not closed)

## What landed this pass
Goal #8 acceptance test: "9+ SVG icons defined in ui/icons.js; used consistently across panels; no emoji remain."
The real gap found: `UI.icon()` existed in ui/icons.js but that file is NOT loaded by the pinned
index.html shell (only core.js / fleet_topology.js / uploads.js are), so the icon system was dead
code at runtime. The only live icon source was a 4-icon emptyState-only IIFE inside core.js exposing
`window.emptyState` (no general `icon()` API).

Concrete changes (all in UNPINNED files — index.html untouched, no pin advance needed):
1. ui/icons.js — added 5 event icons (play, tool, stop, book, save); file set now 17 outline icons,
   all 24x24 viewBox / 1.5px stroke / currentColor.
2. ui/core.js — upgraded the inline IIFE from emptyState-only to the RUNTIME canonical icon system:
   full 16-icon path set + `window.UI.icon(name,{size,cls})` + `window.UI.iconNames`, with
   `window.emptyState` kept for backward compat (uploads.js / goal #4 reuse unchanged).
3. ui/core.js — activity-timeline event markers now use the icon system: `actIcons` maps each event
   to an icon name (start->play, tool->tool, end->check, blocked->stop, error->warning,
   aborted->stop, readmem->book, storemem->save); actRender() builds a `.ai` marker span via
   UI.icon(...) with a safe "•" fallback if the API is absent. Replaces the prior emoji map
   (▶ 🔧 ✓ ⛔ ⚠ ■ 📖 💾).
4. ui/app.css — added `.aev .ai{display:inline-flex;align-items:center;flex:none;line-height:1}` +
   `.aev .ai svg{vertical-align:-2px}` so the 14px marker aligns on the baseline row.

## Evidence
- Static: core.js braces/parens balanced; `window.UI.icon`, `function icon(`, actIcons map all present.
  (Global bracket count shows +1 — pre-existing regex char-class noise e.g. `[&<>]`/`[\w./\\-]`, not from these edits.)
- Runtime: fixture memory/designer/goal8-icon-fixture-2026-11-19.html inlines the ACTUAL core.js IIFE
  and renders all 16 icons + all 8 timeline markers; render_html succeeded with no JS error.

## Still open (why NOT closed)
- "used consistently across panels" — only the activity timeline is wired to UI.icon so far. Other
  panels still use text/emoji UI chrome: ops panel ⚙/✕/✓/⚠ glyphs (renderAgents g/x buttons, opsSay),
  collapsible chevron ▾/▸ in components.js, goal-blocked ⚠ span in uploads.js.
- "no emoji remain" — agent-identity `a.emoji` (user-configured avatars from agents.json) are data, not
  UI chrome; the remaining UI-chrome glyphs listed above still need migration to UI.icon().

Next step: migrate the ops-panel button/status glyphs + collapsible chevron to window.UI.icon(), then
re-run the fixture across all panels for closure.
