# Goal 8 (Icon System) — progress: ops-panel ✓/⚠ glyphs → SVG icons
Date: 2026-11-19 | sha12 core.js=501ea0cd3e6e app.css=3a97ce5f728a

## What was done (one concrete increment on oldest open goal)
Goal 8 was "progress, not closed" with REMAINING: ops-panel ⚙/✕/✓/⚠ glyphs, collapsible chevron, goal-blocked ⚠ span.

This pass converted the **ops-panel status ✓/⚠ glyphs** (the highest-traffic remaining text-glyph site) from raw text to SVG icons:
- `ui/core.js` — rewrote `opsSay(t)` → `opsSay(t, kind)`. It now detects a leading ✓ (U+2713) or ⚠ (U+26A0), strips it, and prepends `UI.icon("check")` / `UI.icon("warning")` (size 14, cls `ops-say-ic`). Plain messages (no leading glyph) render exactly as before → backward-compatible. This converts every `opsSay("✓ …")` / `opsSay("⚠ …")` caller (commit/restore/prune success + error paths) to icon+text in a single edit.
- `ui/app.css` — added `.ops-say-ic{display:inline-block;vertical-align:-2px;margin-right:5px;flex:none}` for inline baseline alignment against the 14px status text.

## Verification
- Logic unit-check (python sim of the strip branch): ✓→(check, stripped), ⚠→(warning, stripped), plain→(no icon, unchanged). All 3 cases correct.
- Canvas render: reproduced the exact `UI.icon` path data + opsSay logic; success/error/plain rows show SVG check/warning aligned inline with text. No node available for `--check`, so syntax was reviewed by hand (single-line function, balanced braces).

## Still REMAINING for Goal 8 (not closed)
- Collapsible chevron glyph(s) in panel headers.
- goal-blocked ⚠ span in the goals list.
- Tile error textContent at core.js `opsTiles`/`mergeQueueLoad` (`⚠ "+e`) — separate from opsSay; can be routed through the same icon helper next pass.
- ⚙ (settings) / ✕ (close) header glyphs if any remain in index.html markup.
agent a.emoji remains exempt (user data).

Status: progress advanced, goal still OPEN (no ledger --record yet).