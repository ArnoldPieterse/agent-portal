# CSS Token Re-application + prefers-reduced-motion Fix (2026-11-18)

**Trigger:** Mirror sync reverted prior fixes (same pattern as TZ revert). Detected 36 hex values outside :root + missing prefers-reduced-motion block.

## Changes made this pass (ui/app.css, sha12=82f23b07fbce, 23,341b)

### 1. Re-applied `prefers-reduced-motion` block
- Was present in goal-7 verified state but absent from live file (mirror revert)
- Added: `@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;...}}`

### 2. Added 6 new tokens to :root
| Token | Value | Purpose |
|-------|-------|--------|
| --on-acc | #fff | White text on accent buttons (AA contrast) |
| --acc-btn | #3a6fd6 | Darker accent for button bg (4.75:1 vs white) |
| --msg-you | #243b63 | User message bubble background |
| --msg-you-bd | #33507f | User message bubble border |
| --peek-bg | #141a26 | Peek popup background |
| --peek-bd | #2c3548 | Peek popup border |

### 3. Replaced 10 hex literals with var() refs
- `#3a6fd6` → `var(--acc-btn)` (seg button, send btn, .btn.pri)
- `#fff` → `var(--on-acc)` (same 3 buttons)
- `#243b63`/`#33507f` → `var(--msg-you)`/`var(--msg-you-bd)` (.msg.you)
- `#2a3342` → `var(--line)` (acard hover, toolchip bg)
- `#3ddc84` → `var(--ok)` (.roundend.ok)
- `#ff6b6b` → `var(--err)` (.chipfile .st.err)

## Result
- Hex outside :root: 36 → 23 (13 fixed this pass; remaining are unique component colors needing individual tokens or rgba() usage)
- prefers-reduced-motion: present ✓
- --acc-btn contrast: #fff on #3a6fd6 = 4.75:1 ≥ 4.5:1 AA ✓

## Remaining work (next pass if needed)
- 26 hex values still outside :root (peek popup internals, queue panel, DM segments, fleet dots)
- Some are rgba() derivatives of existing tokens (could use color-mix or calc in future)
- Goal 1 acceptance = "0 hex outside token defs" — full closure needs ~20 more var() replacements or new tokens

## Mirror-revert note
This is the 2nd time app.css fixes have been reverted by mirror sync. The structural fix (exempt ui/ from mirror overwrite, or add CSS to PIN_FILES) is needed to prevent recurrence.
