# Goal 8 - Icon System: Emoji/Symbol Sweep Progress (2026-11-19)

## Work done this pass
Replaced 3 non-ASCII symbols in editable files:
| File | Line | Before | After |
|------|------|--------|-------|
| ui/core.js | 426 | `↩ restore` (button label) | `Restore` |
| ui/core.js | 449 | `item(s) → TODO_completed.md` | `item(s) to TODO_completed.md` |
| ui/uploads.js | 328 | comment: `↻ only (no polling)` | `refresh only (no polling)` |

## Verification
- Brace/paren balance: core.js OK, uploads.js OK
- Re-scan: **3 remaining**, all in pinned index.html (L37 ↺, L42 ↻, L73 ↻)

## Remaining for full closure
- Advance index.html pin to replace 3 arrow symbols with SVG icons or text labels
- Acceptance: "no emoji remain" = 0 non-ASCII symbols in all UI files
