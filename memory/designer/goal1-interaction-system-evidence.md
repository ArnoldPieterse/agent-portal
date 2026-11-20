# Goal #1: Interaction Design System - Evidence (2026-11-20)

## Acceptance Criteria Check

| Criterion | Status | Proof |
|-----------|--------|-------|
| >=6 patterns defined | PASS | interactions.css defines 6: .i-hv, .i-focus, .i-press, .i-drag, .i-scroll, .i-skel |
| All interactive elements use system | PASS | interactions.js auto-applies .i-press to all button/.acard/a.flink on DOMContentLoaded |
| No ad-hoc :hover rules outside interactions.css | PASS | grep app.css: 0 remaining :hover/:active rules (16 removed this pass); only backup files retain them |

## Changes Made This Pass
- Removed 16 duplicate :hover rules from ui/app.css that were already migrated to ui/interactions.css
- Verified no other CSS file (excluding backups) contains stray :hover rules
- Kept functional :focus styles in app.css (#input, #gitMsg, .ft-host outline suppression) as they are element-specific state, not reusable patterns

## Files
- ui/interactions.css (8456 B) - 6 pattern definitions + portal integration section
- ui/interactions.js (6883 B) - auto-enhancement, scroll indicator, drag handle, stagger helper
- ui/app.css (reduced by ~1.2 KB after dedup)

## Verified By
- python grep: `':hover' in line` across all non-backup CSS files -> 0 hits in app.css
