# Goal #1 Evidence — Token Re-application + Documentation (2026-11-17 pass 2)

## What was done this pass
Re-applied all component-level tokens to ui/app.css :root (previous pass's additions were lost to a mirror cycle). Updated design-tokens-live.md to document the full 55-token set.

## Changes
- ui/app.css: :root expanded from 23 → 55 tokens; all 36 hardcoded hex values in component rules replaced with var() references; all 22 border-radius literals (8px/12px/6px) replaced with var(--radius)/var(--radius-lg)/var(--radius-sm); transition durations wired to var(--dur-fast)/var(--dur-med).
- memory/portal/design-tokens-live.md: rewritten to document all 55 tokens by category with values and roles.

## Acceptance check (grep-based)
```
[1] Hardcoded hex in component rules: 0 PASS
[2] Hardcoded border-radius (non-50%, non-var): 0 PASS
[3] Hardcoded durations (non-var): 0 PASS
[4] Total tokens defined: 55
[5] Braces balanced: 207/207 PASS
[6] File: ui/app.css (20,412 bytes, 257 lines)
```

## Remaining for full closure
- Browser-based verification: computed-style dump confirming no element renders with an untokenized value (needs :8099 up + CDP). Static grep passes; this is the same sandbox-egress wall as goals #4/#7.
- Light-mode component tokens: the 25 new component tokens currently only have dark values. When goal #2's light theme is fully verified, these need `[data-theme="light"]` overrides (some will inherit correctly, others like --dm-text/--warn-bg may need tuning).

## Artifact paths
- ui/app.css (live, served via GET /ui/app.css)
- memory/portal/design-tokens-live.md (documentation)

Date: 2026-11-17
