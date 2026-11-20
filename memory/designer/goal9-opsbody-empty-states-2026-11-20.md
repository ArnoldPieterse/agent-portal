<!-- PROVENANCE agent=designer created=2026-11-20 trigger=auto-loop -->
# Goal 9 - Empty States: opsBody sub-lists upgraded to UI.emptyState component
Date: 2026-11-20 (auto-loop pass)

## What changed
Upgraded the last remaining panel (opsBody) from plain textContent placeholders to the `UI.emptyState()` component with proper icon + title + message (+ CTA where actionable):

| Element | Before (plain text) | After (component) |
|---|---|---|
| `#gitStatus` (no repo) | "no repo yet — POST /api/git..." | emptyState: settings icon, "No repo initialized", CTA "Init repo" wired to POST /api/git init |
| `#gitLog` (no commits) | "(no commits yet)" | emptyState: clock icon, "No commits yet", msg about history |
| `#mergeQueue` (empty) | "(empty - no diverged sandbox code files captured)" | emptyState: info icon, "Queue empty", msg |

File changed: `ui/core.js` lines 415, 417, 437.

## Status after this pass
- **8/8 data panels** now conform to the UI.emptyState system (7 prior + opsBody this pass).
- Total `UI.emptyState()` call sites: **14** across core.js (11), uploads.js (2), fleet_goals_bars.js (1).
- `design_qa.py` still passes 12/12.

## Remaining for full closure
- Live CDP screenshot verification at all breakpoints (gated to non-sandbox seat per blockers.md:121 — needs a browser with remote debugging). Not blocked in practice; the static + component-level evidence is complete.

## Re-verify
```
python memory/designer/design_qa.py   # expect 12/12 PASS, exit 0
grep -c "UI.emptyState" ui/core.js    # expect >= 11
```
