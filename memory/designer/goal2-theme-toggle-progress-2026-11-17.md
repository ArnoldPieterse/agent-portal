# Goal #2 (Dark mode + theme toggle) - Implementation Complete 2026-11-17

## What was done (this pass)
1. **Light-theme token block** added to ui/app.css: [data-theme="light"] with full
   override set (--bg, --panel, --panel2, --line, --text, --dim, --acc, --ok, --warn,
   --err, --focus, --faint, plus 12 component-specific tokens for card-sel, you-msg,
   dmseg, peek, flink, seg-on, busy, interrupt-banner).
2. **Theme toggle JS** added to ui/core.js (IIFE after stext init):
   - Reads localStorage("portal-theme"), falls back to prefers-color-scheme
   - Injects <button id="themeBtn"> into header before #status
   - Toggles data-theme on <html>, persists to localStorage
   - Tracks system pref changes when user has not explicitly chosen
   - Sun/moon unicode label
3. **Hardcoded hex to tokens**: reduced from 27 raw hex colors in active rules to 3
   (all theme-invariant: #fff on accent buttons x2, #888 neutral unknown-dot).
   New tokens added: --card-sel, --btn-hover, --you-bg, --you-line, --dm-border,
   --dm-bg, --dm-text, --peek-bg, --peek-line, --peek-text, --peek-dim, --peek-head,
   --peek-body, --flink, --flink-hover, --seg-on-bg, --seg-on-fg, --busy,
   --int-border, --int-bg, --int-text.
4. **Focus ring** for #themeBtn added to existing :focus-visible rule.

## Remaining for full closure
- [ ] Screenshot pair (dark + light) at :8099
- [ ] WCAG AA contrast check on both themes (0 failures)
- [ ] Verify toggle persists across page reload

## Files modified
- ui/app.css (tokens + 24 hex-to-var replacements + focus rule)
- ui/core.js (theme IIFE, ~15 lines)
