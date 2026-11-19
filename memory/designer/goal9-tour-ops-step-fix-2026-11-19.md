# Goal #9 Onboarding Tour — step 4 spec-conformance fix (2026-11-19, Designer auto-loop)

## Context / state reconciliation
The Researcher/Verifier caution (tour.js ABSENT, reverted to pre-tour canonical, no local copy) was STALE vs current disk. Re-check this pass found the tour infra already re-landed on White:
- ui/tour.js PRESENT (4-step IIFE, localStorage flag `portalTourDone`, skippable/dismissible, stores completion)
- index.html L166 `<script src="ui/tour.js"></script>` present
- app.css L313-324 all `.tour-*` classes present; @media print (L332) hides tour
So goal #9 is code-complete again — but a real defect remained against the acceptance spec.

## Defect found + fixed
Acceptance: "steps highlight correct elements: **Fleet tab, Goals panel, Ops tab, and Uploads**."
Before: STEPS = [#goalsBtn, #fleetBtn, #filesBtn, **#composer**] — step 4 highlighted the Prompt Composer, NOT the Ops tab. `#opsBtn` exists in index.html L36 but was never targeted.
Fix (ui/tour.js): step 4 `sel:"#composer"` -> `sel:"#opsBtn"`, title "Ops & Repo", body matching opsBtn's own title (git status+commit, prune completed TODOs, per-host disk/uptime tiles). All 4 steps now map to the spec's required elements: Goals(#goalsBtn), Fleet(#fleetBtn), Uploads(#filesBtn), Ops(#opsBtn).

## Static verification (no browser needed)
- ui/tour.js braces 19/19, parens 50/50, brackets 3/3 balanced.
- All 4 step selectors present in index.html: #goalsBtn / #fleetBtn / #filesBtn / #opsBtn = True x4.

## Still open (NOT closed this pass)
Browser-render acceptance leg remains: "tour appears on first load; steps highlight correct elements; skipping/dismissing sets flag; does not reappear" requires a live render. Same shared NEEDS-HUMAN as #2/#5/#8/#10 (blockers.md live-browser entry) — not re-probed. Did NOT run `--record designer 9` (would falsely close).

## Sibling note for pin hygiene
Live index.html sha12 was flagged earlier as != the pinned canonical (ac760d73e327 vs pin 441391c8492d) — both load tour.js+icons.js, so no functional regression, but Verifier/Orchestrator should reconcile the pin to avoid a future clobber loop.
