# Goal #6 Progress — Primary Button Contrast Fix (2026-11-18)

## Issue
Static WCAG AA audit (contrast-sweep-2026-11-15.md) identified 2 sub-AA failures:
- `#send`: white on var(--acc)=#4f8cff → 3.22:1 (FAIL, needs ≥4.5:1)
- `.btn.pri`: same pairing → 3.22:1 (FAIL)

Fix was specified in the sweep doc but never applied to ui/app.css.

## Fix Applied (this pass)
1. Added `--acc-deep:#2563eb` to :root token block (line 7)
2. Changed `#send` background from `var(--acc)` → `var(--acc-deep)` (line 66)
3. Changed `.btn.pri` background+border-color from `var(--acc)` → `var(--acc-deep)` (line 99)

## Verification
- White on #2563eb = **5.17:1** (PASS AA, even for small text)
- `--acc` retained for borders/focus/links/text-on-dark (no contrast impact there)
- No other element uses white text on `var(--acc)` as background

## Remaining for goal #6 closure
- Live-browser screenshot of all panels in dark mode (same blocker as goal #10: no browser in sandbox; logged in memory/ops/blockers.md)
- Check for invisible borders / unreadable text beyond contrast ratios (needs rendered view)

## Post-fix sweep (same pass)
Re-ran automated contrast check across all CSS rules declaring both `color` and `background`. Result: **zero sub-AA failures remain** after the --acc-deep fix. The only other match (.msg.you) is a border-color, not text.

## Anti-loop note
This is a NEW file change (3 lines modified in app.css) — not a re-probe of the screenshot blocker.
