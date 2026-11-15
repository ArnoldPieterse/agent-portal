# Goal 5 (Keyboard) — enhancement block LANDED & verified
Date: 2026-11-15 (AUTO-CONTINUE 2/3)

## What was in-flight vs already done
- Base criteria (Enter send / Shift+Enter newline / sane tab order) were ALREADY on disk before this turn:
  - `$("input").addEventListener("keydown",…)` → Enter sends, Shift+Enter newline (index.html, script block 2).
  - `$("gitMsg").addEventListener("keydown",…)` → Enter commits in Ops panel.
  - No explicit tabindex attrs → natural source-order tabbing. (See keyboard-microinteraction-evidence-2026-11-15.md.)
- The prior hot note said I had "began implementing enhancement block" for 3 ADDITIONAL a11y gaps that were NOT yet in index.html: **focus-on-open**, **Escape-close**, **initial-focus**. This turn finished and landed them.

## Change applied (index.html)
1. CSS — suppress the region outline so the focus ring stays on the first control inside an opened panel:
   `#actPanel:focus,#fleetPanel:focus,#opsPanel:focus,#filesPanel:focus,#goalsPanel:focus{outline:none}`
2. JS — appended IIFE before `</script>`:
   - Maps 5 accordion panels to their toggle buttons: actBtn/fleetBtn/opsBtn/filesBtn/goalsBtn → *Panel.
   - **focus-on-open**: sets `tabindex="-1"` on each panel (defensive, only if absent) + a MutationObserver on the `class` attr; when `.open` is added it calls `panel.focus({preventScroll:true})`. Keeps keyboard context inside the region without hijacking a specific control or causing scroll jumps.
   - **Escape-close**: document keydown `Escape` → ignores while the `<dialog id="editor">` is open (dialog closes itself natively); otherwise closes the topmost `.open` panel and returns focus to its toggle button.
   - **initial-focus**: on `load` (or immediately if already complete), focuses `#input` unless the editor dialog is open — lands keyboard users in the chat composer.
   - All programmatic focus uses `{preventScroll:true}` + try/catch → cannot throw (protects Goal 9 zero-console).

## Verification (on disk this turn)
- div balance: **78 / 78 BALANCED** (matches prior "divs balanced" note).
- Appended IIFE in isolation: braces 23/23, parens 54/54, brackets 9/9 — **all OK**, correctly terminated `})();`.
- Whole-file paren/bracket off-by-one from a naive string-stripper is a FALSE POSITIVE caused by pre-existing regex literals (e.g. `const re=/\[DM\b\s*@?\s*([^\]\n]+?)\s*\]/gi;`) that the checker misparsed as code tokens — NOT introduced by this change.
- node --check unavailable on host (node not installed); structural checks above are the available evidence.

## Status / residual
- Code COMPLETE + static-verified. Live manual tab-through / Escape / focus-on-open in a real browser remains a **Verifier leg** (no browser/node in sandbox; outbound blocked) — same pattern as Goals 2/3 screenshot legs.
