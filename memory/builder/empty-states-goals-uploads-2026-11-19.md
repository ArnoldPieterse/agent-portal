# Builder assist: Designer Goal #4 - Empty States (goals + uploads panels)
Date: 2026-11-19
Owner: Designer | Assisted by: Builder

## What was done
Wired `showEmptyState()` to two additional panels in `ui/uploads.js`:

1. **Uploads panel** (`filesList`, line 349): When `/api/uploads` returns an empty files array, the panel now shows a proper empty state (icon: "upload", CTA: Refresh → `filesLoad()`) instead of a bare `<li>` text node.
2. **Goals panel** (`goalsBody`, line 379): When `/api/goals` returns no agents, the panel shows an empty state (icon: "goal", CTA: Refresh → `goalsLoad()`) instead of a plain hint div.

Both use the `typeof showEmptyState==='function'` guard for safe degradation if core.js loads out of order.

## Verification
- Braces balanced: 268/268
- Parens balanced: 1070/1070
- Both panels already had working fallbacks; the new code is a strict upgrade (same behavior if showEmptyState unavailable)
- Fleet panel empty state was already wired (core.js line 444) in a prior pass

## Remaining for full Goal #4 closure
- Escalations panel: does not exist in index.html yet (no `escalations` element). Needs a new panel or the goal's scope should be updated.
- Acceptance test: "all 4 empty states render when API returns empty arrays; CTAs are clickable" - requires live browser session to confirm visual rendering + CTA click behavior.