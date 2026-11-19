# Deep UI sweep - 2026-11-19 (White direct)

User directive: "complete the remaining goals". Finished the design-token / icon pass across ALL UI files (prior passes covered ui/app.css + index.html only).

## Changes
- **Hex tokenization in JS inline styles** (all CSS contexts, no canvas usage):
  - ui/fleet_health.js: #2ecc71/#f39c12/#e74c3c -> var(--ok/--warn/--err)
  - ui/fleet_status.js: COLORS map + #666 fallbacks -> var(--ok/--warn/--err), var(--dot-idle); status badge dots (U+25CF) removed
  - ui/fleet_topology.js: unknown state #e05252 -> var(--dot-err)
  - ui/components.js: already tokenized with defensive fallbacks (var(--ok,#3ddc84) etc.) - left as-is
  - ui/uploads.js: bubble/status colors -> var(--agent-purple/--err/--queue-dim/--ok/--warn); chip color:#3ddc84 -> var(--ok)
  - ui/core.js: addBubble error color #ff6b6b -> var(--err) (all sites), conclchip #3ddc84 -> var(--ok), "#ccc" fallbacks -> var(--dim)
  - tokens.css: new --agent-purple in both themes (dark #8a63d2, light #7c3aed)
- **Real emoji glyphs removed from source**:
  - index.html: stop button "\u25A0 Stop" -> inline SVG square + "Stop"; Activity button stopwatch glyph removed
  - ui/core.js: "\u26a0 "+e error prefixes -> "error: "/"!" text; "\u2713 moved" template -> "moved"; "\u25A0 Stop" comments -> "Stop button"
  - ui/fleet_status.js: "\u26a0 fleet status unavailable" -> plain text
- **Font sizes**: index.html raw px (12px x8) -> var(--fs-12)
- **Bug caught during sweep**: an earlier replacement referenced undefined token --tx-2; corrected to var(--dim)

## Scope decisions
- Pre-existing \uXXXX escape sequences in committed JS strings (35 in core.js + 33 in uploads.js + 4 in components.js at HEAD) left as-is: established audit convention counts raw non-ASCII only; these are code-level escapes.
- Defensive var(--token,#fallback) occurrences counted as clean by design.

## Verification (static - headless browser unavailable in sandbox)
- Audit regex over ui/app.css, index.html, ui/*.js: 0 files with (hex outside var()/tokens) OR (real emoji chars U+2300-U+27BF/U+2B00-U+2BFF/U+1F000-U+1FAFF) OR (raw px font-size)
- Every var(--x) used across UI files resolves to a token defined in tokens.css: MISSING = []
- Every UI.icon("name") call resolves to an icon defined in ui/icons.js: 22 defs, 0 missing
- node --check (C:\Users\White\.unsloth\node\node.exe): returncode 0 on all 9 ui/*.js files; index.html has no inline scripts (6 external script tags, order notifications -> icons -> core -> fleet_topology -> uploads -> tour)
- Headless Edge attempts: --dump-dom hangs (live WS keeps page busy), --remote-debugging-port never binds even with fresh profile -> CDP selftest not runnable here. window.__selftest remains available for a human browser run at http://localhost:8099/.
