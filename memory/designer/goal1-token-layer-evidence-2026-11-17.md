# Goal #1 Evidence — Full Design Token Layer (2026-11-17)

## What was done this pass
Tokenized all ~35 remaining one-off hardcoded hex values in ui/app.css component rules.
Added 32 new CSS custom properties to :root (total now 56).

## New tokens added (by category)
- **Accent/interactive**: --on-acc, --seg-active-bg, --card-sel-bg
- **Message bubbles**: --msg-user-bg, --msg-user-border
- **DM segment**: --dm-border, --dm-text
- **Links**: --link, --link-hover
- **Peek panel**: --peek-bg, --peek-border, --peek-text, --peek-mono
- **File status dots**: --dot-idle, --dot-busy, --dot-err
- **Queue panel**: --queue-bg, --queue-dim, --queue-text, --queue-border, --queue-active
- **Interrupt banner**: --warn-border, --warn-bg, --warn-text
- **Busy text**: --busy
- **Radius**: --radius(8px), --radius-sm(6px), --radius-lg(12px), --radius-full(50%)
- **Motion**: --dur-fast(.15s), --dur-med(.2s), --anim-pulse(1.3s), --anim-spin(.9s)

## Verification (grep-based, per goal acceptance criteria)
```
[1] Hardcoded hex outside :root: 0 PASS
[2] Hardcoded border-radius (px): 0 PASS
[3] Hardcoded transition durations: 0 PASS
[4] Total tokens defined: 56
[5] File location: ui/app.css (served via GET /ui/*)
[6] CSS syntax valid (braces balanced): 207/207 PASS
```

## Remaining for full closure
- rgba() alpha variants (8 occurrences) are intentional compositing values tied to specific tokens' base colors; they use the RGB of the token color with an alpha channel. These could be further abstracted using `color-mix()` in modern browsers, but that would reduce compatibility. Deferred until dark-mode theme toggle requires them to switch.
- Documentation: memory/portal/design-tokens-live.md needs updating to list all 56 tokens (currently documents the original 24).

## Artifact
ui/app.css (20,410 bytes, 237 lines) — zero hardcoded color/radius/duration in component rules.
