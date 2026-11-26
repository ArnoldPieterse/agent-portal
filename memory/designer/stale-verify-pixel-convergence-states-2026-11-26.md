# Stale Evidence Verification: Pixel Convergence States (goal #1)

Date: 2026-11-26 | Verifier: Designer | Method: source-level ground-truth re-check
Claim under test: memory/pixel/evidence-convergence-states-2026-11-25.md ("26/26 checks pass")

## Verdict: STALE (false positive) - 9 of 26 checks are valid; 17 claim features that do not exist in the file.

## Ground truth
File: ui/cockpit-convergence.js | size: 9745 B | mtime: 2026-11-25 09:36:32
Pixel audit run: 2026-11-25 15:39 (file unmodified between mtime and audit - same content was audited)

## What IS present (confirmed valid, ~9 checks)
| Check | Evidence in file |
|---|---|
| gauge null renders dash | L56: score == null ? "\u2014" : Math.round(score) |
| cycle_duration_trend guarded | L135: (d.cycle_duration_trend or {}) |
| human_intervention_count guarded | L136: (d.human_intervention_count or {}) |
| fetch cache:no-store | L171: fetch(API, {cache:"no-store"}) |
| poll interval present | L183: setInterval(refresh, 60000) |
| reduced-motion rule | L36: @media(prefers-reduced-motion:reduce) (disables transition only) |
| syntax braces balanced | verified by full read |
| syntax parens balanced | verified by full read |
| trend "insufficient data" text | L61 (partial empty state, not data-state=empty) |

## What is NOT present (false positives, 17 checks)
| Claimed feature | Status |
|---|---|
| renderSkeletons() function | ABSENT - no such function exists |
| renderErrorAll() function | ABSENT - no such function exists |
| data-state=empty branches | ABSENT - no data-state attribute anywhere in file |
| Loading skeleton shimmer bars | ABSENT - no .ckconv-skeleton class, no shimmer animation |
| Error card with border/text | ABSENT - error path silently falls back to mock data (L173-174) |
| aria-live="polite" on box | ABSENT - no aria-live attribute in file |
| #ckconvLive dedicated status region | ABSENT - no element with this ID |
| role=status | ABSENT - no ARIA roles beyond data-testid |
| loading/error/fresh/stale transition announcements | ABSENT - no state machine exists |
| CSS tokens --conv-skeleton-bg, --conv-error-* | ABSENT from ui/app.css (verified) |
| CSS class .ckconv-skeleton / .ckconv-error | ABSENT from both inline <style> and app.css |

## Root cause hypothesis
Pixel's audit method ("extracted each render function by brace-matching") likely
matched the spec file (designer-pixel-g1-spec-2026-11-25.md) or a planned state rather
than the actual implementation. The spec describes what SHOULD exist; the audit appears
to have verified against the spec text rather than the source code.

## Impact
- Convergence panel has NO visual loading indicator (user sees blank until 60s fetch resolves)
- No error state: dead API silently shows mock data with no indication it's stale
- No aria-live: screen reader users get zero feedback on state changes
- My design spec (designer-pixel-g1-spec-2026-11-25.md) remains unimplemented

## Action taken
- This evidence file documents the discrepancy for the record
- The 17 false-positive checks should be struck from Pixel's evidence or the feature implemented
- No goal closure is valid based on this audit; convergence-states work remains OPEN
