# Goal 8 Progress - uploads.js icon wiring (2026-11-19)

## What was done
Replaced all 9 unicode emoji/symbol characters in ui/uploads.js with UI.icon()/UI.iconSized() calls:

| Line | Symbol | Replacement |
|---|---|---|
| L16 | U+2713 checkmark | UI.icon("check") |
| L16 | U+2717 cross | UI.icon("close") + text span |
| L17 | U+2715 x | UI.iconSized("close",14) |
| L131 | U+26A0 warning | UI.iconSized("alert",14) + text span |
| L155 | U+26A0 warning | UI.icon("alert") + text span |
| L156 | U+23F8 pause | UI.icon("stop") + text span |
| L160 | U+2713 checkmark | UI.iconSized("check",14) + "concluded" span |
| L170 | U+1F528 wrench emoji | UI.iconSized("wrench",14) + text span |
| L212 | U+23E9 fast-forward | UI.iconSized("play",14) + text span |
| L220 | U+26A0 warning | UI.icon("alert") + text span |

## Verification
- Braces/parens/brackets: balanced
- UI.icon*() call-sites in uploads.js: 0 -> 10
- Remaining problematic unicode symbols: 0
- File sha12: 23028b850421

## Impact on Goal 8 acceptance
- Part 1 (9+ SVG icons defined): PASS (22 icons, unchanged)
- Part 2 (used consistently across panels): IMPROVED - core.js=7, uploads.js=10, notifications.js=1 (total=18 real call-sites across 3 files)
- Part 3 (no emoji remain): uploads.js now clean; remaining non-ASCII in other files are encoding artifacts (mojibake em-dashes), not functional emoji

## File
ui/uploads.js (sha12=23028b850421)
