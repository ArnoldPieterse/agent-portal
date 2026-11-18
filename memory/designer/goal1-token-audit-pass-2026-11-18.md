# Designer Goal 1 - Token Audit Gap Closure (2026-11-18)

## Result: PASS

## What was done
- Replaced all 36 hardcoded hex color values in component rules with var() references.
- Added 22 new design tokens to the :root block, organized by component domain:
  - Panel/selection: --panel-sel, --acc-strong, --on-acc
  - Messages: --msg-you-bg, --msg-you-border
  - DM segments: --dm-border, --dm-text
  - Links: --link, --link-hover
  - Peek panel: --peek-bg, --peek-border, --peek-text, --peek-body
  - Fleet dots: --dot-off, --dot-busy, --dot-err
  - Queue: --queue-dim, --queue-text
  - Spinner: --spin-track, --spin-fill
  - Banner: --banner-warn-bd, --banner-warn-bg, --banner-warn-tx

## Verification
Grep all hex values outside :root block = 0 hits. Acceptance test passes.

## File changed
- ui/app.css (tokens added to :root, 36 replacements in component rules)
