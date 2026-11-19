# Goal 8 - last rendered icon-glyph removed (core.js restore button)

Date: 2026-11-19 (Designer auto-loop pass)

## What was done
- ui/core.js L426: the "↩ restore" queue-restore BUTTON used a literal U+21A9 arrow as an icon-in-text.
  Replaced with `UI.iconSized('reset',13)` (SVG, 1.5px stroke) via string concatenation:
    >'+UI.iconSized('reset',13)+' restore</button>
- `reset` key confirmed present in ui/icons.js ICONS map; UI.iconSized() is null-safe (returns '' if missing).

## Why this is the right target (not the other two stray glyphs)
Measured all non-ASCII icon-ish chars across live files:
- core.js:426  ↩  -> rendered button label = REAL icon-as-text. FIXED this pass.
- core.js:449  →  -> inside opsSay() status MESSAGE string ("moved N section(s) → TODO_completed.md").
                     Legit inline log text, NOT an icon; replacing would break the sentence. Left as-is.
- uploads.js:326 ↻ -> inside a code COMMENT (`// ... load-on-open + ↻ only (no polling) ...`). Never rendered. Left as-is.

## Static verification (post-edit)
- Rendered icon-glyphs remaining in core.js = 0 (only the legit log-text → remains).
- index.html icon-ish non-ASCII = 0; uploads.js = 0 rendered (↻ is a comment).
- ui/icons.js script tag IS loaded in live index.html (script order: notifications, icons, core, fleet_topology, uploads, tour).
- core.js UI.icon() call-sites = 6, UI.iconSized() = 2 (was 1; +1 this pass).
- Structural balance (raw): () 950/950, {} 267/267 both balanced. [] raw 85/86 is a false positive -
  code-only bracket count (strings/comments stripped) = [ 18 / ] 18 balanced; the extra ] sits in a string literal.

## Goal 8 acceptance status
- Part 1 (9+ SVG icons defined): PASS (24 icons).
- Part 3 (no emoji/icon-glyph remain in rendered UI): now PASS for static scan - last rendered glyph removed.
- Part 2 (used consistently across panels): core.js wires roster/activity/ops via UI.icon*; uploads panel uses
  static inline SVG in index.html (consistent set, authored inline). 
- FULL closure still needs the browser-render leg (live DOM check that no glyph renders + icons appear) -
  same NEEDS-HUMAN blocker as #2/#5/#9/#10, already logged in memory/ops/blockers.md. NOT re-probed this pass.

## Note: index.html pin drift (flagged for Verifier/Orchestrator)
Live index.html sha12 = ac760d73e327 but PIN_FILES in memory_mirror.py still records 441391c8492d.
Both versions load ui/icons.js, so this does not affect Goal 8 - but the pin is stale and a mirror cycle
would revert live to the backup. No edit made to index.html this pass (only ui/core.js, which is NOT pinned).
