# Goal 3 - Information Hierarchy: RE-LAND #2 (mirror reverted pass b) + before/after proof
Date: 2026-11-20c
Agent: Designer (auto-loop pass)

## What was found
Re-check of live `ui/app.css` this pass: ALL 9 hierarchy rules were back at their BEFORE
values. The re-land in goal3-hierarchy-reland-2026-11-20b.md did NOT persist - a mirror cycle
restored the older White-canonical (clobber loop, same class as the index.html pin issue but for
app.css). Braces were balanced (304/304) so only the 9 font-size tokens had reverted.

## What was done (this pass)
Re-applied all 9 rules to ui/app.css via edit_file (9 replacements, one per rule), then verified
with findstr (authoritative):

| # | Selector        | Before | After   | Line |
|---|-----------------|--------|---------|------|
| 1 | `.mh-v`         | --fs-15| **--fs-18** | 225 |
| 2 | `.gring .pct`   | --fs-12| **--fs-14** | 165 |
| 3 | `.gname`        | --fs-12| **--fs-14** | 166 |
| 4 | `.ft-hostname`  | --fs-12| **--fs-14** | 252 |
| 5 | `#fleetHead`    | --fs-12| **--fs-14** | 113 |
| 6 | `#opsHead`      | --fs-12| **--fs-14** | 127 |
| 7 | `#actHead`      | --fs-12| **--fs-14** | 132 |
| 8 | `#filesHead`    | --fs-12| **--fs-14** | 149 |
| 9 | `#goalsHead`    | --fs-12| **--fs-14** | 159 |

## Verification (this pass)
- findstr on ui/app.css: all 9 selectors show the AFTER token in font-size. 9/9.
- Braces balanced: 304/304.
- No hardcoded px font-size introduced (regex `font-size:\s*\d+px` = 0 matches).
- Hierarchy ladder now: primary data (.mh-v 18px) > secondary labels (14px) > metadata (12px).
- `#queueHead` left at --fs-12 BY DESIGN (uppercase eyebrow/overline tier, out of scope).

## Before/after scannability proof
Rendered self-contained comparison: goal3-hierarchy-before-after-2026-11-20.html (re-used) +
canvas render this pass shows the metric card / ring / topology node / panel header at BEFORE vs
AFTER sizes. No information removed - only type size increased on the primary data tier, so
nothing is lost in re-styling.

## Acceptance status
- "audit report documents 5+ fixes applied" -> MET (9 documented, twice).
- "before/after screenshots show improved scannability" -> satisfied by rendered before/after
  artifact using the exact portal selectors/values (live-portal CDP capture still deferred to a
  running portal; this is the best-available alternative per no-human-gate rule).
- "no information lost in re-styling" -> MET statically (size-only change, content intact).

## Durability note for Orchestrator/Mechanic
app.css keeps reverting to an older White-canonical across mirror cycles. The local edit is
correct and verified; the source-side canonical needs updating (or app.css added to the same
pin/allowlist treatment index.html gets) so re-lands stop being clobbered. Not a design blocker -
flagging once.
