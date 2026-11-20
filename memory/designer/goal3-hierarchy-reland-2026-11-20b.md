# Goal 3 - Information Hierarchy: 9 rules RE-LANDED durably
Date: 2026-11-20b
Agent: Designer (auto-loop pass)

## What was wrong
The previous static pass (goal3-hierarchy-audit-2026-11-20.md) reported the 9 fixes applied,
but a re-check of live `ui/app.css` this pass found ALL 9 rules still held their BEFORE values
(the earlier edit did not persist to the local tracked file). The before/after fixture's closing
note flagged the same: edits reverted, re-land pending.

## What was done (this pass)
Re-applied all 9 hierarchy rules directly to `ui/app.css` via edit_file, then verified in-file:

| # | Selector | Before | After |
|---|----------|--------|-------|
| 1 | `.mh-v`              | --fs-15 | **--fs-18** (metric value dominates card) |
| 2 | `.gring .pct`       | --fs-12 | **--fs-14** (ring % > meta) |
| 3 | `.gname`            | --fs-12 | **--fs-14** (goal name label) |
| 4 | `.ft-hostname`      | --fs-12 | **--fs-14** (topology node primary label) |
| 5 | `#fleetHead`        | --fs-12 | **--fs-14** (section header >= body) |
| 6 | `#opsHead`          | --fs-12 | **--fs-14** |
| 7 | `#actHead`          | --fs-12 | **--fs-14** |
| 8 | `#filesHead`        | --fs-12 | **--fs-14** |
| 9 | `#goalsHead`        | --fs-12 | **--fs-14** |

## Verification (this pass)
- All 9 after-value rules present in ui/app.css: regex check 9/9 OK.
- Braces balanced: 300/300.
- No off-scale font-size introduced (all values are defined tokens).
- `#queueHead` left at --fs-12 BY DESIGN: it is a text-transform:uppercase + letter-spacing
  eyebrow/overline label, a different visual tier from the 5 panel section headers. Not in scope.
- Hierarchy ladder now consistent: primary data (mh-v 18px) > secondary labels (14px) > metadata (12px).

## Durability
`ui/app.css` is in the git allowlist and is pushed White-canonical on hash mismatch by
memory_mirror.py, so this local edit becomes the new canonical and propagates to remotes on the
next mirror cycle. Dated canonical backup: `app_css_CANONICAL_a4162b770b57_2026-11-20b.css`.

## Remaining for full closure (documented, NOT re-probed)
- Live before/after screenshots at the running portal + visual confirmation that .mh-v at 18px
  does not overflow small metric cards. This is the same browser/portal-running blocker already
  reconciled in goal3-hierarchy-before-after-2026-11-20.html (fixture renders the intended values;
  live QA deferred to human's browser). Acceptance test not yet fully met -> goal NOT marked verified.
