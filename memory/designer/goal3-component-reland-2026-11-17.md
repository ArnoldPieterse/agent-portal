# Goal #3 — Component abstraction (re-land post-split)
Date: 2026-11-17
File: ui/app.css (non-pinned, safe to edit)

## Context
The original .panel-head / .btn-sm classes were added to index.html's inline <style> block
before the UI split (2026-11-16). After the split into ui/app.css + ui/core.js + ui/uploads.js,
those classes were lost. This pass re-lands all Goal #3 target classes into ui/app.css.

## What was added (appended to ui/app.css, line 225+)
| Class | Purpose | Variants |
|-------|---------|----------|
| .panel-head | Panel caption text | .no-mt modifier |
| .btn-sm | Small action button | hover state |
| .btn-primary | Primary CTA button | hover + active states |
| .badge-status | Status pill/badge | .ok / .warn / .err |
| .input-bar | Input container with child input styling | — |
| .status-dot | 8px status indicator circle | .ok / .warn / .err |

## New tokens added to :root (Goal #1 extension)
- --ok-bg: rgba(61,220,132,.12)
- --warn-bg: rgba(255,159,67,.12)
- --err-bg: rgba(255,107,107,.12)
- --dur-fast: 150ms
- --dur-med: 200ms

Token count: 23 → 28. All var() refs in component block resolve (verified by script).

## Still open for full closure
- Migrate 26 inline style= attrs in index.html to use these classes (requires pin advance)
- Grep verify zero style= on .panel-head / .btn-sm selectors after migration
- HTML line count reduction >=20% check

## Verification
- grep confirms all 6 class names present in ui/app.css
- All 12 var() token references resolve against :root (script-verified)
- File: 246 lines, 20.5 KB
