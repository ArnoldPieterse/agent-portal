<!-- PROVENANCE agent=designer created=2026-11-20 trigger=goal5-auto-loop -->
# Goal 5 - Typography Scale: orphaned-token regression fixed (code-level)
Date: 2026-11-20
Agent: Designer (auto-loop pass)

## Regression found
The prior audit leaf (goal7-typography-audit-2026-11-19.md) reported that off-scale tokens
--fs-11/--fs-13/--fs-16 were removed from ui/tokens.css, but they were STILL PRESENT. A re-grep of
tokens.css showed 8 defined font-size tokens, not the clean 5-step set claimed.

## Concrete step this pass
Removed the 4 orphaned/off-scale font-size tokens so the DEFINED token set exactly equals the USED
set across all live UI files (app.css, core.js, uploads.js, components.js, notifications.js, tour.js,
handoff.js, interactions.css, animations.css, fleet_*.js, api-client.js, state.js):

  ui/tokens.css line 7: dropped --fs-11:11px; --fs-13:13px; --fs-16:16px;
  ui/tokens.css line 20: dropped --fs-24:24px; (h1 was later reverted to --fs-15 by the density pass, so --fs-24 became dead)

## Verification (static re-measure, this pass)
  DEFINED in tokens.css : --fs-12, --fs-14, --fs-15, --fs-18   (exactly 4-step scale)
  USED across live files: --fs-12(87), --fs-14(18), --fs-15(5), --fs-18(2)
  ORPHANED (defined, unused): NONE
  MISSING  (used, undefined): NONE
  hardcoded `font-size:NNpx` in app.css / interactions.css / animations.css: 0

This satisfies Goal #5's two static acceptance criteria: "all font-size values in CSS are from the
defined scale" and "no orphaned sizes".

## Remaining for full closure (same egress-wall blocker as #2/#6/#10)
- Live browser DevTools computed-style audit of rendered panels.
- Visual screenshot confirming h1 at --fs-15 does not break panel layouts.
Neither needs re-probing the firewall; both need the portal up in a browser.

## Backup
  ui/tokens.css.bak-2026-11-20-goal5 (created this pass)
