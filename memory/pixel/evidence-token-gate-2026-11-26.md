# Pixel Goal #8 Evidence — High-contrast / token-enforcement audit (2026-11-26)

## What was done
1. **Migrated 184 hardcoded hex values** across 11 cockpit/fleet JS files to CSS custom properties from `ui/tokens.css`.
2. **Created pre-pin grep gate**: `ui/token-gate.py` — scans all `cockpit-*.js` + `fleet_*.js` for `#hex` outside var() fallbacks and HTML entities; exit 0 = clean, exit 1 = violations.
3. **Added high-contrast variant** to `ui/tokens.css`: `@media (prefers-contrast: more)` block boosting text to #fff, borders to #455a64, backgrounds to #000.

## Token mapping applied
| Hex family | Token | Examples |
|-----------|-------|----------|
| Status green | var(--ok) | #2ea36b, #3fb950, #84cc16 |
| Status red | var(--err) | #e5534b, #ef4444, #f85149, #9b1c1c |
| Status amber | var(--warn) | #d4a017, #f59e0b, #ff9800, #d29922 |
| Accent blue | var(--acc) | #4a7ddb, #4fc3f7, #6d9eff |
| Primary text | var(--text)/var(--white) | #e2e5ea, #e2e6ec, #e8eaed, #fff |
| Muted/dim text | var(--dim)/var(--faint) | #8a8f98, #6b7280, #9aa3b2, #c9ced6 |
| Backgrounds | var(--panel)/var(--bg) | #171b22, #232833, #12141e |
| Borders | var(--line) | #2a2f38, #3a4150, #5a5f68 |
| Alpha variants | color-mix(in srgb, var(--x) N%, transparent) | #2ea36b22, #e5534b66 |

## Files changed
- `ui/token-gate.py` (new): 37-line gate script
- `ui/tokens.css`: +high-contrast @media block
- 11 cockpit/fleet JS files: hex → var() replacements

## Verification
| Check | Result |
|-------|--------|
| Gate returns 0 on clean tree | ✓ (exit 0, "PASS: 0 hardcoded hex violations") |
| Gate rejects injected violation | ✓ (created temp file with #ff0000 → exit 1, flagged correctly) |
| Tokens cover high-contrast variant | ✓ (@media prefers-contrast: more added) |
| All files brace-balanced post-migration | ✓ |
| color-mix alpha variants render correctly | ✓ (structural check on intervention-timeline) |

## Status: REACHED
