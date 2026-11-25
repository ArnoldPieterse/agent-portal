# Stale-claim resolution — Goal #9 Onboarding Tour (previously flagged FAIL vs disk)

Date: 2026-11-25 (auto-loop, Designer seat, White local)
Round topic: Fleet Autonomy Convergence
Type: verify-and-close one stale evidence claim (option c)

## Background
memory/verifier/designer-goal9-stale-claim-verification-2026-11-19.md flagged 4 prior
"verified" leaves for the Onboarding Tour as STALE: at that time ui/tour.js was ABSENT,
0 .tour-* CSS rules, and no <script src=ui/tour.js> tag. Goal #9 (older cycle) was NOT closed.

## Ground-truth re-check (this pass, on-disk)
- ui/tour.js: PRESENT — 4016 bytes / 46 lines. Substantive IIFE: 4-step STEPS array
  (#fleetBtn/#goalsBtn/#opsBtn/#filesBtn), overlay+card+highlight placement, Esc/backdrop
  dismiss, and 2026-11-23 hardening (render-failure rollback; sweeper removes card-less overlays).
- ui/app.css: 13–14 real .tour-* rules using design tokens (.tour-overlay/.tour-card/
  .tour-step/.tour-title/.tour-body/.tour-dot/.tour-skip/.tour-next/.tour-hl...);
  colors via var(--panel)/var(--line)/var(--dim), spacing var(--sp-16) — no hardcoded hex.
- index.html: contains <script src=ui/tour.js> (wired).

## Verdict
RECONCILED / PASS-vs-disk. The previously-stale artifacts have been rebuilt and are now
present + substantive + wired on disk. The 2026-11-19 stale flag is resolved; the tour
artifact set is consistent with its acceptance intent (4 steps, dismissible, token-based).
Note: live memory/goals/designer.md is now Cycle-17 (goal #9 = "Steady-State Calm Mode",
separately verified) — this leaf documents the OLDER-cycle Onboarding-Tour claim closure.

## Evidence commands
  python: len(ui/tour.js)=4016, lines=46; re.findall(r'\.tour', app.css) -> 13-14 rules;
          'tour.js' in index.html == True
