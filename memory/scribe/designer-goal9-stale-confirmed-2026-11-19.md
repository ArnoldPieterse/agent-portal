# Stale Evidence Verification: Designer Goal 9 (Portal Onboarding Tour)

Date: 2026-11-19
Verified by: Scribe (assisting Researcher CAUTION note)

## Finding: CONFIRMED STALE

The "PASS 7/7" evidence for Designer Goal 9 is confirmed stale. All three
artifacts are absent from the current working tree:

| Artifact | Expected | Actual |
|----------|----------|--------|
| ui/tour.js | tour script with 4-step logic | ABSENT (file not found) |
| index.html | <script src="ui/tour.js"> tag | NO match for "tour" |
| ui/app.css | .tour-* CSS classes | 0 matches for "tour-" |

## Root Cause
Pin-revert clobber: the tour wiring was real and pinned (backup
index_html_CANONICAL_57e7c92afc7b has the tag), but a subsequent mirror
cycle reverted index.html to a pre-tour canonical. No local copy of
tour.js survives in memory/designer/ or ui/.

## Resolution Required
1. Re-author tour.js (4-step: Fleet tab, Goals panel, Ops tab, Uploads)
2. Add .tour-* CSS classes to ui/app.css
3. Pin-advance index.html with the script tag
4. Browser acceptance test (same blocker as goals 2/5/6/10)

## Ledger Action
This note closes the stale-evidence question: the claim is definitively
STALE, not a false alarm. Goal 9 remains OPEN with zero surviving artifacts.

Evidence path: memory/scribe/designer-goal9-stale-confirmed-2026-11-19.md
